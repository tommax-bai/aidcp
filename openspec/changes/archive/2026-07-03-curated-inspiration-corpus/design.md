# Design — curated-inspiration-corpus（精选创作灵感语料）

> 本文档落到具体 `file:line`（截至 2026-06-28 逐处核对，行号可能随后续提交漂移，以符号/上下文为准）。
> 凡引用代码位置，cloud = `../aidcp-cloud`，edge = `../aidcp-edge`。

## 1. 背景与定位

创作灵感的记录现状（已坐实）：边端每篇笔记详情抽取了**标题/全文/作者/点赞数/收藏数/评论数/标签/是否已赞**（`edge/src/browse/note-extractor.ts:17-33`），并把**全文＋点赞数＋收藏数**随详情上报云端（`edge/src/browse/browse-session.ts:860-865`）。云端拿到后：

- 只把**标题＋链接**写进面板展示旁表（`cloud/src/server.ts:588-594` → `interaction-feed-store.ts` 的 `interaction_target_meta`，按 `(account_id, target_id)` upsert，红线「不碰风控/不去重」）；
- 真实点赞时只把**笔记标识**写进点赞血缘表（`server.ts:544` `likedNoteStore.recordLike(evt.noteId)`，从不传详情；事件本身也只带标识 `comm/handler.ts:277-286`）；
- 收藏（`collect`）**不触发任何灵感记录**（`server.ts:544` 只判 `action==='like'`）。

发帖创作消费侧（`publish-agent/publish-scheduler.ts` 的 `buildTriggerInput`）按「上次发布」基线聚合概念关键词＋点赞素材＋最近已发，喂 `prompts.ts` 的 `buildScoutPrompt`/`buildCreatorPrompt`。其中点赞素材标题/摘要恒空（上游没采）、概念只剩裸关键词（`concept-store.ts` 的 `getNewConceptsSince` 只 `SELECT keyword`、丢 `source_note`）。

**定位**：把分散、有损、漏采的灵感记录，收口为清晰三层；新建最上层「精选语料」承载创作的正向素材，下面两层复用现有行为账本。**正向素材唯一来源 = 精选语料**；话题雷达与避免撞题各走各线。

### 1.1 三层模型与现状映射

| 层 | 职责 | 承载表 | 现状 |
| --- | --- | --- | --- |
| 浏览记录 | 看过哪些笔记（标题/链接）；拟人/行为/审计 | `interaction_target_meta`（展示旁表） | **已有**，复用，不改职责 |
| 互动内容 | 点赞/收藏/评论/关注事件；拟人/血缘/去重 | `interaction_feed` + `risk_interactions` + `liked_notes` | **已有**，复用，不改职责 |
| 精选内容 | 过门槛高价值内容的**详细信息**；**创作来源** | `curated_content`（**新建**） | 本 change 主体 |

> 「记每篇浏览过的笔记」这一模式本仓已存在（展示旁表对每篇看过的笔记 upsert 一行标题/链接），故「按笔记建一份内容记录」并非异类；但展示旁表薄且有红线，不能堆正文/赞藏/选材逻辑——故精选层另起新表，绕开「展示旁表职责错＋红线」与「点赞血缘表职责错＋无迁移框架加列别扭」两条路。

## 2. 关键设计决策（逐项落 file:line）

### 2.1 精选语料表 `curated_content`（新建）

新建 `cloud/src/cache/curated-content-store.ts`，DDL `CREATE TABLE IF NOT EXISTS`（仿 `valuable-comment-store.ts:16-30` 风格，本仓**无迁移框架、首发即定列**）。列（草案）：

