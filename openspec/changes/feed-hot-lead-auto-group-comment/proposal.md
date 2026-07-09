## Why

`feed-hot-lead-group-comment`（已归档）做成了「浏览闭环发现热帖 → 入引流待评候选队列 → **人审逐条**挑着发带群码评论」。运营（2026-07-09）要求改为**自动化**：浏览闭环刷到合适热帖后，只要**账号已开自动群评 + 过真正生效的安全闸**，就自动触发一条带群码引流评论、走飞书审批（人点通过才真发），不再人工逐条挑。

> ⚠️ 对抗性评审（2026-07-09）坐实：现有「安全限额」机制**并不给群评计数**——`triggerTargeted` 内部不写群评日上限台账、takeover 群评跳过风控 record（`manualCommentAccounts`）、单场评论预算也不被它消耗。所以「满足全部安全限额就自动发」**不能靠直接调 `triggerTargeted` 实现**，必须把「真正生效的日上限计数」补出来。本 change 的主体工作就是**让安全闸对群评真生效**，而不只是接一个触发。

## What Changes

- **【放开红线·受控】** 原硬不变量「浏览闭环永不自动注入群码」放开为**受控自动**。放开后**真正生效**的闸（评审逐条坐实、去掉空转的）：
  - **① 账号 opt-in**：`group_comment_enabled=true`（默认关＝零回归）。
  - **② 群评每日尝试上限（唯一权威日顶）**：`countGroupAttemptsToday(accountId) < cap`（硬顶≤10、建议≤3）；**与排期群评共用同一 `group_comment_attempts` 台账**。⚠️修复核心：浏览触发路径**此前不写这张台账**，本 change 在触发封装里于回执 ok 后**显式 `recordGroupCommentAttempt`**，令日上限对浏览来源真生效。
  - **③ 风控状态闸**：`canDo('comment')`——注意它对 takeover 群评**不计量频率**，仅作**状态闸**（账号被平台信号升到 warned/restricted/frozen → 配额清零 → 拦截）。
  - **④ 一码一号（现为告警放行，非硬闸）**：跨账号同码集中风险靠**飞书审批卡标注「本码已被 N 个账号共用 + 本账号今日 x/cap」**让人审知情把关（用户 2026-07-09 定：只按账号上限 + 卡面标注，不加按码全局上限）。
  - **⑤ 飞书人审=发**：每条人点通过才真发；**触发时 + 发出时各复检一次**日上限与 canDo（消除「发现→人审→发出」几分钟空窗的 TOCTOU）。
  - **⑥ 单飞**：`triggerTargeted` running set 防同账号并发双发（覆盖排期+浏览双源）。
- **【共享触发封装·防漂移】** 抽一个「受闸群评触发」helper，把 `canDo 状态闸 → 日上限检查 → 触发 → 回执 ok 才 recordGroupCommentAttempt` 收成一处；**排期群评与浏览触发共用**同一份闸序与记账时机，杜绝两份漂移（CLAUDE.md 热点纪律）。
- **【去队列】** 移除「引流待评候选队列」`hot_lead_queue` + `/api/hot-leads*` + 人审逐条。去重：`hasInteracted(noteId,'comment')`（已发出）+ **短时「本帖已尝试过（任意终态）」标记**（防人审拒/超时后重刷时反复再推审）+ `triggerTargeted` 单飞。
- **【审计·零新表】** 给现有 `group_comment_attempts` 加 `note_id / source('scheduled'|'hot_lead') / velocity / age_hours`（可空）列；触发封装记账即写这些 → 台账直接兼作「系统自动给哪些帖发了引流评论」审计。
- **【砍装饰层】** 去掉「每会话自动群评计数」（随会话重置、不消耗预算、纯装饰）；诚实写明**唯一跨会话日顶 = 群评日上限**。
- **【不变】** 发布时刻抽取（edge，已上线）、协议字段、云端解析、热度过滤闸、阈值全局后台可配（安全页卡片）——全部保留不动。

> BREAKING（对 spec）：放开硬不变量 + 移除队列/人审逐条。对运营是行为增强（默认关＝零回归）。

## Capabilities

### Modified Capabilities
- `feed-hot-lead-group-comment`: 命中热帖由「入队 + 人审逐条」改为「账号开自动群评 + 过〔真生效的〕安全闸 → 受闸群评触发 helper → `triggerTargeted(injectGroup)` → 飞书人审=发」；**修复群评日上限对浏览路径的记账**（使其真生效）；如实降级失效的 canDo/单场预算/每会话计数的安全宣称（canDo 保留为状态闸）；跨账号同码靠卡面标注 + 人审；移除持久队列与人审逐条消费；`group_comment_attempts` 加审计列。发布时刻抽取/协议/解析/过滤闸/阈值配置不变。

## Impact

- **aidcp-cloud（主体）**
  - 新增/抽取「受闸群评触发」helper：`canDo 状态闸 + countGroupAttemptsToday<cap + 触发闭包 + 回执 ok 才 recordGroupCommentAttempt(带 note_id/source/snapshot)`；**排期路径（server.ts:2340-2358 triggerGroupComment）重构为调它**，浏览路径也调它。
  - `src/hot-lead/hot-lead-detector.ts`：命中不入队，改为经 helper 触发（source='hot_lead'，target=noteId）；短时 triggered 标记去重；砍每会话计数。
  - `src/config/content-schedule-store.ts`：`group_comment_attempts` 自愈加列 `note_id/source/velocity/age_hours`；`recordGroupCommentAttempt` 接受可选快照；`countGroupAttemptsToday` 不变。共码数查询（某群码被几个账号用）供卡面标注。
  - `src/comment-agent/compose-approve.ts`（或审批卡构造处）：飞书审批卡加「今日 x/cap + 本码被 N 账号共用」标注；发出前（post 前）复检 `canDo + countGroupAttemptsToday<cap`，不过则 honest-fail。
  - `role-dispatcher.ts` + `server.ts`：detector 接线改为注入 helper（+ group_comment_enabled 判定 + hasInteracted）；移除 `hotLeadQueue`。
  - 移除 `src/hot-lead/hot-lead-queue.ts`、panel `/api/hot-leads*` + `PanelHotLeads` + server `hotLeads` 接线。
- **aidcp-edge / aidcp-console**：不动（抽取已上线；安全页阈值卡片保留；审批卡是 cloud 侧飞书消息）。
- **DB**：`group_comment_attempts` 加审计列（自愈 ALTER）；`hot_lead_queue` 停用。
- **红线（新态）**：浏览自动群评仅在〔账号开 + 过真生效的日上限(触发+发出双检) + canDo 状态闸 + 飞书人审 + 单飞〕时发生；跨账号同码靠卡面标注 + 人审；缺码 fail-closed；默认关＝零回归。
