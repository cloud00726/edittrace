# 审查反馈整改证据矩阵

2026-10-20。以下反馈来自用户提供的两条组委会意见。状态必须区分实现、实际验证和真人需求证据。

| 质疑 | 对应阶段 | 当前状态 | 所需证据 |
|---|---|---|---|
| 场景窄、频率有限 | M2/M3/M7 | 三类技术场景已实采；需求频率未证实 | examples/real-world 的格式化、跨文件文本重命名和同步；USER_TRIAL.md 尚无真人反馈 |
| 规范化日志接入成本高 | M1/M3/M6 | 已实现并本地验证 | 13 条真实服务器 trace 直接导入；实际扩展录制/预览；ZIP/VSIX 自带 native 核心；发行验证见 distribution-validation.json |
| 与现有工具重叠 | M2/M4/M5/M7 | 新工作流已验证；无全面竞品优胜结论 | 同基线批量预检、独立宿主 actual 比较、case/suite、按文档筛选重验；WORKFLOW_COMPARISON.md 仅比较实测任务/公开能力 |
| 独立复用不足 | M4/M6 | 独立消费者和迁移通过；外部采用未证明 | examples/consumer 带类型接口；consumer-validation.json；外部 CI 示例已配置，未在远程执行或发布 Mooncakes |

基线通过：256 断言、500 参考会话、4000 检查点、干净目录构建。这些证明基线工程行为，不证明需求规模。探针及新增结果后续追加。

当前扩展支持范围是本地文件/untitled、UTF-16、纯文本编辑；rename 使用稳定 API 的文本投影，因此资源文件操作与提供者原始版本不在验证范围。宿主实采见 capture-evidence.json，新 CLI 及过滤导出验收见 remediation-validation.json。

发布前复核后的已安装 VSIX 真实宿主检查 14 项通过，见 ../host-validation.json；完整验收 337 项、新工作流 80 项、native 19 测试及独立消费者通过。初轮结果见 REMEDIATION_RESULT.md，后续审查见 ../PRE_RELEASE_REVIEW.md。计数不代表真人需求或审核认可。

尚不能声称四条意见全部被审核方认可：真人需求规模、持续使用、公开包消费和重新送审结果仍需独立证据。用户现已授权完成发布前审查、安装演练、推送与 GitHub 预览发布；远程结果须以实际 Actions 和 Releases 为准。未授权对外联系或正式送审。
