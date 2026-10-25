# CLI 参考（0.3.0 候选）

下列命令以已构建的 `edittrace` 为例。Windows 使用 `edittrace.exe`，发行目录未加入 PATH 时使用 `./edittrace` 或 `.\edittrace.exe`。源码构建入口见仓库 README。0.2.0 下载包不含 doctor、summary 或 JUnit 新能力。

| 命令 | 参数 | 用途 |
|---|---|---|
| `doctor` | `[--format text\|json]` | 核心版本与能力；文本含可执行入口，平台及宿主由扩展诊断补充 |
| `audit <trace.jsonl>` | `[--format text\|json] [--fail-on error\|warning] [--omit-excerpts] [--out <new-file>]` | 同步重放与独立检查点 |
| `replay <trace.jsonl>` | `--uri <uri> --at-seq <positive-seq> [--out <new-file>]` | 指定已存在记录后的文档快照 |
| `export <trace.jsonl>` | `--finding <id> [--uri <uri>] --out <new-directory>` | 重验完整目标 finding 的复现证据包 |
| `verify <directory>` | `[--out <new-file>]` | 验证复现一致性，非真实性签名 |
| `import <json-trace>` | `--from vscode-json --out <new-file>` | 导入指定 JSON trace 方言 |
| `check-edits <plan.json>` | `[--format text\|json] [--out <new-file>]` | 同基线 TextEdit 预检及可用 actual 对照 |
| `case create <case.json>` | `--out <new-directory>` | 核对声明期望并封装；不证明期望本身正确 |
| `case run <case.json>` | `[--format text\|json] [--out <new-file>]` | 执行 v1 自包含用例 |
| `suite run <suite.json>` | `[--format text\|json\|junit] [--out <new-file>]` | 按清单运行所有用例；JUnit 区分 failure 与 error |

所有命令有 `--help`；支持 `--version`。所有 `--out` 目标必须不存在；运行不改写输入、源码或期望。import 和 case create 的输出参数为必填。

原 audit/replay/export/verify 可用 `--max-record-bytes`、`--max-input-bytes`、`--max-document-bytes`、`--max-open-documents`、`--max-findings` 降低默认限额；不支持任意升高。工作流输入上限 8 MiB，suite 为嵌入式 cases，最多 256 个。完整语义见 TRACE_FORMAT.md、PROTOCOL_NOTES.md。

退出 0：完整执行并满足检查或声明期望；退出 1：完整执行但检查/断言失败；退出 2：输入、IO、执行或支持范围不完整。成功复现预期故障的 case 可以返回 0，不能据此将底层故障称为正常行为。

## 常见处理

- 核心缺失：安装匹配平台 VSIX，或设置本机绝对可执行路径。扩展每次分析前用 doctor 核对能力，不以版本字符串全等代替协议兼容。
- 未返回格式化编辑：可能已格式化，也可能无提供者；稳定宿主 API 无法可靠区分，先确认语言服务已就绪。
- 提供者错误/超时：查看错误提示、等待服务就绪后重试；预览不应用工程编辑，超时不表示宿主底层任务已被取消。
- 退出 1：查看摘要、规则和声明期望，不自动更新基线。
- 退出 2：JSON 输入可能损坏、编码不支持、超限或文档状态未知；JSON 工作流结构错误可能只写 stderr，没有合法报告。
- `--out` 已存在：选择新的文件名，工具不会覆盖历史证据。
- 回归没有确认用例：显式审核并确认，修改后的文件需重新审核；CLI 直接运行 v1 case 不受扩展审核旁文件影响。

JUnit 默认省略原文及任意错误详情，但保留用例名称，不是完全脱敏输出。完整 JSON 含源码，应按实际分享范围处理。
