# EditTrace 十月黑客松实现方案

版本：1.0；编写日期：2026-10-15；目标提交日期：2026-10-30。

本文是待实现的产品规格，不是已完成的功能清单。项目代码建议放在 `E:/moonbit/edittrace`，本方案目录保留为规划材料。

## 1. 目标与交付定义

EditTrace 是主要以 MoonBit 实现的离线 LSP 文档同步审计工具。它读取规范化会话记录，重建文档，检查生命周期、版本和编辑坐标，并与独立检查点比较，导出可重放的证据包。

面向编辑器插件、语言服务器和增量文本处理工具的开发者。核心价值是把难以人工检查的消息序列转化成有位置、有上下文、能再次运行的证据。

一句话申报描述：基于 MoonBit 的 LSP 增量文档同步审计与复现工具，聚焦 Unicode 坐标、版本与编辑顺序问题，提供离线重放、检查点比对和证据包导出。

交付必须满足：普通开发者在干净环境按 README 安装，运行正常案例得到成功结果；运行错误案例得到明确报告与预期非零退出码；导出的会话能在其他目录重现同一目标 finding。

### 能证明什么

- 日志描述的修改序列在指定编码和支持范围下重放出的文本。
- 输入结构、已支持的生命周期与版本规则是否存在问题。
- 某个独立检查点与当前重建文本是否一致。
- 首个被观察到的不一致发生在哪个检查点，以及上一个通过的检查点到此处的可疑区间。

### 不能证明什么

- 没有服务端独立快照时，不能证明服务端内存文档错误。
- 一个检查点失败，不能直接认定紧邻的上一条编辑就是根因。
- 日志没有报错，不等于服务器或整个 LSP 实现完全正确。
- 重放客户端消息不等于运行了真实语言服务器。
- 导出的复现前缀不等于全局最小复现；自动缩减是扩展功能。

## 2. 与赛事要求对应

核对依据是 2026-10-15 可访问的赛事官网及其公开页面源码。正式飞书章程正文未能读取；最终以章程与主办方通知为准。

| 官网要求 | 本项目的落实方式 | 提交证据 |
|---|---|---|
| 十月报名和验收在 10 月 31 日截止 | 10 月 30 日前完成提交材料 | 提交记录，由参赛者核实 |
| 提交参赛信息、公开仓库、一页项目说明 | 先完成申报草稿与仓库准备 | 申报说明、公开仓库 URL |
| MoonBit 为主要实现语言 | 重放、坐标、审计、报告、CLI 均使用 MoonBit | 源码、架构文档 |
| 仓库公开，开发过程可追踪 | 保留正常的开发提交、问题及变更记录 | Git 历史、CHANGELOG |
| README、运行示例和必要测试 | 提供快速开始、案例、测试与验证脚本 | README、examples、测试结果 |
| 开源许可证与来源说明 | 建议 MIT；依赖逐项核对许可，保留必要声明 | LICENSE、THIRD_PARTY_NOTICES |
| AI 辅助成果需要理解并负责 | 记录 AI 协助范围、人工解释要点与验证证据 | AI_USAGE、设计决策记录 |
| 入群，昵称为 GitHub ID | 参赛者自行完成 | 提交清单 |

以下是本项目的工程质量目标，不冒充官网额外强制条件：持续集成、独立参考实现对照、性能记录、可复用核心库、发布准备。

官网当前公开要求没有给出代码行数门槛、量化评分比例或强制 mooncakes 发布要求。不得从其他届次赛事搬用这些要求。若正式章程另有规定，更新赛事清单，并记录来源。

## 3. 功能边界与优先级

### P0：十月版必须交付

