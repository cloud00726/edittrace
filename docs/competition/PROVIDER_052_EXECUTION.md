# 0.5.2 修复执行记录

## F0 基线与复现

执行起点为本地和 GitHub main 的 `5f5226b`，Windows 工具报告 0.5.1。Python 3.11.5、Node 24.22.1、Moon 0.1.20261012、moonc 0.10.15+943464bfa。原有未跟踪事项为任务书和 `APPLICATION_0.5.1.md`，申报书 SHA-256 为 `4eb223c5f011303a04df3e170585f5b2c7a39067da66d6992a54ec46fd5e117d`。

执行器原有 6 项测试通过。用 `python scripts/check_provider_evidence.py <0.5.1-binary> --baseline-051` 复现未编辑文件变化返回 0、缺失观测返回 1。模拟 GitHub PowerShell 步骤，只有预期退出 2 的命令与成功断言时，旧包装器使步骤返回 2，步骤显式退出 0 后返回 0。

[0.5.1 原生双平台](https://github.com/cloud00726/edittrace/actions/runs/43834854935)成功。[宿主远程结果](https://github.com/cloud00726/edittrace/actions/runs/43834855209)中 Windows 在最后一个预期负例之后失败，Ubuntu 启动器返回 0 但无宿主报告。前者与本地包装器复现相符，后者仍需复验。

## F1 CI 退出码

自测逐项验证运行状态、场景标识、诊断和漏改路径，通过后显式退出 0。消费者 CI 继续传播执行器的原始退出码。两项工作流的 checkout 关闭凭据持久化。

本地包装器检查确认自测遇到预期 2 得到 0、遇到意外结果得到 1；消费者对 2 和 1 原样传播。真实 VS Code 的 Windows 合成自测五种候选依次返回 0、1、0、2、2。

## F2 文本证据

`python scripts/check_provider_evidence.py _build/native/debug/build/cmd/edittrace/edittrace.exe` 验证 11 项，包含旧反例、交换绑定、正常及偏离预期的编辑/同步、旧观察格式、缺失/重复/过期终态。两个旧反例均返回 2，旧 observation v2 得到明确版本错误。冻结 case/suite v1 及旧证据包验证成功。MoonBit native 24 项，干净目录 383 项，Node 扩展 14 项，公共 API 快照和 native/JS 独立消费者均通过。500 个独立会话和 4000 个检查点继续使用原语料。

## F3 宿主生命周期

每次运行使用独立请求编号。宿主入口写就绪标记并原子发布最终结果，等待与启动共用一个截止。Linux 官方归档结构下宿主直接启动桌面二进制，安装仍走 CLI。采用直接启动的做法可与 [Microsoft 的扩展测试启动方式](https://github.com/microsoft/vscode-test/blob/main/lib/runTest.ts)对照。Windows 与 Ubuntu 22.04.5 WSL 的执行器测试各 8 项通过，其中包括启动器先退出后报告到达、缺失和不匹配标记及超时。

续传官方 1.144.0 Linux 归档时，240 秒只增加约 2.4 MB，归档仍不完整。WSL 当前为 root，现有环境缺少 Xvfb。此次没有执行 Linux 的真实 VS Code 宿主，旧 GitHub 故障根因仍未证实。下一次获授权的宿主 CI 应核对 `host_ready`、`process_exit` 和失败阶段，明确报告是否进入扩展测试入口。

## F4 候选归属与实际工具

源码执行器在 Windows VS Code 1.144.0 实测：默认模式候选 1.0.0、1.1.0、1.1.1、1.2.0、1.3.0 分别为 0、1、0、2、2。仅注册全局格式化器的 1.4.0 在默认场景通过，在候选专用 API 场景返回 2；导出专用 API 的 1.0.0 在该场景通过。格式化适配器 2.0.0 实际调用固定 MoonBit `moonfmt`，测试与审核期望相符，返回 0。格式化器文件 SHA-256 为 `5d12e81f5abf46c1163d7701b612a6c18fb4ccd5b69bd4e6336ba6dd52b90068`。这是命令行工具集成实测；官方 MoonBit VS Code 扩展版本对比和独立消费者 GitHub Actions 仍待验证。

## F5 发行候选

Windows 候选从实现提交 `1aeffdd` 的独立干净检出重新编译。两份归档位于 `output/provider-0.5.2-local/`，`SHA256.json` 记录源码全 SHA、输入与制品哈希。

| 归档 | SHA-256 |
|---|---|
| `edittrace-core-0.5.2-win32-x64.zip` | `48ab489c4fcb3b559c25c0202a7da725c4c9a8eadbb48fe6d703124ca5517fc6` |
| `edittrace-0.5.2-win32-x64.vsix` | `3be65408311b3bfc3dadbe6dd146d5744c40b31d80f7cc8f9c94409d0b482de8` |

Windows 发行检查 20 项通过。隔离安装包通过 25 项实际宿主检查。从仓库外解压候选，照快速开始使用随包脚本构造候选，并复跑正确版 `0` 与故障版 `1`。安装前实测 0.5.1 核心和错误哈希各返回 2，正确配置返回 0。

复验入口：

- `python scripts/check_provider_evidence.py <0.5.2-core>`。可用 `--baseline-051` 和旧版核心对照。
- `python -m unittest discover -s scripts -p test_provider_runner.py -v`。Windows 和 Ubuntu 都可运行这一组执行器测试。
- `python scripts/validate.py --clean-room`、`python scripts/check_api.py` 与 `python scripts/validate_stage2.py --legacy-only`。原生构建与校验使用项目固定工具链。
- 解压后按包内 QUICKSTART 运行正确版 1.0.0 和故障版 1.1.0。退出码、工具哈希与逐场景结果保存在候选目录的 `consumer-1.0.0/summary.json` 和 `consumer-1.1.0/summary.json`。

本次完成本地 F0–F5 的可实施范围。Ubuntu 真实宿主与新提交的双平台远程 CI、远程独立消费者及官方 VS Code 扩展的跨版本验证仍待执行。公开 main 仍为 0.5.1，公开 Release 仍为 0.2.0 Preview 1。没有生成 Linux 候选、公开推送、发布或提交赛事材料。用户已有本地申报书保留。

## 0.5.2 上线后的 CI 复查

提交 `1bbbf3f` 的[原生双平台作业](https://github.com/cloud00726/edittrace/actions/runs/44044894513)和[Windows 宿主作业](https://github.com/cloud00726/edittrace/actions/runs/44044894397/job/133908049233)通过。[Ubuntu 宿主作业](https://github.com/cloud00726/edittrace/actions/runs/44044894397/job/133908049616)使用 Ubuntu 26.04，原生证据反例通过。随后三个正确版场景都在宿主就绪前退出，启动进程返回 `-5`，筛选提示为 `electron_sandbox`。这些证据把故障定位到 Electron 沙箱初始化，公开日志未保留完整 Electron 错误。

下一次宿主 CI 在 Ubuntu 启用 AppArmor 用户命名空间限制时，为解压后的固定 VS Code 可执行文件加载只允许 `userns` 的路径规则。该方式参考 [Ubuntu 的 AppArmor 用户命名空间指南](https://documentation.ubuntu.com/release-notes/24.04/#unprivileged-user-namespace-restrictions)。规则仅用于 CI，保留系统范围限制和 Electron 沙箱设置。仍须运行完整宿主作业，才能确认此规则消除了 GitHub 上的故障。
