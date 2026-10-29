///|
pub fn supported_bundle_version(version : String) -> Bool {
  try {
    let parts = version.split(".").map(fn(s) { s.to_owned() }).to_array()
    if parts.length() != 3 {
      return false
    }
    let numbers = parts.map(fn(s) raise { @string.parse_int(s) })
    for i, n in numbers {
      if n < 0 || n.to_string() != parts[i] {
        return false
      }
    }
    numbers[0] == 0 && numbers[1] >= 1 && numbers[1] <= 4
  } catch {
    _ => false
  }
}