1. 有版本的 EditTrace JSONL 输入格式及明确验证错误。
2. UTF-16 文档坐标、LF/CRLF/CR 换行、全文及增量修改。
3. 多文档生命周期与版本追踪；单消息多编辑按顺序应用。
4. 审计规则、状态可信度、独立检查点比较。
5. `audit`、`replay`、`export` 三个子命令与帮助信息。
6. 终端和稳定 JSON 报告，确定的退出码。
7. 重放证据包；不丢失导致同一问题的必要上下文。
8. 正常、Unicode、顺序、版本、生命周期、检查点案例。
9. 边界测试、确定性生成测试和独立参考对照样例。
10. README、协议边界说明、许可证、依赖声明、CI、验收脚本及参赛材料草稿。

### P1：P0 通过后再做

- 原始 LSP `Content-Length` 流的导入器。每个输入流必须由用户声明方向；没有跨流顺序证据时不伪造全局顺序。
- 一次使用真实语言服务器、自己编写的样例文件进行的采集实验；记录采集方式和版本。实验可由开发脚本完成，不要求产品运行时依赖脚本。
- Markdown 报告和简单 HTML 静态报告。
- 对完整初始化记录读取编码协商结果；只有完整证据时才标注为协商所得。
- 自动精简会话。必须保留相同 finding 指纹和重放前提，且明确不保证最小。

### 本期不实现

完整 LSP 服务器、VS Code 插件、透明在线代理、远程协作、数据库、多用户网站、任意语言编译器、rope 性能优化、所有位置编码、所有 LSP 方法、AI 诊断服务。

## 4. 实现前必须完成的环境探测

2026-10-15 的只读检查中，工作区未列出已有项目文件；当前 PATH 未发现 `moon`、`moonc`，发现了 Git。该结果只描述当时环境，不代表机器没有其他位置的安装。

Codex 开始时重新检查：适用的 AGENTS.md、现有文件与 Git 状态、MoonBit 路径和版本、native 后端工具链、文件 IO、标准输入输出和退出码能力。先用微型程序实际编译验证，不依据旧教程猜 API。

- 若工具链已安装，使用实际路径并记录版本，不擅自升级。
- 若工具链缺失，读取官方安装说明，按当前权限完成可行安装；遇到必须由用户完成的安装或权限操作，报告确切原因。同时继续完善不依赖工具链的材料。
- 不改系统执行策略、不安装无关软件来绕过限制。
- 以实际 `moon help` 验证包配置及命令。优先用当前支持的 `moon.mod`、`moon.pkg`。
- 工具链及依赖版本写入可机器读取的版本记录；CI 使用经过验证的版本。
- 模块名可以先使用本地技术标识，公开发布命名空间必须核实 GitHub/Mooncakes 所有者。不得把示例名字当成用户账号。

## 5. 架构与目录

推荐单模块、多个职责明确的包。包名可按实际工具链约定调整，职责不变。

```text
edittrace/
  moon.mod
  README.md
  README.en.md                       # 可后补，中文完整优先
  LICENSE
  THIRD_PARTY_NOTICES.md
  CHANGELOG.md
  AGENTS.md                         # 简短、适用本仓库的工作约定
  PLAN.md                           # 里程碑状态、决策与下一步
  core/model/                       # 输入、状态、finding、报告数据类型
  core/text/                        # 行索引、UTF-16 坐标和编辑
  core/session/                     # 多文档状态机与事务重放
  core/audit/                       # 规则及检查点比较
  core/report/                      # 确定性结构化报告
  io/trace/                         # JSONL 读取、格式验证、资源限制
  io/bundle/                        # 复现包写入及重读
  cmd/edittrace/                    # 薄 CLI，负责参数与文件 IO
  examples/                         # 可直接运行的会话及预期结果
  tests/fixtures/                   # 合法、非法、参考对照数据
  tests/oracle/                     # 固定版本的独立参考输出与来源
  scripts/                          # 验收、参考数据生成、可选采集
  docs/TRACE_FORMAT.md
  docs/PROTOCOL_NOTES.md
  docs/ARCHITECTURE.md
  docs/RULES.md
  docs/VALIDATION.md
  docs/LIMITATIONS.md
  docs/AI_USAGE.md
  docs/competition/PROPOSAL.md
  docs/competition/DEMO.md
  docs/competition/SUBMISSION_CHECKLIST.md
  .github/workflows/ci.yml
```

