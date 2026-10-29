///|
/// Replay is the predicate, not the process exit code alone.
pub fn replay(lines : Array[String]) -> Json raise {
  if lines.length() > 2048 {
    raise @model.InputError("evidence physical line limit: 2048")
  }
  let s = @session.Session::new()
  let mut bytes = 0
  for i, line in lines {
    bytes = bytes + @utf8.encode(line).length() + 1
    if bytes > 8388608 {
      raise @model.InputError("evidence byte limit: 8 MiB")
    }
    s.feed_line(line, i + 1)
  }
  let r = s.report()
  if s.is_stopped() ||
    @model.field(r, "analysis_complete") != Json::boolean(true) {
    raise @model.InputError("evidence requires complete source replay")
  }
  r
}

///|
pub fn target(report : Json, id : String) -> Json raise {
  for f in @model.array(@model.field(report, "findings")) {
    if @model.field(f, "id") == Json::string(id) {
      return f
    }
  }
  raise @model.InputError("target finding not found")
}

///|
fn replace(j : Json, key : String, value : Json) -> Json raise {
  match j {
    Object(m) => {
      let c = m.copy()
      c[key] = value
      Json::object(c)
    }
    _ => raise @model.InputError("expected evidence object")
  }
}

///|
fn rec_uri(rec : Json) -> Json {
  if @model.field(rec, "kind") == Json::string("checkpoint") {
    @model.field(rec, "uri")
  } else {
    @model.field(
      @model.field(
        @model.field(@model.field(rec, "message"), "params"),
        "textDocument",
      ),
      "uri",
    )
  }
}

///|
fn mapped_target(original : Json, uri : String) -> Json raise {
  let fp = replace(
    replace(@model.field(original, "fingerprint"), "uri", Json::string(uri)),
    "label",
    Json::string(""),
  )
  replace(
    replace(
      replace(original, "uri", Json::string(uri)),
      "label",
      Json::string(""),
    ),
    "fingerprint",
    fp,
  )
}

///|
/// Strict allowlist: free-form metadata is not implicitly safe to share.
fn sanitized(rec : Json, uris : Map[String, String]) -> Json raise {
  let kind = @model.string_field(rec, "kind")
  if kind == "meta" {
    @model.only_fields(rec, [
      "kind", "schema_version", "position_encoding", "capture_mode", "provenance",
      "producer", "encoding_basis", "evidence_scope", "host_version",
    ])
    return {
      "kind": "meta",
      "schema_version": 1,
      "position_encoding": "utf-16",
      "capture_mode": "fragment",
      "provenance": @model.field(rec, "provenance"),
      "producer": "edittrace-share",
    }
  }
  let original = @model.str(rec_uri(rec))
  let uri = uris.get(original).unwrap_or("")
  if uri.is_empty() {
    raise @model.InputError("unmapped document identity")
  }
  if kind == "checkpoint" {
    @model.only_fields(rec, [
      "kind", "seq", "uri", "version", "text", "source", "label",
    ])
    return {
      "kind": "checkpoint",
      "seq": @model.field(rec, "seq"),
      "uri": Json::string(uri),
      "version": @model.field(rec, "version"),
      "text": @model.field(rec, "text"),
      "source": "edittrace-share",
      "label": "",
    }
  }
  @model.only_fields(rec, ["kind", "seq", "direction", "message"])
  let message = @model.field(rec, "message")
  @model.only_fields(message, ["jsonrpc", "method", "params"])
  let rpc_method = @model.string_field(message, "method")
  let params = @model.field(message, "params")
  @model.only_fields(params, ["textDocument", "contentChanges"])
  let doc = @model.field(params, "textDocument")
  let next_doc : Json = if rpc_method == "textDocument/didOpen" {
    @model.only_fields(doc, ["uri", "languageId", "version", "text"])
    {
      "uri": Json::string(uri),
      "languageId": "text",
      "version": @model.field(doc, "version"),
      "text": @model.field(doc, "text"),
    }
  } else if rpc_method == "textDocument/didChange" {
    @model.only_fields(doc, ["uri", "version"])
    for edit in @model.array(@model.field(params, "contentChanges")) {
      @model.only_fields(edit, ["range", "rangeLength", "text"])
      if @model.has(edit, "range") {
        let range = @model.field(edit, "range")
        @model.only_fields(range, ["start", "end"])
        @model.only_fields(@model.field(range, "start"), ["line", "character"])
        @model.only_fields(@model.field(range, "end"), ["line", "character"])
      }
    }
    { "uri": Json::string(uri), "version": @model.field(doc, "version") }
  } else if rpc_method == "textDocument/didClose" {
    @model.only_fields(doc, ["uri"])
    { "uri": Json::string(uri) }
  } else {
    raise @model.InputError("share does not support this message rpc_method")
  }
  if rpc_method != "textDocument/didChange" &&
    @model.has(params, "contentChanges") {
    raise @model.InputError("unexpected contentChanges")
  }
  let next_params : Json = if rpc_method == "textDocument/didChange" {
    {
      "textDocument": next_doc,
      "contentChanges": @model.field(params, "contentChanges"),
    }
  } else {
    { "textDocument": next_doc }
  }
  {
    "kind": "message",
    "seq": @model.field(rec, "seq"),
    "direction": @model.field(rec, "direction"),
    "message": {
      "jsonrpc": "2.0",
      "method": Json::string(rpc_method),
      "params": next_params,
    },
  }
}

