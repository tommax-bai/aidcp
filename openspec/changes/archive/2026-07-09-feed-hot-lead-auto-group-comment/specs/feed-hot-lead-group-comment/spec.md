## MODIFIED Requirements

### Requirement: 云端热度速率过滤闸

云端 SHALL 计算每小时点赞速率 `velocity = likeCount / max(hoursAgo, FLOOR_HOURS)`，并以布尔过滤闸判定是否「热帖线索」：当且仅当 `hoursAgo` 非 `null` 且三者皆满足——`ageHours ≤ MAX_AGE_HOURS`、`velocity ≥ VELOCITY_MIN`、`likeCount ≥ LIKES_MIN`——判为热帖线索。`hoursAgo` 为 `null` 或超帖龄上限时 MUST 判为**非线索、不触发**，MUST NOT 臆造速率、MUST NOT 按绝对量硬塞。这是过滤不是排序，MUST 不引入跨候选比较。判定 MUST 为**纯确定性**（不调 LLM）。判为「热帖线索」后是否发评论，另受「自动触发安全闸」需求约束。

#### Scenario: 涨得快且新鲜且够量 → 命中

- **WHEN** 某帖 `likeCount=5000`、`hoursAgo=2`、在上限内、超过速率与最小赞阈值
- **THEN** 判为热帖线索（是否发评论再过自动触发安全闸）

#### Scenario: 帖龄超上限 → 淘汰

- **WHEN** 某帖 `hoursAgo` 超过 `MAX_AGE_HOURS`（或为裸日期哨兵值）
- **THEN** 判为非线索、不触发，无论其绝对赞数多高

#### Scenario: 时刻不可得 → 不臆造

- **WHEN** 某帖 `hoursAgo` 为 `null`
- **THEN** 判为非线索、不触发，不臆造速率

## ADDED Requirements

### Requirement: 受闸自动评论触发 helper（回执 ok 才记账）

系统 SHALL 提供一个「受闸自动评论触发」helper（`triggerGatedAutoComment`），收口自动化联系评论的安全闸序与记账时机。闸序 MUST 为：`canDo('comment')`（共用评论安全配额，时/日）→ 子上限 `countContactAttemptsToday < contactCommentDailyCap`（与共用配额叠加即 min）→ 调触发闭包（浏览＝按 noteId `triggerTargeted({noteId,title},{injectContact})`）→ **仅当触发回执 `ok` 时**：`record('comment')`（消费共用评论安全配额）+ `recordContactCommentAttempt(accountId, {noteId, source, velocity, ageHours})`（子上限计数 + 审计）。任一闸不过 MUST 不触发、不记账。本 change 浏览路径经其触发；**排期评论/排期群评接入同一 helper（令其也 record 消费共用配额）为 follow-up**（本 change 未做，见 tasks/backlog）。

#### Scenario: 回执 ok 才记账（消费共用配额 + 子上限）

- **WHEN** 经 helper 触发一条联系评论且回执 `ok`
- **THEN** `record('comment')` 消费共用配额一次 + `contact_comment_attempts` 当日计数 +1（带 source/noteId 审计）

#### Scenario: 未真开跑不记账

- **WHEN** 触发被单飞/边端离线/缺联系方式等拒（回执非 ok）
- **THEN** MUST NOT 记账（不误占额度、不消耗配额）

#### Scenario: 子上限对浏览来源真生效

- **WHEN** cap=N，浏览路径经 helper 触发 N 次（均 ok）后第 N+1 次命中
- **THEN** 第 N+1 次因 `countContactAttemptsToday >= cap` 被拦、不触发

### Requirement: 引流线索命中即经 helper 自动触发群评

「引流线索评估」角色（`hot_lead_detector`，订阅 `quality.pass` + 缓存 `note.detail.arrived` 按 noteId 对齐）命中热度过滤闸后，SHALL 经「受闸群评触发 helper」（source='hot_lead'、target=noteId）自动触发带群码引流评论；不再持久化「引流待评候选队列」。被 `quality.reject`（含 LLM 出错/解析失败）的笔记 MUST NOT 触发。角色回调 MUST fire-and-forget、不阻塞浏览；roleName 在 `RoleName` 穷举内、纯确定性、MUST NOT 登记 `role-catalog`。系统 MUST NOT 设「每会话自动群评计数」这类随会话重置的装饰性节流；**权威节流 = 共用评论安全配额（时/日）+ 单场评论预算（场次）**，群评日上限为其下的子上限。

#### Scenario: 命中且过闸 → 经 helper 触发（飞书审批）

