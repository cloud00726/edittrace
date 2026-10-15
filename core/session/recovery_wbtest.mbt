///|
test "change after close remains explicitly unresolved until a new open" {
  let s = started("first")
  s.feed_line(
    "{\"kind\":\"message\",\"seq\":2,\"direction\":\"client_to_server\",\"message\":{\"jsonrpc\":\"2.0\",\"method\":\"textDocument/didClose\",\"params\":{\"textDocument\":{\"uri\":\"file:///test\"}}}}",
    3,
  )
  s.feed_line(changed(3, 3, "[{\"text\":\"unowned\"}]"), 4)
  assert_eq(code(s), 2)
  s.feed_line(open_record(4, "new", -1), 5)
  assert_eq(s.docs["file:///test"].generation, 2)
  assert_eq(s.snapshot("file:///test"), Some("new"))
  assert_eq(code(s), 1)
}
