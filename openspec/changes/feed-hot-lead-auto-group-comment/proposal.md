## Why

`feed-hot-lead-group-comment`（已归档）做成了「浏览闭环发现热帖 → 入引流待评候选队列 → **人审逐条**挑着发带群码评论」。运营（2026-07-09）要求改为**自动化**：浏览闭环刷到合适热帖后，只要**账号已开自动群评 + 过真正生效的安全闸**，就自动触发一条带群码引流评论、走飞书审批（人点通过才真发），不再人工逐条挑。

> ⚠️ 对抗性评审（2026-07-09）坐实：现有「安全限额」机制**并不给群评计数**——`triggerTargeted` 内部不写群评日上限台账、takeover 群评跳过风控 record（`manualCommentAccounts`）、单场评论预算也不被它消耗。所以「满足全部安全限额就自动发」**不能靠直接调 `triggerTargeted` 实现**，必须把「真正生效的日上限计数」补出来。本 change 的主体工作就是**让安全闸对群评真生效**，而不只是接一个触发。

## What Changes

- **【统一安全模型·核心】** 定义「**非人工命令场景（自动化）的评论安全模型**」：排期评论、排期群评、浏览触发群评——**群评论与普通评论共用同一套评论安全上限**，包含**场次（单场会话评论预算 `comments`）+ 各时间维度（小时 / 日，经 `canDo('comment')` 窗口）**，同一个池、不分开。**人工 `/comment` 命令仍是「人是刹车」、不占配额**（不变）。
  - **① 账号 opt-in**：浏览自动群评需 `group_comment_enabled=true`（默认关＝零回归）。
  - **② 共用评论安全配额（权威上限）**：自动化触达发出后 MUST **`record('comment')` 进风控** → 消费共用配额；受 `canDo('comment')`（时/日）+ 单场评论预算（场次）约束。⚠️**修复核心**：现在 takeover 评论一律 `skipRiskRecord`（`manualCommentAccounts`）→ 自动化群评不占配额；改为 **`skipRiskRecord` 仅对人工 `/comment` 生效、自动化路径照记**，共用池才成立、canDo 才真反映群评。
  - **③ 自动化配置量受安全额封顶**：`group_comment_daily_cap` 等自动化配置是**子上限**，**生效值 = min(配置, 共用评论安全配额剩余, 单场评论预算)**——配置不能越过安全额。群评日上限 `group_comment_attempts` 保留为子上限 + 审计（触发 ok 后记账，与排期共用同一台账）。
  - **④ 一码一号（现为告警放行，非硬闸）**：跨账号同码集中靠**飞书审批卡标注「本码已被 N 个账号共用 + 本账号今日 x/额度」**让人审把关（用户 2026-07-09 定：只按账号上限 + 卡面标注，不加按码全局上限）。
  - **⑤ 飞书人审=发**：每条人点通过才真发；**触发时 + 发出（post）时各复检一次** `canDo + 子上限`（消除「发现→人审→发出」几分钟空窗的 TOCTOU）。
  - **⑥ 单飞**：`triggerTargeted` running set 防同账号并发双发（覆盖排期+浏览双源）。
- **【共享触发封装·防漂移】** 抽一个「受闸群评触发」helper，把 `canDo 共用配额闸 → 单场预算闸 → 子上限(min) → 触发 → 回执 ok 才 record('comment')+recordGroupCommentAttempt+扣单场预算` 收成一处；**排期与浏览共用**同一份闸序与记账时机，杜绝两份漂移（CLAUDE.md 热点纪律）。**排期评论/排期群评路径一并接入此统一模型**（令自动化评论都占共用配额）。
- **【去队列】** 移除「引流待评候选队列」`hot_lead_queue` + `/api/hot-leads*` + 人审逐条。去重：`hasInteracted(noteId,'comment')`（已发出）+ **短时「本帖已尝试过（任意终态）」标记**（防人审拒/超时后重刷时反复再推审）+ `triggerTargeted` 单飞。
- **【审计·零新表】** 给现有 `group_comment_attempts` 加 `note_id / source('scheduled'|'hot_lead') / velocity / age_hours`（可空）列；触发封装记账即写这些 → 台账直接兼作「系统自动给哪些帖发了引流评论」审计。
- **【砍装饰层】** 去掉原稿「每会话自动群评计数」（随会话重置、纯装饰）——由**真消耗的单场评论预算**（场次维度）+ `canDo` 时/日窗口取代，二者才是真节流；群评日上限降为子上限 + 审计。
- **【不变】** 发布时刻抽取（edge，已上线）、协议字段、云端解析、热度过滤闸、阈值全局后台可配（安全页卡片）——全部保留不动。

