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

使用 audit --omit-excerpts 时，before_excerpt、after_excerpt 和 documents[].last_known_excerpt 为 null，顶层增加 excerpt_mode="omitted"；默认报告结构不变。其他字段不作脱敏保证。

`before_excerpt` 对编辑失败表示整个通知之前最后成功文本的开头；`after_excerpt` 对检查点错误表示独立预期文本的开头。均截到 200 个 Unicode 码点，省略号标记截断；不是可用于替代原文重放的完整数据。`related_seq=0` 表示尚无通过的检查点。有效偏移采用整文 UTF-16 单元偏移。

documents 只列每个 URI 的当前世代状态；旧世代问题仍保留在 findings。last_known_excerpt 在 unknown 时不是当前内容。最终存在 unresolved 文档或全局输入错误时 analysis_complete=false。

文本报告同样逐项列出文档 URI、known/unknown/closed、当前世代、最后成功版本和最高观察版本。URI 使用 JSON 转义，避免换行或终端控制字符干扰阅读；unknown 文档的最后成功版本不表示该版本之后的当前文本已知。

## 导入原始日志

`import --from vscode-json` 支持固定 JSON tracer 方言：一行一个 type/message/timestamp 对象，方向以客户端为视角；支持 send-* 与 receive-* 三类请求/响应/通知。已用 vscode-jsonrpc 8.2.1 与 VS Code 1.138.0 内置 JSON 服务器实采验证。它不是带时间前缀的输出面板文本解析器，也不读取原始 Content-Length 流。生产者的 isLSPMessage 若存在必须为 true。

转换保留消息内容、实际记录顺序，生成 meta、seq 和 source_line/source_type。meta.encoding_basis 区分 initialize 显式 UTF-16、完整初始化的缺省 UTF-16，以及无初始化片段的适配器假设；后者不能冒充已验证协商。双向独立流无全局顺序证据时不能合并。截断、损坏、混合 initialize 或非 UTF-16 会话拒绝输出，不补造基线或检查点。JSON 记录边界之外的完整记录丢失无法仅靠日志自动发现。

0.2.0 导入始终声明 capture_mode=fragment；initialization_observed 仅说明观察到了完整初始化交互，不证明全会话捕获。初始化完成后的正常请求 id 复用不会被误判为重复初始化响应。

编辑器采集通过 evidence_scope=editor_document_events 明示来源。宿主 getText 快照作为独立检查点，保留宿主事件数组的顺序转换成同步修改，不重新按偏移或数组下标排序；同位置插入已由真实宿主验证。与 LSP 通信观察分开。

## 新格式

批量编辑计划、回归 case/suite 独立版本化，不改变旧 v1 的 didChange 语义。字段契约及退出码见 [REMEDIATION_SPEC](REMEDIATION_SPEC.md)，可运行样例见 examples/real-world。
