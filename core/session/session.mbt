///|
struct Document {
  mut generation : Int32
  mut opened : Bool
  mut known : Bool
  mut content : String
  mut version : Int32
  mut highest : Int32
  mut checkpoint : Int32
  mut unknown_reported : Bool
  mut unresolved : Bool
}

///|
pub struct Session {
  priv docs : Map[String, Document]
  priv findings : Array[Json]
  priv mut meta : Json
  priv mut has_meta : Bool
  priv mut stopped : Bool
  priv mut input_error : Json
  priv mut seq : Int32
  priv mut records : Int32
  priv mut supported : Int32
  priv mut ignored : Int32
  priv mut rejected : Int32
  priv mut passed : Int32
  priv mut mismatched : Int32
  priv mut unavailable : Int32
  priv max_document_bytes : Int32
  priv max_open_documents : Int32
  priv max_findings : Int32
}

///|
pub fn Session::new(
  max_document_bytes~ : Int32 = 4194304,
  max_open_documents~ : Int32 = 256,
  max_findings~ : Int32 = 10000,
) -> Session {
  {
    docs: {},
    findings: [],
    meta: Json::null(),
    has_meta: false,
    stopped: false,
    input_error: Json::null(),
    seq: 0,
    records: 0,
    supported: 0,
    ignored: 0,
    rejected: 0,
    passed: 0,
    mismatched: 0,
    unavailable: 0,
    max_document_bytes,
    max_open_documents,
    max_findings,
  }
}

///|
pub fn Session::last_seq(self : Session) -> Int32 {
  self.seq
}

///|
pub fn Session::is_stopped(self : Session) -> Bool {
  self.stopped
}

///|
pub fn Session::all_findings(self : Session) -> Array[Json] {
  self.findings.copy()
}

///|
pub fn Session::fail(self : Session, detail : String, line : Int32) -> Unit {
  if !self.stopped {
    self.stopped = true
    self.input_error = Json::object({
      "message": Json::string(detail),
      "physical_line": @model.num(line),
    })
  }
}

///|
fn Session::open_count(self : Session) -> Int32 {
  let mut count = 0
  for _, d in self.docs {
    if d.opened {
      count = count + 1
    }
  }
  count
}

///|
fn fresh() -> Document {
  {
    generation: 0,
    opened: false,
    known: false,
    content: "",
    version: 0,
    highest: -2147483648,
    checkpoint: 0,
    unknown_reported: false,
    unresolved: false,
  }
}

///|
fn Session::add(
  self : Session,
  code : Int32,
  seq : Int32,
  line : Int32,
  uri : String,
  index : Int32,
  version : Int32,
  detail : String,
  before~ : String = "",
  after~ : String = "",
  coordinates~ : Json = Json::null(),
  related~ : Int32 = 0,
  label~ : String = "",
) -> Unit {
  if self.findings.length() >= self.max_findings {
    self.fail("finding limit exceeded", line)
    return
  }
  let (rule, severity, classification) = match code {
    1 => ("ET001_CHANGE_WITHOUT_OPEN", "error", "protocol")
    2 => ("ET002_DUPLICATE_OPEN", "error", "protocol")
    3 => ("ET003_CLOSE_WITHOUT_OPEN", "warning", "protocol")
    4 => ("ET004_VERSION_NOT_INCREASING", "error", "protocol")
    5 => ("ET005_RANGE_REVERSED", "error", "protocol")
    6 => ("ET006_CHARACTER_CLAMPED", "note", "protocol")
    7 => ("ET007_LINE_UNREPLAYABLE", "warning", "product_policy")
    8 => ("ET008_SURROGATE_BOUNDARY", "warning", "product_policy")
    9 => ("ET009_CHECKPOINT_MISMATCH", "error", "external_checkpoint")
    10 => ("ET010_CHECKPOINT_UNAVAILABLE", "warning", "external_checkpoint")
    11 => ("ET011_DIRECTION_INVALID", "error", "protocol")
    12 => ("ET012_RANGE_LENGTH_MISMATCH", "warning", "protocol")
    13 => ("ET013_STATE_UNKNOWN", "warning", "product_policy")
    _ => ("ET014_EMPTY_CHANGES", "warning", "product_policy")
  }
  let gen = match self.docs.get(uri) {
    Some(d) => d.generation
    None => 0
  }
  let id = rule +
    ":" +
    seq.to_string() +
    ":" +
    index.to_string() +
    ":" +
    self.findings.length().to_string()
  self.findings.push(
    Json::object({
      "id": Json::string(id),
      "rule_id": Json::string(rule),
      "severity": Json::string(severity),
      "classification": Json::string(classification),
      "seq": @model.num(seq),
      "physical_line": @model.num(line),
      "uri": Json::string(uri),
      "generation": @model.num(gen),
      "change_index": @model.num(index),
      "version": @model.num(version),
      "message": Json::string(detail),
      "before_excerpt": Json::string(@model.excerpt(before)),
      "after_excerpt": Json::string(@model.excerpt(after)),
      "coordinates": coordinates,
      "related_seq": @model.num(related),
      "label": Json::string(label),
      "fingerprint": Json::object({
        "rule_id": Json::string(rule),
        "uri": Json::string(uri),
        "generation": @model.num(gen),
        "seq": @model.num(seq),
        "change_index": @model.num(index),
        "label": Json::string(label),
      }),
    }),
  )
}

