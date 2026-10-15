///|
test "strict integer boundaries and no fractional truncation" {
  assert_eq(integer(Json::number(-2147483648.0)), -2147483648)
  assert_eq(integer(Json::number(2147483647.0)), 2147483647)
  for n in [1.5, 2147483648.0, -2147483649.0] {
    let rejected = try {
      let _ = integer(Json::number(n))
      false
    } catch {
      _ => true
    }
    assert_eq(rejected, true)
  }
}

///|
test "nesting guard ignores structural characters inside quoted strings" {
  let source = Json::string("[".repeat(100) + "\\\"{}").stringify()
  assert_eq(parse_bounded(source), Json::string("[".repeat(100) + "\\\"{}"))
  let rejected = try {
    let _ = parse_bounded("[".repeat(65) + "0" + "]".repeat(65))
    false
  } catch {
    _ => true
  }
  assert_eq(rejected, true)
}

///|
test "canonical JSON is stable for different object insertion orders" {
  let a = Json::object({ "z": num(1), "a": num(2) })
  let b = Json::object({ "a": num(2), "z": num(1) })
  assert_eq(canonical(a), canonical(b))
}
