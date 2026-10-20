///|
test "immutable baseline, stable inserts and Unicode" {
  let p = fn(c) { @text.Position::{ line: 0, character: c, } }
  inspect(
    @edit_plan.apply("A🌙B", [
      { start: p(3), end: p(4), new_text: "C", },
      { start: p(0), end: p(1), new_text: "long", },
    ]),
    content="long🌙C",
  )
  inspect(
    @edit_plan.apply("ab", [
      { start: p(1), end: p(1), new_text: "X", },
      { start: p(1), end: p(1), new_text: "Y", },
      { start: p(1), end: p(2), new_text: "Z", },
    ]),
    content="aXYZ",
  )
}

///|
test "overlap and surrogate middle refuse partial result" {
  let p = fn(c) { @text.Position::{ line: 0, character: c, } }
  let rejected = try {
    let _ = @edit_plan.apply("abc", [
      { start: p(0), end: p(2), new_text: "x", },
      { start: p(1), end: p(2), new_text: "y", },
    ])
    false
  } catch {
    _ => true
  }
  inspect(rejected, content="true")
  let surrogate = try {
    let _ = @edit_plan.apply("🌙", [
      { start: p(1), end: p(1), new_text: "x", },
    ])
    false
  } catch {
    _ => true
  }
  inspect(surrogate, content="true")
}
