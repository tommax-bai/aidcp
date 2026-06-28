# Tasks — curated-inspiration-corpus（精选创作灵感语料）

> **依赖序**：Phase 1（纯 cloud）：精选表（task 1）→ 门槛（task 2）→ 观测捕获接线（task 3）→ 动作标记/自有收藏纳入（task 4）→ 创作消费切换 + 概念来源标题补回（task 5）→ 配置（task 6）→ 验收 + 回归（task 7-8）→ 部署（task 9）。
> Phase 2（评论并入 + 边端评论赞数）：task 10-11，依赖 Phase 1 的表与类型标记。
>
> **回写格式**：task 完成后用 HTML 注释把 `[ ]` 标 `[x]`，写清 commit-sha / 偏离说明 —— `<!-- <repo> <commit-sha> 备注 -->`（部署后追加 `<!-- <date> deployed -->`）。进度按 sub-repo 分节回写本仓。
>
> **范围**：默认 Phase 1 先行、Phase 2 紧随。Phase 1 纯 cloud、零边端、大概率零协议改动；可独立交付。

## 1. aidcp-cloud — 精选语料表 `curated_content`

- [ ] 1.1 新增 `src/cache/curated-content-store.ts`：`curated_content` 表 DDL（`CREATE TABLE IF NOT EXISTS`，仿 `valuable-comment-store.ts:16-30`）含 `account_id` / `content_type(note|comment)` / `source_id` / `dedup_key UNIQUE` / `title` / `body` / `author` / `source_url` / `topics TEXT[]`（GIN）/ `like_count` / `collect_count` / `comment_count` / `counts_captured_at` / `bot_liked` / `bot_collected` / `admit_reason` / `first_seen_at` / `updated_at`。验证：单测建表幂等（重复建不报错）。
- [ ] 1.2 `upsertObservation(...)`：`INSERT ... ON CONFLICT (dedup_key) DO UPDATE` 刷新计数快照 + `updated_at`、保留 `first_seen_at`；动作标记**只置位不清零**（合并补标记）。验证：单测——重复观测刷新计数、二次动作合并标记、首见时间不变。
- [ ] 1.3 `markBotAction(account, noteId, 'like'|'collect')`：置 `bot_liked`/`bot_collected`；行不存在且为 collect 时按入参内容补建（content 缺则正文留空 + `admit_reason='bot_collect(content_missing)'`，**不编造**）。验证：单测覆盖「行已存在合并标记」「行不存在收藏补建」「内容缺诚实留空」。
- [ ] 1.4 `selectForCreation(account, type, limit, weights)`：按 `自有动作分级 × 共鸣 × 新鲜度 × 相关性` 排序取 top-K，**收藏档优先但保留点赞档/高共鸣档席位**（按比例混，不赢者通吃）。验证：单测断言收藏档优先且点赞档不被清空。
- [ ] 1.5 保留上限：按账号 newest `retentionMax` 淘汰最旧（仿 `valuable-comment-store.ts:111-116`）。验证：单测超上限裁最旧、按账号互不影响。
- [ ] 1.6 经 `src/cache/index.ts` 导出；`server.ts` 启动时 `init()`，失败诚实降级（不记录、发帖创作回落旧素材路径，不 brick 启动）。验证：单测/手测 init 失败时不抛、捕获路径退化。

## 2. aidcp-cloud — 准入门槛 Gatekeeper

- [ ] 2.1 新增准入判定（`src/agents/curated-content-gatekeeper.ts` 或等价纯函数）：**相关性闸**（笔记 `topics`/`tags` 与账号兴趣关键词重叠 ≥ `minTopicOverlap`；自有收藏豁免相关性）**且** **共鸣闸**（`collect_count ≥ collectFloor` 或 `collect/like ≥ ratioMin 且 like ≥ ratioLikeFloor` 或 `bot_collected`）。验证：单测覆盖——收藏地板过/不过、比率过但赞数不足地板被拦、跑题被相关性拦、自有收藏豁免相关性纳入、单独点赞不纳入。
- [ ] 2.2 阈值全部取配置（task 6），无写死魔数。验证：单测注入不同阈值得不同纳入判定。

