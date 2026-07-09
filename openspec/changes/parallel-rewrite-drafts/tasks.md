# Tasks: parallel-rewrite-drafts

> 三期独立上线独立回滚（design.md Migration Plan）：Phase 1=下发安全阀（§1，治既存连发真空、先行）；Phase 2=并行生成核心（§2-§5）；Phase 3=候选池消费面（§6）。热点文件按 CLAUDE.md §7 串行独占：`server.ts` 装配段、`publish-scheduler.ts`、`publish-dispatcher.ts`、`panel-server.ts` `/api/content/*` 段、console `ContentPage.tsx`/`CuratedContentPage.tsx`。每期收尾：两仓 `npm run test:acceptance` → 全量 `npm test` → `npm run typecheck`，AC-PUB/AC-RISK/AC-PROTO 全过；真机项登记 `docs/real-machine-acceptance-backlog.md`。

## 1. aidcp-cloud — Phase 1 下发安全阀（publish-dispatch-pacing）

- [ ] 1.1 `publish-dispatcher.ts`：runDispatch 授权复核后、onPublishStart 前加 min-interval 等待（锚=该账号上次**下发尝试**时刻的内存记录；`AIDCP_PUBLISH_MIN_INTERVAL_MS` 默认 30min、0=禁用）；醒后重核授权信号+内容版本+草稿状态，失效则按既有语义作废签名/不发
- [ ] 1.2 `publish-dispatcher.ts`：失败路径分界——边缘离线（零副作用）→ 草稿回 `pending_approval` + 作废授权信号（复用 voidApprovalSignal）+ 飞书通知重批；序列执行失败保持 `failed` 终态不自动重试
- [ ] 1.3 `publish-dispatcher.ts`：同账号连续 2 次序列失败熔断（内存 Map，成功清零；env 可配阈值）——兜底扫描跳过熔断账号、新 dispatch 拒绝且不烧授权信号、发飞书告警
- [ ] 1.4 熔断清除接线（防死锁）：对熔断账号的任一批准动作（含 first-writer-wins alreadyDecided 分支的重复批准）清熔断 + 踢一次兜底扫描；`preflightApprovePublish`（server.ts:1630-1652，飞书/web 共用）批准回执附「将于最早 T 发布」（受间隔延后时）与熔断中提示
- [ ] 1.5 `publish-dispatcher.ts:133-141`：scanAndDispatchApproved 逐条 await 改 fire-and-forget（幂等由 inFlight+accountTail 已保）
- [ ] 1.6 「通过即切」文件头红线注释（publish-dispatcher.ts:10）与相关 AC-PUB 断言按新契约**重述**（授权仍是发布必要条件；节流只延后/阻止、绝不放行未授权、绝不静默丢授权）——重述而非删除，review 重点盯
- [ ] 1.7 Phase 1 测试：同窗批两稿第二稿等间隔且等待期不让位；等待期被驳回/编辑则不发；连续失败吃间隔（锚=尝试）；离线回待审+信号作废+通知；连续两败熔断+告警+重批清熔断恢复；一账号等待不拖他账号扫描（用例克制，关键行为各一）
- [ ] 1.8 Phase 1 收尾：验收+全量+typecheck 全过 → commit/push → 部署 dev（§5 安全序列）→ 真机项（30min 真实连发间隔观察、熔断告警实收）登记 backlog

## 2. aidcp-cloud — Phase 2 第一刀：显式归账（publish-account-attribution）

- [ ] 2.1 `roles/base-role.ts` 加 `accountIdFrom(context)` 辅助；~15 个发布角色（server.ts:1908-1983 注册清单）LLM 调用补 `accountId`（样板 image-generator.ts:146）
- [ ] 2.2 `PostProcessorLike.rewrite` 接口穿 accountId（post-processor.ts + server.ts:829-839 注入处），ContentCleaner 沿 process→rewrite 显式传入（今天记 account='-' 的缺口）
- [ ] 2.3 `server.ts` 删槽：613-624 槽定义与 roleLlm 回落分支（保留显式优先）；2118-2129 生成段括起；883-890 下发段写槽（让位/续场按账号参数化保留）——顺带根治既存跨段记账竞态
- [ ] 2.4 并发归账 AC：两账号（及同账号两参照稿）并发生成 llm_token_usage 各归各账，断言覆盖 PostProcessor.rewrite 调用点；本刀行为零变化可独立提交部署

## 3. aidcp-cloud — Phase 2 编排器 run 注册表（publish-generation-concurrency）

- [ ] 3.1 `publish-orchestrator.ts`：activeContext+status 单槽 → `Map<runId, RunHandle>`（{context, accountId, kind, sourceId?, startedAt}）；删 status==='running' 拒绝闸（职责上移 §4）；finally 按 runId 摘除；idGen 换 crypto 随机
- [ ] 3.2 `getStatus()` 兼容形状：保留旧 {status, snapshot}（聚合规则=最新启动的 running 轮，无 running 则最近终态）+ 新增 runs 数组；panel-server.ts:378-381 透传类型同步
- [ ] 3.3 僵尸轮拦截：PipelineContext 加 aborted 位（超时/中止置位）；PublishExecutor 落库与发卡前检查——中止轮绝不 INSERT 待审草稿绝不发卡，消耗如实记账为沉没成本
- [ ] 3.4 多 run 簿记测试：两轮并发先结束不抹在跑；getStatus 聚合规则（running 优先、失败不被遮蔽）；超时僵尸轮不落库不发卡、同键新触发不受干扰

