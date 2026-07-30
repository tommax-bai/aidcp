# ⛔ 已划出计划（2026-07-30，用户裁定）

> **本 change 的剩余任务已被划掉，不再是待办。已落地的代码原样保留、不回滚。**
>
> 用户在通盘复核任务量时裁定：**发布授权信号入库** 这条不继续做。
> 下面**每一条未勾选项都已就地标注「不是待办」**——`- [ ]` 的方框在这里不表示待办，只表示「没做，也不打算做」。
>
> **进度快照（划掉时）：已做 52/58，剩余 6 项作废。**
>
> ## 两条接手时必须知道的
>
> 1. **这不是零开工的 change，是做到一半停的。** 已交付的部分是真上线的行为，
>    **MUST NOT 因为「这条被划掉了」就把已落地的代码当成实验品删掉**。
> 2. **归档是另一个决定，本次没做。** 归档会把 `specs/` 下的 delta 并进主规格、
>    等于声称整套行为已上线，而这里只做了一部分。**若日后要归档，必须先把 delta 收窄到「实际交付的那部分」**，
>    否则就是在主规格里写下一条没人实现的保证。
>
> 恢复做法：删掉本节与各条的「不是待办」标注即可，任务原文未改动。

## 1. aidcp — 控制仓文档与盘点范围

> 本节全部落在控制仓文档上。5 个并行 change 都要改 `docs/cloud-service-decomposition-proposal.md`，
> 为避免互相冲突，本 session **未直接修改**该文件，改为把精确编辑写成 docpatch 交主控 session 串行套用：
> `/private/tmp/claude-501/-Users-baitianxing-codes-aidcp/f0ef76c1-69d8-483a-8df8-115c38a2f9d0/scratchpad/docpatch-publish-approval-signal-to-database.md`