///|
fn validate_changes(changes : Array[Json]) -> Unit raise @model.InputError {
  for c in changes {
    @model.object(c)
    let _ = @model.string_field(c, "text")
    if @model.has(c, "range") {
      let r = @model.field(c, "range")
      @model.object(r)
      let _ = @text.position(@model.field(r, "start"))
      let _ = @text.position(@model.field(r, "end"))
    }
    if @model.has(c, "rangeLength") {
      let _ = @model.uint_field(c, "rangeLength")
    }
  }
}

///|
fn Session::ensure_size(
  self : Session,
  content : String,
) -> Unit raise @model.InputError {
  if @utf8.encode(content).length() > self.max_document_bytes {
    raise @model.InputError("document byte limit exceeded")
  }
}

///|
fn Session::message(
  self : Session,
  rec : Json,
  seq : Int32,
  line : Int32,
) -> Unit raise @model.InputError {
  let direction = @model.string_field(rec, "direction")
  if direction != "client_to_server" && direction != "server_to_client" {
    raise @model.InputError("invalid direction")
  }
  let m = @model.field(rec, "message")
  @model.object(m)
  if @model.string_field(m, "jsonrpc") != "2.0" {
    raise @model.InputError("expected JSON-RPC 2.0")
  }
  let rpc_method = match @model.field(m, "method") {
    String(s) => s
    _ => ""
  }
  if rpc_method != "textDocument/didOpen" &&
    rpc_method != "textDocument/didChange" &&
    rpc_method != "textDocument/didClose" {
    self.ignored = self.ignored + 1
    return
  }
  if @model.has(m, "id") {
    raise @model.InputError("document sync must be a notification, without id")
  }
  let params = @model.field(m, "params")
  @model.object(params)
  let td = @model.field(params, "textDocument")
  @model.object(td)
  let uri = @model.string_field(td, "uri")
  if uri.is_empty() {
    raise @model.InputError("document URI must not be empty")
  }
  let version = if rpc_method == "textDocument/didClose" {
    0
  } else {
    @model.int_field(td, "version")
  }
  // Validate the entire supported notification before making any state changes.
  let initial = if rpc_method == "textDocument/didOpen" {
    let _ = @model.string_field(td, "languageId")
    @model.string_field(td, "text")
  } else {
    ""
  }
  let changes = if rpc_method == "textDocument/didChange" {
    let a = @model.array(@model.field(params, "contentChanges"))
    validate_changes(a)
    a
  } else {
    []
  }
  if direction != "client_to_server" {
    self.rejected = self.rejected + 1
    self.add(
      11, seq, line, uri, -1, version, "Sync notifications must come from the client; message not applied.",
    )
    return
  }
  self.supported = self.supported + 1
  if rpc_method == "textDocument/didOpen" {
    self.ensure_size(initial)
    let d = self.docs.get(uri).unwrap_or(fresh())
    if d.opened {
      self.add(
        2,
        seq,
        line,
        uri,
        -1,
        version,
        "Duplicate open makes the current content unknown; previous content was not overwritten.",
        before=d.content,
      )
      d.known = false
      return
    }
    if self.open_count() >= self.max_open_documents {
      raise @model.InputError("open document limit exceeded")
    }
    d.generation = d.generation + 1
    d.opened = true
    d.known = true
    d.content = initial
    d.version = version
    d.highest = version
    d.checkpoint = 0
    d.unknown_reported = false
    d.unresolved = false
    self.docs[uri] = d
    return
  }
  if rpc_method == "textDocument/didClose" {
    match self.docs.get(uri) {
      Some(d) if d.opened => {
        d.opened = false
        d.known = false
        d.content = ""
        d.unknown_reported = false
      }
      _ =>
        self.add(
          3, seq, line, uri, -1, version, "Close without an open document.",
        )
    }
    return
  }
  let d = self.docs.get(uri).unwrap_or(fresh())
  if !d.opened {
    self.docs[uri] = d
    self.add(
      1, seq, line, uri, -1, version, "Change has no didOpen baseline; current text cannot be reconstructed.",
    )
    d.known = false
    d.unresolved = true
    // Keep the unresolved URI visible in the final completeness check.
    d.highest = version
    return
  }
  if version <= d.highest {
    self.add(
      4,
      seq,
      line,
      uri,
      -1,
      version,
      "Version must increase; gaps are allowed. Notification not applied.",
      before=d.content,
    )
    d.known = false
    return
  }
  d.highest = version
  if changes.is_empty() {
    self.add(
      14, seq, line, uri, -1, version, "v1 conservative policy: empty changes require a new baseline.",
    )
    d.known = false
    return
  }
  let full_first = !@model.has(changes[0], "range")
  if !d.known && !full_first {
    if !d.unknown_reported {
      self.add(
        13, seq, line, uri, -1, version, "Incremental edits depend on unknown text; later repeats suppressed.",
      )
      d.unknown_reported = true
    }
    return
  }
  let before = d.content
  let mut candidate = before
  let mut valid = true
  for i, c in changes {
    let insert = @model.string_field(c, "text")
    self.ensure_size(insert)
    if !@model.has(c, "range") {
      candidate = insert
    } else {
      let range = @model.field(c, "range")
      let a = @text.position(@model.field(range, "start"))
      let b = @text.position(@model.field(range, "end"))
      try {
        let (next, oa, ob) = @text.replace(candidate, a, b, insert)
        let coords = Json::object({
          "original": range,
          "effective_offsets": Json::array([
            @model.num(oa.value),
            @model.num(ob.value),
          ]),
        })
        if oa.clamped || ob.clamped {
          self.add(
            6,
            seq,
            line,
            uri,
            i,
            version,
            "Column clamped to line length as specified by LSP.",
            coordinates=coords,
          )
        }
        if @model.has(c, "rangeLength") &&
          @model.uint_field(c, "rangeLength") != ob.value - oa.value {
          self.add(
            12,
            seq,
            line,
            uri,
            i,
            version,
            "Deprecated rangeLength differs from the range; range controls the edit.",
            coordinates=coords,
          )
        }
        candidate = next
      } catch {
        @text.LineUnreplayable => {
          self.add(
            7,
            seq,
            line,
            uri,
            i,
            version,
            "v1 policy: unsupported line position; batch rolled back.",
            before~,
            coordinates=range,
          )
          valid = false
        }
        @text.SurrogateBoundary => {
          self.add(
            8,
            seq,
            line,
            uri,
            i,
            version,
            "v1 policy: boundary splits a UTF-16 surrogate pair; batch rolled back.",
            before~,
            coordinates=range,
          )
          valid = false
        }
        @text.Reversed => {
          self.add(
            5,
            seq,
            line,
            uri,
            i,
            version,
            "Range start is after end; batch rolled back.",
            before~,
            coordinates=range,
          )
          valid = false
        }
        _ => raise @model.InputError("unexpected edit validation failure")
      }
    }
    self.ensure_size(candidate)
    if !valid || self.stopped {
      break
    }
  }
  if valid && !self.stopped {
    d.content = candidate
    d.version = version
    d.known = true
    d.unknown_reported = false
  } else {
    d.known = false
  }
}

