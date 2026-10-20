# Third-party notices

- MoonBit core: bundled with the pinned official compiler, copyright International Digital Economy Academy, Apache-2.0. Core license is distributed with the installed toolchain.
- moonbitlang/async 0.22.5: official native filesystem/stdio runtime, copyright its contributors, Apache-2.0. Dependency source and LICENSE are available through MoonBit's dependency cache. This project does not modify or vendor its implementation.
- Microsoft vscode-languageserver-textdocument 1.0.12: MIT, development-only independent reference for generated tests. Package integrity is pinned in scripts/oracle/package-lock.json. Runtime does not depend on Node or this package. No reference implementation source is copied into production code. Generated test inputs/results and the observed cache difference are identified in tests/oracle/manifest.json.
- Language Server Protocol 3.17: Microsoft specification used as behavioral reference. Links in docs/PROTOCOL_NOTES.md; no complete specification text is redistributed.

The generated test expectations are produced by the identified reference tool. The optional package installation retains its bundled Microsoft License.txt. A copy of that license is recorded at tests/oracle/REFERENCE_LICENSE.txt for provenance.

- Microsoft vscode-jsonrpc 8.2.1: MIT, development-only actual trace capture against an installed Microsoft JSON language server. Integrity pinned in scripts/capture/pnpm-lock.yaml; not bundled into CLI/VSIX runtime. The package retains its License.txt. VS Code and its built-in JSON/TypeScript providers are external integration-test software, not redistributed by this project.
- Native ZIP/VSIX packaging includes the MoonBit core and moonbitlang/async license texts from the pinned build dependencies under licenses/. The extension uses only the VS Code host API and Node standard library, without bundled npm dependencies.