```
id                 SERIAL PK
account_id         TEXT NOT NULL                      -- 账号隔离
content_type       TEXT NOT NULL CHECK (note|comment) -- 类型标记（Phase 1 = note）
source_id          TEXT NOT NULL                      -- note_id（笔记）/ 评论锚（评论）
dedup_key          TEXT NOT NULL UNIQUE               -- = account_id::content_type::source_id
title              TEXT                               -- 笔记标题（评论为 NULL）
body               TEXT                               -- 笔记全文 / 评论正文
author             TEXT
source_url         TEXT
topics             TEXT[] NOT NULL DEFAULT '{}'       -- 话题键（GIN）
like_count         INT                                -- 笔记点赞数 / 评论赞数（Phase 2）
collect_count      INT                                -- 笔记收藏数（评论无）
comment_count      INT                                -- 笔记评论数（可选）
counts_captured_at TIMESTAMPTZ                        -- 计数采集时刻（快照语义）
bot_liked          BOOLEAN NOT NULL DEFAULT false     -- 机器人自己点赞了
bot_collected      BOOLEAN NOT NULL DEFAULT false     -- 机器人自己收藏了
admit_reason       TEXT                               -- 纳入原因（ratio/collect_floor/bot_collect/...）
first_seen_at      TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
```

- **去重/合并**：`INSERT ... ON CONFLICT (dedup_key) DO UPDATE`——重复观测刷新计数快照与 `updated_at`、保留 `first_seen_at`；动作标记**只置位不清零**（合并补标记，治「谁先发生算谁、后者丢失」）。
- **类型标记**统一笔记与评论：取数时按 `content_type` + `topics` 召回。

### 2.2 观测捕获：详情到达时按门槛纳入（缺口③；纯 cloud）

`server.ts:588-594` 现订阅 `note.detail.arrived` 只 `upsertMeta(noteId, {title,url})`。**在同处旁挂精选捕获**：详情已带 `title`/`content`(全文)/`author`/`likeCount`/`collectCount`（`browse-session.ts:860-865`）——

1. 取账号兴趣（`soul.interests.primary`/`seed_keywords`，经 `getSoul(accountId)`）算相关性；
2. 跑门槛（§2.4）；过则 upsert `curated_content`（`content_type='note'`，写全文＋赞藏数＋话题＋`counts_captured_at=now`＋`admit_reason`）；不过则**只留薄行为记录、详情丢弃**（精选表小、压 PII）。
3. **诚实置空**：计数解析不到落 NULL/0（边端已 `parseCount` 失败回 0，`note-extractor.ts:40-62`），话题缺则空数组——绝不编造。

> 评论数：`note-extractor.ts:184` 已抽 `comments` 数，但 `browse-session.ts:860-865` 的上报 payload 现只带 like/collect 数。把 `commentCount` 纳入上报为**小改（可选）**，供门槛/记录用，非 Phase 1 必需。

### 2.3 机器人自有动作标记与自有收藏自动纳入（缺口②；纯 cloud）

`server.ts:543-548` 现订阅 `interaction.occurred` 只在 `like` 时 `recordLike(noteId)`。改为对 `like` 与 `collect`：

- 把对应标记并入该笔记的精选行（`bot_liked`/`bot_collected` 置位，merge）；
- **自有收藏自动纳入**：`collect` 即便当时共鸣门槛未过也纳入精选（收藏本身已是受风控约束的策展判断）。`like`/`collect` 总发生在 `note.detail` 之后（同访问内），故笔记内容可从同访问已观测的当前笔记取得（`session.currentNoteId` 对应内容）——动作时若精选行尚不存在且为收藏，用该内容补建行。
- `interaction.occurred` 已带 `accountId`（`comm/handler.ts:277-286` 从 `session.accountId` 填），故标记按账号落位、不串账号。
- **点赞为弱信号**：单独 `bot_liked` 不构成自动纳入（仅当共鸣/相关性门槛另行过关才纳入）；只有 `bot_collected` 自动纳入。

> 与点赞血缘表的关系：`liked_notes`（`server.ts:544`）继续按原职责记点赞来源血缘、供 `publish_log.source_liked_ids` 回填，本 change **不动它**。精选语料是另一条「创作素材」线，二者职责不同、可并存（同一笔记可同时在两表，冗余合理）。

### 2.4 准入门槛（缺口核心；可配置、按账号）

一篇被观测笔记纳入精选，须同时满足**相关性**与**共鸣（或自有收藏）**：

