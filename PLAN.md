# EditTrace execution plan

Specification: docs/IMPLEMENTATION_SPEC.md (2026-10-15).

## Milestones

- [x] M0: verify compiler/native IO; compile CLI and parse trace metadata.
- [x] M1: UTF-16 text editing and independent boundary tests.
- [x] M2: transactional multi-document audit, lifecycle and recovery.
- [x] M3: checkpoints, stable reports, CLI and verified reproduction exports.
- [x] M4: 500 independent oracle sequences, limits, integration validation and CI.
- [x] M5: accurate documentation, competition drafts and validation evidence.

## Decisions

- Keep production implementation in MoonBit. Development scripts may generate independent fixtures and run CLI assertions.
- Use workspace-local tooling; do not change system PATH or execution policy.
- Do not publish, push, submit forms or manufacture identity information.
- Implement bounded input and deterministic reports before optional features.

## Current progress

Official toolchain 2026-10-12 installed into ../tooling/moon; archive SHA256 matched official checksum. Native CLI, chunked file IO, stdout/stderr and exit API compiled. Async dependency pinned to 0.22.5.

`moon test --target native`: 13 tests passed, including 500 generated independent sequences and 4000 checkpoints. Hand-calculated Unicode, CRLF-merging, rollback, negative/gapped versions, unknown-state recovery and limits passed. `audit examples/valid-unicode.jsonl --format json` returned 0 and a matching checkpoint.

Reference validation decision: Microsoft textdocument 1.0.12 retained an extra cached line when an inserted CR joined an existing LF. Recorded the exact observation in tests/oracle/reference-cache-observation.json. Generator recreates the independent reference after each edit, so later generated positions use fresh indexes. Expected text still comes from the independent implementation. This change corrected the generator's invalid future coordinates rather than weakening tests.

## Next

Local implementation is complete. Remaining work requires public repository/account and official competition actions, or is optional P1 scope.

## Final validation (2026-10-15)

- Native MoonBit: 17 tests passed; no project compiler warnings.
- Independent reference: 500 sequences / 4000 batch checkpoints, pinned 1.0.12, digest recorded.
- Full acceptance including clean-room build: 207 assertions passed. See docs/validation-results.json and artifacts/moon-*.log.
- Benchmark: 3 documents, a 1 MiB baseline and 10000 small edits, 0.4984 seconds in this run; peak memory not measured.
- New workspace-local toolchain bootstrap and dependency index initialized and verified.
- Windows executed. Linux CI configured, not remotely executed.
- No P1 live capture/import/minimization, no public publishing or competition submission performed.
- P0 local delivery complete; external account/identity steps remain in the competition checklist.

## Final decisions

- JSON nesting is bounded lexically outside strings before standard parsing, avoiding a migrating optional-depth API while retaining a strict 64-level cap.
- Combined core/session audit rules with the transactional state machine rather than creating a forwarding-only core/audit package.
- Human-readable excerpts are capped at 200 Unicode code points, not grapheme width. Original input is retained in reproduction prefixes.
- Entire input prefix is held only for export and bounded by the same 64 MiB limit; historical full document snapshots are never retained.
- Clean-room initial dependency fetch required an allowed network execution because the default sandbox blocked sockets; the subsequent full clean-room validation passed.
