# 发布前审查、安装演练与远程发布结果

日期：2026-10-20。

## 1. 审查与修复

已完成本地发布前审查，修复了版本失败跳过结构检查、步骤断言重复回放、合法 JSON-RPC id 复用误判、捕获完整性声明和 CI 旧报告误上传风险。核心/module/扩展统一为 0.2.0；实际历史 0.1.0 包复核可读。详见 PRE_RELEASE_REVIEW.md。

## 2. 安装及使用演练

已安装 `cloud00726.edittrace@0.2.0` 到用户日常 VS Code 配置。安装文件来自本次通过 CI 的 Windows 产物，安装后的核心与该产物逐字节一致。

自动演练完成：格式化预检、四个回归用例、预期失败的漏事件用例、保存与迁移用例；实际安装包/自带核心另在专用 VS Code 测试宿主通过 14 项检查，包含录制、停止、预览、差异与回归草稿执行。

这是实际安装与自动化使用验证；没有把用户的主观体验、人工保存/确认点击或第三方试用伪称完成。未改写用户原有工程文件或其他扩展设置。证据：install-validation.json、host-validation.json。

## 3. 推送、远程 CI 与可下载预览

代码已提交并正常推送至 origin/main。发布源提交：`bffd56c2e8567dadd71b2214aefb396799bce3f1`。

[发布源 Windows/Linux CI](https://github.com/cloud00726/edittrace/actions/runs/39429451845) 两个任务均成功：各 337 项验收断言、独立消费者和 9 项无需 GUI 的发行包检查通过。原有 500 参考会话/4000 检查点未重生成。

[EditTrace 0.2.0 Preview 1](https://github.com/cloud00726/edittrace/releases/tag/v0.2.0-preview.1) 已公开，提供 Windows/Linux x64 的 CLI ZIP、VSIX、平台 SHA256 清单及 SHA256SUMS。共 7 个附件，全部取自通过 CI 的产物，上传后校验字节数及哈希。它是 GitHub prerelease，没有发布 Marketplace 或 Mooncakes。

详情见 remote-ci-validation.json、release-validation.json；GitHub 自动源码归档对应发布源提交，后续状态文档提交不改变该二进制来源。

下一步：用户可在 VS Code 命令面板搜索 EditTrace 体验，之后按 competition/USER_TRIAL.md 收集真实维护者反馈。赛事人工定稿与重新提交仍未执行，也不保证审查通过。
