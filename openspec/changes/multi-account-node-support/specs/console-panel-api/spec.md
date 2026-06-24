## ADDED Requirements

### Requirement: 账号接口暴露人设绑定状态

`GET /api/accounts`（及 `GET /api/accounts/:id`）SHALL 在账号视图中暴露**人设绑定状态**（如 `personaBound` / `needsPersonaSetup`），供后台账号列表标示「需设置人设」并跳转人设页。该字段 SHALL 沿用面板既有 JWT 鉴权，MUST NOT 另开免鉴权入口。该字段在 cloud 面板类型与 console 端类型为**手工镜像**，两处 MUST 同步以防漂移。

#### Scenario: 账号列表标示需设置人设
- **WHEN** 一个已登记但未绑人设的账号，经鉴权请求 `GET /api/accounts`
- **THEN** 响应中该账号带「未绑人设 / 需设置」状态，后台据此标示并提供跳转人设页的入口

#### Scenario: 状态字段受同一 JWT 守护
- **WHEN** 未携带有效 JWT 请求 `GET /api/accounts`
- **THEN** 返回 401，不泄露任何账号或其人设绑定状态

### Requirement: 看板事件扇出跨每连接私有通道聚合

当编排改为「每连接一条私有事件通道」后，实时看板的事件扇出 SHALL **跨所有连接的私有通道聚合**，对外仍呈现为**单一全局只读流**（与既有面板 WS 契约一致），MUST NOT 因通道私有化而漏掉某连接的事件或重复推送。该聚合仍是纯只读扇出，MUST NOT 触碰边缘 socket、MUST 沿用面板 WS 的 JWT 鉴权。

#### Scenario: 多连接事件汇入单一看板流
- **WHEN** 多个 edge 连接各自在自己的私有通道上产生面板相关事件
- **THEN** 看板聚合这些通道、对浏览器仍输出一条单一全局流，各连接事件不漏不重

#### Scenario: 私有化不破坏单连接看板
- **WHEN** 全机只有一个 edge 连接
- **THEN** 看板流内容与「单一全局总线」时代等价，无可见差异

