# Design: parallel-rewrite-drafts

> 本设计由两轮多 agent 评估产出（18 agents 事实采集/方案/双份三视角对抗评审），所有结论带 `文件:行` 证据并经代码复核。评审修正已全部合入本文（与初稿差异处以「评审修正」标注）。

## Context

**现状（全部经代码坐实）：**

- 发布生成段全局串行由三层闸叠加维持，互相引用同一理由：`PublishScheduler.publishing` 全局布尔（`publish-scheduler.ts:117-122`，注释自证 load-bearing 且写明解锁条件=消灭全局槽）、`PublishOrchestrator` 单例 `status`/`activeContext`（`publish-orchestrator.ts:13-15,41-52`）、panel 入口 `isBusy()` → `publish_busy`（`server.ts:2691`）。
- 全局槽 `publishAccountRef`（`server.ts:616`）：~15 个发布角色的 LLM 调用经 `roleLlm` 包装隐式读槽归账（`server.ts:619-624`）；槽只保护记账准确性（`llm_token_usage` 表按账号计费），不承载功能正确性——账号本就随 `TriggerInput.accountId` 全程在黑板上。仓内已有三处显式归账先例：生图 `image-generator.ts:146`、评论链 `llmFor(accountId)`、浏览闭环 per-connection 实例槽。
- 既存缺口一（记账竞态）：下发段 takeover（`server.ts:883-890`）与另一账号生成段可时间重叠共写同一槽，注释「两段不重叠」无代码强制。
- 既存缺口二（连发真空，**比并行化更紧迫**）：同账号多份 pending 草稿今天就能造出（存储层无唯一约束、手动路径不查 pending），批准 N 张 = 下发段账号链尾零间隔背靠背连发 N 帖（`publish-dispatcher.ts:109-118`，`runDispatch` 只核授权/版本/有图/在线四件事）；风控 publish 配额是死数字——全仓无 `record('publish')`，计数器恒 0。
- 既存缺口三（僵尸轮）：管线 600s 超时只 reject 不取消角色链（`publish-orchestrator.ts:142-147`，`PipelineContext` 无中止传播），在途角色接力可在超时判 failed 数分钟后仍落库待审并发审批卡。
- 洗稿路径输入锚定参照笔记（`server.ts:2696-2709`），并发洗不同笔记=合法的不同草稿；自主创作路径输入是确定性 Top-K 素材选取 + 全局 baseline，同账号并发必产相似草稿。
- 审批基础设施已按 recordId 完全隔离（requestId=`publish-<id>`、信号文件 O_EXCL first-writer-wins、contentVersion 行级 CAS），多卡并存零改动可用；console 已能逐条编辑/批准/驳回多份待审（差距仅：全局 LIMIT 50 窗口挤出老 pending、发布队列卡单例形状）。

**需求**：同账号同时洗多个不同稿件 → 多份待审草稿 → 人工挑选一或多篇发布。

## Goals / Non-Goals

**Goals:**

1. 洗稿路径同账号跨参照稿并行生成，容量有界、拒绝诚实。
2. 记账全局槽退役，并发生成各归各账（含 PostProcessor 调用点）。
3. 下发段补安全阀：最小发布间隔、离线失败回待审、连续失败熔断——治今天就存在的连发真空，且先于并行化独立上线。
4. 候选池「挑选」体验闭环：console 完整可见待审集合、逐条批准/驳回、结果卡可区分。
5. 每期独立上线独立回滚；全程不违背「不静默假成功」。

**Non-Goals（对抗评审裁决，含理由）：**

- 触发排队（任何形式）：上轮评审打出四个失败模式（drain 状态漂移/重启丢队违约/竞速被抢/结果卡无主）；交互式触发帽满快拒 + 重点成本极低，load shedding 是正解。
- 待审草稿 TTL 自动作废：**违背现有 spec**（publish-pipeline「取消发布审批超时，草稿待审无限期、绝不超时自毁或改判」）；且与「已批等待发布/熔断挂起」状态冲突会把批过的草稿误标「未审作废」。清理路径=手动驳回。
- 下发段日上限：`postDailyCap` 默认 0 且语义是排期开关（`content-schedule-store.ts:281`、`content-scheduler.ts:163`），对齐即锁死「同日多发」这个本需求要买的能力；min-interval 已是频率闸。（评审修正：砍掉初稿的日上限双核查）
- DB 层同源查重（`hasPendingForSource`）：挡住的恰是「第一稿不满意再洗一版对比」的合法用法——同源**串行**重洗放行（温度采样天然出不同稿），同源**并发**由内存 claim 拒绝。（评审修正：砍掉初稿的 DB 查重层）
- 每 run 工厂重建角色（角色已证无状态）、AsyncLocalStorage 隐式传账号（全仓零先例、逆显式归账习惯）、自主创作路径并行化（并发必相似）、console 批量勾选发布（批量批准恰是节流要防的）、飞书汇总卡、陪伴端多草稿展示（`UiSnapshotPayload.publish` 单对象是 protocol.ts 四处同步热点，本期不动，「只显示最新一份」声明为已知降级）、风控 `record('publish')` 实时接线（需先定义手动审批记账语义 + 计数器不持久，独立 change）、供应商 429 感知重试/token-bucket（全局帽已界住峰值，等成功率数据）。

