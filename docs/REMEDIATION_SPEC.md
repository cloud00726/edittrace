# EditTrace 整改接口契约（2026-10-20）

基线提交 7ee8b3964836cde50f11ae58041dc3299f739f78。Windows 基线 `python scripts/validate.py --clean-room`：256 断言，500 会话、4000 检查点通过。实际宿主 VS Code 1.138.0，提交 7debcd0e2acdea1c52de81bf9ee1620444407dda；Node 24.19.0；MoonBit 版本继续固定 toolchain.json。

发布前审查后核心/module/扩展为 0.2.0，JSONL 与 bundle schema 仍为 1；旧 tool_version=0.1.0 的证据包仍可 verify。用例步骤断言在单次回放中采集所需快照，不对每个断言重新回放前缀。

## 命令

保留原四命令，新增：

```
edittrace import <json-trace> --from vscode-json --out <new-file>
edittrace check-edits <plan.json> [--format text|json] [--out <new-file>]
edittrace case create <case.json> --out <new-directory>
edittrace case run <case.json-or-package/case.json> [--format text|json]
edittrace suite run <suite.json> [--format text|json]
```

新命令退出码 0 完整且通过，1 完整且发现问题/断言失败，2 不完整/格式/IO。报告确定性 JSON；text 为人可读摘要及 JSON 转义证据。输出不覆盖已有目标。

## 变更计划 v1

`schema_version:1, kind:"edit_plan", position_encoding:"utf-16", source:{...}, documents:[{uri,text,version}], workspace_edit:{documentChanges:[{textDocument:{uri,version},edits:[{range,newText}]}]}`。

支持 `workspace_edit.changes`（URI 到 TextEdit[]，不验证版本）和纯文本 `documentChanges`。二者不能同时出现。`version:null` 表示无版本约束，报告明确标记；基线 version 必须为整数。可选 `actual:[{uri,text}]` 来自独立宿主实际结果；有 actual 时必须完整覆盖本计划受影响文档，不允许漏项、重复或多余 URI。没有 actual 仅预检/预测，不能称为实际一致性验证。

不支持文件资源操作、注释编辑、重复 URI 的多阶段 documentChanges；显式拒绝。以原基线解析所有坐标，稳定排序，按规范处理同位置插入顺序及插入后替换；重叠产生完整失败，非法输入/缺基线/不可处理边界为不完整。列超长保留旧核心行末回退行为并披露 note；代理对中间边界拒绝。计算过程中有字节和编辑数上限，不改写工程。

三种语义分别实现：LSP didChange 顺序作用于更新后的文本；TextEdit 同基线；VS Code 文档事件已由宿主按可顺序应用次序给出，保留数组原顺序转换成同步事件，不再次排序。追加同位置插入实测发现重新排序会反转插入次序；微软 codeConverter 同样保留原数组。禁止用全文覆盖掩盖漏事件。

## 用例 v1

自包含 `schema_version:1, kind:"case", name, source, input:{kind:"edit_plan",plan:...}` 或 `input:{kind:"trace",records:[...]}`；`expect` 明确包含 `analysis_complete` 和 `exit_code`，可选 `texts:[{uri,text,at_seq?}]`、`findings:[{rule_id,uri?,seq?}]`、`absent_rules:[rule_id]`。旧审计 nested exit 与用例 exit 分别报告。未满足完整性要求的源分析不能因匹配某条 finding 而被当成正常通过。

`case create` 只封装已有显式期望，不从运行结果生成 golden，独占新目录并复读验证。失败期望合法，断言不符不得导出为已验证包。`suite` 清单为 `schema_version:1, kind:"suite", cases:[内嵌 case...]`，以自包含输入避免路径逃逸/外部脚本，最多 256 用例。用例包固定 case.json 可迁移，无任意文件读取或命令执行。

## 日志导入与证据

只支持实际验证的 vscode-json 方言：每个物理行 JSON，含 type/message/timestamp；允许其标准 log wrapper，但不模糊猜测任意格式。方向由生产者 type 映射，原顺序不按时间排序。meta 附带 producer、原始记录位置和编码证据，非同步消息保留。初始化响应有明确 encoding 时拒绝非 UTF-16；完整 initialize 请求/响应缺省 UTF-16 才能声称协商依据；缺初始化片段标记 UTF-16 适配器假设，不能称已协商。缺 baseline 不补造；重复 initialize 会话明确拒绝。

## 编辑器采集与安全边界

扩展使用官方稳定 API，通过参数数组调用本机核心。JS 为宿主胶水以避免运行时编译依赖；核心规则仍在 MoonBit。显式启动记录，默认本地，限制文档/记录/字节，停止即停止监听。基线、事件前后版本、实际快照分别记录；版本断裂为不完整。普通文档事件标记 editor_document_events，不冒充 LSP 通信。

格式化/重命名入口只取提供者编辑并预览。真实应用与独立结果采集在专用测试工作区完成。宿主集成测试与纯 Node 测试分开标记。真实日志、提供者输出和故障注入分别标记。发布、真人反馈、正式送审仍为外部状态。

## 依据

- https://code.visualstudio.com/api/references/commands
- https://code.visualstudio.com/api/references/vscode-api#TextDocumentChangeEvent
- https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/

本契约若与实测生产者结构不符，应记录具体探针结果后作最小调整，不静默扩张兼容声明。