- [x] 1.1 在 `docs/cloud-service-decomposition-proposal.md` §5.2「候选版本和审批不能隐式漂移」后补一段：审批授权 MUST 是 `aidcp-api` 单写的持久记录，至少含候选版本标识、决策人、决策时间、决策渠道、`envKey`、`executionTarget` 与决策本身；MUST NOT 以本机文件、本机内存或共享路径承载。
<!-- 2026-07-23 主控套用 docpatch 补丁 2：docs/cloud-service-decomposition-proposal.md §5.2 在「自动化恢复执行时…」之后新增一段（审批授权 MUST 是 api 单写持久记录、原子性靠活跃行唯一约束、作废=状态迁移不删行）。 -->
- [x] 1.2 **降级为核对，MUST NOT 再新增条目**：本项写于定稿整合之前，§6.4 禁止清单**现已是 8 条**，第 8 条逐字为「用共享文件系统、本机路径、本机临时目录或数据库 advisory lock 传递跨服务的授权、锁或业务事实」，已覆盖本 change 的形态（并在其下以「实例一」逐点列出了审批信号文件的读写方与失效形态）。本项的义务改为：核对该条措辞确已覆盖，如有缺口再提最小增补；照原文再加一条会产出重复条目。
<!-- 核对完成：§6.4 第 8 条 + 实例一/实例二逐点覆盖本 change 两个形态，无缺口，不新增条目。结论记于 docpatch「已核对无需改动」一节 -->
- [x] 1.3 **降级为核对，MUST NOT 再新增类别**：定稿 §12 阶段 0 的「状态盘点清单」**现已是六类表**（表 / 进程内内存事实 / 本机文件信号 / 本机锁与 PG advisory lock / EventBus 事件 / 常驻定时任务），本 change 坐实的四类通道已全部在内。本项的义务改为：核对六类已覆盖，并把本 change 新坐实的实例填进对应行。
<!-- 核对完成：六类已覆盖，不扩表。新坐实实例落在 aidcp-cloud/docs/cross-service-shared-state-inventory.md，由 docpatch 补丁 3 在定稿里加指针 -->
- [x] 1.4 **仍是活任务**（定稿六类表现只有「类别 / 盘点内容 / 失效方向」三列）：在 §12 阶段 0 补一句盘点行的必填字段：引用点 `文件:行` → 拆分后归属服务 → 是否跨服务 → 替代机制 → 不替代会怎样失效（必须写出失效方向是静默还是报错）。
<!-- 2026-07-23 主控套用 docpatch 补丁 3：docs/cloud-service-decomposition-proposal.md §12 阶段 0 六类表下方新增「每行盘点行的必填字段」段 + 指向 aidcp-cloud/docs/cross-service-shared-state-inventory.md 的指针。 -->
- [x] 1.5 在 §12 阶段 4 与「删除对连接注册表、RiskController 和内容 Store 的直接读取」并列增一条：把审批授权的文件实现替换为持久授权记录 + `PublishApproved` 命令，并明确 edge 侧文件闸是随迁还是就地废弃。
<!-- 2026-07-23 主控套用 docpatch 补丁 4：docs/cloud-service-decomposition-proposal.md §12 阶段 4「把审批授权从文件通道改为 api 持久记录」一行补 edge 侧同路径文件闸「就地废弃、降级为必须显式启用的开发夹具」。 -->
- [x] 1.6 在 §14 验收红线增一条：审批通过后下发侧不可用时，用户 MUST 看到明确的待下发或失败态，MUST NOT 呈现为与「待审批」不可区分的静默停滞。
<!-- 2026-07-23 主控套用 docpatch 补丁 5：docs/cloud-service-decomposition-proposal.md §14.1 尾部追加红线 AC-DECOMP-32（可检测性·已批准待下发）。原稿拟 31，因三条并行新增红线按套用顺序排号、config-mirror 先取 31，本 change 顺延为 32（boundary-gates=33）。 -->
- [x] 1.7 在仓内产出阶段 0 盘点表初版（六类，至少覆盖本 change 已坐实的：审批信号文件、`interaction-env:<envKey>` advisory lock、`interaction-store.ts:409` / `:989` 两把单服务内锁、常驻定时任务）。**常驻定时任务的计数 MUST 同时给出两个数、且 MUST 在实施当天重测**：定稿 §4.6.5 / §12 阶段 0 的「14」是逐个定归属的**宿主**数（其第 13、14 项并非 `setInterval`），本稿的「24」是 `grep -rn setInterval src` 的**调用点**数（2026-07-22 实测在 23–24 之间漂动）。两者不是一回事，只写一个数会让盘点者提前收工。
<!-- aidcp-cloud 66d05e7 docs/cross-service-shared-state-inventory.md；计数两口径：宿主 14（引定稿）/ 调用点 2026-07-23 当日实测 26（含本 change 新增看门狗，主干应为 25）。表放 sub-repo 而非控制仓：控制仓 docs/ 是 5 个并行 change 的冲突热点，指针由 docpatch 补丁 3 加入定稿 -->
- [ ] **【已划出计划 2026-07-30，不是待办】** 1.8 影子写关闭后更新 `CLAUDE.md` §4 中「发布审批信号文件两端契约路径必须一致」的表述，改为「授权以持久记录为准，两端不得依赖同机路径」。
<!-- BLOCKED: 前置条件未满足——影子写仍默认开（AIDCP_PUBLISH_APPROVAL_LEGACY_SIGNAL_FILE 默认 true），两端确实仍写同一路径，CLAUDE.md 现有表述在过渡窗口内仍准确。改法已备在 docpatch 补丁 6，标注「现在还不能套用」。2026-07-23 主控复核：docpatch 补丁 6 未套用，CLAUDE.md §4 保持原表述（影子写关闭 + 两端满一发布周期无读者后另起独立收尾）。 -->

## 2. aidcp-cloud — 持久授权记录与单写出口（未来 api 域）

