# 第二阶段维护升级交付回执

验证日期：2026-10-29（Asia/Shanghai）。从基线 `5ed61ab` 执行任务书 S0–S7，保留原任务文件及既有历史。产品版本 0.4.0，全部授权范围内的本地实现、测试、文档、候选和提交已完成；S6 的真实 MoonBit 提供者与注册表消费受外部条件限制。

交付收尾日期：2026-10-30；此日期仅表示回执归档，不将 10 月 29 日的实测改写为重新运行。

## 阶段结果

| 阶段 | 状态及实际结果 | 证据 |
|---|---|---|
| S0 | 完成。基线实际验收 353；核实远程 main 为 5ed61ab，0.3.0 的 Windows/Ubuntu CI 成功，公开 Release 为 0.2.0 Preview 1。冻结分享/缩减契约 | STAGE2_PROGRESS.md、STAGE2_SPEC.md；旧 CI 40283672011 |
| S1 | 完成。实际复现旧 0.2 包被拒绝，修复为 schema/策略/完整语义及规范版本家族检查；真实 0.1/0.2/0.3 二进制生成的旧包全部通过 | stage2-legacy-validation.json，包含真实旧归档哈希与修复前/后结果 |
| S2 | 完成。只读、确定的分享清单，说明数量/字节/风险，不输出源码正文或原身份；未知字段拒绝 | `share plan`；stage2-validation.json |
| S3 | 完成。MoonBit 结构化身份映射，源码文字保留、多文档支持、重读复核；篡改 trace/finding/manifest/receipt 均拒绝 | `share export`、`evidence verify`；30 项独立 CLI 验收、安装包演练 |
| S4 | 完成。单文档 ET009，完整 finding 谓词，锁定生命周期/检查点，保留物理空行；次数及总工作量预算 | `minimize`；可缩减/不变/预算 1/关闭重开/多文档及错误路径检查 |
| S5 | 完成。六类完整基准，每类预热 1 次/测量 5 次，真实核心子进程 PeakWorkingSetSize；最终干净构建另有 2 类快速复核 | stage2-benchmark.json、output/stage2-final-quick-20261029/benchmark.json |
| S6 | 本地部分完成，外部受限。新纯核心 share API 的 native/JS 独立消费者通过；签名、命名迁移及发布检查清单就绪。Mooncakes 未登录；隔离宿主无 MoonBit 扩展、无真实 MoonBit 格式化编辑 | consumer-validation.json、host-validation.json、API.md；注册表消费脚本未对远程执行 |
| S7 | 本地交付完成。文档、许可、AI 与来源说明同步；干净源码候选、ZIP/VSIX、CRC/哈希/独立目录及隔离安装验证通过 | distribution-validation.json（20）、host-validation.json（packaged，25）、stage2-result.json |

## 实际验证

- `python scripts/validate.py --clean-room`：383 通过，原独立参考 500 会话/4000 检查点保持不变；native 单元 23。
- `python scripts/validate_stage2.py`：30 通过，已接入完整验收和双平台 CI。最后新增上限、非法 UTF-8、控制字符 URI 和不支持目标规则检查。
- `node --test extensions/vscode/test/unit.cjs`：14 通过。受限环境的临时目录链接/重命名曾失败，按原测试获准运行后通过；未削弱断言。
- `python scripts/check_api.py`：签名一致；`python scripts/validate_consumer.py`：native/JS 均实际调用 share，通过。CI 支持脚本 6 项通过。
- `python scripts/validate_distribution.py --directory output/stage2-0.4.0-20261029-final --install-vsix`：20 通过，解压路径含空格；实际分享/缩减/复核和 VSIX 隔离安装均通过。
- `python scripts/run_host_tests.py --extension-path <distribution-validation.json 中的 installed_extension>`：VS Code 1.143.1，packaged 模式 25 通过，使用已安装 VSIX 自带核心。
- `python scripts/benchmark.py --out output/stage2-benchmark-20261029`：六场景零失败；`--quick --out output/stage2-final-quick-20261029`：最终干净构建两场景零失败。各报告保存原始样本、输入/二进制哈希、机器和工具链。

宿主新增验证覆盖命令注册、实际 core transport 分享预览和预取消；通用 transport 已验证超时/失败/取消。文件选择、人类风险确认对话框没有自动点击，未声称完整真人交互验收。未邀请真人或宣称需求规模。