## 3. aidcp-cloud — 观测捕获接线（详情到达）

- [ ] 3.1 `src/server.ts` 在 `note.detail.arrived` 订阅（现 `:588-594` 只 `upsertMeta`）旁挂精选捕获：取账号兴趣（`getSoul(accountId)`）算相关性 → 跑 task 2 门槛 → 过则 `curatedStore.upsertObservation`（全文＝详情 `content`、赞藏数＝`likeCount`/`collectCount`、话题＝标签派生、`counts_captured_at=now`、`admit_reason`）；不过则不写精选（薄行为记录照旧）。验证：单测——过门槛写精选行、不过门槛不写、计数缺失诚实置空。
- [ ] 3.2 话题键派生复用既有口径（仿 `valuable-comment-store.ts:33-43` `topicKeysFromTitle`，或从标签/概念取）。验证：单测中英文标题都给出可重叠话题键。

## 4. aidcp-cloud — 自有动作标记与自有收藏纳入

- [ ] 4.1 `src/server.ts` 在 `interaction.occurred` 订阅（现 `:543-548` 只 `like→recordLike`）扩 `like` 与 `collect` → `curatedStore.markBotAction(accountId, noteId, action)`；`collect` 即自有收藏自动纳入。`liked_notes` 的点赞血缘落库**保持不变**（职责不同、并存）。验证：单测——`like` 置 `bot_liked`、`collect` 置 `bot_collected` 且纳入、accountId 落位正确不串账号。
- [ ] 4.2 自有收藏补建取「同访问当前笔记内容」：复用云端当前笔记上下文；取不到则诚实降级（task 1.3）。验证：单测覆盖「内容可得正常补建」「内容不可得留空标因」。

## 5. aidcp-cloud — 创作消费切换 + 概念来源标题补回

- [ ] 5.1 `src/publish-agent/publish-scheduler.ts` `buildTriggerInput`：正向素材从 `likedStore.recentSince` 切到 `curatedStore.selectForCreation(account,'note',K,weights)`；保留避免撞题块（`publish_log` 最近已发，不变）；**话题雷达/避免撞题不并入精选**。验证：单测断言素材来自精选语料、按账号、加权选取。
- [ ] 5.2 `src/publish-agent/prompts.ts` 素材块改用精选语料**蒸馏要点**渲染（要点/观点/具体数据），套「仅作灵感、严禁照抄、只借角度口吻」护栏（复用 `valuable-comment-corpus` 非照抄红线）。验证：单测断言 prompt 含护栏文案、非原文直灌；非照抄 overlap guard 沿用评论侧机制（如适用）。
- [ ] 5.3 修概念来源标题丢失：`src/cache/concept-store.ts` `getNewConceptsSince` 取 `source_note`，聚合映射带回，`prompts.ts` 渲染「（来源: 标题）」（现恒空死分支）。验证：单测断言概念项带来源标题、prompt 不再是裸词。
- [ ] 5.4 退化安全：精选语料空/不可用时，发帖创作回落（如旧路径或仅概念），**绝不崩溃、绝不伪造素材**。验证：单测空语料路径。

## 6. aidcp-cloud — 门槛与保留可配置（按账号）

- [ ] 6.1 配置项：`collectFloor` / `ratioMin` / `ratioLikeFloor` / `minTopicOverlap` / `retentionMax` / `selectTopK` + 选材权重；缺省内置，可按账号覆盖（接既有按账号配置口）。**不写死、不记敏感值**。验证：单测——缺省值生效、按账号覆盖生效。

## 7. 验收（中控触发，落 sub-repo 执行）

