# EditTrace Mooncakes 同类项目核查

核查日期：2026-10-16（Asia/Shanghai）。本记录用于说明选题与已发布包的关系，不代表赛事方认可或全站无重复证明。

## 检索方法与范围

实际调用 MoonBit 官方工具链的 `moon search <keyword> --limit 100 --json`，查询 Mooncakes 官方注册表，并交叉检索公开包文档、相关仓库 README 和公开 API。

| 关键词 | 官方查询状态 | 返回模块数 |
|---|---|---:|
| lsp | 成功 | 10 |
| text_document | 首次 TLS 失败，重试成功 | 100 |
| edittrace | 成功 | 0 |
| replay | 成功 | 100 |
| trace | 成功 | 100 |
| didChange | 成功 | 6 |

原始查询结果保存在本地 `artifacts/ecosystem-check/*.json`（该目录按仓库规则不进入版本控制）。接口为 `https://mooncakes.io/api/v0/search?kw=<keyword>&limit=100`。广义关键词达到上限，因此不能视为遍历全部结果；检索会匹配包摘要，不限模块名称。另使用搜索引擎检索 Mooncakes 中 LSP、text synchronization、replay、audit、文档同步等词，作为补充。网页索引可能滞后。

## 重点相关项目比较

| 项目与核对版本 | 已公开的相关能力 | 与 EditTrace 的关系 |
|---|---|---|
| [bzy-debug/text_document 0.1.0](https://mooncakes.io/docs/bzy-debug/text_document) | LSP 风格位置、范围、文档版本和顺序内容修改，使用文本 zipper | 编辑与 UTF-16 处理属于重叠基础能力。其公开源码展示文档操作库；此次未发现会话规则审计、独立检查点报告及复现包工作流。 |
| [mizchi/lsp 0.1.3](https://mooncakes.io/docs/mizchi/lsp%400.1.3) | LSP 客户端/服务端框架、JSON-RPC、协议类型、文档管理和测试桩 | 建立协议通信及服务器的基础设施。EditTrace 处理已有规范化会话，专注同步过程审计，不提供同等服务器框架。 |
| [yinlaomo112/moon-lsp-compiletest 0.1.0](https://mooncakes.io/docs/yinlaomo112/moon-lsp-compiletest%400.1.0) | 启动真实 moon-lsp，检查单文件 before/after 的 publishDiagnostics，保存 trace | 同属 LSP 测试工具。其断言对象是服务器诊断；EditTrace 断言同步事件与重放文本，不连接真实服务器，也不声称验证其诊断。 |
| [Suquster/moonbit-pathfinding 0.2.0 的 lsp_server](https://github.com/Suquster/moonbit-pathfinding/blob/main/src/lsp_server/pkg.generated.mbti) | 增量编辑、UTF-8/16/32 坐标、版本文档、会话生命周期等公开 API | 已有增量同步实现，不能声称 EditTrace 首次实现该能力。EditTrace 的增量工作是规范化历史审计、未知状态处置、检查点证据与复现交付。 |
| [LAOBIAO656/moonreplaykit 0.2.0](https://mooncakes.io/docs/LAOBIAO656/moonreplaykit%400.2.0) | 泛型 reducer 回放、日志完整性、检查点、分支与差异诊断、回放证据 | 与回放及检查点概念重叠，公开 README 要求应用提供 reducer 和指纹；此次未发现内置 LSP 文档同步规则。EditTrace 提供领域语义，未实现其 Merkle 风格证明能力。 |
| [btlqql/moon_tracelens 0.2.0](https://mooncakes.io/docs/btlqql/moon_tracelens%400.2.0) | 离线日志规范化、筛选、请求关联、时间线及指标比较 | 日志分析入口相关；公开 README 的已实现范围是事件查询与统计，此次未发现按 UTF-16 应用文档编辑的审计流程。 |

其余 `lsp` 命中包括编辑器、词法分析器、模板工具链、语言/RTL 分析及 JSON-RPC 插件，按公开描述属于相关基础设施或具体应用。上述判断基于已阅读资料，未对第三方项目执行安装、测试或性能比较，不将未见文档等同于不存在实现。

## 可复核资料

- text_document：[公开编辑实现](https://mooncakes.io/assets/bzy-debug/text_document/text_document.mbt.html)。
- mizchi/lsp：[Mooncakes 文档](https://mooncakes.io/docs/mizchi/lsp%400.1.3)。
- moon-lsp-compiletest：[仓库 README](https://github.com/yinlaomo112/moon-lsp-compiletest/blob/main/README.md)。
- lsp_server：[公开 API](https://github.com/Suquster/moonbit-pathfinding/blob/main/src/lsp_server/pkg.generated.mbti)。
- MoonReplayKit：[仓库 README](https://github.com/LAOBIAO656/MoonReplayKit/blob/main/README.md)。
- Moon TraceLens：[仓库 README](https://github.com/btlqql/moon-tracelens/blob/main/README.md)。

## 核查结论

截至核查日期，在本次检索与重点项目比较范围内，未发现与 EditTrace 的“离线 LSP 增量文档同步审计、独立文本检查点比对、复现包导出”完整工作流直接对应的已发布项目。已存在 LSP、文档编辑、诊断回归和通用回放工具，因此不能表述为“MoonBit 没有 LSP/编辑/回放能力”，也不能保证生态中绝对不存在类似项目。

项目定位应强调在已有基础能力之上提供领域明确的审计与证据交付，而非宣称整体能力首创。提交前可再次运行检索；最终是否构成重复由赛事方判断。
