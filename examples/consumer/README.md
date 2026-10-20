# 独立 MoonBit 消费者

该目录是独立 module，通过 moon.work 本地解析 EditTrace，不修改核心，不拼接 JSONL。

在此目录执行 `moon run . --target native`。示例使用带类型的 `Edit`、`Position` 和 `FindingExpectation`；实际输出应为 `A🌙C`。工具链使用主项目固定版本。

尚未发布到 Mooncakes，因此这里不声称注册表安装可用。
