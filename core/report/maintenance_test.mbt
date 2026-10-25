///|
test "summary rejects malformed status and incomplete remains incomplete" {
  let incomplete : Json = {
    "kind": "case_report",
    "analysis_complete": false,
    "exit_code": 2,
  }
  assert_true(@report.summary(incomplete).contains("INCOMPLETE"))
  assert_true(
    @report.summary({
      "kind": "case_report",
      "analysis_complete": true,
      "exit_code": 0,
    }).contains("declared expectations"),
  )
  let rejected = try {
    let _ = @report.summary({ "exit_code": 0 })
    false
  } catch {
    _ => true
  }
  assert_true(rejected)
}

///|
test "junit separates input errors from assertions without raw source disclosure" {
  let r : Json = {
    "kind": "suite_report",
    "cases": [
      { "name": "a<&\"🌙", "exit_code": 0 },
      { "name": "failure", "exit_code": 1, "failures": ["SECRET SOURCE"] },
      { "exit_code": 2, "error": "SECRET PATH" },
    ],
  }
  let xml = @report.junit(r)
  assert_true(xml.contains("failures=\"1\" errors=\"1\""))
  assert_true(xml.contains("&lt;&amp;&quot;🌙"))
  assert_false(xml.contains("SECRET"))
}
