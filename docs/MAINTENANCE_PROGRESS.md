# 本轮维护执行记录

开始日期：2026-10-25；基线提交 6f0517e。按 CODEX_MAINTENANCE_TASK.md 的 T0–T7 执行，默认单代理。

已有修改：README.md 的维护入口、CODEX_MAINTENANCE_TASK.md、docs/MAINTENANCE_PLAN.md；保留并纳入本轮文档。

| 阶段 | 状态 | 实际依据 / 剩余事项 |
|---|---|---|
| T0 | 验证完成 | 本轮执行 scripts/validate.py --clean-room：337 项通过，native 测试由验收执行；原参考 500 会话/4000 检查点不重生成 |
| T1 | 验证完成 | core doctor、宿主能力诊断、空编辑/失败/超时处理；README/CLI/快速体验/限制已整理；真实 VS Code 1.143.1 已执行 |
| T2 | 验证完成 | MoonBit display_summary、全文件选择、预测/actual 差异、原始 JSON；真实宿主两文件差异通过 |
| T3 | 验证完成，补充边界复核中 | .edittrace 草稿/确认、内容哈希、修改失效、迁移；真实宿主保存与整套运行通过；确认弹窗未自动点击 |
| T4 | 验证完成 | CLI 新维护检查 16 项通过；Python ElementTree 独立解析 XML 与退出 0/1/2 |
| T5 | 本地准备验证完成；外部验证受限 | 类型化 EditResult、native 和 JS 消费调用实际通过；源码候选已生成；注册表无发布授权/已核实命名空间，消费未执行；真实隔离宿主探测无 MoonBit 扩展、语言为 plaintext，无格式化结果 |
| T6 | 本机验证完成；Linux 受限 | Windows 0.3.0 候选 16 项发行检查及实际隔离安装通过，安装包/内置核心真实宿主 22 项通过；Linux 本机无执行环境 |
| T7 | 进行中 | 文档与 API 快照已更新，准备功能提交与最终核对 |

基线命令：设置项目 .tooling/moon 为当前会话 MOON_HOME 后执行 `python scripts/validate.py --clean-room`，退出 0，耗时基准 0.488879 秒（历史基准输入，非性能优胜结论）。详细结果见 docs/validation-results.json；过程日志 artifacts/moon-*.log。

本轮只授权本地实现、测试、文档、候选及有意义提交；不新增公开推送、包发布、赛事提交或对外联系。注册表消费需实际发布版本与账户；Linux 本机运行需可用环境，均按事实单独记录。

中间验证：21 项 native 测试通过；Node 12 项通过（沙箱下 rename/junction 两项 EPERM，提升权限后在隔离临时目录执行同组测试全部通过）；源扩展真实 VS Code 1.143.1 的 22 项检查通过。以上为自动演练，不代表真人试用或人工审核。

源码候选修复：首次 staging 放在被忽略的 output 目录下，固定 moon package 生成空 ZIP，校验拒绝。改为仓库外新临时目录，显式排除构建缓存；隔离目录构建元数据曾受沙箱拒绝，提升权限后实际生成 56 文件候选并核对许可证及排除清单。失败候选保留在 output 的早期目录，不作为交付；最终目录以本记录后续结果为准。

本轮后续验证：完整干净目录验收 353 项、native 21 项、Node 14 项、CI 支持 6 项均通过；API 快照一致。CI 支持中的原子替换测试同样曾受沙箱限制，提升权限后原组 6 项全部通过。源扩展/打包扩展均在实际 VS Code 1.143.1 验证；最终已安装包检查 22 项，没有自动点击人类期望审核弹窗。

已形成提交：9d82827（任务与基线）、a0da2f2（MoonBit 诊断/摘要/JUnit/API）、fb2ebdb（扩展差异与内容确认回归）。发布准备及最终证据另行提交；本轮未推送。
