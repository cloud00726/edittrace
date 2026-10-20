# EditTrace 本轮整改结果

日期：2026-10-20。本地产物已实现并验证；没有推送、公开发布、联系外部人员或重新提交赛事材料。未保证审核接受。

后续发布前审查已完成，当前结果见 [PRE_RELEASE_REVIEW](../PRE_RELEASE_REVIEW.md)：核心/扩展统一为 0.2.0，完整验收更新为 337 项（工作流 80 项），真实宿主演练更新为 14 项。下文保留首次本地整改完成时的版本和计数；公开发布状态以 GitHub Releases 及后续发布记录为准，不能将旧候选包当作最新版本。

## 已实现

1. 真实 JSON tracer 入口：`import --from vscode-json` 自动生成内部会话，保留消息方向、来源行和初始化编码证据。已导入 13 条真实 Microsoft JSON 服务器通信；不补造服务器文本检查点。
2. 日常变更预检：同基线 TextEdit、纯文本 WorkspaceEdit 子集，检查版本、范围和冲突，计算结果并与独立 actual 比较。真实 JSON 格式化与跨文件 TypeScript 重命名通过宿主对照。
3. VS Code 接入：六个用户命令覆盖录制/停止、格式化/重命名预览、首文件差异和回归草稿保存。VSIX 自带核心，预览不改写工程；核心规则仍为 MoonBit。
4. 持续回归：显式文本/步骤/finding/禁止规则及完整性断言，自包含 case/suite、独占封装和迁移复跑。成功复现故障与修复正确性断言分开，未知期望字段明确拒绝。
5. 复用和交接：带类型 Edit、Position、FindingExpectation；独立消费者 module 和 CI 示例；同步证据包可按文档筛选并保持物理行与完整 finding，verify 检查筛选作用域。
6. 本地交付：Windows x64 CLI ZIP、平台 VSIX、SHA256 清单、依赖许可证、快速体验、三类实采与明确标注的故障注入、试用表、工作流对照及新申报草稿。

## 实际验证

| 检查 | 本轮结果 | 证据 |
|---|---|---|
| 完整验收、干净目录构建及新工作流 | 329 项断言通过；其中新增工作流 72 项 | ../validation-results.json、../remediation-validation.json |
| MoonBit native 测试 | 19 项通过；原独立语料 500 会话/4000 检查点保持 | artifacts/moon-test.log、tests/oracle/manifest.json |
| 真实 VS Code 1.138.0 宿主 | 11 项通过，最终针对已安装平台 VSIX；用户预览调用自带核心 | ../host-validation.json |
| Node 传输与捕获顺序回归 | 5 项通过；其中一项为实采事件驱动的模拟宿主回归，不计作真实宿主测试 | extensions/vscode/test/unit.cjs |
| 独立消费者 | 单独 module 编译、运行并验证类型接口成功 | ../consumer-validation.json |
| Windows 发行包 | 11 项通过：校验和、解压运行、当前构建一致、真实隔离安装等 | ../distribution-validation.json |
| 工具链/CI 支持回归 | 6 项通过 | scripts/test_ci_support.py |

计数属于不同层级，不能简单相加当作独立覆盖规模。宿主实采见 examples/real-world/capture-evidence.json，最后的平台 VSIX 宿主复核另记 host-validation.json。实际 ZIP 解压和两条命令耗时已记录，但不含下载、安装 UI 或真人操作，不能据此声称五分钟接入目标已达成。

## 本地运行与产物

源码构建的 CLI：`_build/native/debug/build/cmd/edittrace/edittrace.exe`。

最终本地候选目录：`output/release-20261020/`：
- `edittrace-core-0.1.0-win32-x64.zip`
- `edittrace-0.2.0-win32-x64.vsix`
- `SHA256.json`

保留 core/report/bundle 0.1.0 兼容，扩展独立版本 0.2.0；均为本地未发布候选。当前档案哈希以目录中 SHA256.json 和 distribution-validation.json 为准。

快速运行：

```
edittrace check-edits examples/real-world/format.plan.json
edittrace check-edits examples/real-world/rename.plan.json
edittrace suite run examples/real-world/suite.json
edittrace case run examples/real-world/injected-lost-event.case.json
```

最后一条应退出 1，表明人为删去事件后无法通过独立文本断言。ZIP 内对应样例路径为 `examples/`。详见 QUICKSTART.md。

## 本轮经验

追加真实宿主边界检查捕获了同位置插入的错误：对宿主已排序数组再次排序导致 XY 变为 YX。已保留宿主原顺序，增加实采与模拟宿主回归。还修复了错误提示阻塞调用、测试启动器提前返回 0、宿主配置干扰编译扫描等问题。详见 RETROSPECTIVE.md。

## 四项反馈的解决程度与剩余工作

- 接入成本：已有真实输入入口、编辑器采集及带核心发行物，本地链路已验证；普通用户独立接入成本仍待试用。
- 场景狭窄：已增加格式化和跨文件文本重命名，三类场景有实际输入与结果；需求规模、使用频率和持续使用不能由代码证明。
- 差异化：已有自动预检、独立实际文本比较、回归交付闭环；没有做全面竞品测试或宣称性能优胜。
- 独立复用：独立模块和迁移用例已运行；外部维护者采用、注册表安装和远程消费者 CI 尚无证据。

新 Windows/Linux CI 已配置，尚未远程执行；Linux 新发行、真人试用、Mooncakes 发布、参赛者人工定稿、现行章程核实和正式送审均保留待办。官网动态页和飞书本轮读取未取得可复核正文，没有猜测截止日期。未实现后置的自动最小复现、更多编辑器和完整 WorkspaceEdit 资源操作。

下一步以 USER_TRIAL.md 收集真实维护者任务和反馈，再根据 FEEDBACK_MATRIX.md 补足证据；新的申报材料为 APPLICATION_REMEDIATED.md，演示为 DEMO_REMEDIATED.md。
