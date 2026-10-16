///|
async fn read_json(path : String, max_bytes : Int32) -> Json {
  let f = @fs.open(path, mode=ReadOnly)
  defer f.close()
  let data = @buffer.Buffer()
  while true {
    match f.read_some(max_len=65536) {
      None => break
      Some(bytes) => {
        if data.length() + bytes.length() > max_bytes {
          raise @model.InputError("bundle metadata byte limit exceeded")
        }
        for byte in bytes {
          data.write_byte(byte)
        }
      }
    }
  }
  @model.parse_bounded(@utf8.decode(data.to_bytes()))
}

///|
pub async fn verify(destination : String, limits : @trace.Limits) -> Json {
  let manifest = read_json(destination + "/manifest.json", limits.record_bytes)
  let finding = read_json(destination + "/finding.json", limits.record_bytes)
  if @model.int_field(manifest, "schema_version") != 1 ||
    @model.string_field(manifest, "tool_version") != "0.1.0" ||
    @model.field(manifest, "verified") != Json::boolean(true) ||
    @model.string_field(manifest, "strategy") != "complete_prefix_not_minimized" {
    raise @model.InputError("unsupported or invalid bundle manifest")
  }
  let (session, _) = @trace.load(destination + "/trace.jsonl", limits~)
  let report = session.report()
  if session.is_stopped() ||
    session.last_seq() != @model.int_field(manifest, "through_seq") ||
    @model.field(report, "meta") != @model.field(manifest, "source_meta") ||
    @model.field(report, "exit_code") !=
    @model.field(manifest, "prefix_exit_code") ||
    @model.field(finding, "fingerprint") !=
    @model.field(manifest, "target_fingerprint") ||
    !session.all_findings().contains(finding) {
    raise @model.InputError(
      "bundle does not reproduce its recorded finding and manifest",
    )
  }
  Json::object({
    "verified": Json::boolean(true),
    "target_fingerprint": @model.field(manifest, "target_fingerprint"),
    "through_seq": @model.field(manifest, "through_seq"),
    "prefix_exit_code": @model.field(report, "exit_code"),
  })
}

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
  let (prefix, lines) = @trace.load(
    path,
    limits~,
    until=Some(target),
    collect=true,
  )
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
