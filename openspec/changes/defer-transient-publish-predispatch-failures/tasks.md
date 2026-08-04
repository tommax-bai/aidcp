# Tasks

## 1. aidcp-cloud — 提交前失败分档

- [ ] 1.1 `src/publish-agent/command-sequencer.ts`：`PublishSequenceResult['outcome']` 增加「零副作用可恢复」档；
      逐档注释同步（`:76-84` 的终局说明必须与实际接住的情形一致）。
- [ ] 1.2 `classifyFailureOutcome`（`:370-383`）末位的无条件 `return 'failed_before_submit'` 改为按原因分流：
      结构性集合（`content_too_long` / `all_images_failed` / `not_approved` 等，实读代码穷举）落结构性档，
      其余落可恢复档并具名标注「未识别提交前原因」+ 保留原始串。
      **MUST NOT 动前三态优先级**（`submitted || submitDispatchedNow` → 已提交；`yield_timeout` → 已提交）。
- [ ] 1.3 结构性原因集合与可恢复集合 SHALL 互斥且对提交前原因全集穷尽——按 `docs/stop-or-continue.md` §7 的断言写一条测试。

## 2. aidcp-cloud — 下发段按分档处置

- [ ] 2.1 `src/publish-agent/publish-dispatcher.ts:825-859` 新增可恢复档分支，对齐 `:839-848` 的 `preempted` 样板：
      保持 `pending_approval`、`releaseApprovalToPending`、素材 `release`、**不** `markApprovalProgress('consumed')`、
      **不** `recordSeqFailure`、事件驱动重投。
- [ ] 2.2 `settleFacebookMedia`（`:547` 的 outcome 联合类型）同步新档位映射：可恢复档走 `release`。
- [ ] 2.3 可恢复重投计数与上限（默认 2，env 可配），与 `consecutivePreemptions` 分开计；
      耗尽后落 `failed` 并把通知文案写成「重试 N 次未成」。**恢复预算只由本档失败消费。**
- [ ] 2.4 熔断计数排除零副作用两档（`recordSeqFailure` 只由「页面状态未知」触发）。

## 3. aidcp-cloud — 测试

- [ ] 3.1 单测：提交前抖动 → 保持待审 + 授权保留 + 素材归还 + 熔断计数不变 + 触发重投。
- [ ] 3.2 单测：重投耗尽 → `failed` 终态且文案为「重试 N 次未成」。
- [ ] 3.3 单测：未识别提交前原因 → 走可恢复档 + 日志带原始串（**不得**被折进已有失败值）。
- [ ] 3.4 回归断言：`submitted_unconfirmed` / `yield_timeout` 的处置逐字未变（跨过提交点绝不重投）。
- [ ] 3.5 `npm run test:acceptance` 全过（`AC-PUB-*` 必须全绿）→ `npm test` → `npm run typecheck`。

## 4. 交付

- [ ] 4.1 `openspec validate defer-transient-publish-predispatch-failures --strict` exit 0。
- [ ] 4.2 提交推送 `aidcp-cloud` master + 控制仓 main，回写本文件 sha。
- [ ] 4.3 部署 dev 并按 CLAUDE.md §5 安全序列核验（备份 → rsync → restart → healthcheck）。
