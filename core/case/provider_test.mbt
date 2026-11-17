///|
test "candidate actual must agree with the text compared to the reviewed baseline" {
  let inconsistent : Json = {
    "schema_version": 3,
    "kind": "provider_observation",
    "name": "different-observations",
    "expected": [{ "path": "a", "uri": "file:///a", "text": "approved" }],
    "observed": [{ "path": "a", "uri": "file:///a", "text": "approved" }],
    "verification": {
      "kind": "edit_plan",
      "plan": {
        "schema_version": 1,
        "kind": "edit_plan",
        "position_encoding": "utf-16",
        "source": {},
        "documents": [{ "uri": "file:///a", "version": 1, "text": "candidate" }],
        "workspace_edit": {
          "documentChanges": [
            {
              "textDocument": { "uri": "file:///a", "version": 1 },
              "edits": [],
            },
          ],
        },
        "actual": [{ "uri": "file:///a", "text": "candidate" }],
      },
    },
  }
  let rejected = try {
    let _ = @case.check_provider(inconsistent)
    false
  } catch {
    @model.InputError(message) =>
      message == "edit actual text and host observation disagree"
    _ => false
  }
  assert_true(rejected)
}
