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
fn document_uri(record : Json) -> Json {
  if @model.field(record, "kind") == Json::string("checkpoint") {
    @model.field(record, "uri")
  } else if @model.field(record, "kind") == Json::string("message") {
    let params = @model.field(@model.field(record, "message"), "params")
    @model.field(@model.field(params, "textDocument"), "uri")
  } else {
    Json::null()
  }
}

///|
pub async fn verify(destination : String, limits : @trace.Limits) -> Json {
  let manifest = read_json(destination + "/manifest.json", limits.record_bytes)
  let finding = read_json(destination + "/finding.json", limits.record_bytes)
  if @model.int_field(manifest, "schema_version") != 1 ||
    !["0.1.0", @model.tool_version()].contains(
      @model.string_field(manifest, "tool_version"),
    ) ||
    @model.field(manifest, "verified") != Json::boolean(true) ||
    !["complete_prefix_not_minimized", "document_prefix_preserving_lines"].contains(
      @model.string_field(manifest, "strategy"),
    ) {
    raise @model.InputError("unsupported or invalid bundle manifest")
  }
  let filtered = @model.string_field(manifest, "strategy") ==
    "document_prefix_preserving_lines"
  if filtered {
    let uri = @model.string_field(manifest, "filter_uri")
    if uri.is_empty() ||
      @model.field(@model.field(manifest, "target_fingerprint"), "uri") !=
      Json::string(uri) {
      raise @model.InputError("filtered manifest URI differs from target")
    }
  } else if @model.field(manifest, "filter_uri") != Json::null() {
    raise @model.InputError("full prefix cannot claim document filtering")
  }
  let (session, lines) = @trace.load(
    destination + "/trace.jsonl",
    limits~,
    collect=filtered,
  )
  if filtered {
    for line in lines {
      if !line.trim().is_empty() {
        let uri = document_uri(@model.parse_bounded(line))
        if uri != Json::null() && uri != @model.field(manifest, "filter_uri") {
          raise @model.InputError(
            "filtered trace contains unrelated document records",
          )
        }
      }
    }
  }
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
  filter_uri~ : String? = None,
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
  if filter_uri is Some(uri) {
    if uri.is_empty() || @model.field(selected, "uri") != Json::string(uri) {
      raise @model.InputError("--uri must identify the target finding document")
    }
    let filtered = @session.Session::new(
      max_document_bytes=limits.document_bytes,
      max_open_documents=limits.open_documents,
      max_findings=limits.findings,
    )
    for i, line in lines {
      if !line.trim().is_empty() {
        let record = @model.parse_bounded(line)
        let other = document_uri(record)
        if other != Json::null() && other != Json::string(uri) {
          lines[i] = ""
        }
      }
      filtered.feed_line(lines[i], i + 1)
    }
    if filtered.is_stopped() || !filtered.all_findings().contains(selected) {
      raise @model.InputError(
        "document filtering cannot preserve the complete target; export without --uri",
      )
    }
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
    "tool_version": Json::string(@model.tool_version()),
    "target_fingerprint": fingerprint,
    "through_seq": @model.num(target),
    "verified": Json::boolean(true),
    "strategy": Json::string(
      if filter_uri is Some(_) {
        "document_prefix_preserving_lines"
      } else {
        "complete_prefix_not_minimized"
      },
    ),
    "filter_uri": match filter_uri {
      Some(uri) => Json::string(uri)
      None => Json::null()
    },
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
    "# EditTrace reproduction\n\nRun `edittrace audit trace.jsonl --format json` and `edittrace verify <bundle-directory>`.\n\nTarget fingerprint and strategy are in manifest.json. Optional document filtering replaces unrelated document records with blank lines to preserve source line numbers, and revalidates the complete target finding. Neither strategy guarantees minimality. Prefix exit code may differ from the full session.\n\nThe trace contains source text. Review it before sharing; no automatic redaction is claimed.\n",
    create_mode=CreateNew,
  )
  manifest
}
