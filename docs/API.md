# MoonBit 公共 API 与兼容性

当前源码模块 `local/edittrace`，版本 0.4.0。此命名空间不表示已经发布到 Mooncakes。工作区消费者见 examples/consumer；注册表消费者使用实际拥有且已发布的模块名。

新增纯计算包 `core/evidence`：`replay(lines)`、`target(report,id)`、`share(lines,id)` 与 `minimize(lines,id,max_runs)`；均显式失败，不读取 URI 文件或执行脚本。share 返回转换行与无原身份的预览，minimize 返回保留物理行的候选及预算统计。上限和目标保持条件见 STAGE2_SPEC.md。独立消费者会实际调用 share；native/JS 验证分别记录。

| 包 | 公共入口 | 边界 |
|---|---|---|
| `core/text` | `Position` 与文本坐标操作 | UTF-16，保留换行；非法代理对边界明确拒绝 |
| `core/edit_plan` | `Edit`、`Baseline`、`apply`、`evaluate`、`check` | 同基线批量编辑；`evaluate` 返回 `Applied(text)` 或 `Rejected(reason)` |
| `core/case` | `FindingExpectation`、`matches_finding`、`run`、`safe_run`、`suite` | v1 自包含输入和显式期望；不是文件发现器 |
| `core/session` | `Session` 与 feed/report/snapshot | 顺序同步语义，不读取 URI 所指文件 |
| `core/report` | `summary`、`with_summary`、`junit`、`doctor` | `junit` 接受 suite_report；摘要和 CI 输出不重算文本 |

`evaluate` 是对既有 raising `apply` 的新增类型化入口，现有 Json API 保留。拒绝原因用于诊断，不承诺可按文本解析稳定错误码。消费示例执行 UTF-16 emoji 替换及类型化结果检查；本轮已实际运行 native 和 JS 独立工作区消费者，不据此声称整个 native CLI 能运行在 JS/wasm。

公共签名由 `moon info` 生成到 pkg.generated.mbti，CI 检查生成后是否出现未提交差异。更改公共能力时同步提交源码、生成签名、使用示例与迁移说明。

## 从 0.2.0 迁移

- 原有 JSONL、case/suite v1 和 `apply` 保持可用；新接口为增加能力。
- CLI JSON 报告增加 `display_summary`，调用者应忽略未使用的报告字段；产品输入仍按原严格契约验证。
- 工作流 text 输出改为摘要，不含完整 source_report；机器消费者使用 `--format json`。
- 扩展 0.3.0 需要支持 doctor、summary、bridge protocol 1 的核心，旧 0.2.0 核心不兼容这些新命令。允许版本不同但能力契约兼容的核心；不以字符串全等判断。
- 扩展草稿审核保存在旁文件，原 case v1 可独立运行。确认仅绑定内容哈希，不是签名、正确性证明或身份认证。

## 注册表准备

1. 核实实际账户拥有的 namespace；统一模块路径、导入和生成接口，不能只改元数据名称。
2. 执行全部检查并审阅 `python scripts/package_source.py --out <new-directory>` 的候选与文件清单；不要直接发布包含历史证据的未审阅根目录包。
3. 经授权发布后，运行 `python scripts/validate_registry_consumer.py --module <verified-owner/module> --version <published-version>`。脚本在仓库外新建工程，没有 moon.work 或本地路径替代。

本轮未执行注册表发布和注册表消费，脚本可执行不等于远程验证已通过。
