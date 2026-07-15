# Tasks — comment-approval-target-hold

> cloud-only（`aidcp-cloud`），边缘无改动。`role-dispatcher.ts` 为热点单写文件、与活跃 change `lease-strict-preemption` 同区 → **集成串行**：合入 master 前先 rebase 最新、解冲突、复跑闸。

## 1. aidcp-cloud — 评论支线暂停态（进入 / 出口）

- [ ] 1.1 在评论支线开始的最早稳定点进入暂停态：`ctx.setBrowseSuspended(true)` + `SessionMonitor.pauseClock('comment_inflight')`，覆盖评估/撰写/去 AI 味/审批全程（D2）。确定进入事件锚（评估阶段起点 / `interaction.completed` 派生锚），保证覆盖撰写窗竞态且不与串行 hold 冲突。
- [ ] 1.2 终局解除（D4）：`comment.approved` / `comment.skipped` 处理器**先** `setBrowseSuspended(false)` + resume clock，**再**下发 approved 评论命令 / `open_note{purpose:'navigate'}` 迁移命令；确保评论/迁移命令不被残留暂停态扣住。
- [ ] 1.3 防"同步 skip 卡死"：评估即 `comment.skipped`（同 tick）时进入→解除顺序不残留暂停标志（复用现有对 `comment.cleared` 同步 skip 的防御思路）。
- [ ] 1.4 `browseSuspended` 并发复用处理：若评论支线可能与巡视 / 昵称采集同窗置位，改引用计数或独立标志取并集；否则保留单标志最小改（在代码里坐实是否存在并发场景后决定，注释说明）。
- [ ] 1.5 移除 / 收敛旧 `approvalInFlight` 单点补丁：其 idle-nudge 抑制被暂停态覆盖后，删除或改为断言不再单独承载"停在帖上"职责（避免双写语义漂移）。

## 2. aidcp-cloud — 覆盖两条滚走源 + 推迟结束

- [ ] 2.1 撰写窗 no_target 重扫（H1）：确认 `rescan_after_stale_target`（`role-dispatcher.ts:2223-2234`）经 `sendCommand` 被暂停态扣住；如它绕过统一出口则改为经出口 / 显式门控。互动如实记失败、不重扫、不假成功。
- [ ] 2.2 审批窗 stray 命令（H2）：确认 `open_note` 换帖 / `scroll` / `refresh` / feed 续滚等在暂停态下经统一出口全部被扣；补测覆盖。
- [ ] 2.3 推迟 `session.should_end`（D3）：暂停期间由动作数/时长/配额触发的 `should_end` 推迟到终局后评估，MUST NOT 窗内结束会话废掉在审评论；`session.end` 终局解除后仍可达。

## 3. aidcp-cloud — 测试（回归纪律：先 test:acceptance 再全量再 typecheck）

- [ ] 3.1 acceptance：撰写窗内并行点赞回 `no_target` → 不下发任何离开待评论帖的命令、账号停在帖上（spec Scenario a）。
- [ ] 3.2 acceptance：审批窗内 stray 边缘上报 → 不下发 `open_note`/`scroll`/`refresh`（spec Scenario b）。
- [ ] 3.3 acceptance：审批窗内动作数/时长/配额触阈 → 不提前结束会话、评论支线终局后再评估（spec Scenario c）。
- [ ] 3.4 acceptance：终局先解除暂停再下发评论/迁移命令、命令必达（spec Scenario 终局解除顺序）。
- [ ] 3.5 acceptance：看门狗按"有意暂停"、不误判 idle、`session.end` 仍可达（spec Scenario 不卡死）。
- [ ] 3.6 红线保持：AC-PUB（未授权/超时一律 `comment.skipped` 不发）与 AC-PROTO 全过；XHS 路径（两 surface 同 detail）零回归。
- [ ] 3.7 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全过。

## 4. 集成 / 部署 / 回写

- [ ] 4.1 合入 master 前 `git fetch` + rebase 最新、解 `role-dispatcher.ts` 与 `lease-strict-preemption` 的冲突、复跑 acceptance + typecheck。
- [ ] 4.2 默认部署 `dev`（安全序列：`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck）。
- [ ] 4.3 tasks.md 回写 commit-sha（`<repo> <sha> 备注`），真机灰度项归 `docs/real-machine-acceptance-backlog.md`（并入 FB 灰度簇）。
- [ ] 4.4 `openspec validate comment-approval-target-hold --strict` 通过 → 待部署+真机验收后 archive。
