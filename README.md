# EditTrace

主要以 MoonBit 实现的编辑器文本变更验证与回归工具。

面向编辑器插件和语言工具开发者，支持真实 JSON-RPC trace 导入、VS Code 文档采集、格式化/文本型重命名的批量编辑预检、实际文本比较及可迁移回归用例。保留 UTF-16 同步重放、版本/生命周期审计与复现包能力。核心规则、断言和 CLI 使用 MoonBit，VS Code 接入使用轻量 JavaScript 胶水。

本项目用于 2026 年十月 MoonBit 黑客松，公开仓库为 https://github.com/cloud00726/edittrace 。在早期格式反馈之后，用户提供了场景狭窄、接入成本高、差异化及复用不足的实质驳回意见；当前正在按这些意见整改。工程验证不等于赛事审核通过，尚未重新送审。

## 本轮新增入口（2026-10-20）

无需编译的使用方式见 [快速体验](docs/QUICKSTART.md)。发行 ZIP 与平台 VSIX 包含 native 核心，核心与扩展统一为 0.2.0；可下载版本及状态以 [GitHub Releases](https://github.com/cloud00726/edittrace/releases) 为准。源码开发仍可按下面工具链步骤构建。

```text
edittrace import examples/real-world/vscode-jsonrpc.jsonl --from vscode-json --out imported.jsonl
edittrace audit imported.jsonl
edittrace check-edits examples/real-world/format.plan.json
edittrace check-edits examples/real-world/rename.plan.json
edittrace suite run examples/real-world/suite.json
edittrace case create examples/real-world/format.case.json --out format-regression
edittrace case run format-regression/case.json
```

VS Code 扩展提供录制/停止、格式化与重命名只读预览、首文件差异和用例草稿保存。详见 [扩展说明](extensions/vscode/README.md)。采集的是编辑器事件；原始 LSP trace 是独立入口，两者不混同。重命名预览只验证稳定 API 可见的文本投影，不验证资源文件操作或提供者基线版本。

[实采样例](examples/real-world/README.md)覆盖真实 VS Code JSON 格式化、跨文件 TypeScript 重命名和 Unicode 同步。actual 文本由宿主实际应用取得；URI 已归一化，重跑不读取对应工程文件。真实宿主验证、命令行回归及独立消费者证据分别记录，不以这些结果推断真人需求规模。

[整改契约](docs/REMEDIATION_SPEC.md)说明新格式、边界和退出码；[反馈矩阵](docs/competition/FEEDBACK_MATRIX.md)列出已解决部分及外部待办。[独立消费者](examples/consumer/README.md)展示带类型 API，尚未声称已从 Mooncakes 安装。

## 快速开始

需要 Git、Python 3.11+；Windows native 编译需要可用的 MSVC C 工具链，Linux 需要 C 编译工具链。已有编译器可以先使用；本文验证版本是 MoonBit `v0.10.15+943464bfa`、moon `0.1.20261012`、async `0.22.5`。

安装项目固定的官方工具链到本地目录，不修改系统 PATH 或执行策略：

```powershell
python scripts/bootstrap.py
$env:MOON_HOME = (Resolve-Path .tooling/moon).Path
$env:PATH = "$env:MOON_HOME/bin;$env:PATH"
moon build --target native
moon run cmd/edittrace --target native -- audit examples/valid-unicode.jsonl
```

Linux 使用相同 bootstrap，然后设置当前会话环境：

```sh
python3 scripts/bootstrap.py
export MOON_HOME="$PWD/.tooling/moon"
export PATH="$MOON_HOME/bin:$PATH"
moon build --target native
moon run cmd/edittrace --target native -- audit examples/valid-unicode.jsonl
```

首次安装和首次获取 MoonBit 依赖需要网络。归档地址、版本和 SHA256 见 `toolchain.json`。Windows 本地已验证；基线提交 `79cde2a` 的 [Windows/Linux CI 已通过](https://github.com/cloud00726/edittrace/actions/runs/38738218872)。后续改动的实际结果以对应提交的 Actions 为准。

## 命令

工具链归档先下载到临时文件，通过固定 SHA256 校验后才写入下载缓存；连接中断或校验失败会清理临时文件。重试会重新下载损坏的项目缓存，已通过校验的缓存不会重复下载；通过 `--cache` 提供的外部文件仍只读校验。

`edittrace --help` 查看总览；`edittrace audit --help`、`edittrace replay --help`、`edittrace export --help`、`edittrace verify --help` 查看各命令用法，无需先提供输入文件。

```text
edittrace audit <trace.jsonl> [--format text|json] [--fail-on error|warning] [--omit-excerpts] [--out <new-file>]
edittrace replay <trace.jsonl> --uri <uri> --at-seq <n> [--out <new-file>]
edittrace export <trace.jsonl> --finding <finding-id> [--uri <uri>] --out <new-directory>
edittrace verify <bundle-directory> [--out <new-file>]
```

源码运行时在命令前加 `moon run cmd/edittrace --target native --`。构建后 Windows 可直接运行 `_build/native/debug/build/cmd/edittrace/edittrace.exe`。产物后缀以 MoonBit 实际构建结果为准，验收脚本在指定产物目录中识别 `edittrace.exe` 或 `edittrace`，不会仅按操作系统猜测文件名。

示例：

```powershell
moon run cmd/edittrace --target native -- audit examples/checkpoint-mismatch.jsonl --format json
# 此案例预期退出 1，不代表工具运行失败。
moon run cmd/edittrace --target native -- replay examples/valid-unicode.jsonl --uri file:///demo.mbt --at-seq 3 --out replayed.txt
moon run cmd/edittrace --target native -- export examples/checkpoint-mismatch.jsonl --finding ET009_CHECKPOINT_MISMATCH:3:-1:0 --out demo-repro
moon run cmd/edittrace --target native -- audit demo-repro/trace.jsonl --format json
moon run cmd/edittrace --target native -- verify demo-repro
```

`--out` 要求目标尚不存在，防止覆盖输入或已有结果。replay 写文件保留精确 UTF-8 内容；输出到终端时使用 JSON 字符串转义，防止源码中的控制字符影响终端。

`verify` 重新读取包内固定的 `trace.jsonl`、`finding.json` 和 `manifest.json`，核对完整 finding、目标指纹、结束序号、元数据及前缀退出码；元数据读取受单记录大小限制。验证成功返回 0，结果中的 `prefix_exit_code` 保留审计的 0/1/2 状态。它检查复现一致性，不是防篡改签名或真实性证明；README 和未列出的附加文件不参与校验。

`audit --omit-excerpts` 将 finding 的 before/after 摘录和文档的 last_known_excerpt 设为 null，并添加 `excerpt_mode="omitted"`，保留规则、坐标、指纹、计数和退出码。适用于减少分享报告中的源码文本；URI、meta、label 等字段仍可能含敏感信息，它不等同于完整脱敏，不影响 replay 输出或包含原文的复现包。

| 退出码 | 含义 |
|---|---|
| 0 | 支持范围内处理完整，未达到失败阈值 |
| 1 | 处理完整，存在达到阈值的审计 finding |
| 2 | 参数、输入、IO、未支持编码、资源上限或最终未知文档导致处理不完整 |

默认只有 error 触发退出 1，`--fail-on warning` 将 warning 纳入。note 不触发阈值。检查点无法比较会保留 warning；报告总是单独列出未比较数量。一个文档恢复后仍保留历史 finding。

## 输入格式

EditTrace v1 是自定义规范化 JSONL，并非任意编辑器日志的自动导入格式。文件 UTF-8，每个记录一行，第一条记录声明编码与来源：

```json
{"kind":"meta","schema_version":1,"position_encoding":"utf-16","capture_mode":"fragment","provenance":"synthetic","producer":"my-capture-adapter"}
```

随后放置带 seq 和 direction 的 JSON-RPC 消息。同步核心识别 `textDocument/didOpen`、`didChange`、`didClose`。用非 LSP 的 `checkpoint` 记录提供预期文本。用户可从受支持 JSON trace 导入或编辑器录制取得输入，不必手写该内部格式。完整字段及样例见 [TRACE_FORMAT](docs/TRACE_FORMAT.md)。

文件 URI 仅作标识，不读取对应文件。文本从 didOpen 开始重建。不具备基线时不会从本机文件猜测。

## 关键行为

- 正确区分 UTF-16 单元、Unicode 码点和可见字素；支持中文、emoji、组合字符。
- 同一 didChange 中多次编辑依次作用于更新后的文本。
- 保留 LF、CRLF、CR；超过有效行长的列按协议回退并给出 note。
- 整条通知事务化。中途失败不留下半次修改，后续依赖未知文本的编辑不会产生级联猜测。
- 支持合法负版本、版本跳号、多文档隔离及关闭重开后的新世代。
- 检查点提供独立比较证据，不修改状态，也不自动证明缺陷根因或服务端内部状态。
- 复现包默认保留完整前缀；`export --uri` 可去除其他文档记录，保留物理行号并重新核对完整目标 finding，失败则拒绝导出。尚不自动寻找最小序列。

详见 [协议边界](docs/PROTOCOL_NOTES.md)、[规则](docs/RULES.md)、[架构](docs/ARCHITECTURE.md)和[限制](docs/LIMITATIONS.md)。

## 示例与验收

`examples/expected.json` 列出原有 8 个合成案例。`examples/real-world` 另含真实宿主采集和明确标注的故障注入；故障注入不是发现第三方服务器缺陷的证明。

```powershell
moon test --target native
python scripts/validate.py --clean-room
python scripts/validate_consumer.py
node --test extensions/vscode/test/unit.cjs
# 需已安装 VS Code：真实宿主测试，使用隔离配置与工作区
python scripts/run_host_tests.py
# 在不存在的新目录中生成本地发行包
python scripts/package_release.py --out output/release-new
python scripts/validate_distribution.py --directory output/release-new --install-vsix
```

验收入口会检查格式、类型检查、测试、构建、CLI、资源边界、确定性和异地复现；`--clean-room` 额外复制必要源码到新目录构建并运行示例，保留产物供检查。所有断言实际执行，错误案例必须返回指定的非零退出码。

独立对照：固定 Microsoft `vscode-languageserver-textdocument@1.0.12`，500 组合法编辑会话、4000 个逐步检查点已编入 MoonBit 测试，无需 Node 即可运行。开发期重新生成方式：

```sh
cd scripts/oracle
npm ci
node reference-cache-probe.cjs
node generate.cjs
cd ../..
moon fmt
moon test --target native
```

参考库的 CRLF 行索引缓存观察及采用“每次编辑后重建参考文档”的原因见 [VALIDATION](docs/VALIDATION.md)。并非调整期望来迁就产品结果。

实际验证证据写入 [validation-results.json](docs/validation-results.json)，过程日志位于 `artifacts/`。相同输入的产品 JSON 报告不含时间戳；开发期证据可以记录系统信息与真实耗时。

## 资源上限

默认单记录 8 MiB、输入 64 MiB、单文档 4 MiB（UTF-8 编码字节）、同时打开 256 文档、10 万消息/检查点、1 万 finding、JSON 嵌套 64 层。输入按 64 KiB 块读取，在增长前检查记录上限；单次文件读取缓冲不超过一个块。

可用 `--max-record-bytes`、`--max-input-bytes`、`--max-document-bytes`、`--max-open-documents`、`--max-findings` 降低相应上限，值必须为正数且不超过默认值。达到限制返回不完整报告与退出 2。

## 开源、AI 与参赛材料

本项目采用 MIT，依赖归属见 [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md)，AI 协助情况见 [AI_USAGE](docs/AI_USAGE.md)。没有配置远程服务或上传会话。

[当前申报整改草稿](docs/competition/APPLICATION_REMEDIATED.md)、[同类项目历史核查](docs/competition/ECOSYSTEM_CHECK.md)、[当前演示](docs/competition/DEMO_REMEDIATED.md)、[提交清单](docs/competition/SUBMISSION_CHECKLIST.md)。此前核实的章程要求人工撰写一页 Markdown，草稿经过 AI 辅助，需参赛者按本人理解修改定稿并核对现行要求。本轮官网/飞书读取未获得可复核正文，没有推测新的截止时刻。此前 PDF 不用于本次重新申报。报名修改和验收提交仍需参赛者完成；尚未发布 Mooncakes 包。