## Decisions

### D1. 并行单位 = 参照稿（键控单飞，两种粒度一套框架）

claim 键：洗稿 `rewrite:<accountId>:<sourceId>`、自主 `auto:<accountId>`。选 `sourceId` 不选 `curatedContentId`（精选表去重键本就是 `accountId::contentType::sourceId`；行 id 是 SERIAL、删除非持久会变且可空）。同键在途即拒 `duplicate_source`；跨键并行受帽约束。自主路径保持账号单飞 → 飞书 `/publish` 20s 重推去重（`ws-receiver.ts:230-235` 明言本层不自建去重）与排期顺延语义原样保住。
*替代方案*：全局锁改队列（否决见 Non-Goals）；按账号单飞不分键（吞掉同账号洗不同稿的核心需求）。

### D2. claim 原子性与唯一 owner（评审修正：接线定案）

- **零 await 原子段**：`tryBeginRewrite(accountId, sourceId)` / `tryBeginAutonomous(accountId)` 同步完成「查 claim 表 + 查账号在途帽 + 查全局帽 + 置位」，任何检查不跨 await——关掉现状 `publishing=true` 迟至 `buildTriggerInput` 多次 PG await 之后才置位的 TOCTOU（`publish-scheduler.ts:328,357`）。
- **账号 pending 帽并入同步段**（评审修正）：帽判定 = 「同账号在途 claim 数 + 最近一次已知 DB pending 数 ≥ 帽」在同一原子段内完成；DB pending 计数由调用方在预检段先 await 取好再传入同步方法（DB 数轻微滞后可接受，claim 数精确防并发穿透）。帽检查在 `tryBegin*` 内，**天然覆盖全部触发入口**（console/飞书/排期/旧自动扳机）——只闸 console 会被排期小时格每小时重触发结构性击穿（cap=1 无人审账号 72h 可堆约 72 份草稿）。
- **唯一 claim owner**：claim 的置位与释放都归 scheduler 的 `doTrigger` 全程 try/finally 所有——`tryBegin*` 置位后内部发起异步管线并返回 `{started: true, outcome: Promise<TriggerOutcome>}` 或同步 `{started: false, reason}`；`server.ts` 的 console 入口拿 `outcome` 挂现有 fire-and-forget 结果卡链（`server.ts:2730-2774` 的 `.then` 补黄/红卡逻辑平移到 outcome 上）。finally 覆盖含 `buildTriggerInput` 在内全程——任何 DB 瞬错都不得让键永久卡死（brick 防线）。

### D3. 编排器 run 注册表 + 向后兼容多 run 形状

单例引擎保留（角色无状态、`PipelineContext` 每轮全新），只把三个单数簿记换成 `Map<runId, RunHandle>`（`{context, accountId, kind, sourceId?, startedAt}`）；`trigger` 不再自查 `status==='running'`（闸职责已上移 D2）；finally 按 runId 摘除（顺带修「先结束轮抹在跑轮」串台点）；runId 换 crypto 随机。`getStatus()` 返回 `{status, snapshot, runs: [...]}` 兼容形状，**聚合规则显式定义**（评审修正）：旧字段取「最新启动的 running run；无 running 则最近一次终态」——旧版 console 永远能看到活跃管线且失败态不被并行 running 永久遮蔽。console 同批升级 `ContentQueue` 类型 + 多管线队列卡（空 `runs` 回落旧渲染；枚举漂移白屏前科，两侧同批部署）。

### D4. 显式归账（Phase 2 第一刀，行为零变化可独立上线）

~15 个发布角色调用 `llmClient.chat/complete` 补 `accountId: context.snapshot().trigger?.accountId ?? 'default'`（`base-role.ts` 加 `accountIdFrom(context)` 辅助收敛样板）；`PostProcessorLike.rewrite` 接口穿 `accountId`（ContentCleaner 沿 `process→rewrite` 显式传入——今天该调用记 `account='-'`，不修则「归账已显式」名不符实且并发归账 AC 漏检面）；`roleLlm` 删槽回落分支、保留显式优先；删 `server.ts:616` 槽定义、`:2118-2129` 生成段括起、`:883-890` 下发段写槽（让位/续场按账号参数化保留）——顺带根治既存跨段记账竞态。

