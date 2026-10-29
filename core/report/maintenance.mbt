///|
pub fn doctor(executable~ : String = "") -> Json {
  Json::object({
    "schema_version": @model.num(1),
    "kind": Json::string("doctor_report"),
    "exit_code": @model.num(0),
    "analysis_complete": Json::boolean(true),
    "core_version": Json::string(@model.tool_version()),
    "executable_entry": Json::string(executable),
    "bridge_protocol": @model.num(1),
    "position_encoding": Json::string("utf-16"),
    "case_schema": @model.num(1),
    "evidence_schema": @model.num(1),
    "scope": Json::string(
      "text-only; provider resource operations are not verified",
    ),
  })
}

///|
pub fn with_summary(report : Json) -> Json raise {
  let text = summary(report)
  match report {
    Object(fields) => {
      let copy = fields.copy()
      copy["display_summary"] = Json::string(text)
      Json::object(copy)
    }
    _ => raise @model.InputError("expected report object")
  }
}

///|
pub fn summary(report : Json) -> String raise {
  let kind = if @model.has(report, "kind") {
    @model.string_field(report, "kind")
  } else {
    "audit_report"
  }
  let code = @model.int_field(report, "exit_code")
  let complete = @model.field(report, "analysis_complete")
  if code < 0 ||
    code > 2 ||
    (complete != Json::boolean(true) && complete != Json::boolean(false)) {
    raise @model.InputError("invalid report status")
  }
  let state = if complete == Json::boolean(false) || code == 2 {
    "INCOMPLETE: inspect input, support limits or execution errors."
  } else if code == 1 {
    "FAILED: inspect findings or assertions below."
  } else {
    "PASS: explicit checks completed; see evidence scope below."
  }
  let lines = [kind + " — " + state]
  if kind == "suite_report" {
    for i, item in @model.array(@model.field(report, "cases")) {
      let label = if @model.has(item, "name") {
        @model.field(item, "name").stringify()
      } else {
        "case " + (i + 1).to_string()
      }
      lines.push(
        label + ": exit " + @model.int_field(item, "exit_code").to_string(),
      )
      if @model.has(item, "error") {
        lines.push("  input/execution error (use JSON for details)")
      }
      if @model.has(item, "failures") {
        lines.push(
          "  assertion failures: " +
          @model.array(@model.field(item, "failures")).length().to_string(),
        )
      }
    }
  } else if kind == "edit_plan_report" {
    let docs = @model.array(@model.field(report, "documents"))
    lines.push("Computed documents: " + docs.length().to_string())
    for doc in docs {
      let evidence = if @model.field(doc, "actual_compared") ==
        Json::boolean(true) {
        "independent actual compared (inspect mismatch findings)"
      } else {
        "prediction only; independent actual unavailable"
      }
      lines.push(
        @model.field(doc, "uri").stringify() +
        ": " +
        evidence +
        "; actual compared=" +
        @model.field(doc, "actual_compared").stringify() +
        "; version_checked=" +
        @model.field(doc, "version_checked").stringify(),
      )
    }
  } else if kind == "case_report" {
    lines.push(
      "A passing case satisfies its declared expectations, which may describe an expected fault.",
    )
  } else if kind != "doctor_report" && kind != "audit_report" {
    // Original audit reports do not carry kind; callers use the existing renderer.
    raise @model.InputError("unsupported report kind")
  }
  if @model.has(report, "findings") {
    let findings = @model.array(@model.field(report, "findings"))
    lines.push("Findings: " + findings.length().to_string())
    if findings.length() > 0 {
      lines.push(
        "First: " +
        @model.field(findings[0], "rule_id").stringify() +
        " " +
        @model.field(findings[0], "uri").stringify(),
      )
      if @model.has(findings[0], "message") {
        lines.push(
          "Reason: " + @model.field(findings[0], "message").stringify(),
        )
      }
    }
  }
  if kind == "audit_report" && @model.has(report, "counts") {
    let counts = @model.field(report, "counts")
    lines.push(
      "Independent checkpoints: passed=" +
      @model.field(counts, "checkpoints_passed").stringify() +
      "; mismatched=" +
      @model.field(counts, "checkpoints_mismatched").stringify() +
      "; unavailable=" +
      @model.field(counts, "checkpoints_unavailable").stringify(),
    )
    lines.push(
      "Client replay does not establish server internal state or a unique root cause.",
    )
  }
  lines.join("\n") + "\n"
}

///|
fn xml(value : String) -> String {
  let b = StringBuilder()
  for c in value {
    match c {
      '&' => b.write_string("&amp;")
      '<' => b.write_string("&lt;")
      '>' => b.write_string("&gt;")
      '"' => b.write_string("&quot;")
      '\'' => b.write_string("&apos;")
      _ => {
        let n = c.to_int()
        if n == 9 ||
          n == 10 ||
          n == 13 ||
          (n >= 32 && n <= 55295) ||
          (n >= 57344 && n <= 65533) ||
          n >= 65536 {
          b.write_char(c)
        } else {
          b.write_string("\u{FFFD}")
        }
      }
    }
  }
  b.to_string()
}

///|
pub fn junit(report : Json) -> String raise {
  if @model.string_field(report, "kind") != "suite_report" {
    raise @model.InputError("JUnit requires a suite report")
  }
  let cases = @model.array(@model.field(report, "cases"))
  let mut failures = 0
  let mut errors = 0
  let entries : Array[String] = []
  for i, item in cases {
    let code = @model.int_field(item, "exit_code")
    let name = if @model.has(item, "name") {
      @model.string_field(item, "name")
    } else {
      "case " + (i + 1).to_string()
    }
    let mut entry = "<testcase classname=\"edittrace\" name=\"" +
      xml(name) +
      "\">"
    if code == 2 {
      errors = errors + 1
      entry = entry +
        "<error type=\"InputOrExecutionError\" message=\"Case input or execution incomplete; inspect local JSON evidence\"/>"
    } else if code == 1 {
      failures = failures + 1
      // No URI, source text or arbitrary input-derived exception in default CI output.
      entry = entry +
        "<failure type=\"AssertionFailure\" message=\"Declared expectations were not satisfied; inspect local JSON evidence\"/>"
    } else if code != 0 {
      raise @model.InputError("invalid case exit code")
    }
    entries.push(entry + "</testcase>")
  }
  "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<testsuite name=\"EditTrace\" tests=\"" +
  cases.length().to_string() +
  "\" failures=\"" +
  failures.to_string() +
  "\" errors=\"" +
  errors.to_string() +
  "\">\n" +
  entries.join("\n") +
  "\n</testsuite>\n"
}