///|
fn Session::checkpoint(
  self : Session,
  rec : Json,
  seq : Int32,
  line : Int32,
) -> Unit raise @model.InputError {
  let uri = @model.string_field(rec, "uri")
  let version = @model.int_field(rec, "version")
  let expected = @model.string_field(rec, "text")
  self.ensure_size(expected)
  let source = @model.string_field(rec, "source")
  if source.is_empty() {
    raise @model.InputError("checkpoint source must not be empty")
  }
  let label = if @model.has(rec, "label") {
    @model.string_field(rec, "label")
  } else {
    ""
  }
  match self.docs.get(uri) {
    Some(d) if d.opened && d.known && d.version == version =>
      if d.content == expected {
        self.passed = self.passed + 1
        d.checkpoint = seq
      } else {
        self.mismatched = self.mismatched + 1
        self.add(
          9,
          seq,
          line,
          uri,
          -1,
          version,
          "Independent checkpoint differs. Root cause and server internal state are not established; related_seq is the last passing checkpoint.",
          before=d.content,
          after=expected,
          related=d.checkpoint,
          label~,
        )
      }
    _ => {
      self.unavailable = self.unavailable + 1
      self.add(
        10,
        seq,
        line,
        uri,
        -1,
        version,
        "Checkpoint could not be compared: missing, closed, unknown or different version.",
        label~,
      )
    }
  }
}