依赖方向：CLI/IO → 会话与审计 → 文本与模型。核心包不进行文件访问，不启动进程，不读取时钟，不要求网络。首版可在每次修改后重建行索引，先确保正确。

生产功能必须以 MoonBit 实现；Node/Python/PowerShell 只可用于开发期参考对照、环境安装或辅助验收，不得把核心处理转移到这些脚本。

## 6. JSONL 格式 v1

这是 EditTrace 自定义的规范化记录格式，不是原生 LSP 日志格式。产品必须明确说明转换边界，不能宣称自动读取所有编辑器日志。

文件是 UTF-8。每个非空物理行是一个 JSON 对象；源码换行用 JSON 字符串转义。空行可忽略，文件头允许一个 UTF-8 BOM，其他位置的 BOM 不特殊处理。第一条记录必须是 meta。

### 6.1 meta

```json
{"kind":"meta","schema_version":1,"position_encoding":"utf-16","capture_mode":"fragment","provenance":"synthetic","producer":"edittrace-example","description":"Self-contained UTF-16 replay example"}
```

- v1 强制显式声明 `position_encoding`；P0 仅接受 `utf-16`。
- `capture_mode` 为 `fragment` 或 `full`，是采集者声明。P0 只审计文档同步子集，即使声明 full 也不代表完成全会话合规检查。
- `provenance` 为 `synthetic` 或 `captured`，仅是来源声明，不自动赋予可信度。
- P0 编码证据标注 `declared`。没有初始化消息不能称为协商所得；不得自动猜编码。
- 遇到其他编码返回清楚的未支持错误与退出码 2，而非按 UTF-16 继续。

### 6.2 message

```json
{"kind":"message","seq":1,"direction":"client_to_server","message":{"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":"file:///demo.mbt","languageId":"moonbit","version":1,"text":"A🌙B\n"}}}}
{"kind":"message","seq":2,"direction":"client_to_server","message":{"jsonrpc":"2.0","method":"textDocument/didChange","params":{"textDocument":{"uri":"file:///demo.mbt","version":2},"contentChanges":[{"range":{"start":{"line":0,"character":3},"end":{"line":0,"character":4}},"text":"C"}]}}}
```

此例最终内容为 `A🌙C\n`。`A` 占一个 UTF-16 单元，`🌙` 占两个，所以 `B` 的起点是 character=3。

- 所有非 meta 记录都有正整数 seq，按文件顺序严格增加；可以跳号，不可排序后再处理。
- seq 是会话记录编号，与文档 version 无关。P0 seq 限定在有符号 32 位正整数范围。
- 原始 JSON-RPC message 保留，以便证据导出。已支持的文档通知必须验证结构、方向和参数类型。
- 未支持的普通方法保留并统计为 ignored，不因为它们存在就声称完成了其协议检查。
- 同步通知不能因为 URI 是 file URI 就读取磁盘文件。
- 初始内容来自 didOpen；未收到 didOpen 的文档不能用本机同名文件猜测。

### 6.3 checkpoint

```json
{"kind":"checkpoint","seq":3,"uri":"file:///demo.mbt","version":2,"text":"A🌙C\n","source":"author-written-expected","label":"after-edit"}
```

检查点是 EditTrace 扩展，不是 LSP 方法。它比较此记录到达时的文档；URI、当前打开世代、版本必须对应。`source` 必填，用于说明预期内容来自人工规范样例、客户端缓冲区、服务端调试快照等。

检查点不更新、修复或重新建立文档状态。使用同一个重放引擎生成的检查点不算独立正确性证据。版本不匹配返回明确的未能比较结果，不将其伪装为内容差异。

### 6.4 非法输入与未知字段

允许已知记录中的额外字段用于前向兼容。未知 schema_version、未知 kind、非法 JSON、缺少必要字段、错误类型、重复/倒退 seq 均停止读取，返回已有部分报告、物理行号与完整性 false，退出码 2。