///|
pub fn share(lines : Array[String], id : String) -> (Array[String], Json) raise {
  let before = replay(lines)
  let wanted = target(before, id)
  let uris : Map[String, String] = Map([])
  for line in lines {
    if !line.trim().is_empty() {
      let rec = @model.parse_bounded(line)
      if rec_uri(rec) is String(uri) && !uris.contains(uri) {
        let number = (uris.length() + 1).to_string()
        uris[uri] = "file:///edittrace/document-" + number
      }
    }
  }
  let converted = lines.map(fn(line) raise {
    if line.trim().is_empty() {
      ""
    } else {
      @model.canonical(sanitized(@model.parse_bounded(line), uris))
    }
  })
  let after = replay(converted)
  let transformed = target(after, id)
  let mapped = uris.get(@model.string_field(wanted, "uri")).unwrap_or("")
  if transformed != mapped_target(wanted, mapped) ||
    @model.field(before, "exit_code") != @model.field(after, "exit_code") {
    raise @model.InputError(
      "identity conversion cannot preserve full target evidence",
    )
  }
  let preview : Json = {
    "kind": "share_plan",
    "schema_version": 1,
    "exit_code": 0,
    "analysis_complete": true,
    "document_count": @model.num(uris.length()),
    "physical_lines": @model.num(lines.length()),
    "output_bytes": @model.num(
      @utf8.encode(converted.join("\n") + "\n").length(),
    ),
    "source_text_retained": true,
    "identity_mapping_included": false,
    "display_summary": "Structural URI identities and metadata will be replaced. Source text, literals and secrets in it remain. Not full redaction.",
  }
  (converted, preview)
}

///|
pub fn minimize(
  lines : Array[String],
  id : String,
  max_runs : Int32,
) -> (Array[String], Json) raise {
  if max_runs < 1 || max_runs > 64 {
    raise @model.InputError("max-runs must be 1..64")
  }
  let original = replay(lines)
  let wanted = target(original, id)
  if @model.field(wanted, "rule_id") !=
    Json::string("ET009_CHECKPOINT_MISMATCH") {
    raise @model.InputError("minimize supports ET009_CHECKPOINT_MISMATCH only")
  }
  let uri = @model.field(wanted, "uri")
  for line in lines {
    if !line.trim().is_empty() {
      let other = rec_uri(@model.parse_bounded(line))
      if other != Json::null() && other != uri {
        raise @model.InputError("minimize supports single-document traces only")
      }
    }
  }
  let candidate = lines.copy()
  let weight = @utf8.encode(lines.join("\n")).length() + 1
  // Also bound repeated indexing/copy work for large physical line counts.
  let permitted = if weight > 134217728 / lines.length() {
    0
  } else {
    134217728 / (weight * lines.length())
  }
  let budget = if max_runs < permitted { max_runs } else { permitted }
  let mut runs = 0
  let mut accepted = 0
  let mut exhausted = false
  for i, line in lines {
    if line.trim().is_empty() {
      continue
    }
    let rec = @model.parse_bounded(line)
    let rpc_method = @model.field(@model.field(rec, "message"), "method")
    // Lock all lifecycle and checkpoints; physical lines and target ids remain stable.
    if @model.field(rec, "kind") != Json::string("message") ||
      rpc_method == Json::string("textDocument/didOpen") ||
      rpc_method == Json::string("textDocument/didClose") {
      continue
    }
    if runs >= budget {
      exhausted = true
      break
    }
    runs = runs + 1
    candidate[i] = ""
    let keep = try target(replay(candidate), id) == wanted catch {
      _ => false
    }
    if keep {
      accepted = accepted + 1
    } else {
      candidate[i] = line
    }
  }
  if target(replay(candidate), id) != wanted {
    raise @model.InputError("final minimized target differs")
  }
  let sequences : Array[Json] = []
  for line in candidate {
    if !line.trim().is_empty() {
      let rec = @model.parse_bounded(line)
      if @model.has(rec, "seq") {
        sequences.push(@model.field(rec, "seq"))
      }
    }
  }
  let stats : Json = {
    "kind": "minimize_report",
    "schema_version": 1,
    "exit_code": 0,
    "analysis_complete": true,
    "attempts": @model.num(runs),
    "accepted": @model.num(accepted),
    "budget_exhausted": Json::boolean(exhausted),
    "max_runs": @model.num(max_runs),
    "effective_runs": @model.num(budget),
    "retained_sequences": Json::array(sequences),
    "original_nonblank": @model.num(
      lines.filter(fn(s) { !s.trim().is_empty() }).length(),
    ),
    "retained_nonblank": @model.num(
      candidate.filter(fn(s) { !s.trim().is_empty() }).length(),
    ),
    "display_summary": "Verified full target finding preserved; lifecycle/checkpoints locked, original physical lines retained. Not a globally minimal trace.",
  }
  (candidate, stats)
}
