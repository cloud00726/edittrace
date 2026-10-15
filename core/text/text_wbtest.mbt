///|
test "UTF16 and independent hand-calculated examples" {
  let p = Position::{ line: 0, character: 3, }
  assert_eq("A🌙B".length(), 4)
  let (s, _, _) = replace("A🌙B", p, { line: 0, character: 4, }, "C")
  assert_eq(s, "A🌙C")
  let (s, _, _) = replace(
    "abc",
    { line: 0, character: 0, },
    { line: 0, character: 0, },
    "X",
  )
  let (s, _, _) = replace(
    s,
    { line: 0, character: 1, },
    { line: 0, character: 2, },
    "A",
  )
  assert_eq(s, "XAbc")
}

///|
test "line endings, empty trailing line and clamp" {
  assert_eq(line_ranges("").length(), 1)
  assert_eq(line_ranges("a\r\nb\rc\n"), [(0, 1), (3, 4), (5, 6), (7, 7)])
  assert_eq(offset("abc", { line: 0, character: 99, }).value, 3)
  assert_eq(offset("abc", { line: 0, character: 99, }).clamped, true)
  let (s, _, _) = replace(
    "a\r\nb",
    { line: 0, character: 1, },
    { line: 1, character: 0, },
    "",
  )
  assert_eq(s, "ab")
  let (s, _, _) = replace(
    "\ne\u{0301}\n",
    { line: 1, character: 2, },
    { line: 1, character: 2, },
    "\r",
  )
  assert_eq(line_ranges(s).length(), 3)
  assert_eq(offset(s, { line: 2, character: 0, }).value, s.length())
}

///|
test "surrogate interior, reversed and invalid line policies" {
  let caught = try {
    let _ = offset("🌙", { line: 0, character: 1, })
    false
  } catch {
    SurrogateBoundary => true
    _ => false
  }
  assert_eq(caught, true)
  let caught = try {
    let _ = offset("", { line: 1, character: 0, })
    false
  } catch {
    LineUnreplayable => true
    _ => false
  }
  assert_eq(caught, true)
  let caught = try {
    let _ = replace(
      "ab",
      { line: 0, character: 2, },
      { line: 0, character: 1, },
      "",
    )
    false
  } catch {
    Reversed => true
    _ => false
  }
  assert_eq(caught, true)
}