不要把 JSON 数字直接截断为整数。行、列、版本、seq 必须验证整数性与范围。文档版本遵循 LSP integer 的范围，并允许合法负值；行列遵循 uinteger 范围。不把版本跳号判错。

## 7. 文本与协议语义

### 7.1 坐标

- 行列从 0 开始，范围使用左闭右开。
- character 按 UTF-16 编码单元计数，不是 UTF-8 字节、Unicode 码点或可见字符。
- LF、CRLF、CR 分别作为行结束符；CRLF 是一个换行，保留原始文本，不把换行格式标准化。
- 行内容长度不含换行符；结尾有换行时保留末尾空行；空文档也有可定位的第 0 行。
- 超出有效行长的 character 按规范回退到该行末，产生 note，不作为默认失败项。
- 不支持的行位置、负数、倒置范围和代理对中间边界均有专门策略；不要混成同一种越界。
- 代理对中间边界：P0 为防止输出损坏文本，不应用本条通知，将文档标为未知；输出产品策略 warning，不伪称规范明确禁止。测试必须覆盖并说明参考实现差异。
- 超出文档行数：P0 标为不可重放 warning 并停止该文档的增量推导，视为产品边界策略；若后续按规范及参考库行为实现回退，需在决策记录、规则及测试中同步更改。

### 7.2 编辑

- range 缺省表示全文替换；range 为 null 不是缺省，按非法已支持消息处理。
- 一条 didChange 的 contentChanges 依数组顺序执行；后一条的坐标基于前一条执行后的文本。
- 通知的 version 对应全部修改完成后的版本。
- 不套用 TextEdit[] 针对同一原文的应用规则；两个模型不同。
- contentChanges 为空的 v1 策略：报告 warning，不修改文本及提交版本；文档版本链标为需重新建立。该规则标注产品策略，不能无依据称为 LSP 硬性禁令。
- rangeLength 已废弃；即使检查它，也只报告 warning，不用它替代 range 决定删除长度。
- 每条 didChange 在临时状态执行，只有所有编辑成功才提交；失败时不留下前几条编辑已应用的半成品。

### 7.3 生命周期及状态

按 URI 原始字符串精确匹配文档，不对文件路径大小写、百分号、分隔符做擅自归一化。关闭后重新打开建立新 generation；版本和文本不得混到旧 generation。

每个文档至少存储：URI、generation、是否打开、最后成功版本、最后成功文本、已观察到的最高版本、当前内容可信状态、上个通过的检查点 seq。

状态至少区分 known、unknown、closed。unknown 可保留 last_known_text 供解释，但报告不得把它称为当前文档内容。

未打开就修改的 URI 也必须建立未解析状态条目或等价的 unresolved 记录，确保最终完整性检查能发现它；不能因为文档不在 map 中就漏计，误返回成功。后续合法 didOpen 可为它建立第一个已知世代，历史 finding 保留。

遇到无法应用的编辑、无效版本链、重复打开等会破坏推导前提的事件：保留最后成功状态作为证据，标记当前文档 unknown；后续依赖它的增量修改只报告无法继续，不生成连锁内容错误。其他 URI 继续。

恢复条件：合法关闭后重新打开，或版本满足严格递增、第一条编辑为全文替换且该通知其余编辑全部有效。后者建立新的已知文本，并保留之前的 finding。增量编辑不能从未知内容自行恢复。

一次检查点 mismatch 不把重放状态变为 unknown：它证明外部期望不同，不表示消息本身无法重放。

## 8. 审计规则 v1

