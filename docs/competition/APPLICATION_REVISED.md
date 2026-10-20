# EditTrace 项目申报书

历史稿（2026-10-17）。本轮实质反馈后的当前草稿见 [APPLICATION_REMEDIATED.md](APPLICATION_REMEDIATED.md)，以下能力和数字保留为当时状态。

参赛者：常云志｜GitHub：cloud00726｜邮箱：2843417317@qq.com

方向：开发者工具（LSP 调试）｜许可证：MIT

仓库：https://github.com/cloud00726/edittrace

## 项目简介与通用性

EditTrace 是使用 MoonBit 实现的离线 LSP 文档同步审计工具。我选择检查编辑过程，是因为补全位置或文档内容出现偏差时，仅看日志很难还原每一步文本，尤其容易混淆 emoji 的 UTF-16 长度、换行和多次编辑的顺序。工具读取规范化 JSONL 会话，重放文档变化、检查版本与生命周期、比较独立文本检查点，并导出复现材料。输入围绕 LSP 文档同步消息组织，不绑定某个编辑器或编程语言；不同客户端需先把日志转换为约定格式。

## 三个预期使用场景

1. **排查 Unicode 位置偏差**：插件开发者发现 emoji 后的替换位置异常，将打开事件、修改事件及独立保存的预期文本整理为会话。运行 `audit` 检查 UTF-16 边界和文本差异，再用 `replay` 还原指定步骤，核对坐标换算与消息内容。
2. **检查同步代码回归**：语言服务器或插件维护者修改同步逻辑后，把正常编辑、版本倒退、多文档关闭重开等会话加入 CI。通过 `audit --format json` 对照预期规则和退出码，及时发现版本顺序或文档状态处理发生变化。
3. **交接可复现的问题**：维护者按报告标识运行 `export`，导出触发位置之前的完整会话前缀、目标报告和清单。接收者在另一目录运行 `verify` 校验，再审计包内会话，无需访问报告者的原始工程路径。

## 核心功能与实现方案

核心逻辑和 CLI 使用 MoonBit，提供 `audit`、`replay`、`export`、`verify`。按文档 URI 保存文本、版本与打开世代；坐标按 UTF-16 单元解释并保留 LF、CRLF、CR。同一 `didChange` 内的编辑必须依次作用于更新后的文本，不能统一套用原文；整条通知先在临时文本上执行，全部成功才提交。无法可靠重放时标记未知，等待有效全文替换或重新打开恢复，避免继续生成猜测结果。

首版实现 14 条规则、独立检查点比对、确定性 JSON 报告和有资源上限的输入处理。复现包写入后重新读取验证。当前限定 UTF-16 和文档同步子集，不自动采集任意编辑器日志、不自动最小化序列，也不把客户端重放结果视为服务端内部状态或根因证明。优先验证语义正确，再考虑索引缓存优化。

## 原创性与验证

2026 年 10 月 16 日核查 Mooncakes 后，已确认有 `mizchi/lsp`、`bzy-debug/text_document`、`moon-lsp-compiletest` 和 `MoonReplayKit` 等相关包；本次未发现完整覆盖上述同步审计工作流的项目。EditTrace 的重点是将同步规则、独立文本检查点与可重跑的复现包结合，比较记录见仓库 `docs/competition/ECOSYSTEM_CHECK.md`，不宣称生态中绝无类似工具。

这是原创工具，行为参考 [LSP 3.17](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/)。Microsoft 的 [vscode-languageserver-textdocument](https://github.com/microsoft/vscode-languageserver-node/tree/main/textDocument) 1.0.12（MIT）仅作开发期独立对照，未复制到生产实现。已有 17 个 MoonBit 测试、500 组合法会话和 4000 个检查点；2026 年 10 月 17 日本地完整验收通过 256 项断言，含干净目录构建；另有 6 项安装与 CI 支持测试。提供 8 类合成示例及 Windows/Linux CI。Codex 辅助实现、测试与文档，使用情况已披露。
