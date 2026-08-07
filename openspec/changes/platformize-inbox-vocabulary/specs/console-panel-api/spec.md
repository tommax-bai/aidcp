## MODIFIED Requirements

### Requirement: Runtime-control updates drive account-scoped Edge delivery
After a successful CAS update of `interaction_runtime_controls`, the internal API SHALL make the committed account/version available to the account's negotiated online Edge through `wechat_channels.inbox.runtime.controls`. The database commit and audit record SHALL remain authoritative; delivery count or socket enqueue MUST NOT be reported as Edge application success.

#### Scenario: CAS update reaches one online Edge
- **WHEN** an authorized operator updates runtime controls with the current expected version and exactly one negotiated Edge is online for the account
- **THEN** Cloud commits and audits version `N+1`, pushes a scope-matching `wechat_channels.inbox.runtime.controls` payload to that Edge, and returns the committed controls without claiming Edge application

#### Scenario: Edge is offline during update
- **WHEN** the runtime-control CAS succeeds while no negotiated Edge is online
- **THEN** Cloud keeps the committed version, records delivery as deferred/zero, and includes the latest fail-closed snapshot in the next negotiated welcome

### Requirement: Preview 与 audit 必须无发送副作用并保护正文

preview SHALL 只运行规则、template、可选 AI 与 risk 链并返回 would-action，MUST NOT 创建真实 job/attempt 或发 WS。audit SHALL 记录 actor、版本、实体 ID、状态/diff 摘要；普通日志/audit MUST NOT 保存完整 DM、Cookie 或第三方原始响应。

#### Scenario: Preview 不触发 Edge
- **WHEN** 管理员预览一条模拟私信
- **THEN** Cloud 不向任何 Edge 发 wechat_channels.inbox.reply.send，数据库无真实 inbound message/job/attempt

#### Scenario: Audit 可追溯但不含私信正文
- **WHEN** 管理员发布配置或查看预览审计
- **THEN** 可读 actor/version/rule/template/result tags，普通 audit 中没有模拟/真实私信全文
