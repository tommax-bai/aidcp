## Why

验证码事故现在只能提示运营远程登录出问题的机器处理。对于点选类挑战，这增加了响应时间，也要求运营直接接触 AdsPower 浏览器窗口；但验证码又不能迁移到另一个云端浏览器中处理，因为挑战结果必须落在原账号、原 IP、原指纹、原 DOM 会话里。

本变更提供一个云端远程协助入口：运营可以从 Feishu 告警进入云端处理页，基于 edge 捕获的验证码现场截图发起人工点击，最终点击仍由原 edge 注入到原浏览器，清除也仍由 edge 复检并上报。

## What Changes

- 在验证码 / 未知阻断 incident 中引入 remote assist 会话，包含 incident id、edge/account 归属、截图、验证码区域坐标、状态和过期时间。
- edge 在阻断态下支持只读现场截图采集，以及受 cloud 授权的人工点击命令；点击必须落到当前原浏览器会话，不得在云端另开浏览器处理。
- cloud 暴露受保护的验证码协助接口和页面：读取最新截图、提交点击点位、刷新截图、查看处理状态。
- Feishu 验证码告警卡增加“去处理”入口，指向该 incident 的云端协助页；告警仍保持 notify-only，不复用发布审批信号文件。
- edge 每次人工点击后必须复检遮罩；只有实际清除时才发送 `risk.captcha_cleared`，cloud 才恢复该 edge 下发。
- 保留现有风控语义：验证码 detected 仍置 `restricted`，cleared 不自动回 `normal`，手动关闭告警也不解除 edge 暂停。

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `captcha-incident-handling`: 增加云端远程协助处理验证码 incident 的合同，约束截图、点击、复检、Feishu 入口和恢复语义。

## Impact

- `aidcp-edge`: CDP 截图裁剪、验证码区域坐标映射、人工点击命令执行、点击后复检与结果回报。
- `aidcp-cloud`: CaptchaCoordinator incident 建模、短期截图存储、受 JWT 保护的 assist API、edge 定向命令和结果关联、Feishu actionUrl 生成。
- `aidcp-console`: 验证码协助页面，展示截图、点击选择、刷新、状态和过期/失败反馈。
- `aidcp`: 协议文档、OpenSpec 规格和跨仓测试计划。
- No database destructive changes. If durable incident audit is needed, add append-only metadata only; screenshots should be short-lived and never logged as secrets.
