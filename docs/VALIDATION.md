# 验证证据与复现方式

## 维护候选（2026-10-25）

当前本地 0.3.0：完整验收新增 JUnit/doctor 检查，见 maintenance-validation.json；本轮阶段与外部缺口见 MAINTENANCE_PROGRESS.md。消费者报告分别记录 native 与 JS，仅覆盖纯计算调用。宿主报告记录本次实际版本及 source/packaged，不能与 0.2.0 发布证据混同。

新增验证入口：`python scripts/validate_maintenance.py`（含独立 XML 解析）、`python scripts/check_api.py`（公共接口快照）、`python scripts/package_source.py --out <new-directory>`（显式允许清单的源码候选）。注册表验证入口为 validate_registry_consumer.py，未实际发布时不得标记成功。以下更早日期为历史结果。

## 本轮整改（2026-10-20）

最新完整验收结果以 validation-results.json 为准，新增检查明细见 remediation-validation.json；独立模块见 consumer-validation.json；本地 ZIP/VSIX 见 distribution-validation.json。实采摘要及原报告 SHA256 见 ../examples/real-world/capture-evidence.json；最终已安装 VSIX 的实际宿主复核见 host-validation.json。Node 传输测试与真实宿主检查单独执行，不混入需求验证或性能宣传。以下旧日期记录保留历史。

执行：`python scripts/validate.py --clean-room`、`python scripts/validate_consumer.py`、`node --test extensions/vscode/test/unit.cjs`。有 VS Code 时另运行 `python scripts/run_host_tests.py`，成功后才可 `python scripts/snapshot_host_examples.py`。

发行验证：`python scripts/package_release.py --out <new-directory>`，再 `python scripts/validate_distribution.py --directory <directory> --install-vsix`。安装发生于本仓库隔离配置，不修改日常扩展或发布 Marketplace。

## 当前复核结果（2026-10-17）

- `moon fmt --check`、native check/test/build 全部成功，17 个 MoonBit 测试通过，固定语料仍为 500 会话 / 4000 检查点。
- `python scripts/validate.py --clean-room`：256 项实际断言通过，包含干净目录构建；`python -m unittest discover -s scripts -p test_ci_support.py -v`：6 项通过。
- 新增回归覆盖最大合法序号后的坏输入、各子命令帮助、终端文档状态/控制字符、复现包独立校验及包内文件不一致、未知前缀、元数据限额、输出文件、摘录隐藏及参数重复。
- 下载支持测试模拟连接中断与错误归档，验证临时文件清理、损坏项目缓存恢复及有效缓存重用，不声称本次重新下载了真实工具链。
- 已核对基线 `79cde2a` 的 [Windows/Linux CI 运行 38738218872](https://github.com/cloud00726/edittrace/actions/runs/38738218872) 成功。下文两次失败是修复前的历史记录；本次改动结果以其对应提交的 Actions 为准。
- 当前报名因申报书格式被驳回，尚未重新提交；未发布 Mooncakes 包。

机器可读结果位于 [validation-results.json](validation-results.json)。它由 scripts/validate.py 在所有断言通过后写入，包含实际命令结果、平台、固定工具链版本、参考数据清单和基准耗时。失败时写 artifacts/validation-failure.json，不把失败结果标为通过。

本地执行：

```powershell
python scripts/validate.py --clean-room
```

脚本自动寻找 MOON_HOME、项目 .tooling/moon 或上级 tooling/moon。默认执行 moon fmt --check、moon check --target native、moon test --target native、moon build --target native，然后检查 CLI。--skip-build 仅供已编译开发阶段，不能代替完整验收。

## 核心测试

17 个 MoonBit 测试，其中一个测试遍历独立生成的 500 组会话，验证 4000 个逐步检查点。其余覆盖手算 Unicode、空文本、换行、CRLF 拼接、代理对边界、版本、原子回滚、未知恢复、世代重开、资源限制、数值验证、JSON 深度与稳定序列化。

CLI 验收覆盖全部 8 类演示、0/1/2 退出码、14 条规则、warning 阈值、note 豁免、错误类型/JSON/UTF-8/深度、各可调资源上限、BOM/CRLF、文件路径空格、输出拒绝覆盖、结果确定性及复现包异地重放。独立参考 corpus 的 SHA256 会在验收中再次检查。

## 独立参考的生成

参考是 Microsoft vscode-languageserver-textdocument 1.0.12，MIT。精确版本、归档完整性与依赖锁文件在 scripts/oracle/。生成算法 xorshift32，种子 1369956643。每个会话含 8 次通知，每次通知有 1—3 次编辑，覆盖全文替换和合法增量范围；8 次通知后分别独立保存预期结果。生成输入和期望不调用 EditTrace。

tests/oracle/corpus.jsonl 每行是一个 JSON 编码的完整会话字符串，用于来源审查与 CLI 抽查；core/session/oracle_wbtest.mbt 是同一语料生成的离线测试。正常运行 MoonBit 测试不需要 Node。

## 已记录的参考缓存观察

tests/oracle/reference-cache-observation.json 和 scripts/oracle/reference-cache-probe.cjs 保存一个固定版本观察：初始 `\né\n`，在第 1 行末插入 CR，结果为 `\né\r\n`。该版本增量更新后的 cached positionAt 把文末报告为 line=3，而对相同文本新建文档后为 line=2。

首次对照因此产生了无效后续坐标。解决方式是在参考每次更新之后根据其输出文本重新建立参考对象，后续坐标使用新索引。文本编辑结果仍由独立 Microsoft 实现计算；手工 CRLF 测试同时验证产品的行数。这个观察只针对所固定版本，未将其包装成语言服务器缺陷，也未对外报告。

## 性能

验收实际执行 3 文档、10000 次小范围编辑，并包含一个 1 MiB 的初始文档。耗时和输入大小保存在 validation-results.json 的 benchmark 字段及 artifacts/benchmark.json。耗时随硬件和运行环境变化，没有性能优胜声明。峰值内存未测量。

## 平台与外部状态

以下描述为 2026-10-15 的历史状态，已由上方“当前复核结果”更新。

Windows native 在当前设备实际执行。GitHub Actions 提供 Windows/Linux 矩阵、固定工具链安装和同一验收入口。首次远程运行 38735028069 失败：Windows 的 Git 换行转换改变了 corpus 字节，Linux 工具链归档需要显式补执行权限。本地已增加 .gitattributes 固定 LF，并按官方 Unix 安装器对 bin 文件和 bin/internal/tcc 补执行权限；新增真实 Git 检出回归和权限策略单元测试。完整本地验收 207 项再次通过。修复后的远程结果仍待上传后确认，Linux 运行未在本机验证。真实服务器采集和原始日志导入属于 P1，尚未实现。不声称已报名成功。

## 注意

生产 JSON 报告必须确定性；开发期 evidence 允许包含实际机器路径和系统信息。正式公开仓库前可检查这些本地路径。验收目录保留独立产物，不自动清理，以便核查。

## 第二次远程检查跟进

运行 38736066950：Windows 全流程成功；Ubuntu 完成安装及 fmt/check/test/build，随后验收脚本在检查 native executable exists 时失败。脚本原先根据 OS 选择无后缀文件名。已增加 scripts/native_artifact.py，在明确的包产物目录检查 edittrace.exe 与 edittrace，缺失或歧义均给出诊断；主验收及干净目录使用同一解析函数。新增两项回归测试验证两种命名和错误情况，CI 支持回归共 4 项通过，207 项完整本地验收再次通过。更新后的 Ubuntu 运行仍待上传后确认。
