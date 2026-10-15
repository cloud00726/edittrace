# EditTrace JSONL v1

UTF-8 文件，每个非空物理行一个 JSON 对象。第一物理行可有一个 UTF-8 BOM；其他位置不移除 BOM。空行忽略，CRLF 的物理行也可读取。源码内部换行使用 JSON 转义。未知字段保留兼容，未知 kind/schema、非法类型和非法 JSON 停止读取。nesting 上限 64，错误报告带物理行号。

## meta：首个非空记录

必要字段：kind=`meta`，schema_version=1，position_encoding=`utf-16`，capture_mode=`fragment|full`，provenance=`synthetic|captured`，producer=字符串。description 可选。

这些值是记录生产者的声明。v1 不验证初始化协商，也不因为 full 就做全 LSP 审计。其他编码明确返回退出 2。

## message

必要字段：kind=`message`、seq（1..2147483647）、direction（client_to_server 或 server_to_client）、message（JSON-RPC 对象，jsonrpc=`2.0`）。

所有非 meta 记录 seq 严格递增，可跳号。不要按时间戳排序，文档 version 与 seq 无关。

已支持的同步消息不可有 id，方向必须来自客户端。didOpen 参数包含 textDocument.uri、languageId、version、text；didChange 包含 textDocument.uri/version 和 contentChanges 数组；didClose 包含 textDocument.uri。

version 是 -2147483648..2147483647 的整数；位置 line/character 为 0..2147483647 整数。不截断小数。

编辑 `{text:...}` 为全文替换；`{range:{start:{line,character},end:{line,character}},text:...}` 为范围替换，range=null 非法。rangeLength 是可选非负整数，仅用于兼容警告。

未知方法和响应保留并计为 ignored；工具不会称它们已通过语义验证。已支持消息必须完整通过结构检查才能更新状态。

## checkpoint：本工具扩展

必要字段：kind=`checkpoint`、seq、uri、version、text、非空 source；label 可选。

它在自己的 seq 比较当前打开世代与相同 version 的文本。缺文档、关闭、unknown 或版本不同只报告不可比较。检查点不修改重放状态。source 说明预期的独立来源，不是一个外部文件路径。

最小完整示例见 [valid-unicode.jsonl](../examples/valid-unicode.jsonl)。导出的 trace.jsonl 使用相同格式。

## 报告

顶层 schema_version、tool_version、scope、encoding_evidence、analysis_complete、exit_code、meta、input_error、counts、documents、findings、limitations。

finding 包括 id、rule_id、severity、classification、seq、physical_line、uri、generation、change_index、version、message、before_excerpt、after_excerpt、coordinates、related_seq、label、fingerprint。

`before_excerpt` 对编辑失败表示整个通知之前最后成功文本的开头；`after_excerpt` 对检查点错误表示独立预期文本的开头。均截到 200 个 Unicode 码点，省略号标记截断；不是可用于替代原文重放的完整数据。`related_seq=0` 表示尚无通过的检查点。有效偏移采用整文 UTF-16 单元偏移。

documents 只列每个 URI 的当前世代状态；旧世代问题仍保留在 findings。last_known_excerpt 在 unknown 时不是当前内容。最终存在 unresolved 文档或全局输入错误时 analysis_complete=false。

## 导入原始日志

v1 不自动识别 VS Code 文本日志或原始 Content-Length 字节流。适配器应保留消息内容、方向、实际记录顺序，并生成 meta 和 seq；源日志没有的信息不能补造。双向独立流没有全局顺序证据时不能直接合并成可信时间线。适配器及在线采集是后续扩展。
