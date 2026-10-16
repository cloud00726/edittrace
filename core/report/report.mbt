///|
pub fn render(report : Json) -> String {
  let out = StringBuilder()
  out.write_string("EditTrace 0.1.0 — UTF-16 document-sync audit\n")
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
