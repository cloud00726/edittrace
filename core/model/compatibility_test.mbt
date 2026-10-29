///|
test "bundle producer family rejects noncanonical and future versions" {
  for version in ["0.1.0", "0.2.0", "0.3.0", "0.4.2"] {
    assert_true(@model.supported_bundle_version(version))
  }
  for
    version in [
      "0.0.0", "1.0.0", "0.5.0", "0.02.0", "0.2.-1", "0.3.0-unknown", "not-version",
    ] {
    assert_false(@model.supported_bundle_version(version))
  }
}