- [x] 2.1 新增迁移，建 `publish_approval_decision` 表：`request_id`、`revision`、`subject_kind`、`candidate_ref`、`content_version`、`approved`、`decided_by`、`decided_via`、`decided_at`、`env_key`、`execution_target`、`frozen_payload`、`dispatch_state`、`dispatch_blocked_reason`、`dispatch_state_at`、`void_reason`；主键 `(request_id, revision)`；`CREATE UNIQUE INDEX ... (request_id) WHERE dispatch_state <> 'void'`；`execution_target` 加 `CHECK IN ('dev','ol')`。
<!-- aidcp-cloud 4ad06a2 migrations/0063_publish_approval_decision.sql（另建 publish_approval_outbox 承载 PublishApproved 命令，见 3.9） -->
<!-- aidcp-cloud a9ce113 修：env_key 列建了但**值恒 NULL**（五个写入口手边都只有候选/账号、没有环境键，全都没传）。解析已收口到写出口一处：候选→草稿账号→唯一活跃绑定环境；多绑歧义时留空、绝不猜。 -->
- [x] 2.2 新增 `src/publish-agent/publish-approval-store.ts`（或等价位置）作为该表唯一写者，暴露 `record(decision)`、`readActive(requestId)`、`listPendingDispatch(executionTarget, limit)`、`markDispatching(requestId, revision)`、`markConsumed(...)`、`void(requestId, reason)`、`setBlockedReason(requestId, reason|null)`。
<!-- aidcp-cloud 4ad06a2 偏离：`void()` 实名为 `voidActive()`（`void` 是 TS 关键字、作方法名可读性差）；另补 listStalePendingDispatch / releaseToPending / readActiveMany / listRevisions / claimApprovedCommands -->
- [x] 2.3 `record()` 用 `INSERT ... ON CONFLICT (request_id) WHERE dispatch_state <> 'void' DO NOTHING RETURNING *` 实现 first-writer-wins：返回行 → `{written:true}`；返回空 → 读回活跃行 → `{alreadyDecided:<approved>}`。返回类型保持与 `ApprovalWriteResult` 同形，MUST NOT 返回 `published`。
<!-- aidcp-cloud 4ad06a2 另补：PK (request_id, revision) 也可能被并发写者先占（部分索引与 PK 谁先触发不确定），故同时捕获 23505 并按「有人先到」处理，最多三轮后诚实抛 publish_approval_record_contention，绝不静默返回假成功 -->
- [x] 2.4 `void()` 只做状态迁移（`dispatch_state='void'` + `void_reason`），MUST NOT 删行；后续同 `requestId` 的授权以 `revision+1` 插入。
<!-- aidcp-cloud 4ad06a2 + 3a4ff8e（回归断言：只 UPDATE 不 DELETE、枚举外原因被拒） -->
- [x] 2.5 `execution_target` 由服务端从本机 `AIDCP_DEPLOY_ENV` 注入，MUST NOT 取自请求体；缺失或非法时写入 MUST 失败并返回可区分错误。
<!-- aidcp-cloud 4ad06a2 ApprovalExecutionTargetError；target 缺失时 Store 根本不构造、写出口诚实抛 approval_outlet_unavailable -->
- [x] 2.6 把 `src/feishu/ws-receiver.ts:151` 的 `writeApprovalSignal` 改为委托到 `PublishApprovalStore.record()`，保留 `ApprovalWriteResult` 形状与 `parseApprovalActionValue` 入口不变；保留 `getApprovalSignalPath` 仅供影子写使用并标 `@deprecated`。
<!-- aidcp-cloud 4ad06a2 偏离：未把自由函数 writeApprovalSignal 本身改成委托，而是把它整体降级为「影子写实现」并标 @deprecated，接收端改注入 writeApproval 出口。理由：该函数是纯 fs 函数、被影子写复用；未注入出口时接收端 fail-closed 报错 toast，绝不退回文件互斥 -->
- [x] 2.7 影子写：`record()` 成功后 best-effort 写同路径同格式文件，由 `AIDCP_PUBLISH_APPROVAL_LEGACY_SIGNAL_FILE`（默认 `true`）控制；写失败只记日志，MUST NOT 影响 `record()` 的返回值或抛出。
<!-- aidcp-cloud 4ad06a2 src/publish-agent/publish-approval-outlet.ts + 3a4ff8e 回归 -->
- [x] 2.8 五个写入口全部改经同一 Store：飞书回调（`src/feishu/ws-receiver.ts:321`）、面板路由（`src/panel/panel-server.ts:1302`）、客户端内审批（`src/server.ts:2815`）、委托任务批准 / 拒绝（`src/server.ts:3991`、`:4005`）、排期 `auto_approve` 预授权。每处必须传真实 `decided_by` 与 `decided_via`，MUST NOT 用常量占位。
<!-- aidcp-cloud 4ad06a2 decided_by：飞书=卡片 operator open_id（新从事件透传）/ 面板=panel:<JWT sub> / 客户端=client:<accountId> / 委托=delegated_task:<taskId>（executors 新增透传）/ 排期=schedule_auto_approve:<accountId>。飞书 operator 取不到时落 feishu:unknown_operator（真实事实，不冒充具体人） -->
<!-- aidcp-cloud a9ce113 补：五个入口**都没传 envKey**（手边只有候选/账号），env_key 因此全表恒 NULL。改为在写出口一处解析（见 2.1 修复注），入口签名不动 -->
- [x] 2.9 `src/panel/panel-server.ts:1246`-`:1252` 的 `requestId` 白名单保留，注释与拒因改为「记录主键与 URL 路径段的受控字符集」，删除「参与文件落盘路径拼接」的表述。
<!-- aidcp-cloud 4ad06a2；同批更新 src/agents/comment-approval-request-id.ts 的归一理由（5ebe1d2） -->

## 3. aidcp-cloud — 读侧改造与跨服务合同形状（未来 automation 域）

