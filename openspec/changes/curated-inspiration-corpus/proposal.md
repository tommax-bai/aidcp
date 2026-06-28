## Why

「记录创作灵感」目前是一套**多源采集 → 各自落库 → 按发布窗口聚合 → 注入创作**的机制，逐处核对后发现「记得多、用得少、还把已有的好信号扔掉」。三个核心事实（均已坐实现状）：

1. **点赞素材是空壳**：真实点赞落库时只传了笔记标识、从不传详情（`aidcp-cloud/src/server.ts:544` `recordLike(evt.noteId)`），且上游互动事件本身也只带标识不带详情（`aidcp-cloud/src/comm/handler.ts:277-286`）。于是喂给创作的「可引用真实细节」实际渲染成空行（`prompts.ts` 的点赞素材块），对成文几乎零信息量——只剩点赞计数与 id 血缘有用。
2. **收藏完全不进灵感**：灵感写入只在 `like` 时触发（`server.ts:544` 只判 `action==='like'`）；而收藏在小红书语义上恰恰是「留作参考的好素材」，是比点赞更强的素材意图信号。最该当素材的动作被漏在外面。
3. **共鸣信号一个没存**：边端在每篇笔记详情已抽取了全文正文、点赞数、收藏数、评论数（`aidcp-edge/src/browse/note-extractor.ts:17-33`），并已把全文＋点赞数＋收藏数发到云端（`aidcp-edge/src/browse/browse-session.ts:860-865`）；但云端只把标题＋链接写进了面板展示旁表（`server.ts:588-594`→`interaction-feed-store.ts`），正文与赞藏数据在落库前被丢弃。

此外，创作消费侧把「来源笔记标题」在查询/映射两处丢掉、概念只以裸关键词进 prompt（`concept-store.ts` 的 `getNewConceptsSince` 只 `SELECT keyword`）；灵感按「上次发布」时间窗滚动召回，窗口外的历史素材虽在库里却召回不到；概念表/点赞表都没有账号维度，多账号素材全局混用。

结论：**该记录的内容信号（正文）几乎没记、共鸣信号（赞藏数/比率）完全没记、最强的素材动作（收藏）不触发记录**。本 change 不去逐个打补丁，而是按一套清晰的**三层模型**收口创作灵感的记录与消费。

## What Changes

> 本 change 引入**一个新 capability `curated-inspiration-corpus`（精选创作灵感语料）**，并把发帖创作的「正向素材来源」从「空壳点赞素材＋裸概念」切换到该语料。下面两层（行为账本）**复用现有实现、不重建**。

**三层模型（其中两层已存在，只新建最上层）：**

- **浏览记录层（复用，不新建）**：「看到笔记就写标题＋链接」的面板展示旁表已存在（`interaction-feed-store.ts` 的 `interaction_target_meta`，写入在 `server.ts:588-594`），覆盖「所有看过的笔记」。它薄、面向后台展示、与风控/去重解耦——本 change **不改它的职责**，仅把它认定为「浏览记录层」。
- **互动内容层（复用，不新建）**：点赞/收藏/评论/关注事件账本（`interaction_feed`）＋风控去重台账（`risk_interactions`）＋点赞来源血缘表（`liked_notes`）已存在，合为「互动/拟人/血缘层」。本 change **不改它们的职责**。
- **精选内容层（新建，本 change 主体）**：新表收口「过门槛的高价值笔记」的**详细信息**（全文＋赞藏数＋机器人自有动作标记＋话题＋账号），作为发帖创作的**正向素材唯一来源**。评论作为同层的另一类型，分期并入。

**精选层的关键行为：**

