# 三分钟演示脚本

历史同步子集演示。当前整改演示见 [DEMO_REMEDIATED.md](DEMO_REMEDIATED.md)。

先按 README 完成编译。在项目根目录运行，使用新的输出目录。所有案例明确为合成故障注入，不冒充第三方服务器漏洞。

## 0:00—0:20：问题

“编辑器和语言服务器通过修改消息保持文本同步。连续编辑、emoji 坐标和版本问题难以从消息列表直接看懂。EditTrace 把它们重放成文本与具体证据。”

## 0:20—1:00：正确的 Unicode 重放

`moon run cmd/edittrace --target native -- audit examples/valid-unicode.jsonl`

展示 UTF-16 正确修改了 A🌙B 中的 B；检查点通过，退出 0。打开 examples/valid-sequential.jsonl，说明同消息内第二次编辑基于更新后的文本。

## 1:00—2:00：独立检查点不一致

`moon run cmd/edittrace --target native -- audit examples/checkpoint-mismatch.jsonl --format json`

预期退出 1。解释 actual 和 expected：坐标合法、序列可以重放，但独立检查点不同。工具定位的是证据区间，未自动证明编码混用或服务器内部错误。

## 2:00—2:40：导出与重放

`moon run cmd/edittrace --target native -- export examples/checkpoint-mismatch.jsonl --finding ET009_CHECKPOINT_MISMATCH:3:-1:0 --out demo-repro`

`moon run cmd/edittrace --target native -- audit demo-repro/trace.jsonl --format json`

展示 manifest.verified、相同 fingerprint 和完整前缀；这是复现证据包，尚不声称全局最小。

## 2:40—3:00：验证与边界

展示 tests/oracle/manifest.json 的 500/4000 和 docs/validation-results.json 的实际结果。说明 MoonBit 实现核心与 CLI，脚本只生成独立测试和组织验收；当前仅支持声明 UTF-16 的文档同步子集。

演示后能解释：代理对边界策略、事务回滚、unknown 恢复、参考缓存观察及公开发布待办。
