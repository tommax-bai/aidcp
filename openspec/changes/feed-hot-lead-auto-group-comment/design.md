## Context

归档态：浏览闭环 `hot_lead_detector`（接 `quality.pass`）命中热帖 → 入 `hot_lead_queue` → 运营 `/api/hot-leads/comment` 逐条 `triggerTargeted(injectGroup)`（飞书人审=发）。硬不变量「浏览闭环永不自动注入群码」当时保留。

运营要求自动化：命中 + 账号开自动群评 + 过安全闸 → 自动触发（飞书审批）。**对抗性评审（2026-07-09，坐实代码）推翻了原稿的安全论证**：

- **群评日上限对浏览路径此前形同虚设**：`recordGroupCommentAttempt`（累加日上限）只由排期 wrapper（server.ts:2351）写，`triggerTargeted`/`runTargetedTask` 内部**从不写**（comment-scheduler.ts:274-371,534-596）。原稿误称「triggerTargeted 自带记账」。
- **canDo 与单场预算对 takeover 群评不计量**：takeover 评论入 `manualCommentAccounts`（server.ts:903-905）→ server.ts:1039 对 comment `skipRiskRecord=true` → 群评的 `interaction.occurred` 不进 `RiskController.record` → `canDo('comment')` 恒不随群评变；单场评论预算只在 dispatcher 自治评论处递减（role-dispatcher.ts:1240），群评走 scheduler 自己的 edge 步骤、不经此路径，且会话在 takeover 时结束、恢复重置。
- **一码一号已放松为告警放行**（content-schedule-store.ts:386-399，change loosen-group-comment-shared-code），非硬闸。
- **飞书人审 canDo 只在检测时查**、人审可能数分钟后才点，发出时无频率复检（TOCTOU）。

结论：直接接 `triggerTargeted` 会让浏览群评「只剩飞书人审 + 热帖到达频率」两道真闸，日上限空转 → 不可控。本 change 的主体＝**把日上限对群评补成真生效**，并如实降级失效的安全宣称。

## Goals / Non-Goals

**Goals:**
- 命中 + 账号开自动群评 + 过**真生效**的闸 → 自动 `triggerTargeted(injectGroup)` → 飞书人审=发。
- 让**群评日上限**对浏览触发真生效（回执 ok 后记账），确立为唯一权威跨会话日顶。
- 排期与浏览两源**共用一份**「受闸触发」helper（闸序 + 记账时机），杜绝漂移。
- 去队列；去重靠 hasInteracted + 短时 triggered 标记 + 单飞。
- 跨账号同码靠飞书卡面标注 + 人审（用户定：只按账号上限 + 卡面标注）。
- 默认关＝零回归。

**Non-Goals:**
- 不跳过飞书人审。
- 不为群评移除 `manualCommentAccounts` 的 record 跳过（会改「手动评论不计风控」语义，另案）；故 canDo 只作**状态闸**、不作群评计数器。
- 不加按码全局日上限（用户定：不做；靠卡面标注 + 人审）。
- 不做每会话计数（装饰层，砍掉）。
- 不改 edge 抽取/协议/解析/热度过滤闸/阈值配置。

## Decisions

### D1. 抽「受闸群评触发」helper，排期 + 浏览共用（防漂移，评审 major）
新增 `triggerGatedGroupComment({accountId, source, target?, snapshot?, triggerFn})`：顺序＝`group_comment_enabled?`（浏览路径需，排期路径由其自身开关保证）→ `canDo('comment')` 状态闸 → `countGroupAttemptsToday(accountId) < cap` → 调 `triggerFn`（排期＝`triggerManual({injectGroup})` 搜索选帖；浏览＝`triggerTargeted({noteId,title},{injectGroup})`）→ **回执 `ok` 才** `recordGroupCommentAttempt(accountId, {note_id, source, velocity, age_hours})`。**排期路径（server.ts:2340-2358）重构为调它**，浏览路径也调它——闸序与记账时机一处定义、两源一致。
- 记账**只在 receipt.ok**（排除 running/离线/缺码等未真开跑的拒），对齐排期现写法。

### D2. 修复日上限记账＝红线放开的前置必做（评审 blocker①）
浏览触发经 D1 的 helper，回执 ok 后必写 `recordGroupCommentAttempt` → `countGroupAttemptsToday` 真增长 → 日上限对浏览来源真生效。**这是唯一权威跨会话日顶**。验收断言：cap=N，触发 N+1 次，第 N+1 次被 `countGroupAttemptsToday>=cap` 拦。
- 删除 proposal/design/spec 里「triggerTargeted 自带记账」的错误表述。

