# EditTrace 项目正式申报书

**项目名称：** EditTrace——编辑器文本变更验证与回归工具

**参赛者：** 常云志｜GitHub：cloud00726｜邮箱：2843417317@qq.com

**方向：** 开发者工具｜**许可证：** MIT｜**版本：** 0.2.0 预览版

**项目仓库：** https://github.com/cloud00726/edittrace

**可下载版本：** https://github.com/cloud00726/edittrace/releases/tag/v0.2.0-preview.1

## 一、项目定位与解决的问题

EditTrace 面向编辑器插件、语言服务器和语言工具维护者，将格式化、跨文件文本重命名及文档同步中的编辑过程转化为可检查、可交接、可持续回归的用例。它关注的具体问题是：一组编辑能否正确作用于指定文本，计算结果是否与编辑器实际结果一致，以及修复后如何避免同类错误再次发生。

这类工作往往需要开发者手动核对文本范围、Unicode 坐标、版本与编辑顺序，再自行整理复现材料。EditTrace 将这些操作串成“采集—验证—保存用例—CI 回归”的流程，使一次排查形成的用例能够在后续版本中持续执行，服务于插件与语言工具的日常维护。

## 二、三个完整使用场景

1. **格式化结果回归。** 插件维护者调整格式化逻辑后，通过 VS Code 扩展取得原文及格式化提供者返回的编辑，预检范围、冲突与可获得的版本信息；在验证流程中，将预测文本与宿主独立应用后的实际文本比较，再保存经审核的用例并加入 CI。仓库包含真实 JSON 格式化样例和明确标注的版本过期故障注入，用于验证正常与失败路径。
2. **跨文件文本重命名验证。** 语言工具维护者修改重命名实现后，取得涉及多个文件的文本编辑，逐文件计算预期结果并核对实际文本，保存用例用于后续回归。真实 TypeScript 样例覆盖定义和引用两个文件。该流程检查编辑的可应用性与文本一致性；重命名的语言语义仍由语言工具自身负责。
3. **同步故障复现与交接。** 开发者在 VS Code 中开始录制，执行编辑、批量修改或撤销重做，停止后分析。录制包含打开基线、变更事件和独立文本快照，可检查 Unicode、换行及事件顺序造成的偏差。问题可保存为可迁移回归用例，或导出重新校验过的同步证据包，供另一位维护者离线重跑。

## 三、技术实现与独立复用价值

核心解析、UTF-16 文本操作、同步状态机、批量编辑预检、断言和命令行均使用 MoonBit 实现；VS Code 扩展承担采集与宿主交互。实现区分两类关键语义：批量 TextEdit 作用于同一原文，didChange 中的连续变更依次作用于更新后的文本。报告提供规则、文本差异和完成状态，无法可靠重放时明确报告不完整。

项目已提供 VS Code 本地录制和指定格式的真实 JSON trace 直接导入，常见受支持路径无需用户手工编写内部 JSONL。Windows/Linux x64 的 CLI 与 VSIX 均自带原生核心，无需安装 MoonBit 即可体验。独立 MoonBit 消费者示例验证了类型接口的调用；自包含 case、suite 和确定的退出码支持脱离原始工程运行及 CI 集成。

EditTrace 的独立价值体现在三个相互衔接的能力：以文本计算验证编辑结果，以独立快照提供差异证据，以可迁移用例支持问题交接与持续回归。CLI、类型接口和回归用例均可独立使用，也可与日志查看器及现有 LSP 测试工具配合，为不同工程复用同一套文本验证能力。

## 四、原创属性与参考来源

EditTrace 为原创实现项目，核心审计、编辑预检、证据报告及回归用例流程由本项目使用 MoonBit 实现，开发中的 AI 辅助情况见文末披露。项目并非对某个现有工具的整体移植。已有 LSP 框架和文档操作库提供相邻基础能力，本项目选择独立建设的具体范围是将编辑计算、独立实际结果比较与可迁移回归用例结合，供 CLI、编辑器与 CI 共用；不主张协议、文本编辑或回放概念本身为原创。

行为依据为 Microsoft [Language Server Protocol 3.17](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/)。开发期使用 Microsoft [vscode-languageserver-textdocument 1.0.12](https://github.com/microsoft/vscode-languageserver-node/tree/main/textDocument)（MIT）生成独立对照输入与期望，未将其实现源码复制到生产代码；使用 [vscode-jsonrpc 8.2.1](https://github.com/microsoft/vscode-languageserver-node/tree/main/jsonrpc)（MIT）采集真实通信。这两个 npm 包均非 CLI/VSIX 运行时依赖。原生运行依赖 moonbitlang/async 0.22.5（Apache-2.0）；发行包保留 MoonBit core 与 async 的许可文本。完整归属见 [第三方声明](https://github.com/cloud00726/edittrace/blob/main/THIRD_PARTY_NOTICES.md)，相关生态项目比较见[同类核查记录](https://github.com/cloud00726/edittrace/blob/main/docs/competition/ECOSYSTEM_CHECK.md)。

## 五、完成情况、验证与适用边界

项目已开源并发布可下载预览版。发布源提交的 Windows、Ubuntu CI 均通过 337 项验收断言、独立消费者及发行包检查；原生 MoonBit 测试 19 项，实际 VS Code 测试宿主检查 14 项。固定 Microsoft 参考实现的 500 个会话、4000 个检查点用于独立行为对照。真实采集样例与人为故障注入分别标注，验证记录、三类场景及快速体验说明均随仓库提供。

当前支持 UTF-16 与纯文本编辑子集；重命名使用 VS Code 稳定接口的文本投影，不验证文件资源操作及接口未提供的原始基线版本，也不据客户端重放推断服务端内部状态。现阶段已完成真实宿主采集、自动化验证、独立消费者调用与跨平台交付；第三方持续采用及需求规模尚无验证结论。下一阶段将围绕维护者的实际任务开展试用，优先改进采集接入、差异解释和回归用例维护体验。

**验证入口：** [发布源双平台 CI](https://github.com/cloud00726/edittrace/actions/runs/39429451845)、[快速体验](https://github.com/cloud00726/edittrace/blob/main/docs/QUICKSTART.md)、[发布与安装记录](https://github.com/cloud00726/edittrace/blob/main/docs/PUBLISHING_RESULT.md)、[真实采集样例](https://github.com/cloud00726/edittrace/tree/main/examples/real-world)。

**AI 使用披露：** Codex 辅助代码、测试及本文撰写，详见 [AI_USAGE.md](https://github.com/cloud00726/edittrace/blob/main/docs/AI_USAGE.md)。

**申报日期：** 2026 年 10 月 21 日。
