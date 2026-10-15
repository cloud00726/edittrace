# EditTrace 赛事与验收检查清单

日期依据：2026-10-15 的官网公开信息。以下空框不表示已经完成。

## 报名阶段：参赛者核对

- [ ] 已阅读正式章程及赛事群最新通知，核实 10 月 31 日截止的具体时刻与时区。
- [ ] 明确个人参赛或不超过 3 人的队伍，队长和 GitHub ID 正确。
- [ ] 已加入赛事群，昵称为本人 GitHub ID。
- [ ] 准备项目名称、公开仓库 URL 和一页项目说明。
- [ ] 申报书注明本期范围：UTF-16 离线文档同步审计、检查点比对及复现导出。
- [ ] 在官方表单真实提交，保存回执；注意十月最多提交 3 次的官网说明，具体修改口径核对群通知。
- [ ] 未把“已保存草稿”当成“报名成功”；滚动审核结果已核实。

官方入口：[官网](https://moonbitlang.github.io/Hackathon2026/)；[报名表](https://bxup9uklfcb.feishu.cn/share/base/form/shrcnWUMlgpbwHaXgzV7HmNhNhg)；[正式章程](https://bxup9uklfcb.feishu.cn/wiki/Dx4Bwd6D1i3GfHkajQCcF7SznEd)。

## 工程验收：由实际运行填写

| 项目 | 结果/证据路径 | 状态 |
|---|---|---|
| 工具链、依赖版本及 native 编译环境 | toolchain.json、docs/validation-results.json | Windows 已验证 |
| 格式、check、test、build | artifacts/moon-*.log；17 测试通过 | 已通过 |
| 8 类演示与退出码断言 | examples/expected.json；验收结果 JSON | 已通过 |
| 500 组合规序列的独立参考对照 | tests/oracle/manifest.json；4000 检查点 | 已通过 |
| 事务回滚、未知状态、恢复和世代隔离 | core/session/*_wbtest.mbt | 已通过 |
| 格式错误、资源限制与不完整报告 | scripts/validate.py；验收结果 JSON | 已通过 |
| 相同输入 JSON 字节一致 | 8 类案例重复运行比较 | 已通过 |
| 复现包移到新目录重放目标 finding | scripts/validate.py relocation 检查 | 已通过 |
| Windows 实际验证 | docs/validation-results.json | 已通过 |
| Linux CI 实际结果 | .github/workflows/ci.yml 已配置 | 未远程执行 |
| 真实 LSP 会话采集（可选） | 待填写 | 未执行 |
| 性能测量及测量方法 | validation-results.json；10000 小编辑；未测峰值内存 | 已实测 |

## 材料验收

- [ ] 源码公开可访问，主要实现语言为 MoonBit。
- [ ] 正常开发历史可追踪，没有虚构历史贡献。
- [x] README 命令在干净目录实际运行成功。
- [x] 自定义 JSONL 格式与原生 LSP 日志的差别说明清楚。
- [x] 协议规则、产品保守策略和检查点证据分别说明。
- [x] 限制中写明仅支持 UTF-16 和文档同步子集。
- [x] 未将客户端重放等同于服务端内部状态验证。
- [x] 样例标注合成或真实采集；故障注入不冒充发现真实漏洞。
- [x] 许可证、第三方声明、AI_USAGE 与必要归属信息齐全。
- [ ] 核实正式表单要求后准备最终一页说明及其文件格式。
- [ ] 演示脚本能在三分钟内完成，错误案例有清楚退出码。
- [ ] 验收入口、需提交附件与截止时间已向官方核实。
- [ ] 已实际提交验收并保留回执，不能以代码完成替代提交完成。

## 公开发布前的真实信息

仓库所有者、GitHub URL、发布命名空间、参赛成员、队名、联系方式和最终版本应由真实资料填写。Codex 可准备内容，不自行补造这些信息。

本清单中的 CI、独立对照、性能记录是项目工程目标；是否属于赛事强制条件，以正式章程为准。

## 本地验收结论

2026-10-15：17 个 MoonBit 测试、500 组参考序列和 4000 个逐步检查点通过；完整验收 207 项断言通过，含干净目录构建。P0 具备本地验收条件。未执行公开仓库、远程 CI、报名和验收提交。