> BREAKING（对 spec）：放开硬不变量 + 移除队列/人审逐条。对运营是行为增强（默认关＝零回归）。

## Capabilities

### Modified Capabilities
- `feed-hot-lead-group-comment`: 命中热帖由「入队 + 人审逐条」改为「账号开自动群评 + 过统一评论安全模型 → 受闸群评触发 helper → `triggerTargeted(injectGroup)` → 飞书人审=发」；确立**非人工命令场景下群评与评论共用同一评论安全上限（场次 + 时/日）**、自动化触达发出即 `record('comment')` 消费共用配额（`skipRiskRecord` 仅对人工命令）、自动化配置量受安全额封顶（生效=min）；跨账号同码靠卡面标注 + 人审；移除持久队列与人审逐条消费；`group_comment_attempts` 降为子上限 + 加审计列；排期评论/排期群评一并接入统一模型。发布时刻抽取/协议/解析/过滤闸/阈值配置不变。

## Impact

- **aidcp-cloud（主体）**
  - 抽「受闸群评触发」helper：`canDo('comment') 共用配额闸 + 单场评论预算闸(场次) + 子上限 min(group cap, 余额) + 触发闭包 + 回执 ok 才 record('comment')(消费共用) + recordGroupCommentAttempt(带 note_id/source/snapshot,审计+子上限) + 扣单场预算`；**排期评论/排期群评（server.ts:2340-2358 等）与浏览路径都重构为调它**。
  - **`record` 跳过语义改**：`manualCommentAccounts`/`skipRiskRecord`（server.ts:903-905/1039）改为**仅对人工 `/comment` 命令跳过**；排期评论/排期群评/浏览群评等自动化触达 **`record('comment')` 照记**（消费共用评论配额），令 canDo 真反映、群评与评论共用池成立。
  - `src/hot-lead/hot-lead-detector.ts`：命中不入队，经 helper 触发（source='hot_lead'，target=noteId）；短时 triggered 标记去重；砍每会话计数。
  - `src/config/content-schedule-store.ts`：`group_comment_attempts` 自愈加列 `note_id/source/velocity/age_hours`；`recordGroupCommentAttempt` 接受可选快照；共码数查询（某群码被几账号用）供卡面标注。
  - 审批卡构造处：加「本账号今日 x/生效上限 + 风控态 + 本码被 N 账号共用」标注；**post 前复检** `canDo + 子上限`，不过则 honest-fail。
  - `role-dispatcher.ts` + `server.ts`：detector 接线注入 helper（+ group_comment_enabled + hasInteracted + 单场预算取值口）；移除 `hotLeadQueue`。
  - 移除 `src/hot-lead/hot-lead-queue.ts`、panel `/api/hot-leads*` + `PanelHotLeads` + server `hotLeads` 接线。
- **aidcp-edge / aidcp-console**：不动（抽取已上线；安全页阈值卡片保留；审批卡是 cloud 侧飞书消息）。
- **DB**：`group_comment_attempts` 加审计列（自愈 ALTER）；`hot_lead_queue` 停用。
- **红线（新态）**：非人工命令的评论/群评统一受**共用评论安全上限**（场次 + 时/日，自动化触达照记消费）；自动化配置量被安全额封顶（生效=min）；浏览自动群评另需账号开关 + 飞书人审(触发+发出双检) + 单飞；跨账号同码靠卡面标注 + 人审；缺码 fail-closed；默认关＝零回归。**人工 `/comment` 仍不占配额（人是刹车）。**
