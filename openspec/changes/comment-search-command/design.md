# Design — comment-search-command（飞书 /comment：搜索驱动的按需评论任务）

> cloud = `../aidcp-cloud`，edge = `../aidcp-edge`，console = `../aidcp-console`。行号截至 2026-06-30，以符号/上下文为准。

## Context

现状（勘察坐实）：

- **评论只在自治浏览闭环里被动发生**。评论支线挂在 `interaction.completed`（仅在真 like/collect 后），由 `CommentAppraiser`（硬阈值赞>1000 且 藏>300 + 预算/冷却 + LLM）→ `CommentComposer` → `CommentDeAiFlavor` → `CommentApprovalGate`（飞书人审）→ 调度器 `comment.approved` → 边端 `executeComment`。整条只在「正打开的那篇笔记」上跑，无「从外面指定词/笔记」的命令入口（`comment-interaction` spec 现状）。
- **搜索已端到端但只自治**。`SearchScroller` 连续空刷到阈值 → `SearchEvaluator`（从 `seed_keywords ∪ 概念池` 挑**一个**词、不读精选集）→ 调度器过限频+预算闸 → 边端 `executeSearch`（只输入关键词+回车）→ 结果卡片由 `ContentEvaluator` 按标题匹配挑一篇。**边端不点排序标签（综合/最新/最多点赞/最多收藏/最多评论）、不点时间筛选（一天内/一周内）**；结果卡片 `collectCount` 在 `reportVisibleCards` 里**硬编码 0**、无发布时间。
- **精选集**（`curated_content`，按账号）现仅喂发帖创作（`PublishScheduler.buildTriggerInput` 取 `selectForCreation('note'|'comment',N)`）。
- **按需任务有成熟范式**：`/publish` → `CommandRouter` → `CommandActions.publish` → `PublishScheduler.triggerManual` → 发布编排（黑板/时序器）；边端独占由 `onPublishTakeoverStart/End`（结束自动浏览会话标记不可恢复 → 干活 → `finally` 恢复）实现，按账号串行、边端离线 honest-fail。
- **去重已有底座**：`risk_interactions`（主键 `account_id, note_id, action`，`action ∈ like/collect/comment`），`InteractionDedup.hasInteracted(noteId,'comment')` / `recordInteraction(...)` 现成、按账号。
- **角色配置数据驱动**：角色登记进 `ROLE_CATALOG` 即在后台「角色管理」自动可配；**未登记则运行时 `categoryOf` 返 undefined、回落全局默认模型**（`curated-admission-eval-roles` 真机踩过）。

约束：协议 v2 四处同步红线；边轻云重、状态单写；红线「绝不静默假成功」；每步压在边端约 30s 单步超时内（发布拟人化两次踩坑）；账号隔离 PII 红线。

## Goals / Non-Goals

**Goals:**
- 飞书 `/comment <昵称>` 一句触发，按账号人设 + 精选集生成搜索词，搜小红书并按「最近一天 + 最多收藏」原生筛选，避开已评过的，挑一篇人设相关的，读正文与现场评论后生成一条评论，经飞书人审发出。
- 复用既有撰写→去AI味→人审→发布尾链与协议、风控配额；只新增必要的命令、编排、两个角色、搜索原生筛选与收藏数采集。
- 两个新角色在后台「角色管理」可配模型/温度。

**Non-Goals:**
- 不改自治浏览闭环的搜索/评论行为（命令路径是另一条受控流程）。
- 不做多篇批量评论（每次一篇）；不做无人审自动直发；不引入跨账号合并读（守 PII 红线）。
- 不在本 change 解决 XHS 状态迁移接真实封号信号等既有缺口。

## Decisions

### D1. 受控独占编排，仿发布、不挂自治浏览
`/comment` 是按需、单次、有方向、需独占边端的流程；自治浏览闭环是事件驱动、自选词/笔记、无命令入口。**新建 `src/comment-agent/`**（`CommentScheduler.triggerManual` + 一个有方向的步骤时序器），边端独占复用接管/恢复钩子（新增 `onCommentTakeoverStart/End`，reason `comment_takeover`，仿 `onPublishTakeoverStart/End`），按账号串行（accountTail）、边端离线 honest-fail。
- 备选：把意图注入正在跑的自治会话——否决：自治会话无「外部指定词/笔记」入口，且会与自身 scroll/search/comment 命令在同一边端 FIFO 队列交错、污染导航态。

