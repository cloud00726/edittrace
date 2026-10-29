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
  assert_true(match @edit_plan.evaluate(original, edits) { Applied(s) => s == "A🌙C"; Rejected(_) => false }) catch { _ => panic() }
  let expected = @case.FindingExpectation::{rule_id: "EP001_VERSION_MISMATCH", uri: None, seq: None}
  assert_true(@case.matches_finding({"rule_id":"EP001_VERSION_MISMATCH"}, expected)) catch { _ => panic() }
  println(actual)
  let records : Array[Json] = [
    {"kind":"meta","schema_version":1,"position_encoding":"utf-16","capture_mode":"fragment","provenance":"synthetic","producer":"consumer"},
    {"kind":"message","seq":1,"direction":"client_to_server","message":{"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":"file:///consumer","version":1,"languageId":"text","text":"actual"}}}},
    {"kind":"checkpoint","seq":2,"uri":"file:///consumer","version":1,"text":"expected","source":"consumer-explicit"},
  ]
  let (shared,_) = @evidence.share(records.map(@model.canonical),"ET009_CHECKPOINT_MISMATCH:2:-1:0") catch {_=>panic()}
  assert_true(shared.length()==3) catch {_=>panic()}
}
