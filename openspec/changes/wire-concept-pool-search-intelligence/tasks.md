# Tasks — wire-concept-pool-search-intelligence

> 代码改动落 aidcp-cloud（master）。回写格式：`<!-- <repo> <commit-sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`。

## 1. aidcp-cloud — ConceptStore 接线（持久化脊柱）

- [x] 1.1 在 `server.ts` 实例化 `ConceptStore`（复用 `PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD` 连接口径，与 `PgRiskStore`/`PgAnchorCache` 一致），启动时 `await conceptStore.init()` 幂等建表；PG 不可用则 catch 记 warn 并降级（loadPool 返回空池）<!-- aidcp-cloud 4cd944e init 失败留 conceptStore=undefined → 不注册抽取角色 -->
- [x] 1.2 将 `ConceptStore` 注入 `RoleDispatcher`（构造参数），在 `startSession()` 中 `await loadPool()` 得到 `ConceptPool` 快照供 `SearchEvaluator` 使用；loadPool 失败回退「仅 seed_keywords」不崩闭环<!-- aidcp-cloud 4cd944e refreshConceptPool() fire-and-forget，restartSession 同步刷新 -->

## 2. aidcp-cloud — ConceptExtractorRole（从浏览学概念）

- [x] 2.1 新增 `src/agents/concept-extractor-role.ts`：订阅 `note.detail.arrived`，对 `title+content` 跑 LLM 抽取 1-3 个高置信技术概念关键词（prompt 限定技术名词 + 人设领域）；抽不到返回空数组<!-- aidcp-cloud 4cd944e maxKeywords 默认 3，parseKeywords 去重截断 -->
- [x] 2.2 抽到的每个关键词 `await conceptStore.addCandidate(kw, sourceNote=title)`（去重靠 `ON CONFLICT DO NOTHING`）；整个抽取为 fire-and-forget（`.catch` 记 warn），不阻塞浏览主闭环<!-- aidcp-cloud 4cd944e subscribe 内 void this.onNoteDetailArrived -->
- [x] 2.3 红线断言：抽取结果为空时不写任何行、不产生占位/编造关键词（对应 spec「抽不到概念时不写库」）<!-- aidcp-cloud 4cd944e keywords.length===0 直接 return；AC-SEARCH 无对应反例（抽取走单测路径）。LLM 异常亦不写库 -->
- [x] 2.4 在 `RoleDispatcher.setup()` 注册 `ConceptExtractorRole`（注入 llm + conceptStore）<!-- aidcp-cloud 4cd944e 仅 conceptStore 存在时 push，避免 PG 缺失时空跑 -->

## 3. aidcp-cloud — SearchEvaluator 吃概念池 + 填 source

- [x] 3.1 `search-evaluator.ts`：候选集由「仅 `seed_keywords`」改为「`seed_keywords ∪ 概念池 candidates`」，去掉 `known`/本会话已搜词；并集为空时诚实 skip（不编造）<!-- aidcp-cloud 4cd944e computeKeywordSets()，空集短路 emit search.skipped(no_available_keywords) 不调 LLM -->
- [x] 3.2 `search.approved` 携带所选关键词的来源归属（candidate→`new_concept`；seed→`random_from_interests`），供 RoleDispatcher 填 `SearchExecutePayload.source`<!-- aidcp-cloud 4cd944e attributeSource()；SearchApprovedPayload 加 source 字段 -->
- [x] 3.3 注入概念池快照的通道（构造或 setter），由 `RoleDispatcher.startSession` 的 `loadPool()` 结果喂入<!-- aidcp-cloud 4cd944e getConceptPool: () => this.conceptPool（可选，默认空池保兼容旧测试） -->

## 4. aidcp-cloud — 搜索前限频闸 + budget 真拦截

- [x] 4.1 在 `server.ts`/`RoleDispatcher` 实例化 `SearchFrequencyLimiter`（默认 maxPerSession/maxPerDay，dispatcher 持有单例，`startSession`/`resetSession` 清会话计数）<!-- aidcp-cloud 4cd944e dispatcher 内 new SearchFrequencyLimiter(opts)，start/restart 调 resetSession -->
- [x] 4.2 改 `role-dispatcher.ts` 的 `search.approved` 订阅：下发前先过 `SearchFrequencyLimiter.canSearch(keyword)` 与 `budget.searches > 0`；两道皆通过才 `recordSearch` + `consumeBudget('search')` + `sendCommand`（填 `source`）+ `conceptStore.markSearched(keyword)`<!-- aidcp-cloud 4cd944e markSearched fire-and-forget -->
- [x] 4.3 被拦时诚实 skip：不下发 `search.execute`、不扣 budget、不 markSearched，记被拦原因（`session_limit`/`daily_limit`/`budget_exhausted`）。红线：绝不静默回报成功<!-- aidcp-cloud 4cd944e AC-SEARCH-06/07 守护 -->

## 5. 验收与回归（安全红线必须全过）

- [x] 5.1 新增 `AC-SEARCH-*` 验收：关键词来自概念池、限频/预算闸生效且被拦时不下发、`source` 如实、已搜词跨会话不重复<!-- aidcp-cloud 4cd944e test/acceptance/search-intelligence.test.ts 7 例全过 -->
- [x] 5.2 `cd ../aidcp-cloud && npm run test:acceptance`（含既有 `AC-PROTO-*`/`AC-RISK-*` 不回归）→ `npm test` → `npm run typecheck` 全过<!-- aidcp-cloud 4cd944e acceptance 18 / 全量 192 / typecheck 全绿（基线 185→192，旧 search-evaluator skip 用例改判 no_available_keywords） -->
- [x] 5.3 `openspec validate wire-concept-pool-search-intelligence --strict` 通过<!-- aidcp 本仓 valid -->

## 6. 部署（显式发布动作，本仓触发）

- [ ] 6.1 按安全序列部署 cloud 到 ECS：备份（cloud.bak + .env.bak）→ rsync（exclude .env/node_modules/.git）→ `systemctl restart aidcp-cloud.service` → healthcheck（active + 8787 监听 + 飞书长连接 + PG `select 1` + `concepts` 表已建）→ 失败回滚
- [ ] 6.2 验证：观察日志中 `search.execute` 的 `source` 字段非空、概念抽取写入 `concepts` 表（PG `select count(*) from concepts`）