## 4. aidcp-cloud — Phase 2 键控单飞 + 容量帽（publish-generation-concurrency）

- [ ] 4.1 `publish-scheduler.ts`：publishing 布尔 → 键控 claim 注册表（`rewrite:<accountId>:<sourceId>` / `auto:<accountId>`）；新增同步 `tryBeginRewrite`/`tryBeginAutonomous`——零 await 原子段内完成查键+账号在途帽+全局帽+置位；claim owner 唯一（tryBegin 置位、doTrigger 全程 try/finally 释放，finally 覆盖 buildTriggerInput——DB 瞬错不卡键）；返回 {started, outcome?} 供入口挂结果链
- [ ] 4.2 帽值与语义：账号在途帽=在途 claim 数+DB pending 数（`AIDCP_PUBLISH_PENDING_CAP_PER_ACCOUNT` 默认 3）→ `publish_capacity`；全局帽（`AIDCP_PUBLISH_MAX_CONCURRENT_RUNS` 默认 2）→ 按入口拒绝形态；`publish-log-store.ts` 加 `countPendingForAccount`（可按来源血缘分洗稿/自主）
- [ ] 4.3 `triggerManual` 按 referenceNote 有无分流键类型；`isBusy(accountId?)` 收窄为「该账号自主轮在跑」；飞书 /publish 20s 重推去重语义回归断言（自主账号键单飞兜底）
- [ ] 4.4 `server.ts:2688-2744` createPostFromNote 改接 tryBeginRewrite：同步预检段完成全部拒绝（duplicate_source/publish_capacity/publish_busy/needs_persona/empty_body 均 HTTP 回执可见）；fire-and-forget 结果卡链平移到 outcome promise 上（skipped/failed 有人补卡）；结果卡文案带参照稿标题（并行可区分）
- [ ] 4.5 `content-scheduler.ts` + `server.ts:2152-2153`：isPublishBusy 注入改按账号自主忙判定（Deps 签名加 accountId）；日上限判定改 `posted + pendingAutonomousCount >= cap`（自主在途按真实条数、洗稿候选不计入，按 source_reference 区分）；洗稿在途不让排期槽；postFiring 错峰旗标保留
- [ ] 4.6 `panel/types.ts` 原因码注释清单加 duplicate_source/publish_capacity；publish-scheduler.ts:117-122 load-bearing 注释按新不变量改写
- [ ] 4.7 键控与帽测试：同键并发双触发恰一成功；同源串行重洗放行；同账号跨源并行放行；自主同账号二次 skipped；claim 在 buildTriggerInput 抛错时 finally 释放（brick 回归）；账号帽满 publish_capacity（排期入口同样受帽）；全局帽满三入口各自语义；日上限自主按条数计、洗稿候选不堵排期

## 5. aidcp-console — Phase 2 同批（防形状漂移白屏）

- [ ] 5.1 `src/api/queries.ts` + 类型：ContentQueue 加 runs 数组（旧字段保留）；`ContentPage.tsx` buildQueueStages 按 runs 渲染多管线卡（空 runs 回落旧单快照渲染）
- [ ] 5.2 `CuratedContentPage.tsx` actionReasonLabel 加 duplicate_source（「该笔记已有在途草稿，稍后可再洗一版」）与 publish_capacity（「该账号在途草稿已达上限，请先处理待审」）；publish_busy 文案去「全局串行」改「生成并发已满」
- [ ] 5.3 console 测试：多 run 队列渲染、新原因码映射、未知码 default 兜底不白屏；build 部署 dev（rsync 绝不 --delete）

## 6. Phase 3 候选池消费面 + 收尾

- [ ] 6.1 `panel-store.ts` publishedHistory 加 status?/accountId? 服务端过滤（WHERE），`panel-server.ts` `/api/content/published` 透传参数；console「只看待审」改服务端过滤请求（老 pending 不被 LIMIT 50 窗口挤出）
- [ ] 6.2 端到端验收：同账号并行洗两篇→两卡两草稿→批一驳一→批的按间隔真发（dev 环境）；AC-PUB/AC-RISK 全量回归
- [ ] 6.3 已知缺口登记（design.md D8 全清单）：重启在途下发 at-least-once 重复发帖窗口、风控 record('publish') 死数字、跨账号草稿同质、陪伴端单槽降级、飞书僵尸卡放大——写入 backlog/handoff，不静默
- [ ] 6.4 `openspec validate parallel-rewrite-drafts --strict` → 部署验证通过 → archive → 删 worktree/分支
