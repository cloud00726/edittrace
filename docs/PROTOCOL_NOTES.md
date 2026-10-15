# 协议语义与产品策略

基准：[LSP 3.17](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/)。编码声明只接受 UTF-16，报告 evidence=declared。未读取初始化协商，不支持其他编码自动转换。

- 范围起终点从 0 计数，右端不包含；character 是 UTF-16 单元。
- didChange.contentChanges 依序作用于更新后的文本，version 指向整条消息完成后的版本。不同于应用到共同原文的 TextEdit[]。
- 文档版本严格增加，允许跳号及合法负值；关闭重开建立新世代。
- 超出行内容长度的 character 按 Position 定义回退到行末，列回退是 note，不触发默认失败。
- CRLF 算一次换行，另支持 CR、LF；保留原始字符。删除换行应跨到下一行开头。

本产品的保守策略：非法行位置和代理对中间边界不继续应用，标记 unknown。空 contentChanges 也要求重新建立基线。这些规则明确分类 product_policy，不冒称全是规范硬性禁止。

每条修改通知先完整验证结构，再在临时文本上逐条执行。任一编辑不可应用则不提交整条消息。格式、资源问题是全局不完整；协议/策略问题通常只影响对应 URI。未知文本可由更高版本的全文替换通知或关闭重开恢复；后续纯增量不猜测。

已观察到的最高版本与最后成功版本分开。重复/倒退消息不回退 highest；失败后的全文恢复必须高于已观察到的版本。关闭重开时版本链重新开始。

检查点只陈述“此刻与独立预期不同”。报告给出最后通过的检查点和首次失败检查点之间的区间，不断言相邻上一条编辑是根因，更不从客户端消息推断服务端内存。

实现优化边界：坐标函数对每次编辑重建行索引，优先保证语义；没有声称对大文件提供对数复杂度。

协议来源：[didChange](https://github.com/microsoft/language-server-protocol/blob/gh-pages/_specifications/lsp/3.17/textDocument/didChange.md)、[Position](https://github.com/microsoft/language-server-protocol/blob/gh-pages/_specifications/lsp/3.17/types/position.md)、[Range](https://github.com/microsoft/language-server-protocol/blob/gh-pages/_specifications/lsp/3.17/types/range.md)。
