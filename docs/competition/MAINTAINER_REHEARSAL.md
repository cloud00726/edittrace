# 维护者验收演练

使用同一 0.5.3 候选的 CLI 和执行器、VS Code 1.144.0 与一个新输出目录。Windows 用 `./edittrace.exe`，Linux 使用相应 ZIP 中的 `./edittrace`，解压后赋予执行权限。下载、依赖摘要和完整命令见[候选门禁](../PROVIDER_REGRESSIONS.md)与[消费方示例](../../examples/provider-consumer/README.md)。

1. 运行 `edittrace doctor --format json`，核对版本、observation schema 和 `provider_sync_scope_guard`。
2. 按示例运行完整 TypeScript 5.7.3。查看退出 0、`candidate_api_v1`、候选哈希及审核 suite 哈希。解释文件终态是谁生成、谁审核的。
3. 用相同 suite 运行合成漏改构建。核对退出 1、`client.ts` 和偏移 9。运行 `sync-scope-suite.json`，解释只读打开为何通过，撤销后为何仍报告越界。
4. 用错误候选摘要运行预检或用 0.5.2 核心运行同步预检。查看退出 2 与错误阶段，说明为何证据不完整不应归类为项目行为回归。
5. 用自己的话说明 UTF-16 下 `🌙` 占两个编码单元。解释同一批 `TextEdit[]` 针对共同基线，顺序 `didChange` 更新后续坐标。指出本次验证观察的是客户端文本与隔离工作区，分别确认服务端状态需要的额外证据。
6. 解释 `host_observation` 中可能参与的其他提供者与 `candidate_api_v1` 的归属差异，以及 AppArmor 配置为何匹配指定 VS Code 测试程序。

## 实际参与者记录

本页为演练材料。人工记录待参与者执行后填写，可单独保存。

| 日期和运行者 | 候选源 SHA 及平台 | 结果文件 | 发现、判断和是否认可预期 |
|---|---|---|---|
| 待实际执行 |  |  |  |