- [x] 3.1 新增内部查询接口（阶段 1 用进程内适配器，形状按未来 HTTP）：`GET /internal/publish-approvals/{requestId}` 返回 `{approved, contentVersion, dispatchState, dispatchBlockedReason, envKey, executionTarget}`；不存在返回 404。
<!-- aidcp-cloud 4ad06a2 src/publish-agent/publish-approval-api.ts（createInProcessPublishApprovalApi + createPublishApprovalClient；404/503 严格可区分） -->
- [x] 3.2 新增 `GET /internal/publish-approvals?dispatchState=pending_dispatch&executionTarget=<target>`，只返回本机 target 的活跃行。
<!-- aidcp-cloud 4ad06a2 listApprovals；非 pending_dispatch 的 dispatchState 返回 400 -->
- [x] 3.3 新增 `POST /internal/publish-approvals/{requestId}/void`，reason 限枚举 `version_stale` / `edge_offline` / `preempt_exhausted` / `lease_unconfirmed`；枚举外拒绝。
<!-- aidcp-cloud 4ad06a2 voidApproval（枚举外 400 invalid_void_reason；Store 层再守一道抛 invalid_void_reason） -->
- [x] 3.4 `src/server.ts:2076` 的 `readPublishApproval`、`:2088` 的 `isPublishApproved`、`:2093` 的 `voidApprovalSignal` 三个闭包改为调用 3.1 / 3.3 的接口，删除 `readFile` / `unlink` 实现。
<!-- aidcp-cloud 4ad06a2 三态严格可区分：有活跃行 / 404→null（未授权）/ 503→抛 ApprovalUnreadableError -->
- [x] 3.5 `src/publish-agent/publish-dispatcher.ts:453` 的下发前复核改读持久记录；查询超时 / 不可达 MUST 视为未授权、不下发、写 `dispatch_blocked_reason='approval_unreadable'`，MUST NOT 写任何终态。
<!-- aidcp-cloud 4ad06a2 + 3a4ff8e 回归（不下发、statusUpdates 为空、不作废、blocked=approval_unreadable） -->
- [x] 3.6 `src/publish-agent/publish-dispatcher.ts:370`-`:378` 的兜底扫描改为调 3.2 批量拉取，删除「遍历 `pending_approval` id 逐个读文件」的实现。
<!-- aidcp-cloud 4ad06a2 + 3a4ff8e；拉取失败诚实跳过本轮，绝不当作「扫完了、没有待下发」。旧逐条路径只在未注入批量拉取时（旧构造/单测）保留 -->
- [x] 3.7 `publish-dispatcher.ts:275`、`:464`、`:641` 三处作废改调 3.3，各传对应 reason。
<!-- aidcp-cloud 4ad06a2 preempt_exhausted / version_stale / lease_unconfirmed（3a4ff8e 各有回归断言） -->
- [x] 3.8 `src/agents/comment-approval-gate.ts:218` 的 `isApproved` 轮询改读持久记录；查询失败 MUST 计为「未授权」继续等待到超时并 `comment.skipped{reason:'approval_timeout'}`，MUST NOT 与 `approval_rejected` 混同。
<!-- aidcp-cloud 4ad06a2（注入口 isPublishApproved 已改读持久记录）+ 5ebe1d2（gate 内 catch 分支注释写死该不变量；既有行为本就 fail-closed 到 approval_timeout，未改语义） -->
- [x] 3.9 `src/server.ts:2720` 的 `triggerPublishDispatchOnApprove` 进程内直调改为：api 侧在 `record()` 同事务写 Outbox `PublishApproved{requestId, candidateRef, contentVersion, envKey, executionTarget}`；automation 侧 Inbox 按 `requestId+revision` 去重后触发一次 `dispatch()`。既有幂等闸（`inFlight` / status / 授权复核）保持不变。
<!-- aidcp-cloud 4ad06a2（Outbox 同事务写出 + claimApprovedCommands 原子认领去重）/ 5ebe1d2（Inbox 泵接线）。偏离：进程内直调**保留**未删——它同时承担「already-decided 重批即确认清除熔断」的语义（那条路径不产生 Outbox 行），且删掉会让通过即切退化为最长一个扫描周期的时延。两条路都收敛到 dispatch 的既有幂等闸，阶段 4 提取 api 后直调自然消失 -->
- [x] 3.10 `src/publish-agent/client-publish-approval.ts:91` 的 `readApproval` 改读持久记录，`already_decided` / `version_stale` 拒因语义保持不变。
<!-- aidcp-cloud 4ad06a2；另加：授权查询不可读时回可区分拒因 approval_unreadable，绝不按缺省继续去写第二次决定 -->

