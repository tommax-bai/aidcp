## Context

云端是事件驱动多 Agent（`RoleDispatcher` 注册 15 角色 + 进程内 `EventBus` + `SessionContext`）。搜索现状：`feed.entered` 启动浏览闭环，`ContentEvaluator` 判这屏无价值并连刷达阈值后发 `search.needed` → `SearchEvaluator` 从 `soul.yaml` 的 6 个 `seed_keywords` 里挑一个未搜词 → `search.approved{keyword}` → `RoleDispatcher` 下发 `search`（command-bridge → `search.execute`）。

三个组件已实现但从未接线：
- `src/cache/concept-store.ts`：完整 CRUD + `loadPool()`/`addCandidate()`/`markSearched()`，PG `concepts` 表 DDL 幂等。从未 `new`。
- `src/risk/search-frequency-limiter.ts`：`canSearch()`/`explain()`/`recordSearch()`，每会话/每天上限。从未调用。
- `SearchExecutePayload.source`（`protocol.ts:239`）：字段已在协议里，`RoleDispatcher` 下发时只填 `{keyword}`，`source` 永远 undefined。

`note.detail.arrived`（`event-bus/types.ts` `NoteDetailData`，含 `title`/`content`）目前只被 `RoleDispatcher` 用来 `updateNoteData(currentNote)`，无任何概念抽取消费者。

约束：红线 MUST NOT 静默假成功；`SearchExecutePayload.source` 字段已存在 → 不改协议契约、不触发 `AC-PROTO-*` 漂移；复用 server 已有的 PG 连接口径与 LLM client；不破坏 v2 事件驱动主路径。

## Goals / Non-Goals

**Goals:**
- 浏览到的真实概念跨会话累积进 PG，驱动搜索关键词超出 6 个写死种子词。
- 搜索前经限频 + 预算两道闸，被拦时诚实 skip。
- `search.execute.source` 如实反映关键词来源（可观测）。

**Non-Goals:**
- 不动协议消息类型/数量（只填既有 `source` 字段，不新增消息）→ 不触发协议三处同步流程。
- 不改 edge（`search-handler.ts` 已打通）。
- 不做发帖触发器/配图/人审/回写——属后续 change `activate-publish-pipeline`。
- 不把搜索纳入 `RiskController`（`RISK_ACTIONS` 不含 `search`；搜索约束由 `SearchFrequencyLimiter` + budget 承担，与现有"浏览靠云端预算而非 RiskController 实时拦截"的边界一致）。

## Decisions

### D1：概念抽取用独立 `ConceptExtractorRole`，订阅 `note.detail.arrived`

新增 `src/agents/concept-extractor-role.ts`，注册进 `RoleDispatcher`，订阅 `note.detail.arrived`，对 `title+content` 跑一次 LLM 抽取（输出 0..N 个技术关键词），逐个 `ConceptStore.addCandidate(kw, sourceNote=title)`。

- **为何独立角色而非塞进 `ContentEvaluator`/`RoleDispatcher`**：抽取是旁路写入、不阻塞浏览闭环主路径（`ContentEvaluator` 判价值仍走原路）；独立角色便于脱浏览器单测（注入桩 LLM + 桩 ConceptStore）。
- **抽取失败/为空**：返回空数组即不写库（红线）。LLM 异常被 catch、记 warn、不影响主闭环。
- **去重**：靠 `addCandidate` 的 `ON CONFLICT (keyword) DO NOTHING`，无需角色内自行查重。
- **写入时机异步**：抽取是 fire-and-forget（`.catch` 记 warn），不进 await 主链路，避免拖慢逐动作下发。

**Alternative considered**：在 `interaction.occurred`（点赞后）才抽取——更"高信号"但漏掉未点赞但已深读的笔记，且点赞事件不带正文。决定以 `note.detail.arrived` 为主挂点；点赞内容的来源（`extract_from_liked`）留给发帖 change 的来源血缘，本 change 的 `source` 值以 `new_concept`/`random_from_interests` 为主。

### D2：`SearchEvaluator` 候选集 = `seed_keywords ∪ concept candidates`

