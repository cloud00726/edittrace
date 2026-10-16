///|
pub(all) struct Limits {
  record_bytes : Int32
  input_bytes : Int32
  document_bytes : Int32
  open_documents : Int32
  findings : Int32
}

///|
pub fn defaults() -> Limits {
  {
    record_bytes: 8388608,
    input_bytes: 67108864,
    document_bytes: 4194304,
    open_documents: 256,
    findings: 10000,
  }
}

///|
fn consume(
  s : @session.Session,
  b : @buffer.Buffer,
  line : Int32,
  until : Int32?,
  collected : Array[String],
  collect : Bool,
) -> Bool {
  try {
    let bytes = b.to_bytes()
    let raw = @utf8.decode(bytes, ignore_bom=line == 1)
    if !raw.trim().is_empty() && until is Some(target) {
      let rec = @model.parse_bounded(raw)
      if @model.has(rec, "seq") && @model.int_field(rec, "seq") > target {
        return false
      }
    }
    s.feed_line(raw, line)
    if collect {
      collected.push(raw)
    }
  } catch {
    _ => s.fail("invalid UTF-8 or invalid record while selecting prefix", line)
  }
  !s.is_stopped() &&
  (match until {
    Some(target) => s.last_seq() < target
    None => true
  })
}

///|
pub async fn load(
  path : String,
  limits~ : Limits = defaults(),
  until~ : Int32? = None,
  collect~ : Bool = false,
) -> (@session.Session, Array[String]) {
  let s = @session.Session::new(
    max_document_bytes=limits.document_bytes,
    max_open_documents=limits.open_documents,
    max_findings=limits.findings,
  )
  let lines : Array[String] = []
  let mut line = 1
  try {
    let f = @fs.open(path, mode=ReadOnly)
    defer f.close()
    let buffer = @buffer.Buffer()
    let mut total = 0
    let mut more = true
    while more {
      match f.read_some(max_len=65536) {
        None => {
          if buffer.length() > 0 {
            let _ = consume(s, buffer, line, until, lines, collect)
          }
          break
        }
        Some(bytes) =>
          for byte in bytes {
            total = total + 1
            if total > limits.input_bytes {
              s.fail("input byte limit exceeded", line)
              more = false
              break
            }
            if byte == b'\n' {
              more = consume(s, buffer, line, until, lines, collect)
              buffer.reset()
              line = line + 1
              if !more {
                break
              }
            } else {
              if buffer.length() >= limits.record_bytes {
                s.fail("record byte limit exceeded", line)
                more = false
                break
              }
              buffer.write_byte(byte)
            }
          }
      }
    }
  } catch {
    _ => s.fail("IO failure reading trace", line)
  }
  (s, lines)
}
