# EditTrace 项目申报书

历史扩展版：此文件对应此前 PDF 的内容，未覆盖全部现行申报要求。重新申报使用 [APPLICATION_REVISED.md](APPLICATION_REVISED.md)，按章程人工修改定稿为一页 Markdown。

## 基本信息

- 项目名称：EditTrace：LSP 增量文档同步审计与复现工具
- 参赛者：常云志
- GitHub ID：cloud00726
- 联系方式：2843417317@qq.com
- GitHub 仓库链接：https://github.com/cloud00726/edittrace
- 项目方向：开发者工具 / LSP 调试与开发体验工具
- 是否为移植项目：否。核心逻辑使用 MoonBit 实现，参考 LSP 规范，并使用独立参考库验证编辑结果。
- 开源许可证：MIT

## 项目简介

EditTrace 面向语言服务器、编辑器插件及 IDE 工具开发者，解决文档增量同步过程中“消息难追踪、文本难还原、问题难复现”的调试问题。当连续编辑涉及中文、emoji、不同换行符或版本变化时，单看消息日志往往难以判断每一步应产生的文本。

项目以 MoonBit 实现离线审计引擎和原生命令行工具，读取规范化 JSONL 会话，按 UTF-16 坐标重放编辑，检查文档生命周期和版本顺序，将重放结果与独立检查点比较，并导出可以再次运行的复现包。核心逻辑按模型、文本、会话、报告拆分，供后续工具集成；当前交付入口为 audit、replay、export 三个命令。

项目聚焦文档同步这一细分场景，将事件顺序、文本状态、规则提示和复现材料关联起来，为 MoonBit 开发者工具生态提供可复用的同步审计能力。运行时不依赖模型 API，也不向远程服务上传会话。

## 核心功能范围

1. **规范化输入与安全读取**：支持 UTF-8 JSONL v1，识别 didOpen、didChange、didClose 及自定义 checkpoint；验证结构、顺序和编码，设置输入大小、文档数量与报告数量等上限。URI 仅作为标识，不读取对应本机文件。
2. **UTF-16 编辑重放**：支持中文、emoji、组合字符及 LF/CRLF/CR 换行；同一通知内的多次编辑依次作用于更新后的文本，整条通知事务化执行，失败不会留下部分修改。
3. **多文档同步审计**：实现 14 条规则，检查缺少打开事件、重复打开、版本不递增、范围倒置、代理对边界等情况；区分协议观察、产品保守策略与检查点证据。文本未知时停止猜测，支持有效全文替换或重新打开后恢复。
4. **状态还原与差异证据**：支持按 URI 和指定序号导出可确认的文本，比较独立检查点并给出稳定的规则标识、事件位置和文本摘录；提供文本及确定性 JSON 报告，便于接入脚本与 CI。
5. **复现包导出**：按 finding 导出触发位置之前的完整会话前缀、报告与清单；写入后重新读取，验证目标指纹可复现。当前保留完整上下文，尚不进行自动最小化。
6. **验证与交付**：已通过 17 个 MoonBit 原生测试、包含干净目录构建的 207 项验收断言；固定参考版本生成 500 组合法会话、4000 个逐步检查点。提供 8 类合成示例、Windows/Linux CI、README、协议边界、来源及 AI 使用说明；已展示的最新 CI 运行通过。

本期限定 UTF-16 文档同步和自定义规范化输入，不承诺自动导入任意编辑器日志或完整检查 LSP。检查点差异表示可观测文本不一致，不能单凭客户端重放证明服务端内部状态或缺陷根因。后续拟增加真实日志适配、实际服务器会话验证和复现序列精简。

## 移植或参考说明

- **协议参考**：Microsoft Language Server Protocol 3.17，https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/ 。本项目实现其中的文档同步子集，并明确记录产品策略与协议要求的区别。
- **独立测试参考**：Microsoft vscode-languageserver-textdocument 1.0.12，https://github.com/microsoft/vscode-languageserver-node/tree/main/textDocument ，MIT。仅用于开发期生成对照数据，生产代码未复制其实现，运行时不依赖 Node.js。参考库行索引缓存的观察及生成策略已在验证文档记录。
- **运行依赖与归属**：MoonBit core、moonbitlang/async 0.22.5，Apache-2.0；许可证及参考来源见仓库 THIRD_PARTY_NOTICES.md。
- **AI 使用说明**：使用 Codex 辅助实现、测试和文档，并通过真实编译、独立参考和命令行验收验证；参赛者负责审阅、理解和说明成果，详见 docs/AI_USAGE.md。

---

结构参考：[官方项目申报书样本](https://bxup9uklfcb.feishu.cn/wiki/Rm3PwCxC7iEwJtkK1xMcYHZkn36)。本文描述当前工程成果，不表示已完成报名或验收提交；验证详情见 docs/validation-results.json 和仓库 Actions 记录。
