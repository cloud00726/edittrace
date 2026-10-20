# Changelog

## 0.1.0 — 2026-10-15

- UTF-16 JSONL 文档同步审计：事务编辑、多 URI/世代隔离、版本与生命周期规则。
- 独立检查点、确定性 JSON/终端报告、audit/replay/export CLI。
- 有限资源读取与完整性报告，复现前缀写后重读验证。
- 固定工具链与依赖，500 组独立对照、8 类示例、原生验收脚本。
- 使用文档、CI 配置、参赛草稿及人工提交清单。

本版本为本地参赛准备版本，未宣称已公开发布。
## 0.2.0 Preview — 2026-10-20 review remediation

- Add fixed JSON-RPC trace import with initialization encoding provenance.
- Add immutable-baseline text edit preflight, version/overlap checks and independent actual-text comparison.
- Add self-contained regression cases/suites and typed external-consumer examples.
- Add local VS Code recording, provider text previews, diffs and reviewed case drafts.
- Add optional document-filtered reproduction export with full-target revalidation.
- Add actual-host fixtures, expanded acceptance, native ZIP/platform VSIX packaging and isolated installation checks.
- Core/module/extension now report 0.2.0; old 0.1.0 bundles remain verifiable. GitHub Releases is the authority for published preview status.
- Review fixes validate malformed edit plans even on version failures, evaluate step assertions in one replay, accept legal JSON-RPC request-id reuse, and clear stale CI reports.
