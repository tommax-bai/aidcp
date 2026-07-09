# Proposal: parallel-rewrite-drafts

## Why

运营在 console 精选页对同一账号连续触发洗稿时被全局串行闸拒绝（`publish_busy`「发布链路正在生成其它草稿（全局串行），请稍后再试」），而真实诉求是**同账号同时洗多个不同稿件、产出多份待审草稿、人工挑选一或多篇发布**。两轮多 agent 评估（10+8 agents、双份对抗评审）已查明：全局串行的唯一根因是 LLM token 记账的「当前发布账号」全局可变槽（`aidcp-cloud/src/server.ts:616`），不是边缘资源；且调查暴露一个今天就存在、比并行化更紧迫的真空——**同账号多份草稿获批后零间隔背靠背连发**（下发段无任何间隔/上限/熔断闸，风控 publish 配额是死数字、全仓无 `record('publish')`），多稿世界会放大这个平台侧风险。

## What Changes

- **下发安全阀先行（Phase 1，独立上线）**：边缘离线导致的下发失败回待审 + 作废授权信号 + 通知重批（不再烧成 failed 终态）；同账号连续 2 次序列失败触发熔断停链 + 飞书告警，熔断清除接人工重批确认路径（含 already-decided 分支，防死锁）；兜底扫描改 fire-and-forget（一账号多稿背靠背下发不拖死跨账号扫描）。**BREAKING**：`publish-pipeline` 的「审批通过即下发」增加熔断例外（熔断中授权保留不烧、人工确认后恢复），离线失败从 failed 终态改为回待审可重批；相关 AC-PUB 断言按新契约重述（授权仍是发布的必要条件，绝不删除）。**最小发布间隔本期不做**（用户 2026-07-09 定案）：同账号多稿同窗获批会背靠背连发，暂由运营错峰批准自行控节奏，登记已知缺口、后续按需补间隔机制。
- **显式归账，消灭全局槽（Phase 2 第一刀，行为零变化）**：约 15 个发布角色的 LLM 调用从黑板显式取账号传参（样板 `image-generator.ts:146`、评论链 `llmFor` 先例）；`PostProcessorLike.rewrite` 接口穿账号（今天记 `account='-'` 的既存缺口）；删除 `publishAccountRef` 槽，顺带修掉既存的「下发段 takeover ↔ 另一账号生成段」记账竞态。
- **并行生成核心（Phase 2）**：并行单位 = 参照稿。洗稿路径按 `(accountId, sourceId)` 键控单飞、跨参照稿可并行（含同账号）；自主创作路径（输入确定性、并发必相似）保持按账号单飞，飞书 `/publish` 20s 重推去重与排期顺延语义原样保住。编排器单例 status/activeContext 换 run 注册表（Map），`getStatus` 演进为向后兼容的多 run 形状；claim 的检查与置位在零 await 同步段完成、finally 覆盖含 `buildTriggerInput` 在内全程（防键卡死）；claim owner 唯一、console fire-and-forget 结果卡链显式续接。
- **容量与背压**：每账号在途待审帽（默认 3）**并入同步 claim 段并覆盖全部触发入口**（只闸 console 会被排期小时格结构性击穿堆稿）；全局并发生成帽（默认 2，保护 LLM/生图供应商）；帽满一律诚实快拒（新原因码 `duplicate_source` / `publish_capacity`），明确不做触发排队。排期日上限口径收口：在途草稿不占发帖日上限（候选≠消耗），堆积由 pending 帽独立管理。
- **候选池消费面**：console 待审列表服务端 status 过滤（替代客户端过滤，防全局 LIMIT 50 窗口把老 pending 挤出）；触发结果卡带参照稿标题（并行多稿可区分）；「挑选发布」= 现有逐条批准/驳回，未选中的手动驳回（弃置语义复用驳回→needs_review）。
- **僵尸轮拦截（评审级红线，既存缺口顺带闭合）**：管线 600s 超时不取消角色链、僵尸轮可在超时判 failed 后仍落库待审——落库点增加 run 中止检查，防超时僵尸穿透双层去重与全局帽。
- 明确不做（YAGNI，对抗评审裁决）：触发排队、每 run 工厂重建角色、AsyncLocalStorage 隐式传账号、待审草稿 TTL 自动作废（违背现有 spec「待审无限期绝不超时自毁」）、下发段日上限（`postDailyCap` 默认 0 是排期开关语义，对齐会锁死功能；min-interval 已是频率闸）、console 批量勾选发布、飞书汇总卡、陪伴端多草稿展示（不动 protocol.ts）、风控 `record('publish')` 实时接线（独立缺口登记）。

