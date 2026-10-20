///|
pub fn convert(lines : Array[String]) -> Array[String] raise {
  let messages : Array[Json] = []
  let mut initialize_id = Json::null()
  let mut requested = false
  let mut responded = false
  let mut initialize_id_reused = false
  let mut evidence = "adapter_assumption_fragment_utf16"
  for i, raw in lines {
    if raw.trim().is_empty() {
      continue
    }
    let j = @model.parse_bounded(raw)
    let kind = @model.string_field(j, "type")
    let direction = match kind {
      "send-request" | "send-response" | "send-notification" =>
        "client_to_server"
      "receive-request" | "receive-response" | "receive-notification" =>
        "server_to_client"
      _ =>
        raise @model.InputError(
          "unsupported vscode-json message type at line " + (i + 1).to_string(),
        )
    }
    match @model.field(j, "timestamp") {
      Number(_, ..) => ()
      _ => raise @model.InputError("timestamp required")
    }
    let msg = @model.field(j, "message")
    @model.object(msg)
    if @model.string_field(msg, "jsonrpc") != "2.0" {
      raise @model.InputError("JSON-RPC 2.0 required")
    }
    if @model.has(j, "isLSPMessage") &&
      @model.field(j, "isLSPMessage") != Json::boolean(true) {
      raise @model.InputError("not a JSON-RPC trace message")
    }
    if kind == "send-notification" || kind == "receive-notification" {
      let _ = @model.string_field(msg, "method")
      if @model.has(msg, "id") {
        raise @model.InputError("notification trace cannot contain id")
      }
    } else if kind == "send-request" || kind == "receive-request" {
      let _ = @model.string_field(msg, "method")
      match @model.field(msg, "id") {
        String(_) | Number(_, ..) => ()
        _ =>
          raise @model.InputError("request trace requires string or number id")
      }
    } else if @model.has(msg, "method") ||
      !@model.has(msg, "id") ||
      @model.has(msg, "result") == @model.has(msg, "error") {
      raise @model.InputError("response trace shape differs from declared type")
    }
    if @model.field(msg, "method") == Json::string("initialize") {
      if requested || direction != "client_to_server" || kind != "send-request" {
        raise @model.InputError("mixed sessions or invalid initialize")
      }
      requested = true
      initialize_id = @model.field(msg, "id")
      if initialize_id == Json::null() {
        raise @model.InputError("initialize id missing")
      }
    }
    if requested &&
      kind == "send-request" &&
      @model.field(msg, "method") != Json::string("initialize") &&
      @model.field(msg, "id") == initialize_id {
      if !responded {
        raise @model.InputError("request id reused before initialize completed")
      }
      initialize_id_reused = true
    }
    if requested &&
      !initialize_id_reused &&
      direction == "server_to_client" &&
      kind == "receive-response" &&
      @model.field(msg, "id") == initialize_id {
      if responded {
        raise @model.InputError("duplicate initialize response")
      }
      let caps = @model.field(@model.field(msg, "result"), "capabilities")
      @model.object(caps)
      let encoding = @model.field(caps, "positionEncoding")
      if encoding != Json::null() && encoding != Json::string("utf-16") {
        raise @model.InputError("negotiated position encoding is not UTF-16")
      }
      evidence = if encoding == Json::null() {
        "initialize_default_utf16"
      } else {
        "initialize_explicit_utf16"
      }
      responded = true
    }
    if messages.length() >= 100000 {
      raise @model.InputError("message limit")
    }
    messages.push(
      Json::object({
        "kind": Json::string("message"),
        "seq": @model.num(messages.length() + 1),
        "direction": Json::string(direction),
        "message": msg,
        "source_line": @model.num(i + 1),
        "source_type": Json::string(kind),
      }),
    )
  }
  if messages.is_empty() || (requested && !responded) {
    raise @model.InputError("empty log or incomplete initialization")
  }
  let result = [
    @model.canonical(
      Json::object({
        "kind": Json::string("meta"),
        "schema_version": @model.num(1),
        "position_encoding": Json::string("utf-16"),
        "capture_mode": Json::string("fragment"),
        "initialization_observed": Json::boolean(responded),
        "provenance": Json::string("captured"),
        "producer": Json::string("vscode-json-adapter"),
        "encoding_basis": Json::string(evidence),
        "source_format": Json::string("vscode-json-client-perspective"),
      }),
    ),
  ]
  for msg in messages {
    result.push(@model.canonical(msg))
  }
  result
}
