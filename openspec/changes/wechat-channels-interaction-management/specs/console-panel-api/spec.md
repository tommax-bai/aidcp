## ADDED Requirements

### Requirement: Internal API 必须按账号管理 runtime controls 与版本化回复配置

internal panel API SHALL 提供 `interaction-runtime-controls`、`interaction-reply-policy`、`reply-templates`、`reply-rules`、`reply-profile`、`reply-preview`、`reply-config/publish` 与 `reply-config/audit` 冻结路径。所有路径 MUST 校验 account 存在且 `accounts.platform='wechat_channels'`；MUST 使用共享 internal schema 与统一 envelope，MUST NOT 复用 Facebook 专用表或让客户 JWT 访问。

#### Scenario: 非视频号账号不可写视频号配置
- **WHEN** 管理员对 XHS/Facebook account 调用 reply config 写端点
- **THEN** API 返回稳定 validation/platform mismatch，MUST NOT 创建配置行

#### Scenario: 客户 token 不能进入 internal config API
- **WHEN** 持 customer-auth token 请求任一 `/api/accounts/:accountId/reply-*` 端点
- **THEN** 内部 JWT 校验失败并返回 401，不读写配置

### Requirement: 配置权限必须区分查看编辑发布预览与敏感内容

internal API SHALL 使用显式 permission：`interaction.config.view`、`interaction.config.edit`、`interaction.config.publish`、`interaction.config.preview`、`interaction.dm.view_full`、`interaction.audit.view`。缺 permission MUST fail closed；普通排障/配置列表 MUST 不因 config view 权限获得 DM 原文。

#### Scenario: 编辑者不能越权发布
- **WHEN** actor 有 config.edit 但无 config.publish
- **THEN** 可保存 draft，publish 返回 403 且 published 指针不变

#### Scenario: 无 DM full permission 只见脱敏内容
- **WHEN** actor 有 audit/view 但无 `interaction.dm.view_full`
- **THEN** DM 正文被脱敏或省略，MUST NOT 通过错误、preview 或 audit details 泄漏

### Requirement: Draft 写与 publish 必须非乐观且原子

配置写 SHALL 携 aggregate `expectedVersion`；服务端验证成功并落库后才回显写后真态。version conflict 返回 409/currentVersion；schema、变量、规则冲突或硬门禁错误整块拒绝，MUST NOT 部分落库或前端假保存。publish SHALL 生成 immutable version 和 append-only audit。

#### Scenario: 规则冲突整块拒绝
- **WHEN** draft 请求同时包含合法 profile 和同优先级冲突规则
- **THEN** 整次写/发布返回 validation issues，MUST NOT 只保存 profile 或产生 published version

#### Scenario: 写成功回显服务端真态
- **WHEN** 合法 draft CAS 写入成功
- **THEN** 响应 data 含新 currentVersion/updatedAt/updatedBy，Console 以回显刷新而非本地假设

### Requirement: Preview 与 audit 必须无发送副作用并保护正文

preview SHALL 只运行规则、template、可选 AI 与 risk 链并返回 would-action，MUST NOT 创建真实 job/attempt 或发 WS。audit SHALL 记录 actor、版本、实体 ID、状态/diff 摘要；普通日志/audit MUST NOT 保存完整 DM、Cookie 或第三方原始响应。

#### Scenario: Preview 不触发 Edge
- **WHEN** 管理员预览一条模拟私信
- **THEN** Cloud 不向任何 Edge 发 interaction.reply.send，数据库无真实 inbound message/job/attempt

#### Scenario: Audit 可追溯但不含私信正文
- **WHEN** 管理员发布配置或查看预览审计
- **THEN** 可读 actor/version/rule/template/result tags，普通 audit 中没有模拟/真实私信全文
