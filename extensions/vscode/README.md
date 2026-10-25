# EditTrace for VS Code

Record local editor document changes, preview formatting/rename text edits, and save a draft portable regression case. Validation and text application predictions run in the MoonBit native core.

## Install and use

Install the matching platform VSIX. It contains the native binary; no compiler or automatic download is needed. Source development can set `edittrace.executablePath` to an absolute executable path.

1. Open test documents, then run **EditTrace: Start Recording Open Documents**.
2. Edit, undo/redo, then run **EditTrace: Stop Recording and Analyze**.
3. For a provider preview, run **EditTrace: Preview Formatting Text Edits** or **EditTrace: Preview Rename Text Edits** with the cursor on a symbol. The original files are not modified.
4. **Select File and Show Text Diff** selects any computed file. Choose baseline/predicted, or predicted/independent actual when such evidence is available. Failed documents without computed text remain in the findings summary.
5. **Save Last Result as Regression Case** saves a draft after you explicitly choose to review the recorded expectations. Review expected behavior before using the case as an oracle. The CLI can validate and package it with `case create`.

## 0.3.0 candidate workflow

**Diagnose Installation** checks bridge protocol, case schema, core path, platform and host version. Core compatibility uses declared capabilities rather than equal version strings. **Show Raw JSON Report** opens full local evidence; ordinary result views show only the MoonBit-generated summary.

Initialize Project Regressions creates `.edittrace/project.json`. Save Project Regression Draft saves a case with draft review metadata. Confirm Regression Expectations opens the entire case, shows previous/current expectation differences, checks the declarations with the core, and asks for explicit confirmation. The confirmation binds exact content bytes. Changing the file excludes it until re-reviewed; running never updates expectations.

Run Selected Regression can inspect drafts; Run Confirmed Project Regressions assembles only unchanged confirmed cases. Damaged metadata is an error. Excluded drafts/changed cases are reported. Failures can open the corresponding case; multi-root projects explicitly select their root. Canceling a choice performs no action. See [project regressions](../../docs/REGRESSIONS.md).

The stable provider API cannot reliably distinguish an already-formatted document from no applicable provider. Empty results, provider exceptions and timeouts receive distinct messages. A timeout stops waiting, not necessarily the underlying provider. Do not use an older 0.2.0 core with these maintenance commands.

## Evidence and limits

- Recording observes editor document events and actual text snapshots. It does not intercept another extension's LSP traffic or prove server internal state.
- Rename previews inspect the text projection returned by the stable VS Code API. File creation/deletion/renaming and provider base versions cannot be verified through this projection. The report records that limitation and marks version checking false.
- Formatting and rename require installed providers; tested with VS Code 1.138.0 built-in JSON and TypeScript providers. The minimum engine declaration is not a claim that every earlier host was tested.
- File and untitled documents only; bounded local capture. A version gap or lost baseline stops recording as incomplete. Stop detaches listeners.
- All work stays local; reports/cases can contain complete source text and URIs. Review files before sharing.
- No telemetry, bundled npm runtime dependencies or automatic network installation. The native core still depends on the bundled MoonBit/async runtime.

Development tests: `node --test test/unit.cjs`; actual host integration is run from the repository with `python scripts/run_host_tests.py`.
