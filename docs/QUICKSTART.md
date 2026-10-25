# EditTrace 快速体验

下载/取得与你系统匹配的发行 ZIP，解压后在目录中执行。无需 MoonBit 或 Python。Windows 命令前用 `.\edittrace.exe`；Linux 对解压后的 `edittrace` 赋予执行权限后用 `./edittrace`。当前公开版为 0.2.0 Preview 1；以下 doctor 与 JUnit 命令需要本地 0.3.0 候选，其他示例兼容旧版。

```
edittrace check-edits examples/format.plan.json
edittrace check-edits examples/rename.plan.json
edittrace suite run examples/suite.json
edittrace case run examples/injected-lost-event.case.json
edittrace import examples/vscode-jsonrpc.jsonl --from vscode-json --out imported.jsonl
edittrace audit imported.jsonl
edittrace case create examples/format.case.json --out format-regression
edittrace case run format-regression/case.json
edittrace doctor --format json
edittrace suite run examples/suite.json --format junit --out result.xml
```

丢事件注入用例预期返回 1，证明它无法满足独立实采快照断言；suite 内的版本过期用例预期成功复现该问题，因此 suite 返回 0。0=完整通过，1=完整失败，2=输入/执行不完整。

格式化与重命名样例来自真实 VS Code 提供者，actual 文本来自宿主实际应用结果。URI 已归一化，因此无需读取样例 URI 所指的文件。文本编辑不会改写用户工程。原始服务器通信没有独立服务端文本检查点，不能据审计通过推断其内存正确。

VS Code：安装匹配平台的 VSIX，在命令面板搜索 EditTrace。发行 VSIX 已含核心；从源码运行时需将 edittrace.executablePath 设置为本机构建的绝对路径。先录制再停止分析，或预览格式化/重命名结果；默认不修改工程。导出的回归草稿需人工审核期望。

0.3.0：先 Diagnose Installation，再查看可读摘要；Select File and Show Text Diff 支持全部变更文件。Initialize Project Regressions → Save Project Regression Draft → Confirm Regression Expectations → Run Confirmed Project Regressions，形成项目回归流程。确认前会展示期望差异；修改用例后须重新确认。完整 JSON 通过 Show Raw JSON Report 打开。源码仓库的上述样例位于 `examples/real-world/`，与发行包的 `examples/` 路径不同。

这些是开发者演练资料，尚未证明需求规模或真人首次接入时间。检查发行包的 SHA256.json；工具的证据包一致性校验不等于密码学真实性证明。