| 规则 ID | 级别 | 含义与处理 |
|---|---|---|
| ET001_CHANGE_WITHOUT_OPEN | error | 当前世代尚未打开；不应用 |
| ET002_DUPLICATE_OPEN | error | 尚未关闭时再次打开；不覆盖，标记 unknown |
| ET003_CLOSE_WITHOUT_OPEN | warning | 找不到当前打开世代；不虚构状态 |
| ET004_VERSION_NOT_INCREASING | error | 与已观察到的合法类型版本比较，重复或倒退；不应用并标记 unknown |
| ET005_RANGE_REVERSED | error | 范围起点晚于终点；不应用并标记 unknown |
| ET006_CHARACTER_CLAMPED | note | 按协议将超过行长的列回退；编辑仍可应用 |
| ET007_LINE_UNREPLAYABLE | warning | 行位置超出当前产品支持策略；标记 unknown |
| ET008_SURROGATE_BOUNDARY | warning | 边界落在代理对之间，产品保守策略；标记 unknown |
| ET009_CHECKPOINT_MISMATCH | error | 同版本已知文本与独立检查点不一致；保留比较证据 |
| ET010_CHECKPOINT_UNAVAILABLE | warning | 缺文档、版本不匹配或状态未知，未能比较 |
| ET011_DIRECTION_INVALID | error | 文档同步通知来自错误方向；不应用 |
| ET012_RANGE_LENGTH_MISMATCH | warning | 可选废弃字段与实际范围长度不符；不据此改变编辑 |
| ET013_STATE_UNKNOWN | warning | 当前增量修改依赖未知文本；抑制重复级联消息 |
| ET014_EMPTY_CHANGES | warning | v1 产品策略，见文本语义 |

规则必须有分类：protocol、product_policy、external_checkpoint；并附来源/解释，不能把所有 error 都说成协议错误。

每条 finding 至少包括稳定 ID、规则 ID、级别、分类、seq、物理行号、URI/generation、change_index、版本、说明、相关历史 seq、截断前后上下文、原始与有效坐标。无需的字段用 null 或缺省，格式统一。

找到实际问题的第一条消息与找到第一个失败检查点必须在措辞上区分。没有足够证据时输出“不确定根因”，不能自动宣称编码混用。

## 9. CLI 设计

以下命令是目标接口，尚未实现。源码执行形式以实际工具链帮助为准，在 M0 验证后同步 README。

```text
edittrace audit <trace.jsonl> [--format text|json] [--fail-on error|warning] [--out <report>]
edittrace replay <trace.jsonl> --uri <uri> --at-seq <n> [--out <text-file>]
edittrace export <trace.jsonl> --finding <finding-id> --out <new-directory>
edittrace --help
edittrace --version
```

源码演示候选形式：`moon run cmd/edittrace --target native -- audit examples/valid-unicode.jsonl`。Codex 必须实际执行确认，不能把本句当成已验证命令。

### 退出码

- 0：处理完整，未达到失败阈值；有 warning 时默认仍可为 0。
- 1：处理完整，存在达到用户阈值的审计 finding。
- 2：参数错误、格式/IO/资源限制、未支持编码，或仍有不可重建的文档状态等造成处理不完整。它优先于退出码 1。

note 永远不计入 error/warning 阈值。全部文档已明确恢复且无全局输入失败时，历史失败可保留为 finding、最终处理完整。P0 的审计完整性只指声明支持的文档同步分析，不是全 LSP 完整性。

机器 JSON 写 stdout，进度和内部错误写 stderr；指定 --out 时结果写文件，stdout 不混入人类说明。相同输入和选项产生字节级相同 JSON，不包含当前时间和机器绝对路径。

replay 只能输出指定 seq 时 known 的文档。unknown/closed 返回 2，不能悄悄输出最后成功文本。若输出到终端，处理控制字符展示，避免原始日志控制终端；输出文件保持原始内容。

### 报告

顶层至少有 schema_version、tool_version、scope、encoding_evidence、analysis_complete、exit_code、counts、documents、findings、limitations。

scope 明确 `document_sync_utf16_v1`；统计支持、忽略、拒绝消息数、成功/失败/不可比较检查点、最终 unknown 文档数。不得输出无法支持的“全会话完全合规”结论。

## 10. 复现包

首版采用目标 finding 所在 seq 之前的完整输入前缀，保留 meta、双向消息、其他文档和检查点，优先保证语义不变。暂不做删除中间消息的激进缩减。

