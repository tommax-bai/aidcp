## ADDED Requirements

### Requirement: 运营必须能按 alert_id 手动解决单条告警，且诚实回真实解决行数

云端告警存储 SHALL 提供一个「按 `alert_id` 解决」的方法，其 SQL MUST 复用既有「按 edge 解决」的形状——`UPDATE alerts SET resolved_at=<now / to_timestamp(at)> WHERE alert_id=$1 AND resolved_at IS NULL`——并 MUST 返回真实受影响行数（`rowCount`，`0` = 没这条 / 已被解决，`1` = 本次解决）。该方法 MUST NOT 依赖 `edge_id`，从而使 `edge_id=NULL` 的告警（如节奏过载）与从未收到配对清除的告警（如未知阻断弹窗）都能被解决。MUST NOT 用 raw UPDATE 绕过该存储所有者，MUST NOT 报告乐观假成功。

#### Scenario: 解决一条未解决告警

- **WHEN** 运营对一条 `resolved_at IS NULL` 的告警按其 `alert_id` 触发解决
- **THEN** 该行 `resolved_at` 被置为当前时刻、掉出「未解决」列表，接口回真实行数 `1`

#### Scenario: 解决不存在或已解决的告警诚实回 0

- **WHEN** 按 id 解决一条不存在、或 `resolved_at` 已非空的告警
- **THEN** 存储命中 0 行、返回 `0`，接口诚实回 `{resolved:0}`，绝不假报成功

#### Scenario: edge_id 为空的告警可被解决

- **WHEN** 一条 `edge_id IS NULL` 的节奏过载告警按其 `alert_id` 被解决
- **THEN** 它被正常闭合（不因空 `edge_id` 而匹配不到），验证 by-id 通道不依赖 `edge_id`

### Requirement: 手动解决只闭合告警日志行，绝不联动风控状态单写与边缘恢复

按 id 手动解决 SHALL **只** `UPDATE` 告警行的 `resolved_at`。它 MUST NOT 调用 `RiskController.applySignal` / `setQuotaLevel`，MUST NOT 写 `risk_state`——账号风控终态仍由风控 controller 单写，与告警解决完全解耦。它 MUST NOT 调用传输层的边缘恢复（`resumeEdge`）：手动勾销一条阻断类（`block`/`captcha`）告警**绝不**解除该 edge 的验证码暂停（验证码清除点 `onCleared` 才 `resumeEdge`；二者是不同路径，实装 MUST NOT 把解决接上恢复）。

#### Scenario: 勾销阻断类告警不解除边缘暂停

- **WHEN** 运营手动解决一条仍处于暂停态 edge 的 `block` 告警
- **THEN** 该 edge 的传输层暂停维持不变（不被 `resumeEdge`），账号风控态不变，仅告警行被闭合

#### Scenario: 解决路径不触碰风控单写

- **WHEN** 任一次按 id 手动解决执行
- **THEN** 全程不调用 `applySignal` / `setQuotaLevel`、不写 `risk_state`（以 spy/mock 可断言）

### Requirement: 手动解决必须与边缘自动清除并存且幂等无冲突

按 id 手动解决与既有「按 edge 自动清除」SHALL 共用同一个 `resolved_at IS NULL` 守卫。两条入口对同一行的并发/重复解决 MUST 靠数据库行锁串行——先提交者命中并置 `resolved_at`、后到者重估 `WHERE` 命中 0 行——从而幂等、诚实回真实行数、不二次解决、不报错。手动解决 MUST NOT 改动验证码事件的按 edge 自动清除与暂停/恢复语义。

#### Scenario: 手动解决后边缘配对清除命中 0 行

- **WHEN** 一条 `block` 告警已被人工按 id 解决，随后该 edge 才送来配对的 `risk.captcha_cleared`
- **THEN** 按 edge 自动清除对该行命中 0 行、不二次解决、不报错（按 edge 恢复 edge 下发的既有语义照常）

#### Scenario: 两入口共用同一未解决守卫

- **WHEN** 检视按 id 解决与按 edge 解决的 SQL
- **THEN** 二者都带 `AND resolved_at IS NULL` 守卫，保证并发下行锁串行、后者命中 0 行

### Requirement: 面板解决路由经 JWT 守护、诚实校验、依赖未注入即降级

面板 SHALL 暴露 `POST /api/alerts/:id/resolve`，置于 JWT 保护区（沿用「JWT 守护所有 /api/*」，缺/过期 token 返回 401）。路由 MUST 校验 `:id` 为正整数，非法 SHALL 返回 400（`invalid_id`）。告警存储依赖未注入时 SHALL 返回 503（`alerts_unavailable`）而非崩溃，沿用「面板故障不连累边-云闭环」。成功时 SHALL 返回 `{resolved: 0|1}`（诚实透传真实行数），前端 MUST 据此区分文案：`1`→「已解决」、`0`→「该告警已解决或不存在」，绝不笼统报成功。

#### Scenario: 非法 id 返回 400

- **WHEN** `POST /api/alerts/:id/resolve` 的 `:id` 非正整数
- **THEN** 路由返回 400（`invalid_id`），不调用存储

#### Scenario: 存储未注入返回 503

- **WHEN** 告警存储未注入面板 deps（如 init 失败）而收到解决请求
- **THEN** 路由返回 503（`alerts_unavailable`），进程与边-云闭环不受影响

#### Scenario: 成功诚实透传行数

- **WHEN** 携有效 JWT 对一个合法 id 请求解决，存储回 `1`（或 `0`）
- **THEN** 路由返回 200 与 `{resolved:1}`（或 `{resolved:0}`），前端据 0/1 出可区分文案

### Requirement: 手动解决与验证码去重冷却相互独立，不清冷却记录

手动按 id 解决 SHALL 与验证码协调器的 per-edge 去重冷却相互独立：手动解决**不**经验证码清除点（`onCleared`），故 MUST NOT 清除协调器的 per-edge 冷却记录。由此，若同一 edge 在冷却窗内再次出现阻断，仍按既有冷却语义被去重压制——此行为 SHALL 被固化为已知语义（活状况如实复现），本 change MUST NOT 改动冷却逻辑。

#### Scenario: 勾销不重置验证码冷却

- **WHEN** 运营手动解决一条 `block` 告警后，同一 edge 在冷却窗（约 10min）内再次翻进阻断态
- **THEN** 协调器仍按既有冷却压制（不因旧告警被勾销而重置冷却、不额外发卡/落库），冷却记录不被手动解决清除
