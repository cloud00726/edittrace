# 架构

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