```text
repro/
  trace.jsonl
  finding.json
  manifest.json
  README.md
```

- manifest 写入格式版本、工具版本、目标 finding 指纹、原始序号和输入来源说明。
- finding 指纹使用规则、URI、generation、seq、change_index、检查点标签等稳定字段；不依赖当前时间。
- 导出后自动重读 trace，确认目标指纹仍存在；由于前缀截断导致的完整性状态差异需明确，不要求总 finding 列表完全相同。
- 包内不复制工作目录、不自动读取 URI 文件、不根据文档 URI 决定输出路径。
- --out 默认要求新目录，拒绝覆盖已有目录或输入文件；所有生成文件是固定安全名称。
- 内容包含源码，提供来源说明和分享前检查提示，不声称完成自动脱敏。对源码文本随意替换会改变坐标和问题，不作为默认操作。

## 11. 性能与资源边界

首版接受 O(文档长度) 的字符串替换和重建索引；不要在没有测量前设计 rope。

建议初始默认上限：单条 JSONL 记录 8 MiB、单文档 4 MiB UTF-8 编码量、输入总量 64 MiB、同时打开文档 256 个、记录总数 100000、finding 保留 10000 条、每条上下文 200 个显示字符。所有上限以实际字节和明确单位实现，不能先无限读取再检查。

达到上限时返回结构化原因、analysis_complete=false 和退出码 2，不崩溃、不丢弃后假装成功。数字运算验证溢出；避免把恶意嵌套 JSON 导致的解析异常当成普通通过。

建议基准：固定种子的 10000 次小编辑、多个文档及至少一份较大文档。记录硬件、系统、工具链、输入规模、耗时和内存测量方法；测不到内存就明说，不编造结果，不设置未经验证的性能宣传数字。

默认只保留当前文档、有限上下文与摘要；replay 按需重新扫描到目标 seq，export 第二遍读取前缀，避免保存所有全文快照。

## 12. 测试矩阵与独立证据

### 文本与编辑

- 空文档；空行；结尾有/无换行；LF/CRLF/CR 及混合换行。
- ASCII、中文、补充平面 emoji、组合附加符、ZWJ 序列；不把字素宽度当 character。
- 首尾插入、跨行删除、整文替换、零长度范围、替换后行数变化。
- 合法行尾、超出列长回退、非法行、代理对中间边界、倒置范围。
- 单通知多次编辑必须有一个反例，能区分“依次作用”与“全部基于原文”。
- 固定反例：原文 `abc`，先在 (0,0) 插入 `X`，再把更新后 (0,1)—(0,2) 替换为 `A`，正确结果为 `XAbc`。
- 固定检查点反例：原文 `🌙ab`，把 (0,2)—(0,3) 替换为 `X`，按 UTF-16 重放得到 `🌙Xb`；若独立期望是 `🌙aX`，只能报告不一致，不能仅凭此断言客户端错误地使用了码点坐标。
- 通知后半段失败时，验证不留下前半段的部分提交。

### 会话与报告

- 正常打开/修改/关闭；关闭再打开后的新世代；多 URI 交错。
- 版本可跳号、合法负版本；重复及倒退；无效版本后的恢复。
- 未打开就修改、重复打开、重复关闭、错误方向。
- 一个 URI 失效后，另一个仍正常；未知状态下抑制级联误报。
- 检查点成功、内容不符、版本不符、来源缺失、状态未知。
- 无发现不冒充服务端正确；只有检查点证据时不猜根因。
- 格式错误、截断 JSON、错误类型、浮点数字、未知 schema、资源限制。
- UTF-8 文件输出、Windows 空格路径、stdout/stderr 分离及退出码 0/1/2。
- 重复运行 JSON 完全一致；复现包移到新目录可重放同一目标 finding。

### 独立对照

使用固定版本的 Microsoft `vscode-languageserver-textdocument` 作为合法 UTF-16 编辑序列的开发期参考。Node 只生成参考输入和结果，不进入生产功能。

