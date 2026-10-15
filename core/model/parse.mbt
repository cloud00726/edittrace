// Count structural nesting outside JSON strings before calling the standard parser.

///|
pub fn parse_bounded(raw : String) -> Json raise {
  let mut depth = 0
  let mut quoted = false
  let mut escaped = false
  for c in raw {
    if quoted {
      if escaped {
        escaped = false
      } else if c == '\\' {
        escaped = true
      } else if c == '"' {
        quoted = false
      }
    } else if c == '"' {
      quoted = true
    } else if c == '{' || c == '[' {
      depth = depth + 1
      if depth > 64 {
        raise InputError("JSON nesting depth exceeds 64")
      }
    } else if c == '}' || c == ']' {
      depth = depth - 1
    }
  }
  @json.parse(raw)
}
