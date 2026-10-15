# 规则 v1

| ID 前缀 | 名称 | 级别 | 分类 | 处理 |
|---|---|---|---|---|
| ET001 | CHANGE_WITHOUT_OPEN | error | protocol | 保留 unresolved URI，不应用 |
| ET002 | DUPLICATE_OPEN | error | protocol | 不覆盖文本，状态 unknown |
| ET003 | CLOSE_WITHOUT_OPEN | warning | protocol | 不虚构文档 |
| ET004 | VERSION_NOT_INCREASING | error | protocol | 不应用，状态 unknown |
| ET005 | RANGE_REVERSED | error | protocol | 回滚通知，状态 unknown |
| ET006 | CHARACTER_CLAMPED | note | protocol | 回退到行末，继续编辑 |
| ET007 | LINE_UNREPLAYABLE | warning | product_policy | 行位置不支持，回滚并 unknown |
| ET008 | SURROGATE_BOUNDARY | warning | product_policy | 边界在代理对中间，回滚并 unknown |
| ET009 | CHECKPOINT_MISMATCH | error | external_checkpoint | 保留对比，不改状态 |
| ET010 | CHECKPOINT_UNAVAILABLE | warning | external_checkpoint | 记录不能比较的原因 |
| ET011 | DIRECTION_INVALID | error | protocol | 拒绝反向通知，不应用 |
| ET012 | RANGE_LENGTH_MISMATCH | warning | protocol | 废弃字段只用于警告，range 决定编辑 |
| ET013 | STATE_UNKNOWN | warning | product_policy | 不推导文本，重复同类消息抑制 |
| ET014 | EMPTY_CHANGES | warning | product_policy | v1 保守策略，要求新基线 |

ET012 是废弃协议字段的一致性观察，不因此改变文本。ET006 是符合规范的回退记录。classification 描述依据，severity 描述本工具如何组织结果，两者不等同。

finding ID 由规则、seq、change_index、发现序号组成。fingerprint 由规则、URI、generation、seq、change_index、label 组成；不包含机器路径和当前时间。export 验证 fingerprint。

协议来源与具体产品策略见 [PROTOCOL_NOTES](PROTOCOL_NOTES.md)，必要前提及归类在对应规则测试中覆盖。