`SearchEvaluator` 启动时从 `RoleDispatcher` 注入的概念池快照拿 candidates，与 `seed_keywords` 合并、去掉 `known`/本会话已搜，作为 LLM 可选集。`source` 由所选词的归属决定（candidate→`new_concept`；seed→`random_from_interests`）。

- **概念池如何到达 `SearchEvaluator`**：`RoleDispatcher.startSession()` 时 `await ConceptStore.loadPool()` 得到 `ConceptPool{known,candidates,source}`，注入 `SearchEvaluator`（构造或 setter）。PG 不可用时 `loadPool` 失败 → 回退到「仅 `seed_keywords`」（与现状等价，降级不崩）。

### D3：搜索前闸串在 `RoleDispatcher` 的 `search.approved` 订阅里

现状 `role-dispatcher.ts` 在 `search.approved` 回调里直接 `consumeBudget('search')` + `sendCommand`。改为：先过 `SearchFrequencyLimiter.canSearch(keyword)` 与 `budget.searches > 0`，两者皆通过才 `recordSearch` + `consumeBudget` + `sendCommand` + `markSearched`；否则记被拦原因、不下发。

- **为何放在 `RoleDispatcher` 而非 `SearchEvaluator`**：budget 与 limiter 都是 dispatcher 持有的会话级状态；`SearchEvaluator` 负责"挑词"，dispatcher 负责"放不放行 + 记账"，职责清晰。
- **`SearchFrequencyLimiter` 生命周期**：dispatcher 持有单例，`startSession`/`resetSession` 清会话计数；每天上限靠内部 `dailyRecords` 滑窗。

### D4：只填既有 `source` 字段，不碰协议契约

`SearchExecutePayload.source` 已在两份 `protocol.ts` 定义且类型一致，本 change 仅在 cloud 下发时填值。不新增/删除消息类型 → `MessageType` 穷举不变 → 不触发 `AC-PROTO-*`。

## Risks / Trade-offs

- **[LLM 抽取噪音：抽出非技术/低质关键词污染概念池]** → 抽取 prompt 限定"技术概念名词、人设相关领域"，且概念池只是 `SearchEvaluator` 的*候选*、最终仍由 LLM 挑词把关；后续可加人工/规则过滤，本 change 不做。
- **[PG 不可用导致概念池为空]** → `loadPool` 失败回退「仅 seed_keywords」，与现状等价，不崩闭环；`addCandidate` 失败 `.catch` 记 warn。
- **[每会话/每天限频值设置不当导致搜索过少或过多]** → `SearchFrequencyLimiter` 默认 `maxPerSession=1`/`maxPerDay=3` 偏保守；通过构造参数可调，先按默认上线观察。
- **[与 `skip-profile-visit-if-followed`（未开工，动 role-dispatcher）撞 search.approved 区域]** → 该 change 改的是 profile/互动分支，search 分支不重叠；若并行实装，先合先 rebase，冲突面仅在文件级非函数级。
- **[抽取是 fire-and-forget，本会话刚抽的概念本会话搜不到]** → 可接受：概念跨会话累积，下次会话 `loadPool` 即可见；强一致非目标。

## Migration Plan

1. cloud 本地：新增/接线后 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全过（重点新增 `AC-SEARCH-*` 验收）。
2. 概念表：`ConceptStore.init()` 在启动幂等建表，无需手工 migration；ECS PG `aidcp` 库首次启动自动建 `concepts`。
3. 部署走标准安全序列（备份→rsync→restart→healthcheck→失败回滚），见 `docs/handoff` 与 `deployment-ecs.md`。
4. 回滚：本 change 不改协议、不改 edge，回滚 cloud 即可；`concepts` 表残留无副作用（旧代码不读）。

## Open Questions

- 抽取关键词的粒度与数量上限（每篇笔记抽几个）——倾向 prompt 里限 1-3 个高置信概念，实装时定。
- `SearchFrequencyLimiter` 的 `maxPerSession`/`maxPerDay` 是否要随风控 `tempo`/状态联动——本 change 先用静态默认，联动留后续。
