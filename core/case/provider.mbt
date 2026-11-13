///|
fn provider_texts(value : Json, observed~ : Bool) -> Map[String, String] raise {
  let texts : Map[String, String] = Map([])
  for item in @model.array(value) {
    @model.only_fields(
      item,
      if observed {
        ["path", "uri", "text"]
      } else {
        ["path", "text"]
      },
    )
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
  if @model.int_field(input, "schema_version") != 2 ||
    @model.string_field(input, "kind") != "provider_observation" {
    raise @model.InputError("unsupported provider observation schema")
  }
  let name = @model.string_field(input, "name")
  let expected = provider_texts(@model.field(input, "expected"), observed=false)
  let observation = @model.field(input, "observed")
  let observed = provider_texts(observation, observed=true)
  let by_uri : Map[String, String] = Map([])
  for item in @model.array(observation) {
    let uri = @model.string_field(item, "uri")
    if uri == "" || by_uri.contains(uri) {
      raise @model.InputError("missing or duplicate observed document URI")
    }
    by_uri[uri] = @model.string_field(item, "text")
  }
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
      let actual = @model.array(@model.field(plan, "actual"))
      if actual.is_empty() {
        raise @model.InputError(
          "fresh edit plan has no host actual observations",
        )
      }
      for item in actual {
        let uri = @model.string_field(item, "uri")
        if by_uri.get(uri) != Some(@model.string_field(item, "text")) {
          raise @model.InputError(
            "edit actual text and host observation disagree",
          )
        }
      }
      @edit_plan.check(plan)
    }
    "trace" => {
      let s = @session.Session::new()
      let records = @model.array(@model.field(verification, "records"))
      let final_checkpoints : Map[String, String] = Map([])
      for i, record in records {
        s.feed_line(@model.canonical(record), i + 1)
        if i >= records.length() - by_uri.length() &&
          @model.field(record, "kind") == Json::string("checkpoint") &&
          @model.field(record, "source") ==
          Json::string("vscode.TextDocument.getText.afterCommand") {
          final_checkpoints[@model.string_field(record, "uri")] = @model.string_field(
            record, "text",
          )
        }
      }
      for uri, text in by_uri {
        if final_checkpoints.get(uri) != Some(text) {
          raise @model.InputError(
            "sync checkpoint and host observation disagree",
          )
        }
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
    "schema_version": 2,
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
