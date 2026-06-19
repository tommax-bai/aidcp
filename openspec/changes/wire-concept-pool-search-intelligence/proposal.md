## Why

搜索链路能触发、能执行，但智能含量低：关键词只来自 `soul.yaml` 的 6 个写死种子词，搜完即 skip；`ConceptStore`、`concepts` 表、`SearchFrequencyLimiter` 均为死代码（只定义、无 `new`、无调用）。浏览/点赞看到的真实技术概念喂不回搜索，账号永远在同 6 个词里打转，搜索次数也无真实上限。本变更把"浏览→学概念→驱动搜索"接成闭环，是搜索智能化、也是后续发帖来源血缘的共用脊柱。

## What Changes

- 实例化并接线已有的 `ConceptStore`（PG `concepts` 表跨会话记忆），启动时建表（幂等）+ `loadPool()` 载入候选/已知概念。
- 新增 `ConceptExtractorRole`：订阅 `note.detail.arrived`（含真实 title/content），用 LLM 抽取技术关键词写入 `ConceptStore.addCandidate`。**红线**：抽不到就不写，绝不编造关键词凑数。
- `SearchEvaluator` 候选集从「仅 `seed_keywords`」扩为「`seed_keywords ∪ 概念池 candidates`」，并如实填充 `SearchExecutePayload.source`（来源策略：`new_concept` / `random_from_interests` / `extract_from_liked`）。
- 接线 `SearchFrequencyLimiter` 作为**搜索前闸**，并让 `budget.searches` 真正拦截：配额/限频不通过则诚实 `skip`（不下发、不扣 budget），**绝不静默假成功**。
- 下发搜索后调用 `ConceptStore.markSearched`，使该词不再被重复搜。

## Capabilities

### New Capabilities
- `concept-pool-search`: 概念池驱动的搜索智能——从浏览内容学习关键词、跨会话记忆、搜索前限频闸、来源如实回报。

### Modified Capabilities
<!-- 无：现有 7 个 spec 均不涉及搜索/概念池，本变更不修改既有 spec 的需求。 -->

## Impact

- **aidcp-cloud**（master）：
  - `src/cache/concept-store.ts`（已存在，接线 + 启动 `init`/`loadPool`）
  - 新增 `src/agents/concept-extractor-role.ts`（订阅 `note.detail.arrived`）
  - `src/agents/search-evaluator.ts`（候选集纳入概念池 + 填 `source`）
  - `src/orchestrator/role-dispatcher.ts`（search 分支：接 `SearchFrequencyLimiter` 闸 + `markSearched`；启动载入概念池）
  - `src/risk/search-frequency-limiter.ts`（已存在，接线为搜索前闸）
  - `src/comm/protocol.ts` 的 `SearchExecutePayload.source` 由 SearchEvaluator 真实填充（字段已存在，不改协议契约 → 不触发 `AC-PROTO-*` 漂移）
- **aidcp-edge**：无改动（搜索执行 `search-handler.ts` 已打通）。
- **数据**：PG `aidcp` 库新增/启用 `concepts` 表（DDL 幂等，已在 `concept-store.ts`）。
- **依赖**：复用现有 LLM client、PG 连接口径（`PGHOST/PGPORT/...`，与 `PgRiskStore`/`PgAnchorCache` 一致）。
- **WIP 冲突**：与 4 个已部署 change 无实质冲突；唯一未开工的 `skip-profile-visit-if-followed` 动 `role-dispatcher.ts` 的互动/profile 分支，与本变更的 search 分支不重叠。
- **不在本变更范围**：发帖链路（触发器/配图/人审/回写）属后续 change `activate-publish-pipeline`，其概念阈值扳机与来源血缘依赖本变更先落地。
