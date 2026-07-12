## MODIFIED Requirements

### Requirement: 引流线索命中即经 helper 自动触发群评

「引流线索评估」角色（`hot_lead_detector`，订阅 `quality.pass` + 缓存 `note.detail.arrived` 按 noteId 对齐）命中热度过滤闸后，SHALL 经「受闸群评触发 helper」（source='hot_lead'、target=noteId）自动触发带群码引流评论；不再持久化「引流待评候选队列」。被 `quality.reject`（含 LLM 出错/解析失败）的笔记 MUST NOT 触发。角色回调 MUST fire-and-forget、不阻塞浏览；roleName 在 `RoleName` 穷举内、纯确定性、MUST NOT 登记 `role-catalog`。系统 MUST NOT 设「每会话自动群评计数」这类随会话重置的装饰性节流；**权威节流 = 共用评论安全配额（时/日）+ 单场评论预算（场次）**，群评日上限为其下的子上限。账号联系评论模式为 `review` 时，撰写去 AI 味追加联系方式后推飞书人审卡；人点通过才真发。账号联系评论模式为 `auto_approve` 时，后台配置视为预授权，系统 SHALL 发送飞书免审通知并继续提交链路。账号联系评论模式为 `off` 或未配置时 MUST 不触发。

#### Scenario: 命中且过闸 → review 模式经 helper 触发飞书审批

- **WHEN** 笔记经 `quality.pass`、缓存详情命中过滤闸、本账号未评过/未在近期尝试过、联系评论模式为 `review`、且过全部安全闸
- **THEN** 经 helper 调 `triggerTargeted(injectContact:true)`，撰写去AI味追加联系方式后推飞书人审卡；人点通过才真发

#### Scenario: 命中且过闸 → auto_approve 模式经 helper 触发免审通知

- **WHEN** 笔记经 `quality.pass`、缓存详情命中过滤闸、本账号联系评论模式为 `auto_approve`、且过全部安全闸
- **THEN** 经 helper 调 `triggerTargeted(injectContact:true, approvalMode:'auto_approve')`，撰写后发飞书免审通知并继续提交链路

#### Scenario: 质量未通过不触发

- **WHEN** 笔记被 `quality.reject`（或 LLM 出错/解析失败按 reject 处理）
- **THEN** 即使热度命中也 MUST NOT 触发

#### Scenario: 不落队列

- **WHEN** 命中热帖但任一安全闸不过
- **THEN** 诚实略过、不发、**不入任何持久队列**（不再有 `hot_lead_queue`）

### Requirement: 浏览自动联系评论共用评论安全上限

浏览触发的自动联系评论 SHALL **与普通评论共用同一套评论安全上限**：**时/日**——helper 于触发回执 ok 后 `record('comment')` 消费同一 `RiskController` 评论配额（与自治浏览评论同池）；**场次**——detector 于触发前 gate 单场会话评论预算 `comments`、成功后扣减。自动化配置量 `contactCommentDailyCap` MUST 为**子上限**，与共用配额叠加即 min（`canDo` 先拦即等价 min），配置 MUST NOT 实际越过安全额。账号 `contactCommentMode` 为 `review` 或 `auto_approve`（默认 `off`）方触发；`review` 走人审，`auto_approve` 走后台预授权通知。缺联系方式 MUST fail-closed（本次不发、绝不降级无码评论）；账号未开时 MUST 等价现状（命中仅可记日志、不发），零回归。人工 `/comment` 命令 MUST 仍不占配额（人是刹车，不变）。

> 说明：本 change 未改 takeover 的 `skipRiskRecord` 语义，而由 helper 在浏览路径**显式 `record('comment')`** 达成共用配额消费；排期评论/排期群评纳入同一账本为 follow-up。

#### Scenario: 账号未开自动联系评论 → 不发（零回归）

- **WHEN** 命中热帖但账号 `contactCommentMode='off'`
- **THEN** MUST NOT 自动触发

#### Scenario: 浏览自动联系评论消费共用评论配额

- **WHEN** 某账号浏览触发发出一条联系评论成功
- **THEN** MUST `record('comment')` 消费共用评论配额且扣单场评论预算；后续该账号普通评论与联系评论共见余额减少

#### Scenario: 共用配额/单场预算耗尽 → 拦

- **WHEN** 账号已开自动联系评论但 `canDo('comment')` 被拒（时/日共用配额耗尽或风控态收紧）或单场评论预算已耗尽
- **THEN** MUST NOT 触发

#### Scenario: 缺联系方式 fail-closed

- **WHEN** 账号开了自动联系评论但未配置联系方式
- **THEN** 本次不发（明确失败），绝不降级为无联系方式评论