- **相关性闸**：笔记 `topics`/`tags` 与账号兴趣关键词重叠 ≥ `minTopicOverlap`（缺省 1）；**自有收藏豁免相关性**（机器人自己挑的，相关性已隐含）。理由：共鸣只衡量「火不火/值不值得存」，不衡量「与账号领域搭不搭」；缺这道闸，精选库会塞满高质量但跑题内容。
- **共鸣闸（满足其一）**：
  - `collect_count ≥ collectFloor`（缺省示例 50）——收藏是比点赞更强的「有用、值得留」信号，作主门槛；
  - `collect/like 比率 ≥ ratioMin`（缺省示例 0.25）**且** `like_count ≥ ratioLikeFloor`（缺省示例 200）——比率衡量「不只点赞、还要存下来」的含金量；**比率必须配最低赞数地板**，否则小样本假高比率（如 2 赞 1 收藏）混入；
  - **自有收藏** `bot_collected`——免共鸣门槛直接纳入。
- **阈值不写死**：`collectFloor`/`ratioMin`/`ratioLikeFloor`/`minTopicOverlap`/`retentionMax` 做成配置，缺省内置、可按账号覆盖（接入既有按账号配置口）。这治本仓灵感机制「固定阈值」的旧毛病。

> 绝对计数偏向大热话题——故主筛用**比率**（天然归一）+ 收藏地板；归一化（相对账号常态/按天）留作后续细化，v1 用「原始值＋采集时刻」诚实即可。

### 2.5 账号隔离（缺口）

`curated_content` 带 `account_id`，召回 `WHERE account_id = $1`。对比现状：`concepts`/`liked_notes` 表都无账号列、素材全局混用，与 `publish_log.account_id` 的隔离不一致、且与防关联意图相悖。精选层从第一天起按账号隔离，**绝不跨账号串味取材**。

### 2.6 有界增长与 PII（对齐评论语料库）

保留上限按账号 newest `retentionMax`（缺省示例 1000）淘汰最旧（仿 `valuable-comment-store.ts:96-117` 的「插入后裁到上限」）。精选表存他人正文/作者，明示保留/脱敏姿态（仅来自公开浏览到的内容，带上限，文档明述）——对齐 `valuable-comment-corpus` 既定 PII 姿态。

### 2.7 创作消费：精选语料为正向素材唯一来源（缺口；纯 cloud）

`publish-scheduler.ts` 的 `buildTriggerInput` 现把 `likedStore.recentSince(baseline)` 当点赞素材（恒空）。改为：

- **加权选取**：从 `curated_content`（`content_type='note'`、按账号）取候选，按 `自有动作分级（收藏＞点赞＞无） × 共鸣（收藏数/比率） × 新鲜度 × 相关性` 排序取 top-K。**收藏档优先但不饿死点赞档**——按比例混（如收藏档占多数席位、保留若干点赞档/高共鸣无动作档），不赢者通吃。
- **蒸馏注入＋非照抄护栏**：进 `prompts.ts` 的素材块用**要点蒸馏**（要点/观点/具体数据）而非原文直灌，并套「仅作灵感、严禁照抄、只借角度口吻」（复用 `valuable-comment-corpus` 的非照抄红线，扩到笔记素材）。理由：全文直灌既抬 token 又抬照抄风险（本仓硬红线）。
- **概念补回来源标题**：顺带修 `concept-store.ts` 的 `getNewConceptsSince` 取 `source_note` 并在聚合/`prompts.ts` 渲染「（来源: 标题）」（现为恒空死分支）。
- **不并入精选的两条线**：话题/概念雷达（驱动「该不该发、往哪个方向」）与避免撞题（最近已发，来自 `publish_log`）**各走各线**，不塞进精选内容表——前者是薄关键词信号、后者是负向过滤器，职责与「正向素材」不同。

### 2.8 评论并入精选层（Phase 2）

