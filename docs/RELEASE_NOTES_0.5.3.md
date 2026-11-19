# EditTrace 0.5.3 候选

- 同步门禁跟踪 VS Code 命令执行窗口中的编辑。对未声明缓冲区和审核要求保持不变的文件，编辑后撤销仍会返回 1。只读打开允许，证据不完整返回 2。运行 `edittrace doctor --format json` 确认 `provider_sync_scope_guard`。
- 消费方可以用 `draft_provider_suite.py` 从两份快照起草待审核套件，并用 `--check-input` 验证候选哈希、宿主版本和示例的固定外部依赖，再运行实际宿主。
- TypeScript 示例使用两个固定官方工具版本和一份共同审核基线。另有合成漏改适配器，可在同一基线上观察失败和恢复。
- 新候选与公开旧 Preview 分开。消费方使用同一候选的 CLI、执行器及对应平台 VSIX。0.5.2 的同步执行器/核心仍有范围漏检。现有离线 trace、冻结 case 和 bundle 继续按原入口运行。

ZIP 内运行 `./edittrace audit examples/sync.jsonl --format json`，Windows 使用 `./edittrace.exe`。Linux 解压后执行 `chmod +x ./edittrace`。工作流说明在 `PROVIDER_REGRESSIONS.md` 和 `examples/provider-consumer/README.md`。