## 4. aidcp-cloud — 待下发态与诚实降级

- [x] 4.1 `record(approved=true)` 落库即置 `dispatch_state='pending_dispatch'`，同时记录 `decided_at`。
<!-- aidcp-cloud 4ad06a2；approved=false 无下发可言，落 consumed（仍是活跃行，故后到的批准仍被判 alreadyDecided:false，与旧「文件已存在且 approved=false」逐条对应） -->
<!-- aidcp-cloud a9ce113 修：评论授权也落 pending_dispatch，但下发状态机只被发帖下发器驱动 ⇒ 评论行永久滞留、既刷出 P1 误报又把候选窗口占满（看门狗会自我瘫痪）。两个待下发查询加 subject_kind 过滤；评论人审闸读到「已批准」即迁 consumed（评论没有下发段，读到即用掉） -->
- [x] 4.2 automation 领取执行时置 `dispatching`，序列成功后置 `consumed`；被抢占保持 `pending_dispatch` 并保留授权（对应 `publish-dispatcher.ts:610` 既有分支）。
<!-- aidcp-cloud 4ad06a2 + 3a4ff8e（progress 断言 dispatching→consumed；被抢占走 releaseToPending 保留授权、无阻塞原因） -->
- [x] 4.3 把既有五类下发阻塞映射到 `dispatch_blocked_reason`：`edge_offline_waiting`（`publish-dispatcher.ts:485`）、`browser_slot_waiting`（`:638`）、`breaker_open`（`:434`）、`captcha_paused`（`:508`）、`approval_unreadable`（3.5）。阻塞解除时 MUST 清空该字段。
<!-- aidcp-cloud 4ad06a2 + 3a4ff8e（阻塞解除清空有专门断言） -->
<!-- aidcp-cloud a9ce113 修：五类里只有四类真能落库。browser_slot_waiting 走 releaseToPending，而它的 WHERE 只认 dispatching；唤不醒是在 acquire 阶段 reject 的、markDispatching 从未跑过 ⇒ 命中 0 行、原因被静默丢弃、等槽位的稿被误报成「下发侧失联」。WHERE 已放宽到 IN ('pending_dispatch','dispatching')，并补 store/dispatcher 两级回归 -->
- [x] 4.4 新增常驻检查：`pending_dispatch` 且 `dispatch_blocked_reason IS NULL` 超过阈值（`AIDCP_PUBLISH_PENDING_DISPATCH_ALERT_MS`，默认 15 分钟）即发飞书告警并写 `alerts`；有阻塞原因的不告警。该 worker MUST 按本机 `execution_target` 过滤。
<!-- aidcp-cloud 4ad06a2 src/publish-agent/pending-dispatch-watchdog.ts + 5ebe1d2 接线 + 3a4ff8e 回归（含「扫描失败不当作无异常」） -->
<!-- aidcp-cloud a9ce113 修：「写 alerts」那一半原先从未接线（构造处只传 notify，alertStore 漏注入）⇒ P1 只走飞书、后台告警页看不到、无从对账。已注入既有告警存储（sink 改与 AlertStore.raise 同形，免转接层）；同批修「无飞书群时静默 return 却被记为已送达」（改为抛错）与「候选窗口打满不吭声」（打满即 error 日志） -->
- [x] 4.5 `src/panel/publish-stage-lifecycle.ts:326`-`:329` 的阶段判定改用持久 `dispatch_state`，删除对进程内在途集合的依赖；`pending_approval` + `pending_dispatch` MUST 呈现为「已批准·待下发」，与「待审批」可区分。
<!-- aidcp-cloud 5ebe1d2 + 3a4ff8e（含「进程重启后不退回待审批」断言）。偏离：进程内在途集合作为**未注入持久投影时的回落**保留（零回归），有持久行时它不参与判定 -->
- [x] 4.6 面板发布队列与待审详情投影增量返回 `dispatchState`、`dispatchBlockedReason`、`decidedAt`、`waitingMs`。
<!-- aidcp-cloud 5ebe1d2（/api/content/queue 的 lifecycle）+ c1f18fa（/api/content/published 每行）。status 枚举**不加新取值**——加了会让未升级前端落 default 分支整页白屏，细分改由这四个增量可选字段承担 -->
<!-- aidcp-cloud a9ce113 修：面板侧投影读失败被裸 catch 吞掉（读失败与「未接线」同样返回 null、服务端零留痕）⇒ PG 抖动时「已批准·待下发」会无声消失、排障无线索。已补 warn，与 server.ts 同口径 -->
- [x] 4.7 `src/comm/protocol.ts` 的 `PublishApprovalActionResultPayload` 增量可选字段 `dispatchState?: 'pending_dispatch' | 'dispatching' | 'blocked'` 与 `dispatchBlockedReason?: string`；`state` 的既有取值 MUST NOT 变更。改动与 edge 同名文件逐字一致，并同步 `docs/protocol.md`（该消息按信封 id 应答，不进主动命令白名单）。
<!-- aidcp-cloud 4ad06a2 / aidcp-edge 0b5f536（两份 protocol.ts 该段逐字一致，diff 已核；两文件其余既有差异为本 change 之前就存在的注释/枚举顺序漂移，未触碰）。docs/protocol.md 属控制仓 → docpatch 补丁 1。2026-07-23 主控套用补丁 1：docs/protocol.md publish.approval_action.result 的 jsonc 块加 dispatchState / dispatchBlockedReason 两个增量可选字段 + 说明 bullets；消息类型数未变、头部计数无需改。 -->

