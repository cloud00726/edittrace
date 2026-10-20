///|
pub(all) struct Edit {
  start : @text.Position
  end : @text.Position
  new_text : String
}

///|
pub(all) struct Baseline {
  uri : String
  text : String
  version : Int32
}

///|
// All ranges refer to one immutable baseline. Stable ordering preserves inserts.
pub fn apply(baseline : String, edits : Array[Edit]) -> String raise {
  if edits.length() > 10000 || @utf8.encode(baseline).length() > 4194304 {
    raise @model.InputError("edit plan resource limit exceeded")
  }
  let resolved : Array[(Int32, Int32, Int32, String)] = []
  let mut inserted = 0
  for i, e in edits {
    if e.start.line > e.end.line ||
      (e.start.line == e.end.line && e.start.character > e.end.character) {
      raise @model.InputError("reversed edit range")
    }
    let a = @text.offset(baseline, e.start).value
    let b = @text.offset(baseline, e.end).value
    inserted = inserted + @utf8.encode(e.new_text).length()
    if inserted > 4194304 {
      raise @model.InputError("edit output resource limit exceeded")
    }
    resolved.push((a, b, i, e.new_text))
  }
  resolved.sort_by(fn(a, b) {
    if a.0 < b.0 {
      -1
    } else if a.0 > b.0 {
      1
    } else if a.2 < b.2 {
      -1
    } else if a.2 > b.2 {
      1
    } else {
      0
    }
  })
  let parts : Array[String] = []
  let mut cursor = 0
  for e in resolved {
    if e.0 < cursor {
      raise @model.InputError(
        "overlapping edits or insert after replacement at same position",
      )
    }
    parts.push(baseline[cursor:e.0].to_owned())
    parts.push(e.3)
    cursor = e.1
  }
  parts.push(baseline[cursor:].to_owned())
  let result = parts.join("")
  if @utf8.encode(result).length() > 4194304 {
    raise @model.InputError("edit output resource limit exceeded")
  }
  result
}

///|
pub fn parse_edit(j : Json) -> Edit raise {
  @model.object(j)
  if @model.has(j, "annotationId") {
    raise @model.InputError("annotated edits are unsupported")
  }
  let range = @model.field(j, "range")
  {
    start: @text.position(@model.field(range, "start")),
    end: @text.position(@model.field(range, "end")),
    new_text: @model.string_field(j, "newText"),
  }
}

///|
fn issue(code : String, uri : String, detail : String) -> Json {
  Json::object({
    "rule_id": Json::string(code),
    "uri": Json::string(uri),
    "message": Json::string(detail),
  })
}