- 记录包精确版本、锁文件、许可证和生成种子；先验证其行为与被采用的 LSP 规范条款一致。
- 生成至少 500 组受预算限制的确定性合法序列，包含多编辑与混合文本；对每步结果比较，而不只比较最终结果。
- 已知产品策略不同的非法输入不强行要求相等；单独记录差异与理由。
- 将生成后的参考样例和期望结果提交，普通 MoonBit 测试可离线运行；重新生成参考需要额外开发依赖，文档写明。
- 若无法取得参考依赖，保留人工核算的基准例和确定性性质测试，但如实把独立差分验证标为未完成，不能宣称已通过。

核心性质：合法坐标与偏移往返一致；空插入不改变文本；全文替换结果与指定文本相同；重放同一会话确定；批次依次应用结果符合参考。不要只用生产代码生成期望值再验证自身。

## 13. 演示案例

必须交付下列可直接运行的会话和预期报告。没有真实缺陷发现时，明确标注故障注入/合成样例。

1. `valid-unicode`：中文、emoji、换行及连续编辑，检查点通过，退出 0。
2. `valid-sequential`：同一消息两次编辑，只有正确顺序才能通过检查点，退出 0。
3. `checkpoint-mismatch`：坐标虽可重放，但与独立期望不同，退出 1；报告不声称已证明编码混用。
4. `version-regression-recovered`：出现版本倒退，随后有效全文替换恢复；保留 error，完成分析，退出 1。
5. `unknown-document`：未打开就修改，未能重建，退出 2。
6. `column-clamp`：按协议回退列坐标，只有 note，默认退出 0。
7. `surrogate-boundary`：明确产品策略，状态未知，退出 2。
8. `multi-document`：包含不同世代和交错文档，其中一个出现问题，其他不受污染。

3 分钟演示脚本：20 秒介绍用户痛点；40 秒正常 Unicode 重放；60 秒检查点失败及可疑区间解释；40 秒导出并异地重放；20 秒说明 MoonBit 核心库、测试证据和边界。

## 14. 分阶段开发与每阶段退出条件

日期是建议节奏，实际 Codex 可以连续完成，不需要人为等待到对应日期。

| 阶段 | 建议日期 | 实现 | 可验证的退出条件 |
|---|---|---|---|
| M0 | 10/15—10/16 | 环境、项目骨架、格式与版本记录 | 实际编译一个 CLI，读取正常 trace 并识别 meta |
| M1 | 10/16—10/18 | 文本模型、行索引、UTF-16 与批次编辑 | Unicode/换行/多编辑核心反例全部通过 |
| M2 | 10/18—10/20 | 会话状态机、规则与可信状态 | 生命周期、版本、事务回滚与恢复测试通过 |
| M3 | 10/20—10/22 | 检查点、报告与三个 CLI 命令 | 正常与错误样例退出码符合规格，复现包可重读 |
| M4 | 10/22—10/25 | 参考对照、资源限制、CI、文档 | 独立合法序列对照通过；CI 与干净目录演示成功 |
| M5 | 10/25—10/28 | 验收证据、申报与演示材料、可选真实采集 | P0 清单逐项有真实证据；P1 未完成如实标注 |
| 缓冲 | 10/29—10/30 | 修复、复查、人工提交 | 人工核对正式通知，确认已完成报名及验收提交 |

每阶段更新 PLAN.md：实际完成内容、验证命令和结果、决策、未解决问题、下一步。失败时先修复，不用更多功能掩盖失败。不创建“全部待办”的空壳仓库后停止。

## 15. 自动验证与 CI

以下是目标检查项，具体参数经当前工具链确认：格式检查、native 的 moon check、moon test、moon build、CLI 集成案例、复现包异地重放、JSON 确定性、参考样例对照。