## 5. aidcp-cloud — advisory lock 替换

- [x] 5.1 产出 `pg_advisory_*` 引用点盘点表：`src/client-auth/client-user-store.ts:619`、`:1468`、`:2001`、`:2128`（api）、`src/interactions/interaction-store.ts:339`（automation）、`:409`、`:989`（单服务内），每行标注 key 命名空间、归属服务、是否跨服务。
<!-- aidcp-cloud 66d05e7 docs/cross-service-shared-state-inventory.md 类别 6a -->
- [ ] **【已划出计划 2026-07-30，不是待办】** 5.2 新增内部端点 `PUT /internal/environments/{envKey}/auth-state`，由 api 侧在事务内 `SELECT ... FROM client_environments WHERE env_key=$1 FOR UPDATE` 后写 `interaction_auth_state`。
<!-- BLOCKED: 未做。`upsertAuthStatus` 是一个跨 interaction_offboards / interaction_offboard_audit / interaction_auth_state 的长事务方法，把它整体搬进 ClientUserStore 属跨 Store 边界的大重构，回归面远超本 change 其余改动的总和。**跨服务 advisory lock 已在 5.3/5.4 被行锁消除**（本项的安全目的已达成）：拆库后 automation 连不到 client_environments 是**响亮的失败**而非静默失去互斥。残留缺口（写点仍在 automation）已在盘点表末尾明写 -->
- [ ] **【已划出计划 2026-07-30，不是待办】** 5.3 `src/interactions/interaction-store.ts:333` 的 `upsertAuthStatus` 改经 5.2 的端点，删除该处 `interaction-env:` advisory lock
<!-- 部分完成（aidcp-cloud 66d05e7）：该处 advisory lock **已删除**，改为同事务内 client_environments 行锁（lockEnvironmentRow）。BLOCKED 的是「改经 5.2 端点」那一半，理由同 5.2 -->
<!-- aidcp-cloud a9ce113 修：行锁在**环境未注册**时命中 0 行 ⇒ 既不加锁也不报错，而本写点恰恰不要求注册行存在（上游校验不查注册表，握手时的自动登记还是 fire-and-forget）⇒ 换掉 advisory lock 却留了同一种无声失效。现取锁结果是可判定返回值（locked/unregistered，未取到即记日志），未注册时回落去锁该环境的客户归属行 client_env_scope（解绑侧正是遍历那张表找环境的）；两张表都无行才是真无对手 -->
- [x] 5.4 `src/client-auth/client-user-store.ts` 四处 `interaction-env:` 改为对 `client_environments` 按 `env_key` 升序取行锁；`:1468`、`:2001` 既有的排序取锁顺序 MUST 保持不变（死锁序不回归）。
<!-- aidcp-cloud 66d05e7；两处批量路径仍逐个按 env_key 升序取锁，取锁顺序与改动前逐字相同（未改成 ANY(...)+ORDER BY，因为 PG 的加锁顺序跟执行计划走、不保证跟 ORDER BY） -->
- [x] 5.5 新增静态检查（CI 或测试）：源码中每个 advisory lock key 前缀 MUST 只被单一服务边界目录引用，跨边界引用即失败；`interaction-store.ts:409`、`:989` 两把单服务内锁在检查白名单中显式登记。
<!-- aidcp-cloud 66d05e7 test/acceptance/advisory-lock-ownership.test.ts（AC-LOCK-01 断言 interaction-env: 已归零；AC-LOCK-02 逐引用点核边界 + 白名单登记） -->
<!-- aidcp-cloud a9ce113 修：白名单当时有两份（源码里 SINGLE_SERVICE_ADVISORY_LOCK_KEYS 全仓零引用 = 死代码，且条目已与验收测试那份漂移）。已删源码那份，事实源只剩验收测试里的一份 -->

