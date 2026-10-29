# EditTrace 0.4.0 — 第二阶段本地候选

新增可预览的证据分享、结构化 URI 转换及重验、单文档检查点故障的预算缩减。核心计算均在 MoonBit，VS Code 负责选择输入、显示摘要、风险确认及取消。既有 audit/case/suite 的退出语义保持不变。

分享保留源码正文，不能保证消除正文中的秘密或路径；默认不附原身份映射表。未知扩展字段和方法拒绝分享。缩减只支持 ET009_CHECKPOINT_MISMATCH，完整目标 finding 必须保持一致；保留物理空行和全部生命周期/检查点。默认最多 32 次、上限 64 次候选重放，并设总处理量预算。预算耗尽交付最后验证的候选，不声称全局最小。

新增 `share plan`、`share export`、`minimize`、`evidence verify`，使用方式及可复制故障样例见 QUICKSTART.md。evidence v1 与原 bundle v1 分开；原 bundle 支持规范 0.1.x–0.4.x 生产者，仍完整验证 schema、策略、目标与重放结果。真实 0.1/0.2/0.3 二进制生成的旧包均通过新核心验证。

新增六类重复性能基线；未实施或宣称性能优化。新公共 evidence API 已有 native/JS 本地独立消费者。Mooncakes 未登录，MoonBit 提供者不可用；不声称注册表发布、真实 MoonBit 提供者集成或第三方采用。

本轮只生成 Windows x64 本地 ZIP/VSIX 和 MoonBit 源码候选。最终源码、校验和、安装验证和限制见 STAGE2_RESULT.md。0.4.0 尚未推送或触发远程 CI，不能沿用 0.3.0 的 Windows/Ubuntu CI 结果作为本轮验证。未执行 GitHub Release、Marketplace、Mooncakes 发布或赛事提交。