- Windows 为首个真实验证平台，CI 再增加 Linux。若某平台未运行，不写“跨平台已验证”。
- 格式化修改先完成，再检查工作树；不要用忽略失败的脚本掩盖格式或测试失败。
- 集成脚本显式断言预期退出码；错误案例预期为 1/2，不能用通配的忽略失败方式。
- CI 固定经过验证的工具链，依赖版本固定；不提交凭据，不在 PR 流水线运行发布。
- 从干净目录按 README 操作，验证每个展示命令。文档中的预期结果与实际报告一致。
- 同一套必要检查通过且没有代码变化后，不反复运行无关的大范围检查。

## 16. 本地完成与外部发布的边界

Codex 可以完成源码、测试、文档、申报草稿和本地发布准备。Git 提交须遵循当前用户授权和仓库约定，不自动造提交历史。

公开仓库、推送、Mooncakes 发布、报名表填写与提交、加入群聊、上传身份证明或领奖信息均需真实账号和相应授权。没有授权时把这些列为外部待办；不要伪造公开链接、已发布状态、报名结果或身份信息。

需要 PDF 时，先完成真实的一页申报内容，再按正式表单要求导出。当前只核实了“一页项目说明”，不能断言本赛事强制 PDF。

维护材料：README 快速开始与完整功能边界；TRACE_FORMAT 字段及示例；PROTOCOL_NOTES 规范与产品策略；RULES 规则与证据；VALIDATION 真实测试；LIMITATIONS 未支持内容；AI_USAGE 协助与责任；PROPOSAL 一页草稿；DEMO 三分钟脚本。

## 17. 完成标准

- [ ] 所有 P0 功能真实实现，核心无占位返回、伪造报告或未说明的 TODO。
- [ ] MoonBit 承担全部产品核心逻辑；核心可通过公共 API 复用。
- [ ] 8 类演示样例及关键边界测试通过，退出码 0/1/2 均被验证。
- [ ] 合法序列独立参考验证有版本、来源、生成方法和实际结果。
- [ ] 在新目录可运行 README 演示与导出证据包重放。
- [ ] 不把 warning 产品策略、检查点不一致或部分日志称为已证明的服务端缺陷。
- [ ] 资源限制生效，失败保留明确的完整性状态。
- [ ] 文档、许可证、来源说明、版本记录、CI 和验收记录完整。
- [ ] 真实采集、Linux、性能及公共发布等未做项目如实列出。
- [ ] 人工赛事待办清楚列出，未冒称已经完成报名或验收。

## 18. 资料与核对来源

本方案中的具体产品设计、规则编号、格式、时间安排和测试目标是项目决策，不是赛事或 LSP 官方规定。

- [赛事官网](https://moonbitlang.github.io/Hackathon2026/)
- [官网当前公开源码](https://github.com/moonbitlang/Hackathon2026/blob/main/src/App.tsx)
- [正式章程入口，本文编写时无法取得正文](https://bxup9uklfcb.feishu.cn/wiki/Dx4Bwd6D1i3GfHkajQCcF7SznEd)
- [MoonBit 命令手册](https://moonbitlang.github.io/moon/commands.html)
- [MoonBit 异步与 IO 官方文档](https://github.com/moonbitlang/moonbit-docs/blob/main/next/language/async-experimental.md)
- [LSP 3.17 规范](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/)
- [didChange 原文](https://github.com/microsoft/language-server-protocol/blob/gh-pages/_specifications/lsp/3.17/textDocument/didChange.md)
- [Position 原文](https://github.com/microsoft/language-server-protocol/blob/gh-pages/_specifications/lsp/3.17/types/position.md)
- [Range 原文](https://github.com/microsoft/language-server-protocol/blob/gh-pages/_specifications/lsp/3.17/types/range.md)
- [初始化及编码能力](https://github.com/microsoft/language-server-protocol/blob/gh-pages/_specifications/lsp/3.17/general/initialize.md)
- [独立参考：Microsoft TextDocument](https://github.com/microsoft/vscode-languageserver-node/tree/main/textDocument)
- [相关 MoonBit 文档库](https://github.com/moonbit-community/text_document)
- [OpenAI Docs：长任务的目标、里程碑与验收组织](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex)