## Capabilities

### New Capabilities
- `publish-generation-concurrency`: 发布生成段并发模型——参照稿粒度键控单飞、自主路径账号单飞、run 注册表与多 run 观测、账号 pending 帽 + 全局 run 帽、诚实拒绝原因码、僵尸轮落库拦截、重启在途轮诚实失败。
- `publish-dispatch-resilience`: 下发段韧性——离线失败回待审可重批、连续失败熔断与人工清除（防连环烧稿）、兜底扫描不被单账号阻塞、授权必要性契约重述；已知缺口登记（同窗多批背靠背连发暂无间隔节流、重启在途下发的 at-least-once 重复发帖窗口）。

### Modified Capabilities
- `publish-pipeline`: 「审批通过即下发」保持、增加熔断例外（授权保留不烧、人工确认后恢复）；离线失败从 failed 终态改回待审可重批；生成候审段从全局单跑改为按键并发（生成段仍不让位浏览不变）；下发段按账号单飞保持。
- `publish-account-attribution`: 新增「生成段 LLM/生图记账逐调用显式携带账号」要求——并发生成各归各账，全局槽退役，覆盖 PostProcessor 重写调用点。
- `content-schedule`: 「排期发帖全局串行」→「自主路径按账号单飞 + 全局并发帽」（洗稿在途不再让排期槽）；「发帖日上限对在途草稿原子」→ 在途 pending 不占日上限、堆积由账号 pending 帽管理。
- `curated-note-actions`: 参照洗稿触发支持同账号跨参照稿并行；新增 `duplicate_source` / `publish_capacity` 拒绝原因码；`publish_busy` 语义收窄为并发帽满；触发结果卡携带参照稿标识。
- `console-panel-api`: `/api/content/queue` 演进为向后兼容多 run 形状（保留旧单快照字段 + 新增 runs 数组，聚合规则显式定义）；`/api/content/published` 增加服务端 status/account 过滤参数。

## Impact

- **aidcp-cloud**（全部代码改动所在）：`src/publish-agent/publish-scheduler.ts`（键控 claim + 帽）、`publish-orchestrator.ts`（run 注册表）、`publish-dispatcher.ts`（熔断/失败分界/扫描改造）、`roles/*`（~15 角色显式账号 + 落库中止检查）、`post-processor.ts`（接口穿账号）、`src/server.ts` 装配段（613-624/883-890/1630-1652/2118-2129/2688-2744）、`src/orchestrator/content-scheduler.ts`（忙判定与日上限口径）、`src/panel/panel-server.ts` + `panel-store.ts`（queue 形状、列表过滤）、`publish-log-store.ts`（计数查询）。
- **aidcp-console**：`src/pages/ContentPage.tsx`（多 run 队列卡、status 过滤列表）、`CuratedContentPage.tsx`（新原因码文案）、`src/api/queries.ts` + 类型（ContentQueue 形状，防枚举漂移白屏前科）。
- **不改**：protocol.ts（零协议变更，陪伴端单槽展示声明为已知降级）、aidcp-edge（生成段并行对边缘零影响）、风控状态机。
- **热点串行独占（按文件，CLAUDE.md §7）**：`server.ts` 装配段、`publish-scheduler.ts`、`publish-dispatcher.ts`、`panel-server.ts` `/api/content/*` 段、console `ContentPage.tsx`/`CuratedContentPage.tsx`——实装期间不与触碰同文件的 change 并行（现活跃 `persona-wizard-onboarding-fixes` 亦改 server.ts，需协调合并次序）。
- **运营前置确认**：全局帽 2 意味着 LLM/生图成本峰值≈2 倍现状（decouple change 的「生成单飞避免成本尖峰」动机被正式放弃）；供应商限流表现为缺图/整轮诚实失败，上线先压 `AIDCP_PUBLISH_IMAGE_CONCURRENCY`、按成功率数据调帽。
