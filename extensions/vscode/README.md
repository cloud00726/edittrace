# EditTrace for VS Code

Record local editor document changes, preview formatting/rename text edits, and save a draft portable regression case. Validation and text application predictions run in the MoonBit native core.

## Install and use

Install the matching platform VSIX. It contains the native binary; no compiler or automatic download is needed. Source development can set `edittrace.executablePath` to an absolute executable path.

1. Open test documents, then run **EditTrace: Start Recording Open Documents**.
2. Edit, undo/redo, then run **EditTrace: Stop Recording and Analyze**.
3. For a provider preview, run **EditTrace: Preview Formatting Text Edits** or **EditTrace: Preview Rename Text Edits** with the cursor on a symbol. The original files are not modified.
4. **Show Last Predicted Text Diff** compares the first edited file with its baseline; the JSON report includes all edited documents.
5. **Save Last Result as Regression Case** saves a draft after you explicitly choose to review the recorded expectations. Review expected behavior before using the case as an oracle. The CLI can validate and package it with `case create`.

## Evidence and limits

- Recording observes editor document events and actual text snapshots. It does not intercept another extension's LSP traffic or prove server internal state.
- Rename previews inspect the text projection returned by the stable VS Code API. File creation/deletion/renaming and provider base versions cannot be verified through this projection. The report records that limitation and marks version checking false.
- Formatting and rename require installed providers; tested with VS Code 1.138.0 built-in JSON and TypeScript providers. The minimum engine declaration is not a claim that every earlier host was tested.
- File and untitled documents only; bounded local capture. A version gap or lost baseline stops recording as incomplete. Stop detaches listeners.
- All work stays local; reports/cases can contain complete source text and URIs. Review files before sharing.
- No telemetry, runtime dependencies or automatic network installation.

Development tests: `node --test test/unit.cjs`; actual host integration is run from the repository with `python scripts/run_host_tests.py`.
