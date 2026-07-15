## 1. 证据与设计闸

- [x] 1.1 用 dev 任务事件和源码确认重复通知机制、实际周期及未发生重复平台尝试。 <!-- task 69324efc...: 19 repeated claim_released events at ~35s; attempt stayed 1, success/failure stayed 0 -->
- [x] 1.2 完成多 worker、审批变化、并发控制、重启恢复和通知误去重的对抗性评审，修订 blocker 后再实施。 <!-- adversarial-review.md: 2 BLOCKER + 3 HIGH resolved in design -->
- [x] 1.3 运行 proposal/design/spec/tasks 的 OpenSpec strict 预检。 <!-- 2026-07-15 strict validation pass -->

## 2. Cloud 静默等待审批机制

- [x] 2.1 扩展 Pg/Memory store：waiting_approval claim 保持业务状态和版本，新增带 token 条件的静默 release。 <!-- cloud store.ts: waiting claim retains status/version; token-guarded silent release -->
- [x] 2.2 更新 DelegatedTaskWorker：无变化等待结果不调用用户可见 update，审批变化仍走现有真实收敛路径。 <!-- worker silent branch bypasses onTaskUpdated; approval success/terminal paths unchanged -->
- [x] 2.3 增加用户可见语义指纹通知去重，忽略内部 claim/时间字段但保留状态、计数、结果和控制意图变化。 <!-- DelegatedTaskNotificationGate; waiting internal steps normalized -->

## 3. 回归验证

- [x] 3.1 补 store/worker 测试：多轮等待不增版本、不增 attempt、只通知一次且 lease 可恢复。 <!-- targeted worker/notification suite 8/8 pass -->
- [x] 3.2 补审批通过/驳回、并发取消和通知指纹测试，确保真实变化不被吞掉。 <!-- approval completion, cancellation race and semantic fingerprint covered -->
- [x] 3.3 依次运行 cloud 相关 acceptance、full tests、typecheck，并记录结果。 <!-- acceptance 52/52; full 2145/2145; typecheck pass -->
- [x] 3.4 运行 `openspec validate delegated-task-waiting-approval-notification-dedupe --strict` 与 `git diff --check`。 <!-- strict + both worktree diff checks pass; PostgreSQL EXPLAIN of claim query passes without execution -->

## 4. 提交、集成与 dev 验证

- [ ] 4.1 仅提交本 change 文件，推送同名分支并按快进规范集成 cloud master/control main，不 force。
- [ ] 4.2 运行 `scripts/deploy-target dev --check`，从 clean eligible cloud master 备份并部署 dev，不触碰 isales、不部署 OL。
- [ ] 4.3 验证服务、端口、health、Feishu、PostgreSQL，并观察现有 waiting_approval 任务至少两个旧通知周期不再新增重复事件/卡片。
- [ ] 4.4 回填 commits、测试、部署和诚实验证边界，严格校验后归档并清理同名 worktree/分支。
