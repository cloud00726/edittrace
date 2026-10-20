///|
pub(all) struct FindingExpectation {
  rule_id : String
  uri : String?
  seq : Int32?
}

///|
pub fn matches_finding(finding : Json, expected : FindingExpectation) -> Bool {
  @model.field(finding, "rule_id") == Json::string(expected.rule_id) &&
  (match expected.uri {
    Some(uri) => @model.field(finding, "uri") == Json::string(uri)
    None => true
  }) &&
  (match expected.seq {
    Some(seq) => @model.field(finding, "seq") == @model.num(seq)
    None => true
  })
}

///|
pub fn run(case : Json) -> Json raise {
  if @model.int_field(case, "schema_version") != 1 ||
    @model.string_field(case, "kind") != "case" {
    raise @model.InputError("unsupported case schema")
  }
  let name = @model.string_field(case, "name")
  @model.object(@model.field(case, "source"))
  let input = @model.field(case, "input")
  let expect = @model.field(case, "expect")
  @model.only_fields(expect, [
    "exit_code", "analysis_complete", "findings", "absent_rules", "texts",
  ])
  let expected_exit = @model.int_field(expect, "exit_code")
  if expected_exit < 0 || expected_exit > 2 {
    raise @model.InputError("invalid expected exit")
  }
  let expected_complete = @model.field(expect, "analysis_complete")
  if expected_complete != Json::boolean(true) &&
    expected_complete != Json::boolean(false) {
    raise @model.InputError("explicit analysis_complete expectation required")
  }
  let session = @session.Session::new()
  let input_kind = @model.string_field(input, "kind")
  let requested : Map[Int32, Array[String]] = Map([])
  let snapshots : Map[Int32, Map[String, String]] = Map([])
  if @model.has(expect, "texts") {
    for wanted in @model.array(@model.field(expect, "texts")) {
      @model.only_fields(wanted, ["uri", "text", "at_seq"])
      let uri = @model.string_field(wanted, "uri")
      let _ = @model.string_field(wanted, "text")
      if @model.has(wanted, "at_seq") {
        if input_kind != "trace" {
          raise @model.InputError("at_seq only supported for trace inputs")
        }
        let target = @model.uint_field(wanted, "at_seq")
        if target == 0 {
          raise @model.InputError(
            "at_seq must identify a positive record sequence",
          )
        }
        match requested.get(target) {
          Some(uris) => uris.push(uri)
          None => requested[target] = [uri]
        }
      }
    }
  }
  let report = match input_kind {
    "edit_plan" => @edit_plan.check(@model.field(input, "plan"))
    "trace" => {
      let records = @model.array(@model.field(input, "records"))
      if records.length() > 100001 {
        raise @model.InputError("case record limit")
      }
      for i, record in records {
        session.feed_line(@model.canonical(record), i + 1)
        if !session.is_stopped() && @model.has(record, "seq") {
          let seq = session.last_seq()
          match requested.get(seq) {
            Some(uris) => {
              let observed : Map[String, String] = Map([])
              for uri in uris {
                if session.snapshot(uri) is Some(text) {
                  observed[uri] = text
                }
              }
              snapshots[seq] = observed
            }
            None => ()
          }
        }
      }
      session.report()
    }
    _ => raise @model.InputError("unsupported case input kind")
  }
  let failures : Array[Json] = []
  if @model.field(report, "exit_code") != @model.num(expected_exit) {
    failures.push(Json::string("source exit_code differs from expectation"))
  }
  if @model.field(report, "analysis_complete") != expected_complete {
    failures.push(
      Json::string("analysis completeness differs from expectation"),
    )
  }
  if @model.has(expect, "findings") {
    for wanted in @model.array(@model.field(expect, "findings")) {
      @model.only_fields(wanted, ["rule_id", "uri", "seq"])
      let rule = @model.string_field(wanted, "rule_id")
      let expectation = FindingExpectation::{
        rule_id: rule,
        uri: if @model.has(wanted, "uri") {
          Some(@model.string_field(wanted, "uri"))
        } else {
          None
        },
        seq: if @model.has(wanted, "seq") {
          Some(@model.int_field(wanted, "seq"))
        } else {
          None
        },
      }
      let found = @model.array(@model.field(report, "findings")).any(fn(f) {
        matches_finding(f, expectation)
      })
      if !found {
        failures.push(Json::string("missing expected finding: " + rule))
      }
    }
  }
  if @model.has(expect, "absent_rules") {
    for wanted in @model.array(@model.field(expect, "absent_rules")) {
      let rule = @model.str(wanted)
      if @model.array(@model.field(report, "findings")).any(fn(f) {
          @model.field(f, "rule_id") == wanted
        }) {
        failures.push(Json::string("unexpected finding: " + rule))
      }
    }
  }
  if @model.has(expect, "texts") {
    for wanted in @model.array(@model.field(expect, "texts")) {
      @model.only_fields(wanted, ["uri", "text", "at_seq"])
      let uri = @model.string_field(wanted, "uri")
      let text = @model.string_field(wanted, "text")
      let observed = if input_kind == "trace" {
        if @model.has(wanted, "at_seq") {
          let target = @model.int_field(wanted, "at_seq")
          match snapshots.get(target) {
            Some(observed) => observed.get(uri)
            None => None
          }
        } else {
          session.snapshot(uri)
        }
      } else {
        if @model.has(wanted, "at_seq") {
          raise @model.InputError("at_seq only supported for trace inputs")
        }
        let mut result : String? = None
        for doc in @model.array(@model.field(report, "documents")) {
          if @model.field(doc, "uri") == Json::string(uri) {
            result = Some(@model.string_field(doc, "text"))
          }
        }
        result
      }
      if observed != Some(text) {
        failures.push(Json::string("text assertion failed: " + uri))
      }
    }
  }
  Json::object({
    "schema_version": @model.num(1),
    "kind": Json::string("case_report"),
    "name": Json::string(name),
    "analysis_complete": Json::boolean(true),
    "exit_code": @model.num(if failures.is_empty() { 0 } else { 1 }),
    "passed": Json::boolean(failures.is_empty()),
    "failures": Json::array(failures),
    "source_report": report,
  })
}

///|
pub fn suite(manifest : Json) -> Json raise {
  if @model.int_field(manifest, "schema_version") != 1 ||
    @model.string_field(manifest, "kind") != "suite" {
    raise @model.InputError("unsupported suite schema")
  }
  let cases = @model.array(@model.field(manifest, "cases"))
  if cases.is_empty() || cases.length() > 256 {
    raise @model.InputError("suite must contain 1..256 cases")
  }
  let reports : Array[Json] = []
  let mut code = 0
  for case in cases {
    let r = safe_run(case)
    let case_code = @model.int_field(r, "exit_code")
    if case_code > code {
      code = case_code
    }
    reports.push(r)
  }
  Json::object({
    "schema_version": @model.num(1),
    "kind": Json::string("suite_report"),
    "analysis_complete": Json::boolean(code != 2),
    "exit_code": @model.num(code),
    "cases": Json::array(reports),
  })
}

///|
pub fn safe_run(case : Json) -> Json {
  run(case) catch {
    e =>
      Json::object({
        "kind": Json::string("case_report"),
        "schema_version": @model.num(1),
        "analysis_complete": Json::boolean(false),
        "exit_code": @model.num(2),
        "passed": Json::boolean(false),
        "error": Json::string(e.to_string()),
      })
  }
}
