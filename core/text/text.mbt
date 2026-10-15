///|
pub(all) struct Position {
  line : Int32
  character : Int32
}

///|
pub(all) struct Offset {
  value : Int32
  clamped : Bool
}

///|
pub suberror EditError {
  LineUnreplayable
  SurrogateBoundary
  Reversed
}

///|
pub fn position(j : Json) -> Position raise @model.InputError {
  @model.object(j)
  {
    line: @model.uint_field(j, "line"),
    character: @model.uint_field(j, "character"),
  }
}

// UTF-16 offsets. CRLF is a single line ending; retain the final empty line.

///|
pub fn line_ranges(s : String) -> Array[(Int32, Int32)] {
  let lines = []
  let mut start = 0
  let mut i = 0
  while i < s.length() {
    let c = s.at(i).to_int()
    if c == 13 || c == 10 {
      lines.push((start, i))
      if c == 13 && i + 1 < s.length() && s.at(i + 1).to_int() == 10 {
        i = i + 1
      }
      i = i + 1
      start = i
    } else {
      i = i + 1
    }
  }
  lines.push((start, s.length()))
  lines
}

///|
pub fn offset(s : String, p : Position) -> Offset raise EditError {
  let lines = line_ranges(s)
  if p.line < 0 || p.line >= lines.length() || p.character < 0 {
    raise LineUnreplayable
  }
  let (start, end) = lines[p.line]
  let len = end - start
  let value = start + (if p.character > len { len } else { p.character })
  if value > 0 && value < s.length() {
    let a = s.at(value - 1).to_int()
    let b = s.at(value).to_int()
    if a >= 0xD800 && a <= 0xDBFF && b >= 0xDC00 && b <= 0xDFFF {
      raise SurrogateBoundary
    }
  }
  { value, clamped: p.character > len, }
}

///|
pub fn replace(
  s : String,
  start : Position,
  end : Position,
  insert : String,
) -> (String, Offset, Offset) raise EditError {
  if start.line > end.line ||
    (start.line == end.line && start.character > end.character) {
    raise Reversed
  }
  let a = offset(s, start)
  let b = offset(s, end)
  if a.value > b.value {
    raise Reversed
  }
  (s[:a.value].to_owned() + insert + s[b.value:].to_owned(), a, b)
}
