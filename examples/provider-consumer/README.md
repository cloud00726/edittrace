# Independent consumer example

Copy `suite.json`, `fixture.js`, `build_candidates.py` and `workflow.yml` into a separate consumer repository. Place the Windows EditTrace core ZIP at `toolchain/edittrace.zip` and its reviewed SHA-256 at `toolchain/edittrace.sha256`. Put the workflow under `.github/workflows/`. Run it separately for 1.0.0, 1.1.0 and 1.1.1. These are synthetic provider versions installed in a real VS Code host. The middle version deliberately omits a rename reference and a sync action and changes the formatting result.

For your own extension, replace the fixture build with your candidate VSIX build and define reviewed input/output in `suite.json`. Keep the same suite when running the reference and candidate versions. Use the runner exit code directly in a required job. The example workflow fails for 1.1.0. The EditTrace repository's own verification expects that failure, so it can detect accidental acceptance of the faulty fixture.