### D5. 全局并发帽 + 排期口径收口

全局 run 帽默认 2（`AIDCP_PUBLISH_MAX_CONCURRENT_RUNS`）：文本重试是盲退避不识 429、生图零重试（`retry-strategy.ts:8-35`、`seedream-client.ts:109-114`），生图峰值 9×N 路，小全局帽是保护供应商最便宜的闸。帽满语义按入口复用现有拒绝形态：console `publish_busy`（文案改「生成并发已满」）、飞书 skipped 黄卡、排期让小时槽。排期日上限口径（评审后再校准，兼顾既有 spec 的防超发动机）：**自主路径在途草稿按真实条数计入日上限**（`posted + pendingAutonomousCount >= cap`，替代现状布尔——既有 spec「在途草稿计入上限」防的是两张自动草稿都获批即超发，多稿世界按条数计才原子）；**洗稿路径草稿不计入排期日上限**（人工发起的候选、由账号 pending 帽独立兜量，不再把 cap=1 账号的排期堵死；两类草稿按来源血缘 `source_reference` 区分）；`isPublishBusy` 注入改按账号的自主忙判定（`ContentSchedulerDeps` 签名加 accountId，调用处在账号循环内可取）。排期「让位」收窄：洗稿在途不再让排期槽（原动机=防槽污染，槽亡失效；放任会让活跃客户账号被持续饿槽）。

### D6. 下发节流与熔断（Phase 1 先行，不依赖并行化）

- **min-interval**（默认 30min，`AIDCP_PUBLISH_MIN_INTERVAL_MS`）：挂 `runDispatch` 授权复核后、`onPublishStart` 前——账号链尾天然排队、等待期不占边缘不让位（让位只在真正下发时发生）。**锚定「该账号上次下发尝试时刻」**（dispatcher 内存记录；评审修正——锚上次成功发布则连续失败零间隔横跳，恰是要消的行为指纹；内存态重启丢失无害，重启后首次下发放行本就合理）。醒后重核授权信号+版本+status（等待窗口内可能被驳回/编辑，诚实优先）。
- **失败分界**：边缘离线失败（未产生边缘副作用）→ 草稿回 `pending_approval` + 作废授权信号（复用 `voidApprovalSignal`）+ 通知重批——关掉「批准后离线 TOCTOU 烧稿」、保住生成+生图成本；序列执行失败（页面状态未知）→ 保持 failed 终态（防重复发帖）。
- **熔断**：同账号连续 2 次序列失败 → 停 drain 该账号已批队列（兜底扫描跳过、新 dispatch 拒绝且不烧授权）+ 飞书告警——防一次系统性边缘故障几分钟连环烧掉整批获批草稿（「自愈不自残」在下发段的落点）。**清除接线**（评审修正，防死锁）：熔断中草稿的 approve 信号已在盘上，重批走 first-writer-wins 的 alreadyDecided 分支不产生新事件——故 alreadyDecided 分支在账号处于熔断时视为人工确认、清熔断 + 踢一次兜底扫描；preflight 对新草稿的批准同样清熔断。熔断计数内存态，重启即清（未修复会再烧最多 2 篇后重新熔断，有界代价）。
- `scanAndDispatchApproved` 逐条 await 改 fire-and-forget（一账号等间隔不拖死跨账号扫描；幂等由 inFlight+accountTail 已保）。
- 「通过即切」文件头红线注释与 AC-PUB 断言按新契约**重述**（授权仍是发布必要条件），绝不删除。
- 诚实呈现收敛（评审修正）：批准回执带「将于最早 T 发布」（`preflightApprovePublish` 两端共用、改一处两端生效）；**不做** console waiting 行状态与 `/api/content/queue` 形状再扩（等待窗 ≤30min、信息已在回执，避免又一处形状漂移面）。

### D7. 僵尸轮拦截（评审级红线）

超时路径给当轮 context 打中止标记（`PipelineContext` 增一个 aborted 位，orchestrator 超时/中止时置位）；`PublishExecutor` 落库前检查——中止轮绝不 INSERT 待审草稿、绝不发审批卡（该轮已对外报 failed，落库即「一次触发两个结局」的静默假成功变体）。已发生的 LLM/生图消耗是沉没成本、如实记账。claim 与全局帽仍在 finally 释放（僵尸在途消耗短暂逃逸帽属可接受有界误差，日志如实记）。

