# EditTrace

主要以 MoonBit 实现的离线 LSP 文档同步审计与复现工具。

读取规范化会话，按 UTF-16 坐标重放增量编辑，检查版本和生命周期，比较独立检查点，导出能够再次运行的证据包。面向编辑器插件和语言服务器开发者。

本项目为 2026 年十月 MoonBit 黑客松准备。当前无已公开仓库或已提交报名的声明。

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

首次安装和首次获取 MoonBit 依赖需要网络。归档地址、版本和 SHA256 见 `toolchain.json`。Windows 本地已验证；Linux 已提供 CI 配置，远程 CI 尚未运行，不能据此宣称 Linux 验收通过。

## 命令

```text
edittrace audit <trace.jsonl> [--format text|json] [--fail-on error|warning] [--out <new-file>]
edittrace replay <trace.jsonl> --uri <uri> --at-seq <n> [--out <new-file>]
edittrace export <trace.jsonl> --finding <finding-id> --out <new-directory>
```

源码运行时在命令前加 `moon run cmd/edittrace --target native --`。构建后 Windows 可直接运行 `_build/native/debug/build/cmd/edittrace/edittrace.exe`；Linux 对应文件名为 `edittrace`。

示例：

```powershell
moon run cmd/edittrace --target native -- audit examples/checkpoint-mismatch.jsonl --format json
# 此案例预期退出 1，不代表工具运行失败。
moon run cmd/edittrace --target native -- replay examples/valid-unicode.jsonl --uri file:///demo.mbt --at-seq 3 --out replayed.txt
moon run cmd/edittrace --target native -- export examples/checkpoint-mismatch.jsonl --finding ET009_CHECKPOINT_MISMATCH:3:-1:0 --out demo-repro
moon run cmd/edittrace --target native -- audit demo-repro/trace.jsonl --format json
```

`--out` 要求目标尚不存在，防止覆盖输入或已有结果。replay 写文件保留精确 UTF-8 内容；输出到终端时使用 JSON 字符串转义，防止源码中的控制字符影响终端。

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

随后放置带 seq 和 direction 的 JSON-RPC 消息。当前识别 `textDocument/didOpen`、`didChange`、`didClose`。用非 LSP 的 `checkpoint` 记录提供预期文本。完整字段及样例见 [TRACE_FORMAT](docs/TRACE_FORMAT.md)。

文件 URI 仅作标识，不读取对应文件。文本从 didOpen 开始重建。不具备基线时不会从本机文件猜测。

## 关键行为

- 正确区分 UTF-16 单元、Unicode 码点和可见字素；支持中文、emoji、组合字符。
- 同一 didChange 中多次编辑依次作用于更新后的文本。
- 保留 LF、CRLF、CR；超过有效行长的列按协议回退并给出 note。
- 整条通知事务化。中途失败不留下半次修改，后续依赖未知文本的编辑不会产生级联猜测。
- 支持合法负版本、版本跳号、多文档隔离及关闭重开后的新世代。
- 检查点提供独立比较证据，不修改状态，也不自动证明缺陷根因或服务端内部状态。
- 复现包保留完整输入前缀并重新读取验证，尚不自动寻找最小序列。

详见 [协议边界](docs/PROTOCOL_NOTES.md)、[规则](docs/RULES.md)、[架构](docs/ARCHITECTURE.md)和[限制](docs/LIMITATIONS.md)。

## 示例与验收

`examples/expected.json` 列出 8 个合成案例的预期退出码：正常 Unicode、依次编辑、检查点差异、版本倒退后恢复、缺少基线、列回退、代理对边界、多文档与重开。它们不是发现真实第三方服务器缺陷的证明。

```powershell
moon test --target native
python scripts/validate.py --clean-room
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

[项目申报草稿](docs/competition/PROPOSAL.md)、[三分钟演示](docs/competition/DEMO.md)、[提交清单](docs/competition/SUBMISSION_CHECKLIST.md)。真实身份、仓库公开、报名和验收提交仍需参赛者完成。
