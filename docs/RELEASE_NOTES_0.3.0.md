# EditTrace 0.3.0 — 本地维护候选

新增安装能力诊断、MoonBit 摘要/JUnit、全部变更文件差异、独立 actual 对照入口及项目回归流程。首次使用建议运行 doctor，随后用已知正常/失败样例确认退出语义。

## 对使用者的变化

- 默认扩展结果为可读摘要；完整 JSON 通过独立命令打开。
- 差异入口可选每个已计算文件，actual 不存在时只显示预测。
- `.edittrace` 内保存草稿，显式确认后绑定内容哈希；后续修改须重新审核，不自动更新期望。
- suite 支持 `--format junit --out <new-file>`，failure 与 error 分开，退出 0/1/2 保持不变。
- 类型化 `EditResult` 为新增 API，旧 apply/Json/v1 输入仍支持。默认工作流 text 输出改为摘要，机器调用使用 JSON。

新扩展要求 doctor、summary 与 bridge protocol 1 能力，不可直接搭配旧 0.2.0 核心。报告和回归仍仅验证 UTF-16 纯文本子集，无法据此保证重构语义或服务端状态。

## 交付与外部状态

候选包含本机 Windows x64 ZIP/VSIX、校验和、源文件哈希与许可，以及由显式清单生成的 MoonBit 源码 ZIP。候选不表示已经 GitHub 发布、Marketplace/Mooncakes 发布或赛事提交。

本轮实际命令、平台、原始参考与验证结果见 MAINTENANCE_PROGRESS.md。无本机 Linux 环境；隔离宿主无 MoonBit 提供者，因此不声称已采集实际 MoonBit 格式化场景。人类审核弹窗未自动点击，自动确认状态检查与真人使用反馈分别记录。
