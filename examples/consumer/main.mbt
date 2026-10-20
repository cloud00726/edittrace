///|
fn main {
  let original = "A🌙B"
  let edits : Array[@edit_plan.Edit] = [{
    start: @text.Position::{line: 0, character: 3},
    end: @text.Position::{line: 0, character: 4},
    new_text: "C",
  }]
  let actual = @edit_plan.apply(original, edits) catch { _ => panic() }
  assert_eq(actual, "A🌙C") catch { _ => panic() }
  let expected = @case.FindingExpectation::{rule_id: "EP001_VERSION_MISMATCH", uri: None, seq: None}
  assert_true(@case.matches_finding({"rule_id":"EP001_VERSION_MISMATCH"}, expected)) catch { _ => panic() }
  println(actual)
}
