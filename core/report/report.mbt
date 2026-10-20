///|
fn clear_fields(value : Json, names : Array[String]) -> Json {
  match value {
    Object(fields) => {
      let copy = fields.copy()
      for name in names {
        copy[name] = Json::null()
      }
      Json::object(copy)
    }
    _ => value
  }
}

///|
pub fn without_excerpts(report : Json) -> Json {
  match report {
    Object(fields) => {
      let copy = fields.copy()
      copy["findings"] = Json::array(
        (@model.array(@model.field(report, "findings")) catch { _ => [] }).map(fn(
          f,
        ) {
          clear_fields(f, ["before_excerpt", "after_excerpt"])
        }),
      )
      copy["documents"] = Json::array(
        (@model.array(@model.field(report, "documents")) catch { _ => [] }).map(fn(
            d,
          ) {
            clear_fields(d, ["last_known_excerpt"])
          },
        ),
      )
      copy["excerpt_mode"] = Json::string("omitted")
      Json::object(copy)
    }
    _ => report
  }
}

///|
pub fn render(report : Json) -> String {
  let out = StringBuilder()
  let meta = @model.field(report, "meta")
  if @model.has(meta, "encoding_basis") {
    out.write_string(
      "Encoding basis: " +
      @model.canonical(@model.field(meta, "encoding_basis")) +
      "\n",
    )
  }
  out.write_string(
    "EditTrace " + @model.tool_version() + " — UTF-16 document-sync audit\n",
  )
  out.write_string(
    "Scope: declared encoding, document-sync subset; server internals are not observed.\n",
  )
  out.write_string(
    "Complete: " +
    @model.canonical(@model.field(report, "analysis_complete")) +
    " | exit: " +
    @model.canonical(@model.field(report, "exit_code")) +
    "\n",
  )
  out.write_string(
    "Counts: " + @model.canonical(@model.field(report, "counts")) + "\n",
  )
  for
    document in (@model.array(@model.field(report, "documents")) catch {
      _ => []
    }) {
    out.write_string(
      "Document uri=" +
      @model.canonical(@model.field(document, "uri")) +
      " status=" +
      @model.canonical(@model.field(document, "status")) +
      " generation=" +
      @model.canonical(@model.field(document, "generation")) +
      " last_successful_version=" +
      @model.canonical(@model.field(document, "last_successful_version")) +
      " highest_observed_version=" +
      @model.canonical(@model.field(document, "highest_observed_version")) +
      "\n",
    )
  }
  match @model.field(report, "findings") {
    Array(fs) =>
      for f in fs {
        out.write_string(
          @model.canonical(@model.field(f, "severity")) +
          " " +
          @model.canonical(@model.field(f, "id")) +
          " ",
        )
        out.write_string(@model.canonical(@model.field(f, "message")) + "\n")
        out.write_string(
          "  uri=" +
          @model.canonical(@model.field(f, "uri")) +
          " seq=" +
          @model.canonical(@model.field(f, "seq")) +
          "\n",
        )
        out.write_string(
          "  before=" +
          @model.canonical(@model.field(f, "before_excerpt")) +
          " after=" +
          @model.canonical(@model.field(f, "after_excerpt")) +
          "\n",
        )
      }
    _ => ()
  }
  if @model.field(report, "input_error") != Json::null() {
    out.write_string(
      "Input error: " +
      @model.canonical(@model.field(report, "input_error")) +
      "\n",
    )
  }
  out.to_string()
}

///|
pub fn render_workflow(report : Json) -> String {
  let lines = [
    "EditTrace: " +
    @model.canonical(@model.field(report, "kind")) +
    " | complete=" +
    @model.canonical(@model.field(report, "analysis_complete")) +
    " | exit=" +
    @model.canonical(@model.field(report, "exit_code")),
  ]
  match @model.field(report, "documents") {
    Array(docs) =>
      for doc in docs {
        lines.push(
          "  File " +
          @model.canonical(@model.field(doc, "uri")) +
          " | version checked=" +
          @model.canonical(@model.field(doc, "version_checked")) +
          " | actual compared=" +
          @model.canonical(@model.field(doc, "actual_compared")),
        )
      }
    _ => ()
  }
  for key in ["findings", "failures"] {
    match @model.field(report, key) {
      Array(items) =>
        for item in items {
          lines.push("  " + @model.canonical(item))
        }
      _ => ()
    }
  }
  for key in ["source_report", "error"] {
    if @model.has(report, key) {
      lines.push(
        "  " + key + ": " + @model.canonical(@model.field(report, key)),
      )
    }
  }
  match @model.field(report, "cases") {
    Array(cases) =>
      for case in cases {
        lines.push(
          "  Case " +
          @model.canonical(@model.field(case, "name")) +
          " | exit=" +
          @model.canonical(@model.field(case, "exit_code")) +
          " | failures=" +
          @model.canonical(@model.field(case, "failures")),
        )
      }
    _ => ()
  }
  lines.join("\n") + "\n"
}