- **观测捕获**：在笔记详情到达云端时（详情已带全文＋赞藏数），按门槛判定是否纳入精选；纳入则落详细行，不纳入则只留薄的行为记录、详情丢弃（精选表天然小、压住 PII）。计数为**采集时刻快照**（带 `counts_captured_at`），缺失诚实置空、绝不编造。
- **准入门槛（可配置、按账号）**：共鸣门槛 ∪ 机器人自有收藏，且**叠加相关性门槛**（与账号兴趣/话题匹配）。共鸣门槛默认为「收藏数 ≥ 阈值」或「收藏/点赞比率 ≥ 阈值且点赞数 ≥ 地板（防小样本噪声）」；机器人自己收藏的**免共鸣门槛直接纳入**（收藏本身已是受风控约束的策展判断）；单独点赞为弱信号、不足以单独纳入。阈值不写死、做成可配置。
- **机器人自有动作分级标记**：每篇精选行带「点赞/收藏」**双标记**（可组合，"两者"＝都为真）；重复动作**合并补标记**而非忽略。收藏＞点赞的强度差用于选材加权。
- **账号隔离**：精选行带账号维度，召回按账号过滤，**绝不跨账号串味取材**。
- **有界增长＋PII 姿态**：保留上限（按账号 newest N）淘汰最旧，明示他人正文/作者的保留/脱敏姿态（对齐已有评论语料库 `valuable-comment-corpus` 的做法）。
- **创作消费**：发帖创作的正向素材改从精选语料按「自有动作分级 × 共鸣 × 新鲜度 × 相关性」加权选取 top-K，并以**蒸馏要点**注入、套「仅作灵感、严禁照抄」护栏（复用评论语料的非照抄红线），**收藏档优先但不饿死点赞档**。话题/概念雷达（驱动「该不该发」）与避免撞题（自己发过的帖）**仍各走各线、不并入精选表**。
- **评论并入（分期）**：精选层用**类型标记**统一笔记与评论；Phase 1 落「笔记」类型并接通发帖创作，Phase 2 把现有评论语料以「评论」类型并入、并补「评论逐条赞数」的边端抽取（当前未抓，`comment-like-appraiser` 候选只带正文/作者/已赞态）。**取数仍按用途分**：写帖拉精选笔记（＋评论当角度线索），写评论拉精选评论当口吻范例。

> 兼容性：本 change **不删除** `liked_notes`（仍作点赞来源血缘）、**不改** `concepts` / `valuable_comments` 的现有职责。它是**新增正向素材来源 + 创作消费切换**，旧表语义不破。发帖创作的素材来源由「空壳点赞 + 裸概念」切到「精选语料」，属创作输入的 BREAKING 切换（产出风格会变好、不改是否发布/人审/风控判定）。

## Capabilities

### New `curated-inspiration-corpus`

- `curated-inspiration-corpus`：精选创作灵感语料层——观测捕获（详情到达时按门槛纳入、计数快照诚实、不编造）、可配置按账号的准入门槛（共鸣 ∪ 自有收藏，叠加相关性；收藏免共鸣门槛、点赞为弱信号）、机器人自有动作双标记（合并补标记、收藏＞点赞）、账号隔离召回、有界增长＋PII 姿态、创作消费（正向素材唯一来源、加权选取、仅作灵感不照抄、收藏档优先不饿死点赞档）、评论以类型标记分期并入。话题雷达与避免撞题不并入本层。

### Modified Capabilities

<!-- 不修改任何已合并 capability 的 requirement。发帖创作「素材来源」的切换通过本新 capability 的「创作消费」requirement 表达；publish-pipeline 当前仍是跨多个 active change 的 delta、尚未并入 openspec/specs，故本 change 不写 publish-pipeline 的 MODIFIED delta，creation 侧改动落 cloud 代码、契约归本新 capability。复用 valuable-comment-corpus 的「非照抄参考」红线（机制不变，仅扩展到笔记素材），不列为 modified。note-extraction-fidelity（边端正文/计数抽取）已就绪、仅复用，不改。 -->

## Impact

