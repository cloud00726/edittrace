///|
pub async fn evidence_lines(path : String) -> Array[String] {
  let raw = read(path)
  let lines = raw.split("\n").map(fn(s) { s.to_owned() }).to_array()
  if raw.has_suffix("\n") {
    let _ = lines.pop()
  }
  lines
}

///|
pub async fn verify_evidence(directory : String) -> Json {
  let manifest = @model.parse_bounded(
    read(directory + "/manifest.json", max_bytes=33554432),
  )
  @model.only_fields(manifest, [
    "kind", "schema_version", "tool_version", "strategy", "verified", "target", "source_exit_code",
    "canonical_trace", "source_text_retained", "identity_mapping_included", "receipt",
  ])
  if @model.field(manifest, "kind") != Json::string("evidence_bundle") ||
    @model.int_field(manifest, "schema_version") != 1 ||
    @model.field(manifest, "verified") != Json::boolean(true) ||
    !@model.supported_bundle_version(
      @model.string_field(manifest, "tool_version"),
    ) ||
    !["share_structural_identity", "minimize_full_target"].contains(
      @model.string_field(manifest, "strategy"),
    ) {
    raise @model.InputError("unsupported evidence manifest")
  }
  let raw = read(directory + "/trace.jsonl")
  if @model.field(manifest, "canonical_trace") != Json::string(raw) {
    raise @model.InputError("evidence trace bytes changed")
  }
  let lines = evidence_lines(directory + "/trace.jsonl")
  let report = @evidence.replay(lines)
  let recorded = @model.parse_bounded(read(directory + "/finding.json"))
  let actual = @evidence.target(report, @model.string_field(recorded, "id"))
  let receipt = @model.parse_bounded(read(directory + "/receipt.json"))
  if @model.field(manifest, "source_text_retained") != Json::boolean(true) ||
    @model.field(manifest, "identity_mapping_included") != Json::boolean(false) {
    raise @model.InputError("invalid disclosure flags")
  }
  if @model.field(manifest, "strategy") ==
    Json::string("share_structural_identity") {
    let (normalized, expected) = @evidence.share(
      lines,
      @model.string_field(recorded, "id"),
    )
    if normalized != lines || expected != receipt {
      raise @model.InputError("share disclosure or normalized trace differs")
    }
  } else if @model.field(receipt, "kind") != Json::string("minimize_report") ||
    @model.int_field(receipt, "retained_nonblank") !=
    lines.filter(fn(s) { !s.trim().is_empty() }).length() ||
    @model.int_field(receipt, "attempts") <
    @model.int_field(receipt, "accepted") ||
    @model.int_field(receipt, "attempts") >
    @model.int_field(receipt, "effective_runs") {
    raise @model.InputError("invalid minimization receipt")
  }
  if actual != recorded ||
    @model.field(manifest, "target") != actual ||
    @model.field(manifest, "source_exit_code") !=
    @model.field(report, "exit_code") ||
    @model.field(manifest, "receipt") != receipt {
    raise @model.InputError("evidence target or receipt changed")
  }
  {
    "kind": "evidence_verification",
    "exit_code": 0,
    "analysis_complete": true,
    "verified": true,
    "display_summary": "Evidence replay and package consistency verified. Not a signature, safety or authenticity proof.",
  }
}

///|
pub async fn evidence_operation(
  action : String,
  path : String,
  id : String,
  destination : String?,
  max_runs : Int32,
) -> Json {
  if action == "verify" {
    return verify_evidence(path)
  }
  let lines = evidence_lines(path)
  let (output, receipt) = if action == "minimize" {
    @evidence.minimize(lines, id, max_runs)
  } else {
    @evidence.share(lines, id)
  }
  if action == "plan" {
    return receipt
  }
  let directory = match destination {
    Some(d) => d
    None => raise @model.InputError("evidence export requires --out")
  }
  let replayed = @evidence.replay(output)
  let wanted = @evidence.target(replayed, id)
  let raw = output.join("\n") + "\n"
  let manifest : Json = {
    "kind": "evidence_bundle",
    "schema_version": 1,
    "tool_version": Json::string(@model.tool_version()),
    "strategy": Json::string(
      if action == "minimize" {
        "minimize_full_target"
      } else {
        "share_structural_identity"
      },
    ),
    "verified": true,
    "target": wanted,
    "source_exit_code": @model.field(replayed, "exit_code"),
    "canonical_trace": Json::string(raw),
    "source_text_retained": true,
    "identity_mapping_included": false,
    "receipt": receipt,
  }
  let serialized = @model.canonical(manifest)
  if serialized.length() > 33554432 {
    raise @model.InputError("evidence manifest limit")
  }
  @fs.mkdir(directory, allow_exist=false)
  @fs.write_file(directory + "/trace.jsonl", raw, create_mode=CreateNew)
  @fs.write_file(
    directory + "/finding.json",
    @model.canonical(wanted) + "\n",
    create_mode=CreateNew,
  )
  @fs.write_file(
    directory + "/receipt.json",
    @model.canonical(receipt) + "\n",
    create_mode=CreateNew,
  )
  // Verify written payloads before publishing the verified manifest.
  if read(directory + "/trace.jsonl") != raw ||
    @model.parse_bounded(read(directory + "/finding.json")) != wanted ||
    @model.parse_bounded(read(directory + "/receipt.json")) != receipt ||
    @evidence.target(
      @evidence.replay(evidence_lines(directory + "/trace.jsonl")),
      id,
    ) !=
    wanted {
    raise @model.InputError(
      "written evidence payload failed independent reread",
    )
  }
  @fs.write_file(
    directory + "/README.md",
    "# EditTrace evidence\n\nRun: edittrace evidence verify <this-directory>\n\nSource text is retained and may contain secrets or original paths. Structural identity conversion is not full redaction. The manifest repeats trace content for consistency, not cryptographic authenticity. Minimized files retain original physical lines as blank lines; no global minimality is claimed. Original input is not modified.\n",
    create_mode=CreateNew,
  )
  @fs.write_file(
    directory + "/manifest.json",
    serialized + "\n",
    create_mode=CreateNew,
  )
  let _ = verify_evidence(directory)
  receipt
}
