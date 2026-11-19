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

生成草稿的命令独立于运行门禁。测试复核草稿保留 CRLF 和 emoji、默认不能运行，人工改为正式 suite 后可通过结构验证。消费方模板在 GitHub push、PR 或手动执行时传播原始退出码。公开独立消费方运行、外部维护者试用及上游历史缺陷待另取证。
