# Tasks — facebook-manual-comment-keepopen-lease

> cloud-only（`aidcp-cloud`），边缘无改动（`main.ts:873` FB 命令入口已按 `payload.taskId` 门控）。landed cloud **0bb45f6** + deployed dev。

## 1. aidcp-cloud — FB 边端步骤透传 taskId

- [x] 1.1 `facebook-edge-steps.ts`：`FacebookEdgeStepsDeps` 加 `taskId?: string`。<!-- aidcp-cloud 0bb45f6 -->
- [x] 1.2 三条 envelope（`search.execute`/`note.open`/`interaction.comment`）payload 各挂 `...(deps.taskId ? { taskId } : {})`（无租约旧构造零回归）。<!-- aidcp-cloud 0bb45f6 test 2 例 -->

## 2. aidcp-cloud — FB 定向评论路径包 keep-open 租约

- [x] 2.1 `runFacebookTargetedTaskBody`：cloud-only 前置留租约外；「建 steps → search → pick → open → compose → validate → contact → shadow → approve → submit → audit」整段移进 `edgeTaskLeases.withLease({kind:'comment_prepare', priority, leaseMs})`，steps 用 `lease.taskId` 构建（conn.edgeId/bus 捕成 const 破闭包收窄丢失）。<!-- aidcp-cloud 0bb45f6 -->
- [x] 2.2 `priority = options.manualOverride ? 'human' : 'automatic'`。<!-- aidcp-cloud 0bb45f6 test 派生 -->
- [x] 2.3 `FB_KEEP_OPEN_LEASE_MS = 6min`：**对抗复核后从 4min 抬到 6min**，严格 > 撰写(~180s LLM 天花板)+人审(90s)+搜索/开帖+往返——否则边端 idle 计时在 note.open→comment 纯云窗内过期、解冻自治浏览滚走页面、已授权评论提交被挡。<!-- aidcp-cloud 0bb45f6 test 断言 leaseMs>270s -->
- [x] 2.4 租约获取超时（`EdgeTaskLeaseError`）catch → audit 诚实非提交（不打去重、可重试），非 acquire 失败 rethrow 交外层。<!-- aidcp-cloud 0bb45f6 test acquire 超时 -->
- [x] 2.5 诚实：被抢占/提交超时走既有 `reallySubmitted=false`（不打去重、可重试）；不评错帖、就地核对身份、AC-PUB 全不动。<!-- aidcp-cloud 0bb45f6 -->

## 3. aidcp-cloud — 测试

- [x] 3.1–3.4 单测：keep-open 单租约包住 search→approve→submit（kind=comment_prepare、priority 派生、leaseMs>270s）/ 三命令带 taskId / acquire 超时诚实非提交。facebook-edge-steps.test.ts +2、comment-scheduler.test.ts +3。<!-- aidcp-cloud 0bb45f6 -->
- [x] 3.5 红线：AC-PUB 保持；XHS 路径与 RoleDispatcher 浏览闭环零回归（既有 FB happy-path 全过 lease-wrapped 代码）。<!-- aidcp-cloud 0bb45f6 acceptance 54/54 -->
- [x] 3.6 `test:acceptance`(54/54) → `test`(2261 pass/0 fail) → `typecheck` 全过。<!-- aidcp-cloud 0bb45f6 -->

## 4. 对抗性复核 + 集成 / 部署 / 回写

- [x] 4.1 对抗性复核 diff（wf_933f178c，3 视角）：唯一确证=leaseMs 薄裕度（compose+approval 可 >4min 致租约过期丢已授权评论，诚实非假成功）→ 修 2.3（4min→6min + 测试锁）。无 blocker。<!-- aidcp-cloud 0bb45f6 -->
- [x] 4.2 合入 master：rebase origin/master（无冲突）、复跑 acceptance+full+typecheck 全绿、ff-push。<!-- aidcp-cloud 0bb45f6 landed master -->
- [x] 4.3 默认部署 dev：clean snapshot(git archive 0bb45f6) rsync（deps 未变、免 npm ci）→ restart → healthcheck 全绿（svc active / 8787+8090 / CommentScheduler 就绪 / 飞书长连接 / 无错误）。<!-- 2026-07-15 deployed dev 121.89.85.150; 备份 cloud.bak.20260715-223307.tar.gz -->
- [x] 4.4 真机灰度项归 backlog 簇 48/58。<!-- 见 backlog -->
- [x] 4.5 `openspec validate --strict` → landed+deployed → archive。<!-- 2026-07-15 archived -->

## 残留（登记，不在本 change 修）

- XHS keep-open（`comment-scheduler.ts:1307` 的 4min）同一 leaseMs 薄裕度隐患（预算注释只算 ~150s、未含撰写）——越界不动、登记 backlog 待 XHS owner 一并抬。
- FB 边端对失配 taskId 命令静默丢弃（`main.ts:873` warn+return 无回执）→ 被抢占报 timeout 而非 preempted，语义略糙但诚实（非提交、可重试）。
