# 三分钟整改演示

前提：取得本地平台发行 ZIP/VSIX。CLI 以下用 edittrace 表示，Windows 使用实际 exe 路径。新目录用于导出，不能覆盖旧结果。演示脚本不等于实测三分钟已达成。

## 0:00–0:30：真实入口

展示 VS Code 的开始记录/停止分析和两个提供者预览命令。说明核心随 VSIX 附带，用户无需编译或手写 JSONL；现场操作使用临时工程。

备选 CLI：`edittrace import examples/real-world/vscode-jsonrpc.jsonl --from vscode-json --out demo-imported.jsonl`，再 `edittrace audit demo-imported.jsonl`。这是实采原始 JSON tracer，未提供独立服务器快照。

## 0:30–1:15：格式化与重命名

`edittrace check-edits examples/real-world/format.plan.json` 与 `edittrace check-edits examples/real-world/rename.plan.json`。

展示 actual_compared=true；重命名 version_checked=false，说明实际宿主独立比较与版本约束是不同证据。文本投影不覆盖文件资源操作。

## 1:15–2:00：保留回归

`edittrace suite run examples/real-world/suite.json`：三类实采任务及版本故障复现通过。

`edittrace case run examples/real-world/injected-lost-event.case.json`：预期退出 1。说明这是明确的漏事件注入；独立快照断言未通过，不是工具崩溃或发现第三方漏洞。

## 2:00–2:35：异地运行

`edittrace case create examples/real-world/format.case.json --out demo-case`，将目录移至另一位置后 `edittrace case run <new-location>/case.json`。展示自包含基线、编辑和显式期望；不读取原工程路径。

## 2:35–3:00：证据与边界

展示真实宿主证据、独立消费者和验收结果。说明目前只有本地技术验证，真人使用频率和需求规模待试用；本轮产物未公开发布或重新送审。评委可以按 QUICKSTART 复核，而不是依赖口头承诺。