- **WHEN** 笔记经 `quality.pass`、缓存详情命中过滤闸、本账号未评过/未在近期尝试过、且过全部安全闸
- **THEN** 经 helper 调 `triggerTargeted(injectGroup:true)`，撰写去AI味追加群码后推飞书人审卡；人点通过才真发

#### Scenario: 质量未通过不触发

- **WHEN** 笔记被 `quality.reject`（或 LLM 出错/解析失败按 reject 处理）
- **THEN** 即使热度命中也 MUST NOT 触发

#### Scenario: 不落队列

- **WHEN** 命中热帖但任一安全闸不过
- **THEN** 诚实略过、不发、**不入任何持久队列**（不再有 `hot_lead_queue`）

### Requirement: 浏览自动联系评论共用评论安全上限

浏览触发的自动联系评论 SHALL **与普通评论共用同一套评论安全上限**：**时/日**——helper 于触发回执 ok 后 `record('comment')` 消费同一 `RiskController` 评论配额（与自治浏览评论同池）；**场次**——detector 于触发前 gate 单场会话评论预算 `comments`、成功后扣减。自动化配置量 `contactCommentDailyCap` MUST 为**子上限**，与共用配额叠加即 min（`canDo` 先拦即等价 min），配置 MUST NOT 实际越过安全额。账号 `contactCommentEnabled=true`（默认关）方触发；缺联系方式 MUST fail-closed（本次不发、绝不降级无码评论）；账号未开时 MUST 等价现状（命中仅可记日志、不发），零回归。人工 `/comment` 命令 MUST 仍不占配额（人是刹车，不变）。

> 说明：本 change 未改 takeover 的 `skipRiskRecord` 语义，而由 helper 在浏览路径**显式 `record('comment')`** 达成共用配额消费；排期评论/排期群评纳入同一账本为 follow-up。

#### Scenario: 账号未开自动联系评论 → 不发（零回归）

- **WHEN** 命中热帖但账号 `contactCommentEnabled=false`
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

### Requirement: 去重覆盖未发出终态 + 尝试台账兼审计

系统 SHALL 对浏览触发去重覆盖三层：① `hasInteracted(noteId,'comment')`（已发出，risk_interactions）；② **短时 per-account「本 note 已尝试过（任意终态：发出/拒/超时/离线）」标记**，防人审拒或失败后重刷时反复推同一帖；③ `triggerTargeted` 单飞。`contact_comment_attempts` 台账 SHALL 加 `note_id / source / velocity / age_hours`（可空）列，令其兼作「系统自动给哪些帖、因多热发了联系评论」审计（零新表）。

#### Scenario: 人审拒后不立即重触发

- **WHEN** 某热帖触发后人审拒/超时，账号稍后重刷到同一 noteId（仍在短时标记窗口内）
- **THEN** MUST NOT 立即再触发同一帖

#### Scenario: 台账带审计维度

- **WHEN** 浏览路径记一条群评尝试
- **THEN** 该行带 `source='hot_lead'` + `note_id` + 速率/帖龄快照，可回查系统自动触达了哪些帖

## REMOVED Requirements

### Requirement: 引流待评候选队列（只发现不发布，入队去重）

**Reason**: 改为「命中即过真生效安全闸自动触发」，不再持久化候选队列（用户 2026-07-09 定：不要队列）。
**Migration**: 去重改用 `hasInteracted` + 短时 triggered 标记 + 单飞；`hot_lead_queue` 表停用（不再读写，可后续迁移删）。

### Requirement: 人审逐条消费引流候选发定向群评

**Reason**: 取消人工逐条挑，改为满足条件自动触发（仍走飞书人审=发）。
**Migration**: 移除面板 `/api/hot-leads` 列表与 `/api/hot-leads/comment` 及 `PanelHotLeads`；自动触发经共享 helper 复用同一 `triggerTargeted(injectGroup)` + 飞书人审。

### Requirement: 浏览闭环永不自动发群码红线保留

**Reason**: 按运营要求放开为「受真生效安全闸约束的受控自动」，由「浏览闭环自动群评的真生效安全闸」等需求取代。
**Migration**: 不再硬禁；改由〔账号开关 + 群评日上限(触发+发出双检、唯一日顶) + canDo 状态闸 + 飞书人审=发(卡带频率/共码数) + 短时去重 + 单飞〕约束；一码一号如实为告警放行、跨账号同码靠卡面标注+人审；账号默认关＝零回归；群码注入点不变（compose-approve 去AI味后、人审前 verbatim 追加）。
