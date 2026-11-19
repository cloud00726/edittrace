# Independent consumer example

Copy `suite.json`, `fixture.js`, `build_candidates.py` and `workflow.yml` into a separate consumer repository. Place the Windows EditTrace core ZIP at `toolchain/edittrace.zip` and its reviewed SHA-256 at `toolchain/edittrace.sha256`. Put the workflow under `.github/workflows/`. Set `candidate-version.txt` to `1.0.0`, `1.1.0`, or `1.1.1` in successive commits, or select the version on a manual run. These are synthetic provider versions installed in a real VS Code host. The middle version deliberately omits a rename reference and a sync action and changes the formatting result.

For your own extension, replace the fixture build with your candidate VSIX build and define reviewed input/output in `suite.json`. Keep the same suite when running the reference and candidate versions. Use the runner exit code directly in a required job. The example workflow fails for 1.1.0. The EditTrace repository's own verification expects that failure, so it can detect accidental acceptance of the faulty fixture.

## Real TypeScript cross-file rename

Use `candidate_api_v1` with a small local adapter, `typescript-rename.js`. The adapter calls the pinned TypeScript language service for the export, import and references, and returns the resulting text edits. The third source file contains the same spelling in a string and must stay unchanged. The fixture includes mixed LF/CRLF across files and an emoji before the definition. The two verified npm releases and archive integrity are in `typescript-lock.json`.

```powershell
curl.exe -fL https://registry.npmjs.org/typescript/-/typescript-5.7.3.tgz -o typescript-5.7.3.tgz
python examples/provider-consumer/build_typescript_candidate.py 5.7.3 typescript-5.7.3.tgz ts-candidate
$env:EDITTRACE_TYPESCRIPT_JS = (Resolve-Path ts-candidate/typescript.js).Path
$candidate = Get-Content ts-candidate/receipt.json -Raw | ConvertFrom-Json
python scripts/run_provider_regression.py examples/provider-consumer/typescript-rename-suite.json --candidate ts-candidate/typescript-rename.vsix --sha256 $candidate.candidate_sha256 --core <edittrace.exe> --host 1.144.0 --out ts-results
```

Use the same suite with 5.6.3 and 5.7.3. For a separate test of gate failure, build 5.7.3 with `--synthetic-omit-reference`. It deliberately drops cross-file edits after calling the real language service. The report should show `client.ts` and `first_difference_utf16: 9`. Restore the complete adapter and the same suite should pass. This setup exercises TextEdit output from the standalone language service through an actual VS Code host. External publisher adoption and a historical TypeScript defect are separate evidence.

From a current EditTrace binary ZIP, use `provider-runner/scripts/run_provider_regression.py` and `./edittrace.exe` in the command. The examples directory contains the same adapter and build scripts. On Linux use the matching native ZIP, `python3`, `./edittrace` (set executable permission after extraction), a capable graphical host, and `export EDITTRACE_TYPESCRIPT_JS=/absolute/path/to/typescript.js`.
