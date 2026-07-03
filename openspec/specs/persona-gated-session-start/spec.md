# persona-gated-session-start Specification

## Purpose
TBD - created by archiving change multi-account-node-support. Update Purpose after archive.
## Requirements
### Requirement: 仅对已绑人设的账号启动会话，未绑诚实拒绝

云端 SHALL 在启动某连接的浏览会话前，用**独立于人设解析器**的判据确认该账号**已绑定人设**（以人设存储中存在该账号的人设行为准）。已绑 → 照常启动。未绑 → MUST NOT 启动浏览循环、MUST NOT 发出巡刷信号、MUST 在角色重订阅/指令翻译重连**之前**短路，并将该账号置 `needs_persona_setup` 态、发出运营告警。**该闸对所有账号一视同仁、无任何豁免**（`default` 账号已退役、系统已无默认人设可回落）。绝不以任何人设静默把未绑账号跑起来（违反「绝不静默假成功」）。

#### Scenario: 新账号未绑人设被诚实拒绝

- **WHEN** 一个此前未在后台设过人设的真实账号握手接入
- **THEN** 云端不启动其浏览循环、不发巡刷信号，将该账号标为 `needs_persona_setup` 并告警，绝不以任何默认人设开跑

#### Scenario: 原有账号复用已绑人设直接启动

- **WHEN** 一个先前已在后台绑过人设的账号握手接入
- **THEN** 云端用其已绑人设照常启动浏览会话，无需重新设置

#### Scenario: 判绑与解析分离

- **WHEN** 判定某账号是否已绑人设
- **THEN** 判据基于人设行是否存在，而非解析结果——显式绑定算「已绑」，没有人设行算「未绑」，两者不混为一谈

### Requirement: 缺失账号身份按配置错误拒绝握手，不得偷映射为 default

当握手缺失或为空 `accountId` 时，云端 MUST 将其当作**配置错误拒绝握手 / 不建立会话**并发出运营告警，MUST NOT 把缺失账号静默映射成任何账号后开跑。一个无名连接没有可路由 / 可限频 / 可在后台设人设的身份，因此 MUST NOT 被当作一个匿名「需设置」账号挂起。每个节点 MUST 在握手显式声明自己的 `accountId`，且该账号须已在后台绑定人设方可运行任务。

#### Scenario: 空账号被当配置错误拒绝

- **WHEN** 一个 edge 不带 `accountId`（或为空）握手
- **THEN** 云端拒绝该握手 / 不建立会话、发出配置错误告警，绝不以任何默认人设为其开跑

#### Scenario: 声明了身份但未绑人设仍被启动闸拒

- **WHEN** 一个 edge 显式声明了 `accountId` 握手成功，但该账号未在后台绑人设
- **THEN** 握手可建立（身份合法），但其浏览 / 发布 / 评论任务被入口闸以 `needs_persona_setup` 拒绝，直至后台补绑人设