- [ ] 7.1 捕获诚实：计数缺失落 NULL/0、话题缺空数组、自有收藏内容缺正文留空——**绝不编造**。验证：`AC` 级断言无伪造字段。
- [ ] 7.2 账号隔离：召回严格按账号，跨账号不串味。验证：多账号语料下 `selectForCreation` 只返回本账号行。
- [ ] 7.3 非照抄：创作素材以蒸馏要点 + 护栏注入，不原文直灌；overlap guard（如启用）改写一次仍重叠则跳过。验证：复用/扩展 `valuable-comment-corpus` 的非照抄断言。
- [ ] 7.4 风控不动：本 change 不改任何风控阈值；收藏记录只发生在已过闸的真实收藏后。验证：`AC-RISK-*` 全过、grep 确认未改风控常量。
- [ ] 7.5（若动协议）`AC-PROTO-*`：两份 `protocol.ts` 不漂移。验证：Phase 1 零协议则计数不变两端一致；若加评论数字段则两端逐字同步全过。

## 8. cloud 全量回归（先 acceptance 再全量再 typecheck）

- [ ] 8.1 `cd ../aidcp-cloud && npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿。
- [ ] 8.2 中控：`openspec validate curated-inspiration-corpus --strict` 通过。

## 9. 部署（ECS 安全序列；执行前先做中控 §0 前置检查）

- [ ] 9.1 §0 前置：`ls -d ../aidcp-cloud` + 私钥 `~/codes/isales-4.pem` 存在且 `chmod 600`；缺失即停手告知。
- [ ] 9.2 ECS 先备份（`/opt/aidcp/cloud.bak.<ts>.tar.gz` + `.env.bak.<date>`）→ `rsync`（`--exclude .env --exclude node_modules --exclude .git`）→ DB 迁移（`curated_content` 建表，DDL `IF NOT EXISTS` 幂等）→ `systemctl restart aidcp-cloud.service`。**任何 ECS 操作绝不碰同机 isales。**
- [ ] 9.3 healthcheck：`active (running)` + 8787 监听 + 飞书长连接 + PG `select 1` + `curated_content` 表存在；失败即回滚。
- [ ] 9.4 真机观察：浏览跑一段后核 `curated_content` 是否按门槛纳入（赞藏/收藏/比率符合预期）、账号隔离、发帖创作素材确为精选语料蒸馏（真机验，参照昵称采集那次「3 个集成时序 bug 只有真机验才暴露」的教训）。

## Phase 2（评论并入精选层 + 边端评论赞数）

- [ ] 10.1 aidcp-cloud：把 `valuable-comment-store` 以 `content_type='comment'` 并入精选层（迁移或建桥）；写帖时把精选评论作为「角度线索」次级素材注入，写评论仍拉精选评论当口吻范例。验证：单测——`note`/`comment` 按用途分别召回。
- [ ] 10.2 aidcp-cloud：评论门槛接入精选门槛框架（按评论赞数 + 话题 + 已确认点赞）。验证：单测评论准入。
- [ ] 11.1 aidcp-edge：扩评论抽取以采「逐条评论赞数」（现 `comment-like-appraiser` 候选无赞数）；若上报需带赞数则两份 `src/comm/protocol.ts` 逐字同步 + `command-bridge.ts` + `docs/protocol.md`。验证：边端单测抽到赞数、`AC-PROTO-*` 不漂移。
- [ ] 11.2 （可选，Phase 1 即可搭车）把笔记「评论数」纳入 `note.detail` 上报 payload（`browse-session.ts:860-865` 现只带 like/collect；`note-extractor.ts:184` 已抽）。验证：上报带 `commentCount`、协议两端一致。

> <!-- 拆分预案：若 task 11.1 边端评论赞数抽取实测选择器校准风险超预期，Phase 2 整体下沉为 follow-up change（暂名 `curated-comments-fold-in`），Phase 1 已交付不受影响。 -->
