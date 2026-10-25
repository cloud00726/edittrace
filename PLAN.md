# EditTrace execution plan

## Maintenance execution — 2026-10-25

Current work follows CODEX_MAINTENANCE_TASK.md T0–T7; stage results and external dependencies are maintained in docs/MAINTENANCE_PROGRESS.md. Local 0.3.0 adds capability diagnosis, MoonBit evidence summaries/JUnit, all-file diffs, reviewed project regressions and typed consumer APIs. Local native/JS consumers and a staged source candidate do not represent Mooncakes publication. No new push, registry release, competition submission or external contact is authorized by this execution task.

The first three meaningful local commits are 9d82827, a0da2f2 and fb2ebdb. Full maintenance acceptance reached 353, native tests 21, Node tests 14, CI support 6; actual installed candidate Extension Host checks 22 on VS Code 1.143.1. Final package receipts and deferred external items are recorded in the stage report rather than inferred from old release evidence.

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
- Do not publish or push without explicit session authorization; current authorizations are recorded below. Do not submit competition forms or manufacture identity information.
- 2026-10-17 session authorization: user explicitly requested substantive improvements, commits and push to origin/main. Package publishing, competition form submission and fabricated authorship remain outside this authorization.
- Implement bounded input and deterministic reports before optional features.

## Current progress

Official toolchain 2026-10-12 installed into ../tooling/moon; archive SHA256 matched official checksum. Native CLI, chunked file IO, stdout/stderr and exit API compiled. Async dependency pinned to 0.22.5.

`moon test --target native`: 13 tests passed, including 500 generated independent sequences and 4000 checkpoints. Hand-calculated Unicode, CRLF-merging, rollback, negative/gapped versions, unknown-state recovery and limits passed. `audit examples/valid-unicode.jsonl --format json` returned 0 and a matching checkpoint.

Reference validation decision: Microsoft textdocument 1.0.12 retained an extra cached line when an inserted CR joined an existing LF. Recorded the exact observation in tests/oracle/reference-cache-observation.json. Generator recreates the independent reference after each edit, so later generated positions use fresh indexes. Expected text still comes from the independent implementation. This change corrected the generator's invalid future coordinates rather than weakening tests.

## Next

The original offline-sync implementation is complete. The 2026-10-20 remediation below supersedes the old P1 priorities; see docs/competition/REMEDIATION_PLAN.md for the current scope and evidence.

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

### First remote CI follow-up

Run 38735028069: Windows reached oracle digest validation but Git's checkout conversion changed LF to CRLF; Ubuntu failed before compilation because official archive executables needed chmod, matching the official Unix installer. Added .gitattributes with LF checkout and a Unix permission step (including internal/tcc); also repairs an existing incomplete installation. Added two portable regression checks. Reran all 207 local acceptance assertions including clean-room build successfully. Remote rerun awaits publishing these fixes; no push is performed without authorization. CI clears the committed validation snapshot before starting so failed jobs cannot upload old local evidence as if freshly generated.

- JSON nesting is bounded lexically outside strings before standard parsing, avoiding a migrating optional-depth API while retaining a strict 64-level cap.
- Combined core/session audit rules with the transactional state machine rather than creating a forwarding-only core/audit package.
- Human-readable excerpts are capped at 200 Unicode code points, not grapheme width. Original input is retained in reproduction prefixes.
- Entire input prefix is held only for export and bounded by the same 64 MiB limit; historical full document snapshots are never retained.
- Clean-room initial dependency fetch required an allowed network execution because the default sandbox blocked sockets; the subsequent full clean-room validation passed.

### Second remote CI follow-up

Run 38736066950: Windows succeeded. Ubuntu bootstrap and fmt/check/test/build succeeded; the harness assumed a suffixless executable and failed artifact lookup. Centralized native artifact lookup for both normal and clean-room builds; accept the unique actual edittrace.exe or edittrace output, reject missing/ambiguous results with directory diagnostics. Added two naming regressions; all 4 CI support tests and 207 local acceptance checks passed. Updated Ubuntu end-to-end result awaits user push.

### Competition ecosystem review (2026-10-16)

Queried the live Mooncakes registry with six keywords and reviewed related documentation/API surfaces. Recorded overlapping LSP, text-document, diagnostic-regression, replay and log-analysis tools in docs/competition/ECOSYSTEM_CHECK.md. Added a qualified scope comparison to APPLICATION_REVISED.md; no absolute uniqueness or eligibility claim. Search output is retained locally in artifacts/ecosystem-check. Documentation-only change; no product tests rerun and no publishing/submission performed.

### Substantive improvements and proposal review (2026-10-17)