完整六场景基准为开发过程中的 dirty 构建，原始报告如实保留；最终快速报告来自干净提交 9627341。两组二进制哈希不同，不能混合推导性能提升。未实施或宣称性能优化；1 MiB/1000 批量编辑场景中位数约 13.67 秒，保留为后续剖析依据。

## 可复制操作

发行 ZIP 解压后执行，Windows 用 `.\edittrace.exe` 替换下列 `edittrace`。源码运行时样例路径为 `examples/real-world/stage2-checkpoint.jsonl`。样例明确标为 synthetic。

```
edittrace share plan examples/stage2-checkpoint.jsonl --finding ET009_CHECKPOINT_MISMATCH:4:-1:0
edittrace share export examples/stage2-checkpoint.jsonl --finding ET009_CHECKPOINT_MISMATCH:4:-1:0 --out shared-evidence
edittrace evidence verify shared-evidence
edittrace minimize examples/stage2-checkpoint.jsonl --finding ET009_CHECKPOINT_MISMATCH:4:-1:0 --max-runs 1 --out budget-limited-evidence
edittrace evidence verify budget-limited-evidence
edittrace share plan examples/stage2-checkpoint.jsonl --finding missing
edittrace minimize examples/stage2-checkpoint.jsonl --finding ET009_CHECKPOINT_MISMATCH:4:-1:0 --max-runs 0 --out rejected-evidence
```

前五条成功返回 0；预算为 1 的样例最后一个验证候选有 `budget_exhausted:true`。后两条预期返回 2，不创建有效分享/缩减包。重复使用已有输出目录也返回 2。底层 `audit` 对该故障仍返回 1。

分享保留源码正文及其中可能的秘密/路径，只变换受支持的结构化身份；默认不附原映射。8 MiB/2048 行，缩减默认 32/上限 64 次候选重放，并有 128 MiB-equivalent 工作量上限。manifest 最多 32 MiB，重复 trace 内容用于自一致性核对，不是签名或内容安全证明。取消或写失败可能留下不完整目录，不应当作已验证包。缩减不承诺全局最小。

## 候选与来源

以下均为本地候选，源提交 `9627341177086c1ef7b67a30d0fc3f5ecf7b4afe`，打包时工作区干净。后续边界验收脚本及回执不改变产品输入；已逐项重算归档来源清单中的全部产品输入哈希，均相同。

| 文件（相对于仓库根） | SHA256 |
|---|---|
| output/stage2-0.4.0-20261029-final/edittrace-core-0.4.0-win32-x64.zip | 2bce2ea5dc59ba2348073ed2154b2110f871fee2a5a307828673a3cf5c0d321e |
| output/stage2-0.4.0-20261029-final/edittrace-0.4.0-win32-x64.vsix | 7af1ddd460416d75f9edd2b759912d7e6d160346b46ddef6b00fb4af307bdbe3 |
| output/stage2-source-0.4.0-20261029-final/local-edittrace-0.4.0.zip | 9560fa040ae9a3af0706d1b397be17152903b8d0f3b433a731ded414c1b96425 |

源码 ZIP 64 个文件，CRC 通过，明确清单包含许可证/声明，不含凭据、工具链、主机私有结果或历史 output/artifacts；模块仍为 local/edittrace，不假定账户 namespace。SHA256.json、source-manifest.json 记录来源及文件清单。output 属于忽略目录，不随 Git 自动上传，须单独保存这些本地候选。

本轮功能提交：db86e79（基线/契约）、f5253bb（兼容）、20fa8ef（核心/CLI/验收）、3fa567b（扩展/宿主）、9627341（性能/文档/候选准备）。最后的边界验收与交付回执另作本地提交，不改二进制来源。

## 剩余事项与公开边界

1. 有可用 MoonBit 提供者后，在隔离工程采集真实格式化/重命名，保留提供者、工具链、原文和实际编辑；本轮未为日常环境安装插件。
2. 维护者登录 Mooncakes、确认 namespace 归属并明确授权后，再整体迁移模块名、发布；之后用仓库外固定版本消费者验证。源码候选不等于注册表包。
3. 0.4.0 未获本轮公开推送授权，未运行新 SHA 的 Windows/Ubuntu 远程 CI，也未生成 Linux 候选。CI 已保留双平台执行入口；旧 0.3.0 CI 结果不能冒充本轮结果。
4. 未执行 GitHub Release、Marketplace、赛事提交或联系他人。真人风险确认与首次使用体验、第三方持续采用仍需真实参与，不能由自动检查补造。

机器可读状态、哈希和验证来源见 stage2-result.json；后续从上述真实缺口继续，无需重新从 S0 开发。
