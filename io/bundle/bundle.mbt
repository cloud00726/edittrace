///|
pub async fn export_prefix(
  path : String,
  id : String,
  destination : String,
  limits : @trace.Limits,
) -> Json {
  let (source, _) = @trace.load(path, limits~)
  let mut selected = Json::null()
  for f in source.all_findings() {
    if @model.field(f, "id") == Json::string(id) {
      selected = f
      break
    }
  }
  if selected == Json::null() {
    raise @model.InputError("finding id not found")
  }
  let target = @model.int_field(selected, "seq")
  let (prefix, lines) = @trace.load(path, limits~, until=target, collect=true)
  let fingerprint = @model.field(selected, "fingerprint")
  if !prefix
    .all_findings()
    .any(fn(f) { @model.field(f, "fingerprint") == fingerprint }) {
    raise @model.InputError(
      "source changed or prefix does not reproduce the target",
    )
  }
  @fs.mkdir(destination, allow_exist=false)
  @fs.write_file(
    destination + "/trace.jsonl",
    lines.join("\n") + "\n",
    create_mode=CreateNew,
  )
  let (verified, _) = @trace.load(destination + "/trace.jsonl", limits~)
  if !verified
    .all_findings()
    .any(fn(f) { @model.field(f, "fingerprint") == fingerprint }) {
    raise @model.InputError("written bundle failed reproduction verification")
  }
  @fs.write_file(
    destination + "/finding.json",
    @model.canonical(selected) + "\n",
    create_mode=CreateNew,
  )
  let manifest = Json::object({
    "schema_version": @model.num(1),
    "tool_version": Json::string("0.1.0"),
    "target_fingerprint": fingerprint,
    "through_seq": @model.num(target),
    "verified": Json::boolean(true),
    "strategy": Json::string("complete_prefix_not_minimized"),
    "prefix_exit_code": @model.field(verified.report(), "exit_code"),
    "source_meta": @model.field(source.report(), "meta"),
  })
  @fs.write_file(
    destination + "/manifest.json",
    @model.canonical(manifest) + "\n",
    create_mode=CreateNew,
  )
  @fs.write_file(
    destination + "/README.md",
    "# EditTrace reproduction\n\nRun `edittrace audit trace.jsonl --format json`.\n\nTarget fingerprint is in manifest.json. The complete prefix preserves context; it is not a minimal reproduction. Prefix exit code may differ from the full session because recovery can occur later.\n\nThe trace contains source text. Review it before sharing; no automatic redaction is claimed.\n",
    create_mode=CreateNew,
  )
  manifest
}