- Fixed full audit ending early at Int32 maximum seq; explicit optional prefix selection now distinguishes replay from reading to EOF. Regression covers a bad suffix and valid maximum-seq replay.
- Added per-command help without requiring a trace, escaped document state/version summaries, independent bundle verify, and opt-in audit excerpt omission. Each change includes native CLI regressions and its own substantive commit.
- Bootstrap downloads use temporary files, streaming checksum verification and atomic cache promotion; interrupted/incorrect downloads do not become cache entries. Added retry/reuse/cleanup regressions.
- Reviewed the Markdown proposal, three complete scenarios, related-package scope and measured outcomes. Preserved supplied identity, disclosed AI assistance, identified the separate human-authorship requirement. Old PDF content is marked historical and generated output ignored.
- Full validation: 256 assertions including clean-room build, 17 MoonBit tests and 6 CI-support tests passed. No new performance superiority or memory claims.
- Verified prior Windows/Linux CI run 38738218872 succeeded for 79cde2a. Latest publication and CI results will be checked after push; external form submission and Mooncakes release have not been performed.

## Review remediation — 2026-10-20

- M0: baseline 7ee8b396, 256 clean-room assertions passed; froze REMEDIATION_SPEC and FEEDBACK_MATRIX. Installed host VS Code 1.138.0; fixed development tracer vscode-jsonrpc 8.2.1; production logic stays MoonBit. Extension uses dependency-free JavaScript host glue instead of a TypeScript build step.
- M1: fixed JSON trace importer, source line/direction preservation, initialization encoding evidence and malformed/mixed-session rejection. Captured 13 real messages against installed Microsoft JSON server; no server snapshot is invented.
- M2: immutable-baseline edit plans with typed Edit/Baseline, versions, overlap detection, Unicode boundaries and independent actual comparison; explicit unsupported resource operations.
- M3: actual Extension Host tests for recorder, providers and user commands. Formatting and cross-file TypeScript rename match independently applied host results. Text-only rename projection and unavailable base versions explicitly disclosed. Profile data moved under .tooling to avoid compiler traversal of host sockets.
- M4: self-contained case/suite assertions, package reread/relocation, typed FindingExpectation, separate local consumer module and CI example. Unknown assertion fields rejected; a malformed case does not suppress later cases.
- M5: human summaries, first-difference evidence, optional export --uri preserving physical lines and complete target finding; verify checks filtering scope. Automatic delta debugging remains optional and unimplemented.
- M6: local native ZIP/platform VSIX with core/dependency licenses; standalone archive execution and real isolated VSIX install passed. Final artifacts/evidence are referenced from REMEDIATION_RESULT.md. New remote Linux/Windows CI configured, not executed this turn.
- M7: actual captures + clearly labeled injection examples, workflow comparison, trial form, revised one-page AI-assisted draft and demo. No external contacts, public package release or submission. Official website/Feishu reread did not yield verifiable current rules; deadline/human-authorship requirements must be confirmed before submission.
- Verification commands/results: docs/validation-results.json (latest full acceptance), docs/remediation-validation.json, docs/consumer-validation.json, docs/distribution-validation.json and examples/real-world/capture-evidence.json. No old oracle fixtures regenerated. Native/transport/host checks remain distinct from real-user demand.
- Remaining external evidence: actual maintainers' trial and ongoing use, remotely executed new CI, registry publication, human proposal finalization and formal resubmission. Do not call these completed on the basis of local tests.

## Authorized review, rehearsal and publication — 2026-10-20

The user explicitly requested completion of the first three follow-up steps: pre-release review, installation/use rehearsal, and pushing code to verify remote Windows/Linux CI followed by a downloadable release. This authorizes commits, normal push to origin/main, installing the reviewed VSIX and a GitHub prerelease after CI passes; it does not authorize Marketplace/Mooncakes publication, outside-user contact or competition submission.

Review fixes and evidence: docs/PRE_RELEASE_REVIEW.md. Core/module/extension now 0.2.0, with legacy 0.1 bundles still readable. Local full acceptance is 337 (80 new workflow assertions), 19 native tests; 14 actual host checks, 5 Node checks and 6 CI-support tests passed. Native reference fixtures were not regenerated. Remote results and release URL must be recorded only after actual success.

Source commit bffd56c2e8567dadd71b2214aefb396799bce3f1 pushed to origin/main. Remote run 39429451845 succeeded on Windows and Ubuntu: each ran 337 acceptance assertions, the independent consumer and 9 standalone packaging checks; see docs/remote-ci-validation.json. The CI-produced Windows VSIX was installed in the user's default VS Code profile; exact embedded native bytes matched the CI archive, and the installed package/core passed 14 real host checks in an isolated test workspace. CLI save/relocate/fault rehearsal passed; docs/install-validation.json separates this automation from human subjective use.

Published GitHub prerelease v0.2.0-preview.1 from that verified source commit with seven checksum-verified CI artifacts: https://github.com/cloud00726/edittrace/releases/tag/v0.2.0-preview.1 . See docs/PUBLISHING_RESULT.md and docs/release-validation.json. No Marketplace/Mooncakes publication, third-party contact or competition submission was performed.