- **aidcp-cloud（主体）**
  - 新增 `src/cache/curated-content-store.ts`（`curated_content` 表 DDL `IF NOT EXISTS` 幂等；upsert-by-(account,type,source) 合并标记；按账号 + 话题召回；保留上限淘汰最旧——仿 `valuable-comment-store.ts` 风格）。
  - 新增 `src/agents/curated-content-gatekeeper.ts`（或等价决策口）：详情到达时判定准入（共鸣 ∪ 自有收藏，叠加相关性；阈值取配置）。
  - 改 `src/server.ts`：在 `note.detail.arrived` 订阅（现 `:588-594` 只补展示旁表）旁挂精选捕获——过门槛则写 `curated_content`（含全文＋赞藏数＋话题＋采集时刻）；在 `interaction.occurred` 订阅（现 `:543-548`）把 `like`/`collect` 合并为该笔记精选行的双标记，收藏触发自有收藏自动纳入（用同一访问内已观测的笔记内容）。
  - 改 `src/publish-agent/publish-scheduler.ts`：`buildTriggerInput` 的正向素材从 `likedStore.recentSince` 切到精选语料按账号加权选取 top-K（`generateInput.likedContents`/新增素材字段）；概念注入补回来源标题（顺带修 `concept-store.ts` 的 `getNewConceptsSince` 丢 `source_note`）。
  - 改 `src/publish-agent/prompts.ts`：素材块由精选语料蒸馏要点渲染、套「仅作灵感、严禁照抄」护栏；保留避免撞题块（来自发布台账，不变）。
  - 新增/扩 配置：精选门槛阈值（收藏地板 / 比率阈值 / 比率地板 / 相关性最小重叠 / 保留上限）可配置，缺省内置、可按账号覆盖（接入既有按账号配置口）。
  - （Phase 2）把 `valuable-comment-store` 以「评论」类型并入精选层或建桥；写帖时把精选评论作为角度线索。

- **aidcp-edge（仅 Phase 2 触及）**
  - Phase 1 **零改动**（笔记全文＋赞藏数已在现有上报里）。
  - Phase 2：扩评论抽取以采「逐条评论赞数」（当前 `comment-like-appraiser` 候选只带正文/作者/已赞态，无赞数）；若上报需带评论赞数则协议两份 `protocol.ts` 逐字同步。
  - 可选：把笔记「评论数」纳入上报 payload（`browse-session.ts:860-865` 现只带 like/collect 数，`note-extractor.ts:184` 已抽 comments 数）——小改，供门槛/记录用，非必需。

- **协议**
  - Phase 1 大概率**零协议改动**（笔记全文＋赞藏数已在现有 `note.detail` 上报）。如把「评论数」纳入笔记上报或 Phase 2 评论赞数上报，MUST 两份 `src/comm/protocol.ts` 逐字一致 + `command-bridge.ts` 映射 + `docs/protocol.md` 同步，漂移由 `Record<MessageType,true>` 穷举与 `AC-PROTO-*` 守护。

- **DB（ECS PostgreSQL 库 `aidcp`）**
  - 新表 `curated_content`（精选灵感语料；带 `account_id`、`content_type`、保留上限）。DDL `IF NOT EXISTS` 幂等。
  - 不改 `liked_notes` / `concepts` / `valuable_comments` / `interaction_feed` 现有表结构（仅 `concept-store` 查询补取 `source_note`，非 DDL 改动）。
  - 不记敏感值，仅在 tasks/部署文档记 DDL 与服务位置；精选表存他人正文/作者，明示保留上限＋脱敏姿态。

- **依赖与红线**
  - 复用 `valuable-comment-corpus` 的「仅作灵感、严禁照抄」非照抄护栏（扩展到笔记素材）。
  - 复用边端正文/计数抽取（`note-extraction-fidelity`，不改）。
  - 安全红线仍全过：`AC-PROTO-*`（两份 protocol.ts 不漂移，若动协议）、不静默假成功 / 不编造（计数缺失诚实置空、无来源如实空）、账号隔离不串味、创作素材不照抄。
  - **风控不动**：收藏已比点赞更严（单场上限更低、冷却更长、同笔记去重），本 change 只「记录已发生且已过闸的收藏」，不改任何风控阈值、不增加收藏频率。

> 拆分说明：Phase 1（笔记精选语料 + 观测捕获 + 门槛 + 双标记 + 账号隔离 + 保留上限 + 发帖创作消费切换）为一体，互为前提，纯 cloud、零边端、大概率零协议改动，可独立交付与验证。Phase 2（评论并入精选层 + 边端评论赞数抽取）依赖 Phase 1 的语料表与类型标记，作为本 change 的第二批 task（或必要时分拆为 follow-up change）。当前默认 Phase 1 先行、Phase 2 紧随。