精选层用 `content_type` 统一；Phase 2 把现有评论语料（`valuable-comment-store.ts`）以 `content_type='comment'` 并入（迁移或建桥），并补**评论逐条赞数**采集——当前评论候选只带正文/作者/已赞态（`cloud/src/agents/comment-like-appraiser.ts:172` 的候选形态 `anchorId/author/text/alreadyLiked`），无赞数；要按赞数给评论设门槛需扩边端评论抽取（`edge` 改 + 若上报带赞数则协议两份同步）。**取数按用途分**：写帖拉 `note`（＋ `comment` 当角度线索），写评论拉 `comment` 当口吻范例。Phase 2 依赖 Phase 1 的表与类型标记，可作本 change 第二批 task 或拆 follow-up。

## 3. 时序与竞态分析

同一笔记访问内的事件序：`note.detail.arrived`（带全文＋赞藏数）→ 机器人决策 → 可能的 `like`/`collect` 完成（`interaction.occurred`）。

- 详情**先于**动作到达，故捕获门槛在详情时即可判（用当时计数）；动作标记在其后合并。
- **自有收藏补建**：若详情时门槛未过、随后机器人收藏（自动纳入），需笔记内容——取同访问当前笔记内容（详情已观测）。须保证「动作处能拿到当前笔记内容」：复用云端已有的当前笔记上下文（详情上报后保留在会话/上下文中）。若取不到内容则**诚实降级**：以标识＋计数补建、正文留空并标 `admit_reason='bot_collect(content_missing)'`，绝不编造正文。
- 计数为**快照**：一篇当时没过门槛、以后才火的笔记，只有再次被浏览到才会刷新计数——可接受（计数本就只有浏览时可知）。

## 4. 协议影响

- **Phase 1 大概率零协议改动**：笔记全文＋点赞数＋收藏数已在现有 `note.detail` 上报（`browse-session.ts:860-865`）。
- **可选**：把笔记「评论数」纳入上报 payload（边端已抽，仅 payload 未带）——若做，两份 `src/comm/protocol.ts` 逐字一致 + `command-bridge.ts` 映射 + `docs/protocol.md` 同步。
- **Phase 2**：评论逐条赞数若需上报，同样两份协议同步；漂移由 `Record<MessageType,true>` 穷举与 `AC-PROTO-*` 守护。

## 5. 风险与缓解

| 风险 | 级别 | 缓解 |
| --- | --- | --- |
| 精选表无界增长 / PII | 中 | 按账号保留上限淘汰最旧 + 明示 PII 姿态（对齐评论语料库）；只存过门槛的少量行 |
| 全文直灌创作导致照抄 | 中 | 蒸馏要点注入 + 「仅作灵感、严禁照抄」护栏（复用评论语料非照抄红线）；存全文但不原样进 prompt |
| 门槛过严→精选空 / 过松→灌跑题 | 中 | 阈值可配置（按账号）+ 相关性闸；冷启动期可临时放宽收藏地板/比率 |
| 自有收藏补建时取不到正文 | 低 | 诚实降级：标识＋计数补建、正文留空并标因，绝不编造 |
| 收藏被误以为「放量」 | 低（无） | 风控不动：收藏已比点赞更严（上限低/冷却长/去重），本 change 只记录已过闸的收藏、不增频率 |
| 计数快照漂移 | 低 | 带 `counts_captured_at`，当点对点证据用、不宣称实时 |
| 多账号素材串味 | 中 | 精选行带 `account_id`、召回按账号过滤（本 change 即修该旧缺口） |

## 6. 拆分判断

- **Phase 1（笔记，纯 cloud、零边端、大概率零协议）**：精选表 + 观测捕获 + 门槛 + 双标记 + 账号隔离 + 保留上限 + 发帖创作消费切换。一体、互为前提（无表则无处落、无消费切换则记了不用），可独立交付与验证。
- **Phase 2（评论并入 + 边端评论赞数抽取）**：依赖 Phase 1 的表与类型标记。作本 change 第二批 task；若边端评论赞数抽取实测风险超预期（选择器校准），可拆为 follow-up change，Phase 1 不受影响。

当前默认 Phase 1 先行、Phase 2 紧随；二者通过同一精选表与类型标记衔接。
