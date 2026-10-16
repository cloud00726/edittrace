///|
extern "C" fn exit_process(code : Int32) = "exit"

///|
let help : String =
  #|EditTrace 0.1.0 — offline UTF-16 LSP document-sync auditing
  #|edittrace audit <trace.jsonl> [--format text|json] [--fail-on error|warning] [--out <file>]
  #|edittrace replay <trace.jsonl> --uri <uri> --at-seq <n> [--out <file>]
  #|edittrace export <trace.jsonl> --finding <id> --out <new-directory>
  #|edittrace verify <bundle-directory> [--out <new-file>]
  #|Limits (positive values, only lower the defaults):
  #|--max-record-bytes --max-input-bytes --max-document-bytes --max-open-documents --max-findings
  #|Exit: 0 complete/pass; 1 complete/findings; 2 incomplete/input/IO/usage.
  #|Input is EditTrace JSONL v1, not arbitrary editor logs. No server internals are observed.

///|
fn command_help(command : String) -> String {
  match command {
    "audit" =>
      "edittrace audit <trace.jsonl> [--format text|json] [--fail-on error|warning] [--out <new-file>]\nAudit returns 0 for complete/pass, 1 for complete/findings, 2 for incomplete/input/IO.\n"
    "replay" =>
      "edittrace replay <trace.jsonl> --uri <uri> --at-seq <positive-record-seq> [--out <new-file>]\nThe requested record must exist. Terminal output is JSON-escaped; files contain exact UTF-8.\n"
    "export" =>
      "edittrace export <trace.jsonl> --finding <finding-id> --out <new-directory>\nExports the complete prefix, verifies its target fingerprint, and refuses an existing directory.\n"
    _ =>
      "edittrace verify <bundle-directory> [--out <new-file>]\nRechecks trace.jsonl, finding.json and manifest.json. Success exits 0 even if the reproduced audit has findings. Not a cryptographic authenticity check.\n"
  }
}

///|
fn option_int(
  opts : Map[String, String],
  key : String,
  default : Int32,
) -> Int32 raise {
  match opts.get(key) {
    None => default
    Some(s) => {
      let n = @string.parse_int(s)
      if n <= 0 || n > default {
        raise @model.InputError("invalid lowered limit: " + key)
      }
      n
    }
  }
}

///|
async fn emit(content : String, output : String?) -> Unit {
  match output {
    Some(path) => @fs.write_file(path, content, create_mode=CreateNew)
    None => @stdio.stdout.write(content)
  }
}

///|
async fn run(args : Array[String]) -> Int32 {
  if args.length() == 1 || (args.length() == 2 && args[1] == "--help") {
    @stdio.stdout.write(help + "\n")
    return 0
  }
  if args.length() == 2 && args[1] == "--version" {
    @stdio.stdout.write("0.1.0\n")
    return 0
  }
  if args.length() < 3 {
    raise @model.InputError("missing command or input path; use --help")
  }
  let command = args[1]
  if command != "audit" &&
    command != "replay" &&
    command != "export" &&
    command != "verify" {
    raise @model.InputError("unknown command")
  }
  if args.length() == 3 && args[2] == "--help" {
    @stdio.stdout.write(command_help(command))
    return 0
  }
  let path = args[2]
  let opts : Map[String, String] = Map([])
  let common = [
    "--out", "--max-record-bytes", "--max-input-bytes", "--max-document-bytes", "--max-open-documents",
    "--max-findings",
  ]
  let specific = match command {
    "audit" => ["--format", "--fail-on"]
    "replay" => ["--uri", "--at-seq"]
    "export" => ["--finding"]
    _ => []
  }
  let mut i = 3
  while i < args.length() {
    let key = args[i]
    if (!common.contains(key) && !specific.contains(key)) ||
      opts.contains(key) ||
      i + 1 >= args.length() {
      raise @model.InputError("unknown, duplicate or missing option: " + key)
    }
    opts[key] = args[i + 1]
    i = i + 2
  }
  let defaults = @trace.defaults()
  let limits = @trace.Limits::{
    record_bytes: option_int(opts, "--max-record-bytes", defaults.record_bytes),
    input_bytes: option_int(opts, "--max-input-bytes", defaults.input_bytes),
    document_bytes: option_int(
      opts,
      "--max-document-bytes",
      defaults.document_bytes,
    ),
    open_documents: option_int(
      opts,
      "--max-open-documents",
      defaults.open_documents,
    ),
    findings: option_int(opts, "--max-findings", defaults.findings),
  }
  let output = opts.get("--out")
  if command == "verify" {
    emit(@model.canonical(@bundle.verify(path, limits)) + "\n", output)
    return 0
  }
  if command == "export" {
    let id = opts.get("--finding").unwrap_or("")
    let destination = output.unwrap_or("")
    if id.is_empty() || destination.is_empty() {
      raise @model.InputError("export requires --finding and --out")
    }
    let result = @bundle.export_prefix(path, id, destination, limits)
    @stdio.stdout.write(@model.canonical(result) + "\n")
    return 0
  }
  if command == "replay" {
    let uri = opts.get("--uri").unwrap_or("")
    let n = @string.parse_int(opts.get("--at-seq").unwrap_or("0"))
    if uri.is_empty() || n <= 0 {
      raise @model.InputError("replay requires --uri and positive --at-seq")
    }
    let (s, _) = @trace.load(path, limits~, until=Some(n))
    if s.is_stopped() || s.last_seq() < n {
      raise @model.InputError(
        "requested prefix unavailable or input incomplete",
      )
    }
    match s.snapshot(uri) {
      Some(text) => {
        emit(
          if output is None {
            Json::string(text).stringify() + "\n"
          } else {
            text
          },
          output,
        )
        return 0
      }
      None =>
        raise @model.InputError(
          "document is unknown or closed at the requested seq",
        )
    }
  }
  let format = opts.get("--format").unwrap_or("text")
  let fail_on = opts.get("--fail-on").unwrap_or("error")
  if format != "text" && format != "json" {
    raise @model.InputError("format must be text or json")
  }
  if fail_on != "error" && fail_on != "warning" {
    raise @model.InputError("fail-on must be error or warning")
  }
  let (s, _) = @trace.load(path, limits~)
  let result = s.report(fail_warning=fail_on == "warning")
  emit(
    if format == "json" {
      @model.canonical(result) + "\n"
    } else {
      @report.render(result)
    },
    output,
  )
  @model.int_field(result, "exit_code")
}

///|
async fn main {
  let code = run(@env.args()) catch {
    @model.InputError(s) => {
      @stdio.stderr.write("EditTrace: " + Json::string(s).stringify() + "\n")
      2
    }
    _ => {
      @stdio.stderr.write("EditTrace: IO or argument parsing failed\n")
      2
    }
  }
  exit_process(code)
}
