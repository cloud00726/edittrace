///|
pub async fn read(path : String, max_bytes~ : Int32 = 8388608) -> String {
  let f = @fs.open(path, mode=ReadOnly)
  defer f.close()
  let buffer = @buffer.Buffer()
  while true {
    match f.read_some(max_len=65536) {
      None => break
      Some(bytes) => {
        if buffer.length() + bytes.length() > max_bytes {
          raise @model.InputError("workflow input byte limit")
        }
        for b in bytes {
          buffer.write_byte(b)
        }
      }
    }
  }
  @utf8.decode(buffer.to_bytes(), ignore_bom=true)
}

///|
pub async fn import_log(path : String, destination : String) -> Unit {
  let raw = read(path, max_bytes=67108864)
  let lines : Array[String] = []
  for line in raw.split("\n") {
    let s = line.to_owned()
    if @utf8.encode(s).length() > 8388608 {
      raise @model.InputError("trace record byte limit")
    }
    lines.push(s)
  }
  let converted = @vscode_trace.convert(lines)
  let mut total = 0
  for line in converted {
    let bytes = @utf8.encode(line).length()
    total = total + bytes + 1
    if bytes > 8388608 || total > 67108864 {
      raise @model.InputError("normalized trace exceeds audit resource limits")
    }
  }
  @fs.write_file(
    destination,
    converted.join("\n") + "\n",
    create_mode=CreateNew,
  )
}

///|
pub async fn execute(command : String, path : String) -> Json {
  let input = @model.parse_bounded(read(path))
  match command {
    "check-edits" => @edit_plan.check(input)
    "case" => @case.safe_run(input)
    "suite" => @case.suite(input)
    _ => raise @model.InputError("unsupported workflow command")
  }
}

///|
pub async fn create_case(path : String, destination : String) -> Json {
  let input = @model.parse_bounded(read(path))
  let result = @case.run(input)
  if @model.int_field(result, "exit_code") != 0 {
    raise @model.InputError(
      "case expectations do not match; refusing verified export",
    )
  }
  @fs.mkdir(destination, allow_exist=false)
  @fs.write_file(
    destination + "/case.json",
    @model.canonical(input) + "\n",
    create_mode=CreateNew,
  )
  let verified = execute("case", destination + "/case.json")
  if @model.int_field(verified, "exit_code") != 0 {
    raise @model.InputError("written case failed verification")
  }
  @fs.write_file(
    destination + "/README.md",
    "# EditTrace regression case\n\nRun: edittrace case run case.json --format json\n\nContains source text; review before sharing. No scripts or external paths are executed.\n",
    create_mode=CreateNew,
  )
  verified
}