### D2. 两个新角色（判定类），不复用 content_evaluator
- **角色①·搜索词生成**：输入 `getSoul`（identity + interests）+ `curatedStore.selectForCreation('note'|'comment',N)`（高收藏标题/主题）；输出一小批搜索词（结构化 JSON 数组）。精选集稀疏 → 退回 `seed_keywords`，不编造。现有 `SearchEvaluator` 只从固定池挑**一个**、不读精选集，故新建。
- **角色②·搜索笔记甄选**：输入「去重后的候选卡片（带收藏数）+ 人设」；判定**人设强相关**（不是沾边/泛泛相关），只在强相关候选里挑收藏最高的一篇；当前词无强相关 → 该词无果（触发 D8 换词）。现有 `ContentEvaluator` 为自治会话设计、按标题匹配、且 `collectCount` 现恒 0，不复用。
- 两角色均判定类（`browse_judge`、低温度、严格 JSON），登记进 `ROLE_CATALOG`。
- 备选：合成一个「生成+甄选」角色——否决：两步输入/时机不同（生成在搜索前、甄选在拿到候选后），拆开各自可在后台单配、单测。

### D3. 「最近一天 + 最多收藏」用平台原生筛选 + 排序，收藏数随卡片回传（已与用户拍板）
- 边端搜索后**驱动原生「最多收藏」排序标签 +「一天内」时间筛选**控件，再采卡片。时间窗用原生（发布时间难从卡片可靠抓）、排序用原生（直接拿排好序结果），云端只取前 N 做相关性甄选。
- **采每卡真实收藏数**回传（修 `reportVisibleCards` 的硬编码 0），供云端在相关候选里择「最多收藏」。
- 协议增量：搜索指令加排序/时间参数（如 `sort` / `timeWindow`）、结果卡片加 `collectCount`；按 v2 四处同步。
- 备选：纯云端排序（边端抓收藏数+发布时间，云端过滤≤24h）——否决：卡片上发布时间不稳定可抓；原生筛选更贴用户描述、数据更干净。代价=筛选控件选择器脆、需真机标定。
- **诚实红线**：筛选控件定位失败 → 报筛选未生效/降级，**不**把「综合/无时间窗」结果冒充「最近一天最多收藏」。

### D4. 去重在择优之前，复用每笔记去重
拿到候选卡片后**先**滤掉本账号 `hasInteracted(noteId,'comment')==true` 的笔记，**再**交角色②甄选——避免在已评过的笔记上浪费一次模型判定，也避免重复打扰同一篇。发布成功后 `recordInteraction(noteId,'comment')` 供下次去重。按账号隔离。

### D5. 撰写复用、小改为读现场评论
复用 `CommentComposer`→`CommentDeAiFlavor`→`CommentApprovalGate`→`executeComment`。唯一改动：`CommentComposer.buildPrompt` 增加**可选「现场评论」输入**（现状只看标题+正文+精选参考）。现场评论采集已有（`scroll_comments` → `harvestCommentCandidates` 产 `CommentCandidate{author,text,likeCount}`），命令编排在开笔记后先翻一屏评论再撰写。自治闭环的撰写是否也吃这个可选输入留作实现细节、不强制。

### D6. 门槛取舍：跳过自动硬阈值，保留人审 + 配额
命令路径**不经** `CommentAppraiser` 的硬数值阈值（赞>1000 且 藏>300）与「是否值得」LLM——用户已手动指定意图、相关性由角色②把关。但**保留**飞书人工审核闸（`AC-PUB`：未授权/超时不发）、**仍过** `riskController.canDo('comment')` 且**计入**按天评论配额（被拒诚实跳过）。

### D7. 两段式回执 + 账号隔离 + 诚实红线
飞书回执两段：命令同步回「已触发/honest-fail（昵称无匹配、边端离线）」；评论经人审发出后再补结果卡片（仿发布异步）。人设/精选集/去重/落评论/落精选全按命令解析到的账号，**不跨账号**。任一步（搜索、筛选、开笔记、撰写、发布）失败 → honest-fail，绝不静默假成功。

### D8. 强相关 + 找不到就换搜索词（有界重试，用户拍板）
甄选要的是**强相关**，不是沾边即可。所以编排不是「搜一个词→挑一篇→挑不到就结束」，而是**逐词尝试**：角色①产出**有序多词**，编排对当前词跑〔搜索（原生筛选）→采列表→去重→甄选〕；得到强相关未评过的一篇即**停下评论、不再试余下词**；当前词无强相关 → **换下一个词**重试。
- **有界**：设尝试上限（试到第 K 个词为止，可配），并受 `SearchFrequencyLimiter`（每词每会话/每天）+ 搜索预算约束——不无限换词刷搜索（既省成本也不像 bot）。**首中即止**。
- **用尽诚实结束**：所有词试完或达上限仍无强相关合格候选 → 本次不评、honest 回执，绝不在弱相关里凑一篇。
- 备选：单次搜索挑不到就结束——否决：强相关门槛下单词常空手，换词重试才能在「严格相关」与「有产出」间取得平衡。