## 6. aidcp-edge — 文件闸降级与协议同步

- [x] 6.1 `src/publish/approval-gate.ts:95` 的 `waitForPublishApproval` 增显式启用门：同时要求 `AIDCP_PUBLISH_APPROVAL_SIGNAL_DIR` 与 `AIDCP_DEV_PUBLISH=1`，否则立即返回 `{ok:false, reason:'approval_gate_disabled'}`，MUST NOT 静默通过、MUST NOT 静默等待到超时。
<!-- aidcp-edge 0b5f536；`forceEnabledForTest` 只供本闸自身单测（生产无调用者），AC-PUB-03 断言未启用时 reads=0 且 slept=0 -->
- [x] 6.2 更新 `src/publish/approval-gate.ts:36`-`:41` 的注释：该闸是本机开发夹具，不是跨服务契约；生产人审在云端完成。
<!-- aidcp-edge 0b5f536；buildPublishApprovalSignalPath 同批标 @deprecated -->
- [x] 6.3 新增回归断言：生产算子表内 `publish.request` 无处理器（对照 `src/client/operation-registry.ts:104` 的墓碑与 `src/client/edge-client.ts:797` 的 `handler_unavailable` 分支）。
<!-- aidcp-edge 0b5f536 AC-PUB-01（复现生产形态：不注册 onPublishCommand → 诊断 rejected/handler_unavailable，且不回任何发布结果） -->
- [x] 6.4 `src/comm/protocol.ts` 同步 4.7 的增量字段，与 cloud 逐字一致；`npm run typecheck` MUST 通过。
<!-- aidcp-edge 0b5f536；两侧该段 diff 为空，typecheck 全绿 -->
- [x] 6.5 客户端内审批的稿件卡在收到 `dispatchState='pending_dispatch'` 时显示「已批准·待下发」；字段缺省（旧云端）时行为 MUST 与今天一致，MUST NOT 显示为失败。
<!-- aidcp-edge 0b5f536 src/electron/renderer/ui-logic.js + renderer.js；ui-logic.test.ts 加两条断言：带阻塞原因可区分、字段缺省时 head/foot/stepStates 与今天逐字一致 -->

## 7. aidcp-console — 待下发态呈现

- [x] 7.1 发布队列与待审详情的 API 类型增量加 `dispatchState`、`dispatchBlockedReason`、`decidedAt`、`waitingMs`。
<!-- aidcp-console 851df74（ContentQueueJourney）+ 2ec8e9a（PanelPublish） -->
- [x] 7.2 已批准待下发的行 MUST 与待审批行视觉可区分，并展示阻塞原因与等待时长；无阻塞原因且超阈值时展示告警标记。
<!-- aidcp-console 851df74（队列卡：标签「已批准·待下发」+ 等待时长 Tag + 阻塞原因 Tag + 无原因超 15 分钟打 error 色「下发侧疑似失联」）+ 2ec8e9a（待审列表 lifecycleTag） -->
- [x] 7.3 字段缺省时回落为今天的呈现，MUST NOT 整页白屏（对齐 console 与 cloud 枚举漂移纪律）。
<!-- aidcp-console 851df74；全部字段可选、未知取值经 labelOf 原样透出不落 default；ContentPage.test.tsx 有专门的「字段缺省回落」用例 -->

## 8. 测试与验收

