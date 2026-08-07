## MODIFIED Requirements

### Requirement: 云端必须接收并解析验证码上报，不得静默丢弃

云端 SHALL 在 `protocol.ts` 镜像 `captcha.detected` / `captcha.cleared` 两个消息类型与对应 payload（验证码检测与协助自本 change 起同属 `captcha.*` 顶层域，一族一属主；历史 `risk.` 前缀因把「消费方拿它干什么」编码进名字而废止），并在 `DefaultMessageHandler` 路由它们到验证码协调器；MUST NOT 让这两类上报落到 switch 的 `unsupported_type` default 被静默丢弃。两份 `protocol.ts` MUST 逐字一致、消息总数同步、`docs/protocol.md` 计数与表同步。

**`MessageType` 穷举守卫只护消息类型、不护 payload 字段。** 当协助能力以「扩既有载荷的可选字段」而非「新增消息类型」的方式演进时，字段级漂移（一侧加了字段、另一侧没加）**typecheck 与消息数断言都抓不到**。因此协助命令与回执的 payload MUST 有逐字段的两侧往返断言，且 panel HTTP 边界（从 `unknown` 手写解构处）MUST 有透传断言——在那里漏一个字段是静默丢弃且全绿。

#### Scenario: 验证码上报被正确路由

- **WHEN** 云端收到一帧 `captcha.detected{edgeId,kind,url}`
- **THEN** 云端将其交给验证码协调器处理（迁移状态 / 暂停 / 通知），而非返回 `error{code:'unsupported_type'}`

#### Scenario: 协议两侧不漂移

- **WHEN** 运行 `npm run typecheck` 与 `AC-PROTO` 合约测试
- **THEN** 边缘与云端两份 `protocol.ts` 的 `MessageType` 穷举一致、消息总数断言一致，且 `docs/protocol.md` 头部计数与表与代码一致

#### Scenario: 扩载荷字段不漂移

- **WHEN** 一侧的协助命令或回执 payload 新增 / 删改字段而另一侧未同步
- **THEN** 逐字段往返断言 MUST 失败；panel HTTP 边界未透传新字段时透传断言 MUST 失败
