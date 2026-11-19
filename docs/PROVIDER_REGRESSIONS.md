# 执行待测版本的回归场景

EditTrace 0.5.2 候选提供独立 VS Code 执行器。它在隔离工程中安装指定 VSIX，执行格式化、跨文件纯文本重命名，或运行候选插件的编辑器同步命令。它读取宿主实际文本，交给 MoonBit 与已审核预期比较。既有 case 和 suite 继续用于冻结输入的重放。

## 使用

准备可信 VSIX、其预先核实的 SHA-256、固定版本的 VS Code 和 0.5.2 原生核心。发行 ZIP 中的脚本位于 `provider-runner/scripts/`，源码仓库中位于 `scripts/`。以下命令使用发行版目录。Linux CI 使用 Xvfb，Ubuntu 宿主验证状态见仓库的 `docs/competition/PROVIDER_052_EXECUTION.md`。

```text
python provider-runner/scripts/run_provider_regression.py suite.json --candidate candidate.vsix --sha256 <digest> --core <edittrace-executable> --host 1.144.0 --code <code-launcher> --out <new-directory>
```

工作流应直接使用进程退出码。0 表示场景通过，1 表示结果与已审核预期不同，2 表示运行或证据不完整。1 和 2 都应阻断门禁。只上传 `summary.json` 和 `junit.xml`。输出目录还包含临时工程副本、候选副本、宿主配置和本地诊断日志。

在同一命令中增加 `--check-input` 可先验证场景、VSIX 哈希、核心能力和启动器版本。该模式不安装候选。实际验证使用单独的新输出目录。场景 v1/v2、宿主报告协议 3 和核心 observation v3 继续使用。对于同步场景，0.5.3 执行器还要求 `doctor --format json` 返回 `provider_sync_scope_guard: true`。0.5.2 核心缺少该能力，返回 2 并提示升级。格式化及重命名场景仍可使用支持 observation v3 的核心。旧冻结 case、suite 和证据包继续独立运行。

`--check-input` 也核对随附 Moonfmt 和 TypeScript 示例的固定外部依赖摘要。用户插件的其他运行依赖由消费方安装和锁定，实际宿主验证仍必须运行。

从小工程整理草稿时，准备两个目录 `before/`、`after/`，各放审核范围内的同名文件。`after/` 由维护者核对预期行为，适合同时包含必须改动的文件和保护文件。先用 `git diff --no-index before after` 检查每处变更。`scenario.json` 示例为 `{"name":"format-demo","language":"typescript","operation":{"kind":"format","path":"main.ts"}}`。

```text
python scripts/draft_provider_suite.py --before before --after after --file main.ts --file untouched.ts --provider publisher.extension --scenario scenario.json --out review.draft.json
```

若使用候选直接 API，增加 `--candidate-api`。草稿保留原有换行及 UTF-8 内容，已有路径会被拒绝覆盖。复核后另存为 `suite.json`，把 `kind` 改成 `provider_suite`，替换 `review.source` 为实际审核依据，再用 `--check-input` 预检。把审核 suite 纳入版本控制，把执行结果写入另一个目录。

同步窗口始于显示审核目标前，止于候选命令返回。允许打开背景文档。此期间对未声明文本缓冲区或 `before` 与 `after` 相同文件的有效文本修改，即使随后撤销，也按行为偏差返回 1。报告给出首次捕获序号，已声明文件另有相对路径。错误方向、丢失基线、无效重放或缺少终态按证据不完整返回 2。观察范围是该宿主捕获的编辑事件和隔离工作区最终磁盘状态，覆盖不了命令返回后的活动、外部文件系统写入或服务端内存。

摘要中的 `stage` 和 `reason` 用于区分失败阶段。启动器异常带退出状态和已识别的错误提示类别。宿主就绪后还会区分提供者未返回可观察编辑、请求超时和核心判定不完整。已完成的场景记录安装时间和宿主进程耗时，后者包括启动、执行和判定。详细本地日志可能含路径或源码，CI 只上传上述两个报告。

宿主入口写入与请求编号绑定的就绪标记，报告写完后原子发布。启动器退出后，从启动计时的同一截止时间内仍可收到报告。缺少标记时报告 `host_not_ready`，已就绪却缺少报告时报告 `missing_host_report`。错配标记、半截报告和不完整证据均阻断。

## 编写和审核场景

参考源码中的 `examples/provider-consumer/suite.json`。v1 使用内联工程快照。每个文件声明相对路径、操作前文本和操作后文本。用相同的前后文本断言文件保持不变。对有工具配置文件的工程也需要声明这些文件。重命名位置采用零基 UTF-16 坐标。同步场景的候选命令应等待编辑完成后返回，执行器录制编辑器事件和独立宿主快照。以版本控制评审固定期望，记录期望来源。报告提供整份场景文件哈希，覆盖其中的输入及期望。运行器没有更新基线的命令。

格式化和重命名验证使用 VS Code 稳定 API 的纯文本投影。预检与实际文本比较覆盖返回的编辑，另外对所有声明文件独立比较预期与实际。工作区磁盘变化会导致失败。当前支持单个自包含 VSIX、候选声明的语言及本地工程，要求该语言在隔离环境只有一个适用提供者。编辑器内建提供者争用、依赖扩展、无可观测编辑、需要读写磁盘的场景及资源操作需要单独的适配和验收。同步结果只涵盖编辑器侧动作和快照。

VSIX 会执行代码。只对可信候选运行，CI 为候选使用独立、低权限且无发布凭据的任务。

## 指定候选接口

默认场景 v1 的报告将 `invocation` 标为 `host_observation`，表示调用 VS Code 通用提供者或命令接口并核对宿主结果。候选扩展已激活，但通用接口可能经由另一个提供者。

场景 v2 增加 `"invocation": "candidate_api_v1"`。候选扩展在 `activate()` 的返回对象中提供 `edittraceProviderV1.format(document, options)` 或 `edittraceProviderV1.rename(document, position, newName)`。它们可异步返回标准 VS Code `TextEdit[]` 或 `WorkspaceEdit`。执行器从已核对身份的扩展实例取得这个接口。缺失时退出 2。v2 目前只支持格式化和文本重命名。它证明调用进入该候选的接口，扩展内部的依赖仍由其适配器验证。

`examples/provider-consumer/moonfmt-suite.json` 演示一个调用真实 MoonBit 格式化器的本地适配器。构建示例时使用 `--moonfmt <formatter-path>` 将工具 SHA-256 写入 2.0.0 示例 VSIX。运行时提供绝对路径 `EDITTRACE_MOONFMT_EXE`，适配器重新验证哈希并将输入经 stdin 交给格式化器。