### D3. 诚实降级失效的安全宣称（评审 major）
- `canDo('comment')`：**状态闸**（warned/restricted/frozen → 配额清零 → 拦）；**不**当群评频率计数器（takeover 群评不进 record）。
- 单场评论预算：**不消耗于群评**，不作群评节流，spec 不再宣称。
- 每会话自动群评计数：**砍掉**（随会话重置、不消耗预算、装饰性）。
真正对群评生效的频率闸＝**群评日上限（唯一日顶）** + 飞书人审 + 单飞。design/spec 如实这么写。

### D4. 发出时刻复检，闭 TOCTOU（评审 major）
`triggerTargeted` 是 fire-and-forget（检测→撰写→推审→等人点→post 可跨数分钟）。在 **post 步骤前**加一道廉价复检 `canDo('comment') + countGroupAttemptsToday<cap`，任一不过则本条 honest-fail 不发。消除「检测时过闸、发出时已超」的窗口。
- 飞书审批卡 surface：**「本账号今日群评 x/cap（排期+浏览合计）+ 当前风控态 + 本群码已被 N 个账号共用」**，让人审对频率与跨账号同码集中真正把关（用户定：卡面标注防同码集中）。

### D5. 一码一号如实写＝告警放行；跨账号同码靠卡面 + 人审（用户定）
spec/design 停止把一码一号当硬闸；如实写「共码仅告警放行」。跨账号同码集中风险**不加按码全局上限**（用户定），改由 D4 的卡面标注（「本码被 N 账号共用」）+ 飞书人审逐条把关。共码账号可开浏览自动群评，但每条审批卡显式提示共用数。

### D6. 去队列，去重三层（评审 blocker②/major）
移除 `hot_lead_queue`/`PgHotLeadQueue`/`/api/hot-leads*`/`PanelHotLeads`/人审逐条。去重：① `hasInteracted(noteId,'comment')`（已发出，risk_interactions）；② **短时 per-account「本 note 已尝试过（任意终态）」标记**（内存 TTL，防人审拒/超时/离线后重刷时反复推审）；③ `triggerTargeted` 单飞。修好记账后，每次真触发都吃 cap（保守）。

### D7. 审计＝给 group_comment_attempts 加列，零新表（评审 major）
`group_comment_attempts` 自愈加 `note_id TEXT NULL / source TEXT NULL / velocity DOUBLE PRECISION NULL / age_hours DOUBLE PRECISION NULL`。排期路径传 source='scheduled'（note_id null），浏览传 source='hot_lead' + 快照。台账兼作「系统自动给哪些帖、因多热发了引流评论」审计。不复活队列。

### D8. 复用 triggerTargeted（按 noteId 搜索定位），灰度看 note_not_found 率（评审 minor）
热帖此刻已在浏览闭环打开，但仍走 triggerTargeted（takeover→按标题搜索→精配 noteId→重开）以复用受审计注入链路。**灰度验收指标：该路径 note_not_found 率**；若真机落空显著，follow-up 再让触发通道吃「已打开 noteId 上下文」跳过重搜（不阻塞本 change）。

## Risks / Trade-offs

- **[放开红线→封号]** → 真生效的闸＝日上限（触发+发出双检、唯一日顶）+ canDo 状态闸 + 飞书人审(卡面带频率/共码数) + 单飞 + 默认关。**残留**：浏览目标是高热帖（曝光大审查严），比排期更显眼；跨账号同码无机制硬顶、靠人审——运营须把 cap 设小（≤3）、审时看共用数。
- **[两份闸序漂移]** → D1 helper 一处定义两源共用。
- **[takeover 频繁打断浏览]** → 日上限 + 单飞天然限次；砍每会话计数不增风险（它本就不生效）。
- **[note_not_found on 最热帖]** → 沿用诚实失败、不重试；D8 灰度指标盯。
- **[审计散落]** → D7 台账列兜住「发了哪些」。

## Migration Plan

- 纯 cloud + 默认关 → 零回归。顺序：① content-schedule-store 加审计列 + helper 抽取 + 排期路径重构调 helper（先不接浏览，回归确认排期群评行为不变）→ ② detector 接 helper + 去队列 + 发出复检 + 卡面标注 → ③ 移除 panel /api/hot-leads*。
- 部署 cloud dev 安全序列；edge/console 不动。回滚：单服务回滚，或运营关账号开关即时止血。
- 灰度：tom 分组测试账号开 `group_comment_enabled` + cap≤2 + 配码，真机看命中→审批卡（频率/共码标注）→发出、日上限触发+发出双检、note_not_found 率。

## Open Questions

- 短时 triggered 标记 TTL 取值（默认如 30–60min，够覆盖人审时长即可）——真机看人审时延再定。
- 是否给浏览自动群评独立于排期的日上限（当前共用同一 cap）——先共用；若运营要分开预算再拆。
