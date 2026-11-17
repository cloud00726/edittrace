///|
fn provider_texts(
  value : Json,
) -> (Map[String, String], Map[String, String]) raise {
  let texts : Map[String, String] = Map([])
  let bindings : Map[String, String] = Map([])
  let uris : Map[String, Bool] = Map([])
  for item in @model.array(value) {
    @model.only_fields(item, ["path", "uri", "text"])
    let path = @model.string_field(item, "path")
    let uri = @model.string_field(item, "uri")
    if path == "" ||
      uri == "" ||
      texts.contains(path) ||
      uris.contains(uri) ||
      texts.length() >= 64 {
      raise @model.InputError("missing or duplicate provider file identity")
    }
    texts[path] = @model.string_field(item, "text")
    bindings[path] = uri
    uris[uri] = true
  }
  (texts, bindings)
}

///|
pub fn check_provider(input : Json) -> Json raise {
  @model.only_fields(input, [
    "schema_version", "kind", "name", "expected", "observed", "verification",
  ])
  if @model.int_field(input, "schema_version") != 3 ||
    @model.string_field(input, "kind") != "provider_observation" {
    raise @model.InputError("unsupported provider observation schema")
  }
  let name = @model.string_field(input, "name")
  let (expected, bindings) = provider_texts(@model.field(input, "expected"))
  let (observed, observed_bindings) = provider_texts(
    @model.field(input, "observed"),
  )
  if expected.is_empty() || expected.length() != observed.length() {
    raise @model.InputError("incomplete provider observation set")
  }
  let by_uri : Map[String, String] = Map([])
  for path, uri in bindings {
    if observed_bindings.get(path) != Some(uri) {
      raise @model.InputError(
        "observed file identity differs from the scenario binding",
      )
    }
    by_uri[uri] = observed[path]
  }
  let failures : Array[Json] = []
  let verification = @model.field(input, "verification")
  let (source_report, consistent) = match
    @model.string_field(verification, "kind") {
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
      let edited : Map[String, Bool] = Map([])
      for item in actual {
        let uri = @model.string_field(item, "uri")
        if by_uri.get(uri) != Some(@model.string_field(item, "text")) {
          raise @model.InputError(
            "edit actual text and host observation disagree",
          )
        }
        edited[uri] = true
      }
      let baselines : Map[String, String] = Map([])
      for item in @model.array(@model.field(plan, "documents")) {
        let uri = @model.string_field(item, "uri")
        if !by_uri.contains(uri) || baselines.contains(uri) {
          raise @model.InputError("invalid provider baseline identity")
        }
        baselines[uri] = @model.string_field(item, "text")
      }
      for uri, text in by_uri {
        match baselines.get(uri) {
          Some(baseline) if edited.contains(uri) || baseline == text => ()
          _ => raise @model.InputError("missing baseline or unexplained change")
        }
      }
      let result = @edit_plan.check(plan)
      (result, @model.int_field(result, "exit_code") == 0)
    }
    "trace" => {
      let s = @session.Session::new()
      let records = @model.array(@model.field(verification, "records"))
      let checkpoint_source = "vscode.TextDocument.getText.afterCommand"
      let checkpoint_start = records.length() - by_uri.length()
      let final_checkpoints : Map[String, Bool] = Map([])
      for i, record in records {
        s.feed_line(@model.canonical(record), i + 1)
        let is_final = @model.field(record, "kind") ==
          Json::string("checkpoint") &&
          @model.field(record, "source") == Json::string(checkpoint_source)
        if (i >= checkpoint_start) != is_final {
          raise @model.InputError(
            "final sync checkpoints must cover the declared files once",
          )
        }
        if is_final {
          let uri = @model.string_field(record, "uri")
          if final_checkpoints.contains(uri) ||
            by_uri.get(uri) != Some(@model.string_field(record, "text")) {
            raise @model.InputError(
              "sync checkpoint and host observation disagree",
            )
          }
          final_checkpoints[uri] = true
        }
      }
      let result = s.report()
      let counts = @model.field(result, "counts")
      let valid = final_checkpoints.length() == by_uri.length() &&
        @model.int_field(counts, "checkpoints_unavailable") == 0 &&
        by_uri.keys().all(fn(uri) { s.snapshot(uri) == by_uri.get(uri) })
      (result, valid)
    }
    _ => raise @model.InputError("unknown provider verification kind")
  }
  let complete = consistent &&
    @model.field(source_report, "analysis_complete") == Json::boolean(true)
  if !complete || @model.int_field(source_report, "exit_code") != 0 {
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
  {
    "kind": "provider_report",
    "schema_version": 3,
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
