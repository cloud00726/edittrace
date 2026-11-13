///|
fn provider_texts(value : Json) -> Map[String, String] raise {
  let texts : Map[String, String] = Map([])
  for item in @model.array(value) {
    @model.only_fields(item, ["path", "text"])
    let path = @model.string_field(item, "path")
    if path == "" || texts.contains(path) || texts.length() >= 64 {
      raise @model.InputError("invalid or duplicate provider observation path")
    }
    texts[path] = @model.string_field(item, "text")
  }
  texts
}

///|
pub fn check_provider(input : Json) -> Json raise {
  @model.only_fields(input, [
    "schema_version", "kind", "name", "expected", "observed", "verification",
  ])
  if @model.int_field(input, "schema_version") != 1 ||
    @model.string_field(input, "kind") != "provider_observation" {
    raise @model.InputError("unsupported provider observation schema")
  }
  let name = @model.string_field(input, "name")
  let expected = provider_texts(@model.field(input, "expected"))
  let observed = provider_texts(@model.field(input, "observed"))
  if expected.is_empty() {
    raise @model.InputError("provider expectation is empty")
  }
  let failures : Array[Json] = []
  let verification = @model.field(input, "verification")
  let source_report = match @model.string_field(verification, "kind") {
    "edit_plan" => {
      let plan = @model.field(verification, "plan")
      if !@model.has(plan, "actual") {
        raise @model.InputError(
          "fresh edit plan requires host actual observations",
        )
      }
      @edit_plan.check(plan)
    }
    "trace" => {
      let s = @session.Session::new()
      let records = @model.array(@model.field(verification, "records"))
      for i, record in records {
        s.feed_line(@model.canonical(record), i + 1)
      }
      s.report()
    }
    _ => raise @model.InputError("unknown provider verification kind")
  }
  let complete = @model.field(source_report, "analysis_complete") ==
    Json::boolean(true)
  if @model.int_field(source_report, "exit_code") != 0 {
    failures.push({ "reason": "fresh edit verification failed" })
  }
  for path, wanted in expected {
    match observed.get(path) {
      None => failures.push({ "path": path, "reason": "missing observation" })
      Some(actual) =>
        if actual != wanted {
          let mut offset = 0
          while offset < actual.length() &&
                offset < wanted.length() &&
                actual.at(offset) == wanted.at(offset) {
            offset = offset + 1
          }
          failures.push({
            "path": path,
            "reason": "reviewed text mismatch",
            "first_difference_utf16": @model.num(offset),
          })
        }
    }
  }
  for path, _ in observed {
    if !expected.contains(path) {
      failures.push({ "path": path, "reason": "unexpected observation" })
    }
  }
  {
    "kind": "provider_report",
    "schema_version": 1,
    "name": name,
    "analysis_complete": complete,
    "exit_code": @model.num(
      if !complete {
        2
      } else if failures.is_empty() {
        0
      } else {
        1
      },
    ),
    "failures": Json::array(failures),
    "rules": Json::array(
      @model.array(@model.field(source_report, "findings")).map(fn(f) {
        @model.field(f, "rule_id")
      }),
    ),
  }
}
