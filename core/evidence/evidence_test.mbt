///|
test "sharing rejects unknown fields and retains source rather than replacing literals" {
  let lines = [
    @model.canonical({
      "kind": "meta",
      "schema_version": 1,
      "position_encoding": "utf-16",
      "capture_mode": "fragment",
      "provenance": "synthetic",
      "producer": "test",
    }),
    @model.canonical({
      "kind": "message",
      "seq": 1,
      "direction": "client_to_server",
      "message": {
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
          "textDocument": {
            "uri": "file:///private",
            "version": 1,
            "languageId": "text",
            "text": "file:///private",
          },
        },
      },
    }),
    @model.canonical({
      "kind": "checkpoint",
      "seq": 2,
      "uri": "file:///private",
      "version": 1,
      "text": "expected",
      "source": "manual",
    }),
  ]
  let id = "ET009_CHECKPOINT_MISMATCH:2:-1:0"
  let (output, preview) = @evidence.share(lines, id)
  assert_true(output[1].contains("file:///private"))
  assert_true(output[1].contains("file:///edittrace/document-1"))
  assert_eq(@model.field(preview, "source_text_retained"), Json::boolean(true))
  let (small, stats) = @evidence.minimize(lines, id, 1)
  assert_eq(small, lines)
  assert_eq(@model.field(stats, "attempts"), @model.num(0))
}
