# 实采场景与复现

2026-10-20，在本机实际 VS Code 1.138.0 的独立测试宿主执行，使用内置 JSON 格式化和 TypeScript 重命名提供者。具体提供者版本、检查结果、原始宿主报告 SHA256 见 capture-evidence.json。不是用户量或真人试用记录。

| 文件 | 来源及用途 | 预期 |
|---|---|---|
| format.plan.json / format.case.json | 真实 JSON 提供者编辑，actual 来自 VS Code 实际应用后文本 | 预检、比较、断言通过 |
| rename.plan.json / rename.case.json | 真实 TypeScript 跨文件符号重命名；只采文本投影，不验证资源操作/提供者版本 | 两文件实际文本匹配；version_checked=false |
| sync.jsonl / sync.case.json | 真正文档事件，含 emoji、CRLF、批量编辑、undo/redo 和另一文档 | 4 个宿主独立快照通过 |
| injected-stale.case.json | 在真实格式化计划中人为改错版本 | 成功复现 EP001，用例返回 0，嵌套预检返回 1 |
| injected-lost-event.case.json | 人为删去一条实采编辑，保留实际快照及断言 | 用例失败，返回 1 |
| vscode-jsonrpc.jsonl | 固定 vscode-jsonrpc 8.2.1 JSON tracer 与实际内置 JSON 服务器通信，13 条记录 | 导入后审计通过；没有独立服务器文本检查点 |
| suite.json | 三类实采通过用例和版本故障复现用例 | 4 个用例通过 |
| same-position.plan.json / same-position-events.case.json | 追加真实宿主同位置插入探针，事件数组保持宿主原顺序 | 预测及事件重放均与 aXYb 相符 |

真实宿主记录中只对 URI 标识做稳定映射，编辑范围、版本、文本和 actual 未经手工修正。URI 不用于读取本机文件。原始完整报告位于开发机 artifacts/vscode-host/result.json，不随发行包暴露工作区绝对路径。

重跑已捕获用例：

```
edittrace suite run examples/real-world/suite.json --format json
edittrace case run examples/real-world/injected-lost-event.case.json --format json
```

重新实采：先构建核心，再运行 `python scripts/run_host_tests.py`。成功后才可运行 `python scripts/snapshot_host_examples.py` 更新这些宿主来源样例。JSON-RPC 实采另通过 `scripts/capture/capture.cjs`，需要按 lockfile 安装开发依赖并提供已安装 jsonServerMain.js 路径；不能以该脚本代替编辑器真实事件验证。

本轮未发现或声称真实第三方缺陷。注入只用于验证检测路径，不能证明真实需求规模或定位唯一根因。

`stage2-checkpoint.jsonl` 是明确标为 synthetic 的第二阶段演练，非真实宿主故障：包含一个可删除的全文不变更新，随后刻意给出与重放结果不符的检查点。目标 ID 为 `ET009_CHECKPOINT_MISMATCH:4:-1:0`，供分享/缩减/独立复核使用，不加入原真实提供者 suite。
