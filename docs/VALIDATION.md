# 验证证据与复现方式

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

Windows native 在当前设备实际执行。GitHub Actions 提供 Windows/Linux 矩阵、固定工具链安装和同一验收入口；远程 CI 尚未触发，Linux 未实际验证。真实服务器采集和原始日志导入属于 P1，尚未实现。不声称存在公开发布或报名成功记录。

## 注意

生产 JSON 报告必须确定性；开发期 evidence 允许包含实际机器路径和系统信息。正式公开仓库前可检查这些本地路径。验收目录保留独立产物，不自动清理，以便核查。
