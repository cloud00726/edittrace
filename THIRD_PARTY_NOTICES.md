# Third-party notices

## Provider regression candidates (0.5.x)

| Source | Use and redistribution |
|---|---|
| [Visual Studio Code stable 1.144.0](https://code.visualstudio.com/updates/v1_144), [stable extension API](https://code.visualstudio.com/api/references/vscode-api), [binary license](https://code.visualstudio.com/license) | External host. EditTrace calls `WorkspaceEdit`, `TextDocument` events, extension exports and built-in provider commands. The Microsoft VS Code binary is downloaded separately and is excluded from EditTrace archives. |
| [MoonBit official downloads](https://www.moonbitlang.com/download/) | `moonfmt` from pinned toolchain `0.10.15+943464bfa` is an externally executed formatter. The example builds a small adapter for the actual executable SHA-256. Local Windows baseline hash is `5d12e81f5abf46c1163d7701b612a6c18fb4ccd5b69bd4e6336ba6dd52b90068`. EditTrace packages the adapter, not the formatter. |
| [Microsoft TypeScript](https://github.com/microsoft/TypeScript), [compiler and language service API](https://github.com/microsoft/TypeScript/wiki/Using-the-Compiler-API) | Apache-2.0. The example uses `typescript` npm 5.6.3 and 5.7.3, with registry integrity and runtime SHA-256 in `examples/provider-consumer/typescript-lock.json`. The consumer obtains the upstream archive independently, whose `LICENSE.txt` and notices apply to those upstream files. The EditTrace ZIP and the adapter VSIX include no TypeScript runtime or source. |
| [Ubuntu AppArmor documentation](https://documentation.ubuntu.com/security/security-features/privilege-restriction/apparmor/) | Reference for the provider CI's runner-specific `userns` profile. The original repository configuration targets only the fixed test executable. No AppArmor code or profiles from Ubuntu are redistributed. |

`examples/provider-consumer/suite.json` and `sync-scope-suite.json` are EditTrace-authored synthetic editor commands. The Moonfmt and TypeScript fixtures are EditTrace-authored inputs executed by the identified external tools. The omission switch deliberately drops a valid TypeScript edit in the example adapter. Its output is evidence of the gate's behavior under injection. `examples/real-world/` labels actual editor or JSON-RPC capture separately from injected faults. `tests/oracle/manifest.json` identifies independently generated fixtures and their frozen corpus digest.

The 0.5.3 native ZIP and platform VSIX carry EditTrace's MIT `LICENSE`, this notice and `licenses/MoonBit-core-LICENSE`, `licenses/MoonBit-core-NOTICE` and `licenses/moonbitlang-async-LICENSE` (under `extension/` in the VSIX). The staged MoonBit source archive carries `LICENSE`, this notice, the reference fixture and its independent-reference license. The `SHA256.json` and `source-manifest.json` list packaged paths. Mooncakes account ownership, the final namespace, publication and external installation are separate steps.

## Earlier dependencies and fixtures

2026-10-29 stage2: no new production third-party dependency. Evidence conversion/reduction is MoonBit; benchmark orchestration uses Python standard libraries and Windows process-memory counters. Legacy verification uses actual prior executables with recorded archive hashes. No reference fixtures regenerated.

- MoonBit core: bundled with the pinned official compiler, copyright International Digital Economy Academy, Apache-2.0. Core license is distributed with the installed toolchain.
- moonbitlang/async 0.22.5: official native filesystem/stdio runtime, copyright its contributors, Apache-2.0. Dependency source and LICENSE are available through MoonBit's dependency cache. This project does not modify or vendor its implementation.
- Microsoft vscode-languageserver-textdocument 1.0.12: MIT, development-only independent reference for generated tests. Package integrity is pinned in scripts/oracle/package-lock.json. Runtime does not depend on Node or this package. No reference implementation source is copied into production code. Generated test inputs/results and the observed cache difference are identified in tests/oracle/manifest.json.
- Language Server Protocol 3.17: Microsoft specification used as behavioral reference. Links in docs/PROTOCOL_NOTES.md; no complete specification text is redistributed.

The generated test expectations are produced by the identified reference tool. The optional package installation retains its bundled Microsoft License.txt. A copy of that license is recorded at tests/oracle/REFERENCE_LICENSE.txt for provenance.

- Microsoft vscode-jsonrpc 8.2.1: MIT, development-only actual trace capture against an installed Microsoft JSON language server. Integrity pinned in scripts/capture/pnpm-lock.yaml; not bundled into CLI/VSIX runtime. The package retains its License.txt. VS Code and its built-in JSON/TypeScript providers are external integration-test software, not redistributed by this project.
- Native ZIP/VSIX packaging includes the MoonBit core and moonbitlang/async license texts from the pinned build dependencies under licenses/. The extension uses only the VS Code host API and Node standard library, without bundled npm dependencies.

2026-10-25 maintenance candidate 0.3.0: no new production third-party dependency was added. Report/JUnit computation remains MoonBit; host diagnostics and regression file management use Node standard libraries. Python ElementTree independently parses JUnit in development tests. Local source-package candidates use an explicit allowlist and include this notice and the reference fixture license; they do not bundle the async source or represent a registry publication.
