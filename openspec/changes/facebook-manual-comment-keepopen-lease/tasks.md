# Tasks — facebook-manual-comment-keepopen-lease

> cloud-only（`aidcp-cloud`），边缘无改动（`main.ts:873` FB 命令入口已按 `payload.taskId` 门控）。`comment-scheduler.ts` 属租约/命令映射热点片区 → 集成串行：合入前 rebase 最新、复跑闸。

## 1. aidcp-cloud — FB 边端步骤透传 taskId

- [ ] 1.1 `facebook-edge-steps.ts`：`FacebookEdgeStepsDeps` 加 `taskId?: string`。
- [ ] 1.2 三条 envelope payload 各挂 taskId：`search.execute`（:168）/ `note.open`（:204）/ `interaction.comment`（:233），用 `...(deps.taskId ? { taskId: deps.taskId } : {})`（无租约旧构造零回归）。

## 2. aidcp-cloud — FB 定向评论路径包 keep-open 租约

- [ ] 2.1 `runFacebookTargetedTaskBody`：cloud-only 前置（config / 配额闸 / 连接检查）留在租约外；把「建 steps → search → pick → open → compose → validate → contact → shadow → approve → submit → audit」整段移进 `this.deps.edgeTaskLeases.withLease({ edgeId, kind:'comment_prepare', priority, leaseMs: FB_KEEP_OPEN_LEASE_MS }, async (lease) => {...})`，steps 用 `lease.taskId` 构建。
- [ ] 2.2 `priority` 由 `options.manualOverride ? 'human' : 'automatic'` 派生。
- [ ] 2.3 `FB_KEEP_OPEN_LEASE_MS` 覆盖 搜索+读+人审超时(90s)+提交 最坏耗时（≈4min，对齐 XHS）。
- [ ] 2.4 租约获取超时（`EdgeTaskLeaseError`）在 body 内 catch → audit 诚实非提交终态（不打去重、可重试），不落外层泛化 exception。
- [ ] 2.5 保持诚实：被抢占 / 提交超时走既有 `reallySubmitted=false`（不打去重、可重试）；不评错帖、发布前就地核对身份、AC-PUB 全不动。

## 3. aidcp-cloud — 测试（回归纪律：先 test:acceptance 再全量再 typecheck）

- [ ] 3.1 单测：FB 定向评论在 keep-open 租约内完成 search→open→approve→submit（断言 withLease 被调、kind=comment_prepare、priority 按 manual/auto）。
- [ ] 3.2 单测：三条 FB 命令 envelope 都带 taskId（= 租约 taskId）。
- [ ] 3.3 单测：租约获取超时 → 诚实非提交终态、不打去重。
- [ ] 3.4 单测：提交被抢占 / 超时 → `reallySubmitted=false`、不打去重、可重试。
- [ ] 3.5 红线：AC-PUB（未授权 / 人审超时绝不提交）保持；XHS 路径与 RoleDispatcher 浏览闭环零回归。
- [ ] 3.6 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全过。

## 4. 对抗性复核 + 集成 / 部署 / 回写

- [ ] 4.1 对抗性复核 diff（租约边界 / taskId 透传完整性 / 死锁自锁 / 诚实终态 / 与 lease-strict-preemption 交互），修 confirmed 发现 + 回归。
- [ ] 4.2 合入 master 前 `git fetch` + rebase、解冲突、复跑 acceptance + typecheck；ff-push。
- [ ] 4.3 默认部署 dev（clean snapshot rsync → restart → healthcheck）。
- [ ] 4.4 tasks.md 回写 commit-sha；真机灰度项归 `docs/real-machine-acceptance-backlog.md`（簇 48/58 手动 /comment）。
- [ ] 4.5 `openspec validate facebook-manual-comment-keepopen-lease --strict` → landed+deployed → archive。