## Prompt 与输出契约

- **搜索词生成**：给「账号身份 + 兴趣领域（人设 interests）+ 精选集高收藏标题/主题样本」→ 严格 JSON `{terms: string[], source: 'persona'|'curated'|'mixed'}`；精选稀疏则基于种子词，`terms` 非空且贴合领域；解析失败/空 → 诚实回退种子词或不出词（不编造）。
- **搜索笔记甄选**：给「账号领域 + 候选卡片列表（标题/作者/收藏数，已去重）」→ 严格 JSON `{pickIndex: number|null, stronglyRelevantIndexes: number[], reason}`；判**强相关**（沾边/泛泛相关不算），只在强相关候选里挑收藏最高者；无强相关候选 → `pickIndex=null`（触发换下一个搜索词；词用尽再诚实结束，不强评弱相关笔记）。
- 解析失败/缺字段 → 诚实判无可评（绝不默认挑一篇）。

## 时序与竞态

- 任务全程独占边端：开跑前结束自动浏览会话（标记不可恢复），`finally` 恢复——恢复重过所有闸（排程/人设/活跃窗/配额/风控）。
- 每个云端步骤（搜索、采列表、开笔记、翻评论、发评论）压在边端约 30s 单步超时内；拟人停顿走云端中心值下发。
- 人审等待期间会话进「等评论审批」暂停态（看门狗按有意暂停、不 idle 杀；复用既有评论审批暂停通道）。
- 同账号已有发布接管/另一评论任务 → accountTail 串行，不并发抢边端。

## Risks / Trade-offs

| 风险 | 级别 | 缓解 |
| --- | --- | --- |
| 边端原生筛选控件选择器随宽窄屏布局变（最大不确定性） | 高 | 双布局选择器 + 后置校验「确实切到最多收藏/一天内」；未生效 honest 报降级、不冒充；真机标定（参 [[xhs-responsive-nav-layout]]） |
| 卡片收藏数采不到 | 中 | 采不到→该卡收藏数缺省/置空、不编造；甄选退化为原生排序顺序取前者 |
| 精选集稀疏（生产近乎空）→ 搜索词无源 | 中 | 退回人设 `seed_keywords` 兜底（设计已含） |
| 强相关门槛 + 换词重试烧搜索配额 / 像 bot | 中 | 尝试上限 K（可配）+ 复用 `SearchFrequencyLimiter`（每词每会话/每天）+ 搜索预算 + 首中即止；用尽诚实结束 |
| 强相关过严 → 多数运行空手不评 | 中 | 强相关严格度真机标定；换词重试拉高产出率；空手是诚实结果、非 bug |
| 每步超 30s 边端超时 | 中 | 拟人延迟压云端中心值；分步小化；参发布拟人两次踩坑 |
| 新角色未登记目录→回落默认模型「判得不对」 | 中 | 登记进 `ROLE_CATALOG`（判定类）；后台可见即对（`curated-admission-eval-roles` 6.1 教训） |
| 命令路径误绕人审/风控 | 高（红线） | 保留 `CommentApprovalGate` + `canDo('comment')` + 配额；`AC-PUB`/`AC-RISK` 全过 |
| 与自治浏览/通知巡视抢边端 | 中 | accountTail 串行 + 接管/恢复钩子；honest-fail 若边端离线 |

## Migration Plan

- 纯增量：新命令/角色/编排 + 可选协议字段；无新表（复用 `curated_content`、`risk_interactions`）、无破坏。
- 上线序列：cloud 先（命令+编排+2角色+撰写小改+去重+协议 cloud 侧）→ edge（原生筛选+收藏数+协议 edge 侧逐字一致）。协议增量须 cloud+edge 同版，故 edge 未更新前命令对「原生筛选/收藏数」honest 降级、不报错。
- 回滚：命令未启用即无副作用；协议字段为可选、旧 edge 忽略不崩。按 ECS 安全序列（备份→同步→restart→healthcheck→失败回滚），git archive committed-only 绕并发 WIP。

## Open Questions

- 搜索词条数 / 每词取多少结果 / 候选池大小 / 换词尝试上限 K 的缺省值 → 实现期定，可配。
- 角色②「人设强相关」的判定严格度（已定方向=强相关、宁缺毋滥）的具体松紧 → 真机标定。
- 是否把被评论的笔记正文/现场评论也写入 `curated_content`（复用既有捕获路径）→ 设计列为可选，默认开（与既有精选捕获一致）。
- 原生「最多收藏 + 一天内」在当前真机布局是否稳定可点 → 真机先验证再依赖（最大未知）。
