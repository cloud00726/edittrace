///|
fn meta() -> String {
  "{\"kind\":\"meta\",\"schema_version\":1,\"position_encoding\":\"utf-16\",\"capture_mode\":\"fragment\",\"provenance\":\"synthetic\",\"producer\":\"tests\"}"
}

///|
fn started(text : String, version~ : Int32 = 1) -> Session {
  let s = Session::new()
  s.feed_line(meta(), 1)
  s.feed_line(open_record(1, text, version), 2)
  s
}

///|
fn open_record(seq : Int32, text : String, version : Int32) -> String {
  "{\"kind\":\"message\",\"seq\":" +
  seq.to_string() +
  ",\"direction\":\"client_to_server\",\"message\":{\"jsonrpc\":\"2.0\",\"method\":\"textDocument/didOpen\",\"params\":{\"textDocument\":{\"uri\":\"file:///test\",\"languageId\":\"test\",\"version\":" +
  version.to_string() +
  ",\"text\":" +
  Json::string(text).stringify() +
  "}}}}"
}

///|
fn changed(seq : Int32, version : Int32, changes : String) -> String {
  "{\"kind\":\"message\",\"seq\":" +
  seq.to_string() +
  ",\"direction\":\"client_to_server\",\"message\":{\"jsonrpc\":\"2.0\",\"method\":\"textDocument/didChange\",\"params\":{\"textDocument\":{\"uri\":\"file:///test\",\"version\":" +
  version.to_string() +
  "},\"contentChanges\":" +
  changes +
  "}}}"
}

///|
fn code(s : Session) -> Int32 raise {
  @model.int_field(s.report(), "exit_code")
}

///|
test "batch failure is atomic and full replacement restores known state" {
  let s = started("abc")
  s.feed_line(
    changed(
      2, 2, "[{\"text\":\"should rollback\"},{\"range\":{\"start\":{\"line\":0,\"character\":2},\"end\":{\"line\":0,\"character\":1}},\"text\":\"!\"}]",
    ),
    3,
  )
  assert_eq(s.docs["file:///test"].content, "abc")
  assert_eq(s.snapshot("file:///test"), None)
  assert_eq(code(s), 2)
  s.feed_line(changed(3, 5, "[{\"text\":\"restored\"}]"), 4)
  assert_eq(s.snapshot("file:///test"), Some("restored"))
  assert_eq(code(s), 1)
}

///|
test "unopened changes remain unresolved and later open repairs baseline" {
  let s = Session::new()
  s.feed_line(meta(), 1)
  s.feed_line(changed(1, 4, "[{\"text\":\"x\"}]"), 2)
  assert_eq(code(s), 2)
  s.feed_line(open_record(2, "baseline", -7), 3)
  assert_eq(s.snapshot("file:///test"), Some("baseline"))
  assert_eq(code(s), 1)
}

///|
test "version gaps and negative versions are valid; regression taints" {
  let s = started("a", version=-10)
  s.feed_line(changed(2, -3, "[{\"text\":\"b\"}]"), 3)
  assert_eq(code(s), 0)
  s.feed_line(changed(3, -4, "[{\"text\":\"wrong\"}]"), 4)
  assert_eq(code(s), 2)
  assert_eq(s.docs["file:///test"].content, "b")
}

///|
test "duplicate open does not overwrite, closed generations restart" {
  let s = started("first")
  s.feed_line(open_record(2, "wrong", 2), 3)
  assert_eq(s.docs["file:///test"].content, "first")
  assert_eq(code(s), 2)
  s.feed_line(
    "{\"kind\":\"message\",\"seq\":3,\"direction\":\"client_to_server\",\"message\":{\"jsonrpc\":\"2.0\",\"method\":\"textDocument/didClose\",\"params\":{\"textDocument\":{\"uri\":\"file:///test\"}}}}",
    4,
  )
  assert_eq(s.snapshot("file:///test"), None)
  s.feed_line(open_record(4, "second", -2), 5)
  assert_eq(s.docs["file:///test"].generation, 2)
  assert_eq(s.snapshot("file:///test"), Some("second"))
  assert_eq(code(s), 1)
}

///|
test "unknown state suppresses cascading increments" {
  let s = started("🌙")
  let incremental = "[{\"range\":{\"start\":{\"line\":0,\"character\":1},\"end\":{\"line\":0,\"character\":1}},\"text\":\"!\"}]"
  s.feed_line(changed(2, 2, incremental), 3)
  s.feed_line(changed(3, 3, incremental), 4)
  s.feed_line(changed(4, 4, incremental), 5)
  assert_eq(s.findings.length(), 2)
  assert_eq(code(s), 2)
}

///|
test "checkpoint mismatch is evidence, not state repair or taint" {
  let s = started("actual")
  s.feed_line(
    "{\"kind\":\"checkpoint\",\"seq\":2,\"uri\":\"file:///test\",\"version\":1,\"text\":\"expected\",\"source\":\"manual\"}",
    3,
  )
  assert_eq(s.snapshot("file:///test"), Some("actual"))
  assert_eq(code(s), 1)
  assert_eq(
    @model.field(s.findings[0], "classification"),
    Json::string("external_checkpoint"),
  )
}

///|
test "invalid shapes and null range stop, not truncate or continue" {
  for
    bad in [
      changed(2, 2, "[{\"range\":null,\"text\":\"x\"}]"),
      changed(
        2, 2, "[{\"range\":{\"start\":{\"line\":0,\"character\":-1},\"end\":{\"line\":0,\"character\":0}},\"text\":\"x\"}]",
      ),
      "{\"kind\":\"checkpoint\",\"seq\":2.5}",
      "{broken",
      "{\"kind\":\"other\",\"seq\":2}",
    ] {
    let s = started("a")
    s.feed_line(bad, 3)
    assert_eq(s.is_stopped(), true)
    assert_eq(code(s), 2)
    assert_eq(s.snapshot("file:///test"), Some("a"))
  }
}

///|
test "document and finding limits are real failures" {
  let s = Session::new(max_document_bytes=2)
  s.feed_line(meta(), 1)
  s.feed_line(open_record(1, "你好", 1), 2)
  assert_eq(s.is_stopped(), true)
  assert_eq(code(s), 2)
  let s = Session::new(max_findings=1)
  s.feed_line(meta(), 1)
  s.feed_line(changed(1, 2, "[{\"text\":\"x\"}]"), 2)
  s.feed_line(changed(2, 3, "[{\"text\":\"x\"}]"), 3)
  assert_eq(s.findings.length(), 1)
  assert_eq(s.is_stopped(), true)
}

///|
test "warning threshold and note exemption" {
  let s = started("abc")
  s.feed_line(
    changed(
      2, 2, "[{\"range\":{\"start\":{\"line\":0,\"character\":9},\"end\":{\"line\":0,\"character\":9}},\"text\":\"!\"}]",
    ),
    3,
  )
  assert_eq(@model.int_field(s.report(fail_warning=true), "exit_code"), 0)
  assert_eq(s.snapshot("file:///test"), Some("abc!"))
}
