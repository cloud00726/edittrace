# 架构

0.3.0 维护层：core/report 生成摘要/JUnit，core/edit_plan 新增 EditResult；extensions/vscode 的 diagnostics/presentation/project 分别负责能力探测、纯展示与本地回归文件管理。确认旁文件记录期望快照及内容哈希，文本计算和断言仍全部交给 MoonBit。项目 suite 在运行时组合，失败不更新期望；doctor 与 summary 能力是新扩展与核心的契约。

```text
cmd/edittrace → io/trace → core/session → core/text
             → io/bundle             → core/model
             → core/report           → core/model
```

- core/model：JSON 字段校验、32 位整数验证、结构深度预检、稳定序列化和有限摘要。
- core/text：UTF-16 行索引、边界和范围替换，不访问 IO。
- core/session：事务重放、多文档状态机、14 条规则和检查点。审计逻辑与状态机紧密共享状态，首版合并在一个包，避免无意义的层间转发。
- core/report：终端报告及固定摘录字段隐藏，所有外来字符串使用 JSON 转义。隐藏处理复制数据，不修改会话中的 finding。
- io/trace：64 KiB 分块读取、单记录与总量限制、UTF-8 严格解码、可选前缀选择。完整读取没有序号哨兵，遇到最大合法序号后仍校验剩余输入。
- io/bundle：两遍读取保留完整前缀，独占建立目录，写入后重新审计并验证目标指纹；独立 verify 对固定文件做有界读取与一致性校验，不提供密码学签名。
- cmd/edittrace：参数、输出目标和退出码；直接调用 C 标准库 exit 的 MoonBit 外部声明，无自编 C 业务逻辑。

公共使用方式：导入 local/edittrace/core/session，new()，逐行 feed_line()，report()；snapshot(uri) 只返回 known 内容。构建命名空间 local/edittrace 用于本地，不代表用户有相应公共账号。

文档状态分为已打开且 known、已打开且 unknown、closed；额外 unresolved 标志保留“关闭/缺失基线时收到修改”的未解决问题。current version、highest observed、generation、last passing checkpoint 分别维护。

首版每次替换及重建索引 O(n)，只保留每个 URI 当前文本；关闭清空文本，旧世代 finding 保留。replay 按需重新读取，export 可在总输入限制内保留前缀字符串，但不保存全部历史全文快照。

## 2026-10-20 整改扩展

- adapters/vscode_trace：真实 JSON tracer 格式校验、方向和初始化编码证据转换；不负责文件 IO。
- core/edit_plan：带类型的 Edit/Baseline，解析纯文本 WorkspaceEdit 子集，以不可变基线定位、稳定排序并应用；版本/重叠/actual 差异报告。没有实际结果时只提供预测。
- core/case：显式期望、文本/步骤/finding/禁止规则断言、批量用例；带类型 FindingExpectation。无外部脚本或路径执行；非法用例不会抑制 suite 后续用例，汇总取 0/1/2 最高状态。
- io/workflow：有界读取、新 CLI 调度、独占创建自包含用例包并复读验证。
- io/bundle：可选按文档筛选，其他文档记录替换为空行，保持 seq/物理行/完整目标 finding；verify 另核对筛选作用域。
- extensions/vscode：轻量宿主胶水，记录基线/事件/实际快照，取得官方提供者的文本编辑，参数数组调用 MoonBit 核心，提供只读差异和用例草稿。规则没有移到 JS。
- examples/consumer：独立 MoonBit module，moon.work 引用本地依赖，验证带类型 API；无注册表发布声明。

原审计核心有界流式读取；新工作流为上限 8 MiB 的有界整文件 JSON，导入为上限 64 MiB 的有界整文件处理，不声称同样的流式内存特征。批量编辑的坐标计算仍会重复扫描行，不声称高性能编辑器数据结构。