### D8. 已知缺口登记（不修但必须写明）

- 重启时在途下发是 at-least-once 重复发帖窗口（既存：崩溃前边缘已提交而结果未回写 → 重启后兜底扫描全量重跑序列）；批量批准+min-interval 使同一时段排队下发数变多、暴露面变大。本期登记，后续可选「已开始下发」持久标记 + 重启转人工确认。
- 风控 publish 配额死数字（无 `record('publish')`）、封号/限流信号驱动的状态迁移缺失——全系统已知缺口，独立 change。
- 跨账号草稿同质（concepts/liked_notes 无 account_id、baseline 全局）——素材层缺口，仅影响自主路径，与本 change 正交。
- 陪伴端单槽只显示最新一份 pending、多 recordId 状态推送互相覆盖——已知降级，动它需改 protocol.ts 四处同步。
- 飞书僵尸卡随并行数线性放大（卡不可主动刷新、点了才知过期）——误发已被版本闸+status 闸双重拦住，console 定为多选主入口、飞书每稿一卡兜底。

## Risks / Trade-offs

- [server.ts 装配热点交织，多 change 撞车] → 按文件标记串行独占：`server.ts` 装配段、`publish-scheduler.ts`、`publish-dispatcher.ts`、`panel-server.ts` `/api/content/*` 段、console `ContentPage.tsx`/`CuratedContentPage.tsx`；与现活跃 `persona-wizard-onboarding-fixes`（亦改 server.ts）协调合并次序。
- [console↔cloud 形状漂移白屏前科] → getStatus 兼容形状 + 聚合规则显式 + 两侧同批部署 + console default 兜底断言。
- [AC-PUB 断言改写弱化防线] → 测试改写必须是重述而非删除，review 重点盯这批 diff。
- [供应商限流放大：全局帽 2 下文本 QPM 与生图并发翻倍] → 全部有界预算+诚实失败不假成功；上线先压 `AIDCP_PUBLISH_IMAGE_CONCURRENCY`，帽值按成功率数据回调；成本峰值≈2 倍现状需运营确认。
- [平台侧连发/协同指纹] → min-interval 治同账号连发；错峰 `offsetMinute` 是平台风控层、与云端并行正交，**绝不可当串行遗产删除**；真实风控信号接线仍缺（D8）。
- [内存态跨重启丢失（claim/全局帽/熔断/间隔锚）] → 在途生成轮诚实失败（console 无产出、用户重点即可）；已批未发靠 60s 兜底扫描+信号文件恢复；间隔锚重启放行合理；熔断重清有界代价。
- [排期让位收窄是行为变化] → 已列 Open Questions 待拍板，测试覆盖。
- [同源串行重洗放行 = 同账号可存多份同源草稿] → 账号 pending 帽兜量；挑选场景本就要多版本对比，属需求本身。

## Migration Plan

三期独立上线独立回滚（总量约 7-9 人日）：

- **Phase 1 下发安全阀**（D6，约 2 人日）：不依赖任何并行化改动，治今天已存在的连发真空；必须先于（或同批于）Phase 2 上线，否则并行生成放大未设防的连发风险。回滚=env 关间隔（0=禁用）+ 还原 dispatcher。
- **Phase 2 并行生成核心**（D1-D5+D7，约 3.5-4.5 人日）：D4 显式归账可再拆独立先行小提交（上线后行为零变化，风险最低的第一刀）；随后 run 注册表 → 键控 claim+帽+原因码一批上线；console 同批（形状兼容下可短暂错峰）。回滚=全局帽设 1 即回到事实串行（键控闸仍在，语义不回退）。
- **Phase 3 候选池消费面**（约 1-1.5 人日）：console status 过滤列表、结果卡带参照稿标题、多 run 队列卡完善。纯消费面，独立回滚。

部署走 CLAUDE.md §5 安全序列（dev 默认；两仓 `test:acceptance` → 全量 `npm test` → `typecheck` 全过再上）；真机验收项登记 `docs/real-machine-acceptance-backlog.md`。

## Open Questions（推荐值即默认，不改则按此实施）

1. 账号 pending 帽默认 3、全局 run 帽默认 2（env 可调；上线首周按成功率再放）——确认？
2. min-interval 默认 30 分钟（须远大于单篇 1-3 分钟下发时长才有风控意义）——确认？
3. 排期让位收窄（洗稿在途不再让排期槽、自主轮与洗稿轮可重叠受全局帽约束）——确认？
4. LLM/生图成本峰值≈2 倍现状（生成单飞的成本尖峰保护正式放弃）——运营确认？
