# multi-tenant-orchestration Specification

## Purpose
TBD - created by archiving change multi-account-node-support. Update Purpose after archive.
## Requirements
### Requirement: 每个 edge 连接拥有独立的决策上下文

云端编排 SHALL 为**每个 edge 连接**维护一束独立的决策上下文（信息流状态 / 会话预算 / 待评论 / 当前账号），按连接（`sessionId`/`edgeId`）隔离。一个连接的上报 MUST NOT 改写另一个连接的上下文，新连接接入 MUST NOT 重置已有连接正在进行的会话。

#### Scenario: 两连接互不污染
- **WHEN** 两个 edge 连接分别上报各自的信息流卡片
- **THEN** 两套决策上下文各自演进，互不混入对方的卡片/笔记/预算

#### Scenario: 新连接不重置在跑会话
- **WHEN** 第二个 edge 连接接入
- **THEN** 第一个连接正在进行的浏览会话不被重置或中断

### Requirement: 账号身份穿透握手事件

握手 SHALL 把连接的 `accountId` 一并带入触发会话启动的事件载荷，使决策层据此设定该连接的当前账号；MUST NOT 在事件中丢弃 `accountId` 而让决策层无从得知连接归属（不再钉死 `default`）。

#### Scenario: 决策层得知连接归属账号
- **WHEN** 一个 edge 以某 `accountId` 握手
- **THEN** 该连接的决策上下文当前账号被设为该 `accountId`，而非固定的 `default`

### Requirement: 下行指令只发回发起该决策的连接

云端 SHALL 把每条下行指令**只发回产生该决策的那个连接**（按 `edgeId` 定向），MUST NOT 广播给所有连接。单连接场景下「定向到唯一连接」与原广播行为等价（非 BREAKING）。

#### Scenario: 不同账号不串号
- **WHEN** 依据账号 A 连接的上报算出一条互动指令，同时账号 B 的连接也在线
- **THEN** 该指令只发到账号 A 的连接，账号 B 的连接收不到它

#### Scenario: 单连接行为不变
- **WHEN** 全机只有一个 edge 连接在线
- **THEN** 定向到该唯一连接，下发行为与原广播完全一致

