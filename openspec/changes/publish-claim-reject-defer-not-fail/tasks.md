# Tasks — publish-claim-reject-defer-not-fail

> 单仓：`aidcp-cloud`。**动工前必做**：`openspec list` 复核 `publish-trigger-and-apply` 是否仍活跃——
> 它与本 change 争 `publish-scheduler.ts`（热点文件，CLAUDE.md §7 单写者）。在飞则串行等待，勿并行。

## 1. aidcp-cloud — scheduler 给出机器可读形状

- [ ] 1.1 复核 `publish-scheduler.ts:499-517` 的 `tryClaim` 拒绝分支，确认四个拒绝码（`already_running` / `duplicate_source` / `publish_capacity` / 并发已满）的真实出口形状
- [ ] 1.2 让 claim 拒绝携带机器可读码（走既有 `{ result:'skipped'; reason }` 变体，或在 `triggered` 上加 `claimReject`）；保留既有中文 `failureReason` 供人读，勿删
- [ ] 1.3 单测：四个拒绝码各自的出口形状；既有 `/publish` 同步路径的回执文案不回归

## 2. aidcp-cloud — 委托层按形状判 deferred

- [ ] 2.1 `executors.ts` 的 `publishResult`：按新形状把四类判 `{ kind:'deferred', retryAt }`，退避 60s 量级（对齐 `risk_*` 那支）
- [ ] 2.2 **删掉 `executors.ts:133` 的死条件**（`publish_capacity|publish_busy|already_running` 在 `blocked` 分支永不可达），避免下一个人照着它推理
- [ ] 2.3 确认 `risk_*` 仍走 deferred（零回归），人设未绑 / `empty_body` 等仍走 `failed retryable:false`
- [ ] 2.4 单测：撞车 → deferred 且**不**增 failureCount；人设未绑 → 仍诚实不可重试失败（负向回归，spec 明列）

## 3. 回归与验证

- [ ] 3.1 `npm run test:acceptance`（`AC-PUB-*` / `AC-RISK-*` 必须全过）
- [ ] 3.2 `npm test` 全量 + `npm run typecheck`
- [ ] 3.3 驱一次：桩 scheduler 返回 claim 拒绝 → 确认 worker 不再 2 秒烧光预算、而是退避后重试

## 4. 集成与部署

- [ ] 4.1 `scripts/land-change aidcp-cloud publish-claim-reject-defer-not-fail --yes`
- [ ] 4.2 部署前探 ECS 现状 → 按 §5 安全序列部署 dev → 回写 sha（须已推送，判据 `git merge-base --is-ancestor`）

## 5. 真机验收与收口

- [ ] 5.1 真机项登记 `docs/real-machine-acceptance-backlog.md` 簇 86：**撞车时不该出失败卡**——同账号一轮发帖在跑时再发 `/publish <昵称>`，第二条应退避后真发出去（对照 `delegated-terminal-failure-reason` 那批验的是「出卡时说不说得清原因」）
- [ ] 5.2 `openspec validate publish-claim-reject-defer-not-fail --strict` → archive（MODIFY `user-delegated-tasks`，与 `delegated-terminal-failure-reason` 同 capability → 归档须串行、注意依赖序）