///|
pub fn check(plan : Json) -> Json raise {
  if @model.int_field(plan, "schema_version") != 1 ||
    @model.string_field(plan, "kind") != "edit_plan" ||
    @model.string_field(plan, "position_encoding") != "utf-16" {
    raise @model.InputError("unsupported edit plan schema or encoding")
  }
  @model.object(@model.field(plan, "source"))
  let bases : Map[String, Baseline] = Map([])
  for b in @model.array(@model.field(plan, "documents")) {
    let uri = @model.string_field(b, "uri")
    if bases.contains(uri) || bases.length() >= 256 {
      raise @model.InputError("duplicate baseline or document limit")
    }
    let text = @model.string_field(b, "text")
    if @utf8.encode(text).length() > 4194304 {
      raise @model.InputError("baseline document byte limit")
    }
    bases[uri] = { uri, text, version: @model.int_field(b, "version"), }
  }
  let w = @model.field(plan, "workspace_edit")
  @model.object(w)
  if @model.has(w, "changeAnnotations") ||
    @model.has(w, "changes") == @model.has(w, "documentChanges") {
    raise @model.InputError(
      "provide exactly one supported workspace edit representation",
    )
  }
  let operations : Array[Json] = []
  if @model.has(w, "documentChanges") {
    for op in @model.array(@model.field(w, "documentChanges")) {
      operations.push(op)
    }
  } else {
    match @model.field(w, "changes") {
      Object(m) => {
        let keys : Array[String] = []
        for k, _ in m {
          keys.push(k)
        }
        keys.sort()
        for k in keys {
          operations.push(
            Json::object({
              "textDocument": Json::object({
                "uri": Json::string(k),
                "version": Json::null(),
              }),
              "edits": m[k],
            }),
          )
        }
      }
      _ => raise @model.InputError("changes must be an object")
    }
  }
  if operations.length() > 256 {
    raise @model.InputError("document operation limit")
  }
  let actual : Map[String, String] = Map([])
  if @model.has(plan, "actual") {
    for a in @model.array(@model.field(plan, "actual")) {
      let uri = @model.string_field(a, "uri")
      if actual.contains(uri) {
        raise @model.InputError("duplicate actual URI")
      }
      actual[uri] = @model.string_field(a, "text")
    }
    if actual.length() != operations.length() {
      raise @model.InputError("actual must cover exactly the edited documents")
    }
  }
  let seen : Map[String, Bool] = Map([])
  let findings : Array[Json] = []
  let results : Array[Json] = []
  for op in operations {
    if @model.has(op, "kind") {
      raise @model.InputError("resource operations unsupported")
    }
    let td = @model.field(op, "textDocument")
    let uri = @model.string_field(td, "uri")
    if seen.contains(uri) {
      raise @model.InputError("repeated document operations unsupported")
    }
    seen[uri] = true
    if @model.has(plan, "actual") && !actual.contains(uri) {
      raise @model.InputError("missing actual URI: " + uri)
    }
    let baseline = match bases.get(uri) {
      Some(b) => b
      None => raise @model.InputError("missing document baseline: " + uri)
    }
    if !@model.has(td, "version") {
      raise @model.InputError(
        "version field required (null means unconstrained)",
      )
    }
    let constrained = @model.field(td, "version") != Json::null()
    // Validate the complete edit shape even when a semantic precondition fails.
    let edits : Array[Edit] = []
    for e in @model.array(@model.field(op, "edits")) {
      edits.push(parse_edit(e))
    }
    if edits.length() > 10000 {
      raise @model.InputError("edit count limit")
    }
    if constrained && @model.int_field(td, "version") != baseline.version {
      findings.push(
        issue(
          "EP001_VERSION_MISMATCH", uri, "edit version differs from baseline",
        ),
      )
      continue
    }
    let mut clamped = false
    for parsed in edits {
      clamped = clamped ||
        @text.offset(baseline.text, parsed.start).clamped ||
        @text.offset(baseline.text, parsed.end).clamped
    }
    let output = apply(baseline.text, edits) catch {
      @model.InputError(detail) =>
        if detail ==
          "overlapping edits or insert after replacement at same position" {
          findings.push(issue("EP002_OVERLAPPING_EDITS", uri, detail))
          continue
        } else {
          raise @model.InputError(detail)
        }
      e => raise e
    }
    let observed = if @model.has(plan, "actual") {
      match actual.get(uri) {
        Some(s) => Some(s)
        None => raise @model.InputError("missing actual URI: " + uri)
      }
    } else {
      None
    }
    if observed is Some(s) && s != output {
      let mut offset = 0
      while offset < output.length() &&
            offset < s.length() &&
            output.at(offset) == s.at(offset) {
        offset = offset + 1
      }
      findings.push(
        Json::object({
          "rule_id": Json::string("EP003_ACTUAL_MISMATCH"),
          "uri": Json::string(uri),
          "message": Json::string(
            "independent actual text differs; inspect the edit plan and baseline, not proof of a unique root cause",
          ),
          "first_difference_utf16": @model.num(offset),
          "expected_excerpt": Json::string(@model.excerpt(output)),
          "actual_excerpt": Json::string(@model.excerpt(s)),
        }),
      )
    }
    results.push(
      Json::object({
        "uri": Json::string(uri),
        "text": Json::string(output),
        "baseline_version": @model.num(baseline.version),
        "version_checked": Json::boolean(constrained),
        "column_clamped": Json::boolean(clamped),
        "actual_compared": Json::boolean(observed is Some(_)),
        "actual_text": match observed {
          Some(s) => Json::string(s)
          None => Json::null()
        },
      }),
    )
  }
  Json::object({
    "schema_version": @model.num(1),
    "kind": Json::string("edit_plan_report"),
    "analysis_complete": Json::boolean(true),
    "exit_code": @model.num(if findings.is_empty() { 0 } else { 1 }),
    "source": @model.field(plan, "source"),
    "documents": Json::array(results),
    "findings": Json::array(findings),
    "scope": Json::string(
      "text-only edits; not program semantics or server memory",
    ),
  })
}
