EditTrace 0.2.0 Preview adds real-input entry points and portable text-edit regressions:

- Import fixed JSON-RPC JSON traces with initialization encoding evidence.
- Preview immutable-baseline text edits for formatting and cross-file textual rename; check versions, overlaps and independently observed actual text.
- Record VS Code document events, inspect predicted diffs and save reviewable regression drafts. Platform VSIX files bundle the native MoonBit core.
- Run self-contained cases/suites in CI, use typed MoonBit APIs, and export document-filtered reproduction packages with target revalidation.

This preview was checked with 337 native/CLI acceptance assertions, 19 native tests, 500 independent reference sessions / 4000 checkpoints, 5 Node transport/regression checks, and 14 actual VS Code 1.138.0 host checks on Windows. The release includes only archives produced by the passing Windows/Linux workflow for the linked source commit. Linux archives are exercised in CI; Linux GUI integration has not been manually tested.

Download the platform CLI ZIP or VSIX and follow the included QUICKSTART/extension README. Verify files against SHA256SUMS. The CLI and extension are both version 0.2.0; older 0.1.0 reproduction bundles remain supported.

Scope: UTF-16 and text-only edits. Rename previews cannot verify file resource operations or provider base versions. Editor event capture does not prove language-server memory or program semantics. Real host captures and labeled fault injections demonstrate behavior, not human adoption or demand size. Source text can be present in shared cases. This is a prerelease for evaluation; no Marketplace or Mooncakes publication is claimed.
