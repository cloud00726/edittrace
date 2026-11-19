# EditTrace 六项验收升级记录

## U0 基线

- 起点 `88b7f7ae8f395815417d0ec4b56efa20ef3cad2f`，本地 `HEAD` 与 `origin/main` 一致。该提交的公开 [宿主 CI](https://github.com/cloud00726/edittrace/actions/runs/44046938764) 和 [原生 CI](https://github.com/cloud00726/edittrace/actions/runs/44046938725) 均覆盖 Windows、Ubuntu。它们是 0.5.2 历史证据。发行页上的公开下载为 [0.2.0 Preview 1](https://github.com/cloud00726/edittrace/releases/tag/v0.2.0-preview.1)。
- 0.5.2 本地 Windows 候选的编译源为 `1aeffdd1ce49c5d358bcae8fb33403cbc7318c7a`。重新计算的 ZIP SHA-256 为 `48ab489c4fcb3b559c25c0202a7da725c4c9a8eadbb48fe6d703124ca5517fc6`，VSIX 为 `3be65408311b3bfc3dadbe6dd146d5744c40b31d80f7cc8f9c94409d0b482de8`。基线工具为 moon `0.1.20261012`、MoonBit `0.10.15+943464bfa`、Python `3.11.5`、VS Code `1.144.0`。
- 工作区原有任务书和本地申报稿。申报稿的 SHA-256 为 `4eb223c5f011303a04df3e170585f5b2c7a39067da66d6992a54ec46fd5e117d`。参考语料基线 Git tree 为 `tests/oracle` 的 `fb08920333dc57dfe703bc895d0258ae9ac3b044`，`core/session/oracle_wbtest.mbt` 的 SHA-256 为 `439615c6867f6b418fe4d3084f2b5d49d436bd1f757cc9c334e6609d8fd87791`。
- 从已核验的 0.5.2 ZIP 解压原始 CLI，运行 `python scripts/check_provider_evidence.py <0.5.2-exe> --baseline-052`。额外文件、未保存文档、额外文档后撤销及审核不变文件后撤销均返回 0。只读打开也返回 0。错误方向返回 1，缺失观察、缺失打开和格式错误为 2。

| 2026 年 11 月提交 | 实质变化 | 复验 |
|---|---|---|
| `a724ff0`（11 月 13 日） | 实际安装并运行待测 VSIX，审核格式化、多文件文本重命名与客户端同步 | 使用当前 `examples/provider-consumer/suite.json`，运行文档中的候选门禁命令 |
| `2d1a7b8`（11 月 13 日） | 强化文件身份和宿主分阶段诊断，拒绝无解释变更 | `python scripts/check_provider_evidence.py <0.5.1-exe> --baseline-051`，再用本地新核心执行全量检查 |
| `1aeffdd`（11 月 17 日） | 候选直接 API、终态检查点、宿主报告关联和启动诊断 | `python -m unittest discover -s scripts -p test_provider_runner.py` 与候选 API 示例 |
| `88b7f7a`（11 月 17 日） | Ubuntu 为精确 VS Code 路径启用 Electron 用户命名空间，恢复宿主矩阵 | [该提交的宿主 run](https://github.com/cloud00726/edittrace/actions/runs/44046938764) |

这些日期来自 Git。赛事计入范围、类别和补交资格仍由组委会确认。

## U1 同步范围修复

0.5.3 的 MoonBit 判定检测未声明文本缓冲区和审核不变文件的写入事件，报告首次序号，确认后返回 1。允许只读打开，身份或重放证据缺失返回 2。观察格式仍为 v3，同步执行器额外检查 `provider_sync_scope_guard`，实测与原 0.5.2 核心配对时预检返回 2。普通离线入口沿用原规则。

Windows VS Code 1.144.0 的五个同步宿主场景分别返回 `0,1,1,1,1`，每个回归均有 `seq=8`，`frozen-undo` 同时报出 `frozen.etrf`。原生 MoonBit 24 项和证据 CLI 20 项通过。命令为 `moon test --target native`、`python scripts/check_provider_evidence.py <core>`，以及按 [候选门禁](PROVIDER_REGRESSIONS.md) 对 `examples/provider-consumer/sync-scope-suite.json` 运行 `versioned-provider-1.0.0.vsix`。新用例已接入宿主矩阵。

## U2 真实消费者

在仓库外含空格的临时目录中，通过实际 VS Code 1.144.0 宿主运行 [TypeScript 适配器](../examples/provider-consumer/README.md)。官方 npm 包的 `dist.integrity` 与下载内容逐一匹配，适配器启动时核对 runtime SHA-256 及 `ts.version`。同一个基线 SHA-256 `e0bea6ff52cdfba0811026cb991949f67dcf5c0226549c2de46a84d0a12e0c25` 用于以下结果。

| 工具与适配器 | 退出 | 观察 |
|---|---:|---|
| TypeScript 5.6.3，完整 | 0 | 定义、导入和引用均修改，保护文件保持原文 |
| TypeScript 5.7.3，合成遗漏 | 1 | `client.ts` 缺少编辑，首个差异 UTF-16 偏移 `9` |
| TypeScript 5.7.3，完整 | 0 | 同一审核基线恢复通过 |

生成草稿的命令独立于运行门禁。实测从解压包起草三文件 TypeScript 场景，完整保留 CRLF、LF 与 emoji，重复对同一目标运行返回 2。草稿默认不能运行，人工改为正式 suite 后可通过结构验证。消费方模板在 GitHub push、PR 或手动执行时传播原始退出码。公开独立消费方运行、外部维护者试用及上游历史缺陷待另取证。

## U3 干净构建与可运行候选

两平台制品与源码候选使用干净提交 `93951db3cda68f28d1f030016b6ed18cadebed78`、MoonBit `0.10.15+943464bfa`、moon `0.1.20261012` 和 async `0.22.5`。Windows 使用本机 VS Code 1.144.0。Ubuntu 22.04.5 使用 WSLg 中以非 root 运行的微软 VS Code 1.144.0，安装了隔离目录内的必需共享库。Electron 沙箱保持启用。

| 层级 | Windows | Ubuntu WSLg |
|---|---:|---:|
| `python scripts/validate.py --clean-room` | 383 | 383 |
| MoonBit native 测试 | 24 | 24 |
| `check_provider_evidence.py` | 20 | 20 |
| Python 执行器与 CI 支持测试 | 16 | 16 |
| Node 扩展传输测试 | 14 | 14 |
| 独立 MoonBit 工作区消费者 | native、JS | native、JS |
| 独立解压、安装、核心执行与归档校验 | 28 | 30 |
| 安装后核心与实际 VS Code 扩展集成 | 25 | 25 |
| 解压包内执行器与独立工程场景 | 32 | 32 |

首次完整验证暴露了测试中固定的 0.5.2 版本断言，已改为比对模块声明。Ubuntu 初始环境缺少图形宿主归档、四个依赖包和 Python 3.11，随后核验官方归档与 Ubuntu 索引摘要，解压到本机隔离目录。首次 Linux 打包检查还找到了 ELF 调试段里的绝对构建路径。移除调试段后，安装运行暴露 ZIP 条目的执行位丢失。最终包恢复 Unix 可执行模式，并通过安装后实际执行 `--version` 和宿主复验。

复验入口见[验证矩阵](VALIDATION.md)。双平台从最终 ZIP 分别运行 16 份门禁报告，覆盖 32 次场景或预检。真实 TypeScript 的完整、合成漏改、恢复结果均为 `0/1/0`。独立调用的官方 `moonfmt` 示例均为 0。错误摘要、缺失工具、缺少候选 API 和候选超时均为 2。

候选报告含安装、宿主就绪、候选响应、核心判定和总宿主耗时。首次从本地已下载素材执行三场景，与复用同一 VSIX 的第二轮对照，两轮都使用新配置和新工作区。总宿主耗时中位数 Windows 为 6.547 秒与 5.047 秒，Ubuntu WSLg 为 4.097 秒与 3.375 秒。单轮对照未隔离 OS 缓存、进程状态或同机负载影响。

构建产物位于工作区 `output/acceptance-0.5.3/{windows,linux,source}`。Windows 与 Linux 目录各含 `SHA256.json`、归档、检测和宿主回执。源码目录含 `source-manifest.json`。版本、摘要、结果和测量汇总见[机器可读回执](acceptance-053-validation.json)。公开 Actions 的通过结果仍指向 0.5.2 的 `88b7f7a`。

## U4 许可证、来源和文件清单

[来源说明](../THIRD_PARTY_NOTICES.md)记录了 VS Code、Moonfmt、TypeScript、AppArmor 策略和样例的来源。源包使用已跟踪文件和显式文档清单。原生归档和 VSIX 使用显式资源清单。最终检查核对 CRC、各自 SHA-256、归档路径、包之间的实际核心字节、MIT 与依赖许可及 NOTICE。已按已知本机构建路径和常见凭据标记检查最终归档。原始参考树、源示例和申报稿哈希与起点一致。源码候选使用 `local/edittrace`，账号、公开命名空间、Mooncakes 发布和外部安装仍待核实。

## U5 验收索引与人工演练

README 给出下载、源码构建、接入候选插件三个入口。[六项验收索引](competition/ACCEPTANCE_INDEX.md)串联工程证据和独立验证边界，[维护者演练](competition/MAINTAINER_REHEARSAL.md)提供可直接执行的步骤，[AI 记录](AI_USAGE.md)说明本轮实际使用及责任分配。人工演练、参赛者亲自审阅、官方活动资格和外部维护者使用记录仍需由实际参与者或组委会确认。现有申报稿保留在本地。
