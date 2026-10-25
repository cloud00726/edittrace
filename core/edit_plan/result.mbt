///|
/// Typed alternative to raising apply. Existing API remains available.
pub(all) enum EditResult {
  Applied(String)
  Rejected(String)
}

///|
pub fn evaluate(baseline : String, edits : Array[Edit]) -> EditResult {
  Applied(apply(baseline, edits)) catch {
    e => Rejected(e.to_string())
  }
}
