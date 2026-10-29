///|
pub(all) suberror InputError {
  InputError(String)
}

///|
pub fn tool_version() -> String {
  "0.4.0"
}

///|
pub fn only_fields(j : Json, allowed : Array[String]) -> Unit raise InputError {
  match j {
    Object(m) =>
      for key, _ in m {
        if !allowed.contains(key) {
          raise InputError("unsupported field: " + key)
        }
      }
    _ => raise InputError("expected object")
  }
}

///|
pub fn field(j : Json, name : String) -> Json {
  match j {
    Object(m) => m.get(name).unwrap_or(Json::null())
    _ => Json::null()
  }
}

///|
pub fn has(j : Json, name : String) -> Bool {
  match j {
    Object(m) => m.contains(name)
    _ => false
  }
}

///|
pub fn str(j : Json) -> String raise InputError {
  match j {
    String(s) => s
    _ => raise InputError("expected string")
  }
}

///|
pub fn string_field(j : Json, name : String) -> String raise InputError {
  match field(j, name) {
    String(s) => s
    _ => raise InputError("expected string field: " + name)
  }
}

///|
pub fn integer(j : Json) -> Int32 raise InputError {
  match j {
    Number(n, ..) => {
      if n < -2147483648.0 || n > 2147483647.0 || n != n {
        raise InputError("integer out of 32-bit range")
      }
      let i = n.to_int()
      if i.to_double() != n {
        raise InputError("expected integral number")
      }
      i
    }
    _ => raise InputError("expected integer")
  }
}

///|
pub fn int_field(j : Json, name : String) -> Int32 raise InputError {
  integer(field(j, name))
}

///|
pub fn uint_field(j : Json, name : String) -> Int32 raise InputError {
  let n = int_field(j, name)
  if n < 0 {
    raise InputError("expected unsigned field: " + name)
  }
  n
}

///|
pub fn array(j : Json) -> Array[Json] raise InputError {
  match j {
    Array(a) => a
    _ => raise InputError("expected array")
  }
}

///|
pub fn object(j : Json) -> Unit raise InputError {
  match j {
    Object(_) => ()
    _ => raise InputError("expected object")
  }
}

///|
pub fn num(n : Int32) -> Json {
  Json::number(n.to_double())
}

///|
pub fn canonical(j : Json) -> String {
  match j {
    Object(m) => {
      let keys = m.keys().to_array()
      keys.sort()
      let parts : Array[String] = []
      for k in keys {
        parts.push(Json::string(k).stringify() + ":" + canonical(m[k]))
      }
      "{" + parts.join(",") + "}"
    }
    Array(a) => "[" + a.map(canonical).join(",") + "]"
    _ => j.stringify()
  }
}

///|
pub fn excerpt(s : String) -> String {
  if s.char_length() <= 200 {
    s
  } else {
    s[:s.offset_of_nth_char(200).unwrap_or(s.length())].to_owned() + "…"
  }
}
