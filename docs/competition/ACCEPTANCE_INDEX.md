# EditTrace 六项验收索引

本地 0.5.3 的实测、候选源 SHA 和校验和见[执行记录](../ACCEPTANCE_UPGRADE.md)。[公开 `main`](https://github.com/cloud00726/edittrace/tree/main) 的已有结果与本地候选分别记录。

| 验收项 | 可复核证据 | 边界或待办 |
|---|---|---|
| MoonBit 为主 | `core/session/session.mbt`、`core/case/provider.mbt`、`core/edit_plan/edit_plan.mbt` 和 `cmd/edittrace/main.mbt` 负责文本、重放、判定、报告与 CLI。README 数据流标明宿主与脚本的职责。 | JavaScript 接入 VS Code，Python 调度进程和打包。 |
| 仓库公开 | [公开仓库](https://github.com/cloud00726/edittrace)及 `88b7f7a` 的[宿主矩阵](https://github.com/cloud00726/edittrace/actions/runs/44046938764)和[原生矩阵](https://github.com/cloud00726/edittrace/actions/runs/44046938725)。本轮提交可在本地由 `git log 88b7f7a..HEAD` 追踪。 | 0.5.3 本地候选的公开推送及远程矩阵待授权。 |
| 能够运行 | [README](../../README.md)列出三条入口，[验证矩阵](../VALIDATION.md)提供测试命令。真实 TypeScript 版本和故障注入记录于[执行记录](../ACCEPTANCE_UPGRADE.md)。 | 0.2.0 Preview 1 是现有公开下载版。新候选制品保留在本地。 |
| 工作有效 | [U0 提交及复验表](../ACCEPTANCE_UPGRADE.md#u0-基线)记录 11 月新增，本轮还增加同步范围拦截、固定版本语言工具消费者与发行物校验。 | 本期可计入起止、对应申报类别、补交资格需按活动页面和组委会确认。 [赛事官网](https://moonbitlang.github.io/Hackathon2026/) |
| 开源合规 | [MIT](../../LICENSE)、[第三方来源](../../THIRD_PARTY_NOTICES.md)、实际归档文件清单及独立参考声明。 | Mooncakes 命名空间与发布另行核实。 |
| AI 可解释 | [AI 责任记录](../AI_USAGE.md)和[演练清单](MAINTAINER_REHEARSAL.md)覆盖判定、来源、错误复验与职责。 | 人工理解、实际演练、结论和最终申报由参赛者完成。 |