- [x] 8.1 cloud：`record()` 并发写测试——两个并发授权只有一个 `written:true`，另一个得 `alreadyDecided`，表内活跃行恰好一条。
<!-- aidcp-cloud 3a4ff8e test/publish-agent/publish-approval-store.test.ts。**桩验的是 Store 的分支逻辑（ON CONFLICT 返回空 → 读回活跃行）与 schema 文本（活跃行唯一部分索引），不是真库并发**——真正的原子性只能在真 PG 上证明，已登记为真机验收项 -->
- [x] 8.2 cloud：作废后重新授权测试——`void()` 后同 `requestId` 可再次 `written:true`，历史轮次保留且不被活跃读接口返回。
<!-- aidcp-cloud 3a4ff8e：断言 voidActive 只 UPDATE 不 DELETE、活跃读带 dispatch_state <> 'void'、revision 由 MAX+1 递增。同上，「作废后再写成功」的端到端只能在真库证明 -->
- [x] 8.3 cloud：授权查询不可达测试——下发前复核超时时不下发、不写终态、`dispatch_blocked_reason='approval_unreadable'`。
<!-- aidcp-cloud 3a4ff8e test/publish-agent/publish-dispatcher.test.ts -->
- [x] 8.4 cloud：待下发告警测试——无阻塞原因超阈值发告警，有阻塞原因不发。
<!-- aidcp-cloud 3a4ff8e test/publish-agent/pending-dispatch-watchdog.test.ts（另含「扫描失败不当作无异常」与只扫本机 target） -->
<!-- aidcp-cloud a9ce113 补三条回归：告警必须指明账号（alerts 行 + 文案）；一个接收端都没有时 MUST NOT 计成已送达；候选窗口打满本身要响。原用例全部用 subjectKind='publish' 的行，故完全没覆盖评论行滞留这一形态（见 4.1 / 4.3 修复注） -->
- [x] 8.5 cloud：`execution_target` 隔离测试——非本机 target 的 `pending_dispatch` 行不被兜底扫描拉取。
<!-- aidcp-cloud 3a4ff8e：Store 层断言查询带 execution_target = $1 且实参为本机 target；看门狗断言只传本机 target -->
- [ ] **【已划出计划 2026-07-30，不是待办】** 8.6 cloud：advisory lock 替换后的串行测试——首次登录态写入与客户解绑对同一 `envKey` 仍观察到单一串行顺序。
<!-- BLOCKED: 桩验不了。行锁的串行性是 PostgreSQL 的运行时性质，必须两个并发真事务打同一 envKey 才能证明；用假 pool 只能断言「发了哪条 SQL」，那是把结论写进桩里。已改为静态检查（5.5 的 AC-LOCK-01/02，防回归）+ 真机验收项 -->
- [x] 8.7 cloud + edge：`publish-approval-contract` 验收改判据——从「同一文件路径」改为「同一 `requestId` + 同一 `contentVersion` 的授权判定」；edge 侧断言改为「生产路径无文件依赖」。`AC-PUB-*` MUST 仍全过。
<!-- aidcp-edge 0b5f536 重写 test/acceptance/publish-approval-contract.test.ts（AC-PUB-01 生产路径无文件依赖 / AC-PUB-03 未启用即拒 / 其余判据保留）；cloud 侧 test/acceptance/publish-approval-contract.test.ts 保留（它验的是 parseApprovalActionValue 入口与路径构造，作为影子写实现的契约仍成立），授权判定的新回归落在 3a4ff8e 的 Store / outlet / dispatcher 三组用例 -->
- [x] 8.8 cloud + edge：`npm run test:acceptance` → `npm test` → `npm run typecheck` 三步按序全过（协议改动的既定回归纪律）。
<!-- cloud: acceptance 70/70、full 2937 中 2929 pass 0 fail、typecheck 干净；edge: acceptance 30/30、full 2252/2252、typecheck 干净；console: typecheck 干净、vitest 37 文件 258 pass 1 skip -->
<!-- aidcp-cloud a9ce113 复跑（修完六处静默后）：acceptance 70/70 fail 0；full tests 2944 / pass 2936 / fail 0 / skipped 8；typecheck 干净。edge / console 本轮无改动，沿用上一行实测 -->
- [x] 8.9 console：待下发态呈现与字段缺省回落的聚焦测试。
<!-- aidcp-console 851df74 src/pages/ContentPage.test.tsx 三条：可区分 + 无原因超阈值告警标记 + 字段缺省回落 -->
- [ ] **【已划出计划 2026-07-30，不是待办】** 8.10 端到端（dev）：审批通过后停掉下发侧，确认界面在阈值内显示「已批准·待下发」+ 阻塞原因，阈值后收到告警；恢复下发侧后稿件正常发出，全程无重复发布。
<!-- BLOCKED: 真机验收项，需 dev ECS + 真库 + 真边缘。本 session 不部署、不碰 ECS -->
- [ ] **【已划出计划 2026-07-30，不是待办】** 8.11 关闭影子写前的验证：确认无任何读者读取 `/tmp/aidcp-publish-approve-*`，dev 与 ol 各观察满一个发布周期；关闭动作单独提交、可单独回滚。
<!-- BLOCKED: 真机验收项 + 需要观察期。影子写开关已实装（AIDCP_PUBLISH_APPROVAL_LEGACY_SIGNAL_FILE，默认 true），关闭是一次改 env 即可回滚的独立动作，但关闭本身与观察期不在本 session 范围 -->