///|
fn Session::feed(
  self : Session,
  rec : Json,
  line : Int32,
) -> Unit raise @model.InputError {
  @model.object(rec)
  let kind = @model.string_field(rec, "kind")
  if !self.has_meta {
    if kind != "meta" {
      raise @model.InputError("first record must be meta")
    }
    if @model.int_field(rec, "schema_version") != 1 {
      raise @model.InputError("unsupported schema_version")
    }
    if @model.string_field(rec, "position_encoding") != "utf-16" {
      raise @model.InputError(
        "unsupported position_encoding; v1 requires utf-16",
      )
    }
    let capture = @model.string_field(rec, "capture_mode")
    let provenance = @model.string_field(rec, "provenance")
    let _ = @model.string_field(rec, "producer")
    if capture != "full" && capture != "fragment" {
      raise @model.InputError("invalid capture_mode")
    }
    if provenance != "synthetic" && provenance != "captured" {
      raise @model.InputError("invalid provenance")
    }
    self.meta = rec
    self.has_meta = true
    return
  }
  let seq = @model.int_field(rec, "seq")
  if seq <= self.seq {
    raise @model.InputError("seq must be positive and strictly increasing")
  }
  self.seq = seq
  self.records = self.records + 1
  if self.records > 100000 {
    raise @model.InputError("record limit exceeded")
  }
  match kind {
    "message" => self.message(rec, seq, line)
    "checkpoint" => self.checkpoint(rec, seq, line)
    _ => raise @model.InputError("unknown record kind: " + kind)
  }
}

///|
pub fn Session::feed_line(self : Session, raw : String, line : Int32) -> Unit {
  if self.stopped || raw.trim().is_empty() {
    return
  }
  try {
    let j = @model.parse_bounded(raw)
    self.feed(j, line)
  } catch {
    @model.InputError(s) => self.fail(s, line)
    _ => self.fail("invalid JSON or nesting depth exceeded", line)
  }
}

///|
pub fn Session::snapshot(self : Session, uri : String) -> String? {
  match self.docs.get(uri) {
    Some(d) if d.opened && d.known => Some(d.content)
    _ => None
  }
}

///|
pub fn Session::report(self : Session, fail_warning~ : Bool = false) -> Json {
  if !self.has_meta && !self.stopped {
    self.fail("missing meta record", 1)
  }
  let keys = self.docs.keys().to_array()
  keys.sort()
  let documents : Array[Json] = []
  let mut unknown = 0
  for uri in keys {
    let d = self.docs[uri]
    let unresolved = d.unresolved || (!d.known && d.opened)
    if unresolved {
      unknown = unknown + 1
    }
    documents.push(
      Json::object({
        "uri": Json::string(uri),
        "generation": @model.num(d.generation),
        "status": Json::string(
          if unresolved {
            "unknown"
          } else if d.opened {
            "known"
          } else {
            "closed"
          },
        ),
        "last_successful_version": if d.generation == 0 {
          Json::null()
        } else {
          @model.num(d.version)
        },
        "highest_observed_version": @model.num(d.highest),
        "last_known_excerpt": Json::string(@model.excerpt(d.content)),
      }),
    )
  }
  let complete = !self.stopped && unknown == 0
  let mut errors = 0
  let mut warnings = 0
  let mut notes = 0
  for f in self.findings {
    match @model.field(f, "severity") {
      String("error") => errors = errors + 1
      String("warning") => warnings = warnings + 1
      _ => notes = notes + 1
    }
  }
  let exit_code = if !complete {
    2
  } else if errors > 0 || (fail_warning && warnings > 0) {
    1
  } else {
    0
  }
  Json::object({
    "schema_version": @model.num(1),
    "tool_version": Json::string(@model.tool_version()),
    "scope": Json::string("document_sync_utf16_v1"),
    "encoding_evidence": Json::string("declared"),
    "analysis_complete": Json::boolean(complete),
    "exit_code": @model.num(exit_code),
    "meta": self.meta,
    "input_error": self.input_error,
    "counts": Json::object({
      "records": @model.num(self.records),
      "supported_messages": @model.num(self.supported),
      "ignored_messages": @model.num(self.ignored),
      "rejected_messages": @model.num(self.rejected),
      "checkpoints_passed": @model.num(self.passed),
      "checkpoints_mismatched": @model.num(self.mismatched),
      "checkpoints_unavailable": @model.num(self.unavailable),
      "unknown_documents": @model.num(unknown),
      "errors": @model.num(errors),
      "warnings": @model.num(warnings),
      "notes": @model.num(notes),
    }),
    "documents": Json::array(documents),
    "findings": Json::array(self.findings.copy()),
    "limitations": Json::array([
      Json::string(
        "Declared UTF-16 document-sync subset only; ignored methods are not audited.",
      ),
      Json::string(
        "Client-message replay does not establish server internal state or root cause.",
      ),
    ]),
  })
}
