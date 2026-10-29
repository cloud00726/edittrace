# 分享与缩减契约 v1

新命令 share plan/export/verify、minimize 及 evidence verify。成功验证操作返回 0，即使底层保持的是预期故障；输入/IO/不支持返回 2。既有 audit/case 语义不变。

分享/缩减输入最多 8 MiB、2048 个物理行，含末尾换行以外的空行。源分析必须完整；选定 finding 必须真实存在。记录 seq 和物理行通过保留空行固定。分享严格拒绝未知字段/方法，支持 meta、didOpen/didChange/didClose、checkpoint；只映射结构化 URI，清除标签、来源及自由身份元数据，languageId 归一化为 text。源码/换行保留，可能仍含秘密；manifest 明示 retained_source=true，绝不声称全面脱敏，不附原始映射表。

分享保持完整目标 finding（仅允许结构化 URI、label 和 fingerprint 的对应变换），同时保留源报告退出状态。目标报告来自重放而不是字段伪造。分享清单仅包含数量/字节/风险，不输出原文或原 URI。分享 manifest 使用独立 evidence v1，不扩张旧 bundle v1 策略。

缩减第一版只支持单文档 ET009_CHECKPOINT_MISMATCH；保留全部打开/关闭与检查点，避免世代及最后通过检查点改变。仅尝试删除其他记录，保留物理空行，要求完整目标 finding（包含 before/after 摘录、版本、世代、related_seq、seq、行号、id 等）逐字段相等，且整体分析完整。此严格谓词可拒绝某些仍表现同类故障的缩减，优先保证证据一致。

限制：最多 64 次候选重放，默认 32；输入实际字节×物理行数计为保守每次处理工作量，总预算 128 MiB-equivalent。预算在每次尝试前检查；源/最终验证各一次不计入候选次数，亦受固定输入上限。缩减可能不变，预算耗尽输出最后验证候选并注明，绝不称全局最小。宿主/进程取消或超时不创建 verified 产物；写出需最后重新读包验证。

evidence manifest 包含策略、完整目标、报告退出状态、输入记录规范内容（用于自一致核对，不是签名）和缩减统计/保留序号。verify 重跑并逐项核对；manifest 及内容同改不提供真实性保证。原文件始终保留，输出目录须不存在；写失败可能留下未完成目录，拒绝无 verified manifest 的复核。

旧 bundle：支持 schema1 的 0.1.x–0.4.x 规范三段数字生产者，仍严格验证策略、元数据、完整 finding 和重放状态；未知 minor/major、非规范版本拒绝。版本字段不是安全信任凭据。
