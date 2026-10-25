# 项目回归与 CI（0.3.0 候选）

在 VS Code 打开本地目录。多根工作区每次明确选择项目；取消选择不执行后续动作。

1. 运行 Initialize Project Regressions，创建 `.edittrace/project.json` 与说明，不覆盖现有文件。
2. 录制并停止，或预览格式化/重命名。查看摘要、全部文件差异及必要的 Raw JSON。
3. Save Project Regression Draft 保存 `case-<id>.json` 和 `.review.json`。草稿含采集来源、输入、文本及声明期望。
4. 编辑并审核输入与期望，运行 Confirm Regression Expectations。界面展示上次确认与当前期望的差异，核心核对声明，再由用户显式确认。**当前输出不是天然正确答案。**
5. Run Confirmed Project Regressions 每次重新发现文件，仅组合内容哈希未改变的已确认用例。草稿/变化文件显示排除提示；损坏输入或元数据明确报错，不能静默跳过。
6. 单例入口可运行未确认草稿以检查声明；失败跳转到该 case 输入。整套失败可选择失败文件。界面不会自动修改期望。

默认只读取选定 `.edittrace` 的直接文件，最多 256 个用例、1024 个目录项、64 MiB 发现输入；单文件和组合 suite 最多 8 MiB。拒绝链接目录和链接用例；名称限制防止路径逃逸。确认记录只是本地状态，不提供防篡改或审核者身份认证。

运行 v1 case 不依赖旁文件。已有外部 case 可用 Save Last Result as Regression Case 或 CLI 直接运行；项目发现只接纳约定的 `case-*.json`。suite 是嵌入式用例 JSON，跨目录可迁移，运行不读取 URI 指向的工程。

仓库示例：

```text
edittrace suite run examples/real-world/suite.json
edittrace suite run examples/real-world/suite.json --format junit --out result.xml
edittrace case run examples/real-world/injected-lost-event.case.json
```

最后一条预期退出 1。发行 ZIP 中样例位于 `examples/`，去掉命令中的 `real-world/`。`--out` 必须为新路径。

CI 可使用 examples/ci-consumer/workflow.yml。该示例下载公开 0.2.0 固定二进制并核对校验和，使用消费工程自己的 suite 运行 JSON 回归，避免引用尚未公开的 0.3.0。待 0.3.0 实际发布后，换成经验证的发行地址/哈希，启用 JUnit。不要使用不存在的新版本 URL 或把示例文件存在当作远程 CI 已运行。
