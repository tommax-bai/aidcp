## 1. aidcp-cloud — 分诊循环到零（D1/D4）

- [x] 1.1 `agents/notification-triage.ts`：改循环语义为「每处理完一类后重读首页三栏未读计数，任一 > 0 即继续，直到三栏全 0」，取代「标记已处理、≤N 轮、不回头」 <!-- aidcp-cloud f9b2092 -->
- [x] 1.2 加最大尝试上限（轮次/时长，与现有巡视总超时兜底对齐），到顶仍有栏未清 → 记该栏未清原因并结束本趟（诚实放弃，不空转、不假报已清） <!-- aidcp-cloud f9b2092 DEFAULT_MAX_ATTEMPTS_PER_CATEGORY=3，可经 maxAttemptsPerCategory 覆盖 -->
- [x] 1.3 `agents/excursion-resumer.ts` 与收敛口径：`notification.triage_done`（或等价终止信号）改为「三栏=0 或 到上限放弃」时发，确保任一出口仍恰好一次「解除软暂停 → 回 feed」 <!-- aidcp-cloud f9b2092 triage_done 已涵盖两种终止；resumer 单一收敛逻辑不变，仅补注释 -->
- [x] 1.4 单测：多类未读循环到三栏清零；某栏未清在上限内重试；到上限诚实放弃且仍恢复浏览 <!-- aidcp-cloud f9b2092 新增 3 个 triage 用例（loop-to-zero/上限放弃/放弃后处理低优先） -->

## 2. aidcp-cloud — 去「已处理过」准入闸（D3）

- [x] 2.1 `agents/notification-gatekeeper.ts`：删除 epoch「已处理过」判定（`lastHandledEpoch` 比较），保留「正在处理中」闸（`excursionActive`）与硬暂停闸（`isHardPaused`） <!-- aidcp-cloud f9b2092 -->
- [x] 2.2 `agents/session-context.ts`：移除 `lastHandledEpoch` 字段及相关读写（`beginExcursion`/`endExcursion`/`reset`），保留 `excursion active`/`processedCategories`（若循环改造后仍需）与 `notifiedItemKeys` <!-- aidcp-cloud f9b2092 processedCategories(Set)→categoryAttempts(Map)；notifiedItemKeys 保留并补注释 -->
- [x] 2.3 单测：处理过一波后新「无→有」仍开巡视；巡视进行中新一波不开并发第二趟（由 active 闸拦，新波由循环吸收）；硬暂停期间不开巡视 <!-- aidcp-cloud f9b2092 gatekeeper 用例改写（去 epoch）+硬暂停用例保留 -->

## 3. aidcp-cloud — 去重维度解耦（D5）

- [x] 3.1 确认并固化「飞书通知去重水位」（`notifiedItemKeys`）保留、与「巡视触发去重」解耦；代码注释标明二者是两个维度，勿连带误删 <!-- aidcp-cloud f9b2092 session-context + deduper 头注释明示两维度正交 -->
- [x] 3.2 回归：清零循环反复扫到同一条已推过飞书的评论/@ 不重复推送；巡视失败/超时不推进已通知水位（失败可干净重来、不静默漏真评论） <!-- aidcp-cloud f9b2092 由既有 deduper(all_seen)/notifier(失败不推水位) 用例覆盖，全绿 -->

## 4. aidcp-edge — 评论/@ 滚到底清零（D6）

- [x] 4.1 `browse/browse-session.ts` 评论/@ 浏览：改「滚到底 / 直到不再有新项或角标清零」，替代固定 3 屏滚动；终止判据按 design Open Question 定（连续 K 次无新项 或 角标清零，取先到） <!-- aidcp-edge 0899e84 采「连续 STABLE_ROUNDS=2 次评论行数不增」判到底 + HARD_CAP=max(scrollMax,12) 有界 -->
- [x] 4.2 赞/关注「看一眼即清」保持不变（已真机验证） <!-- aidcp-edge 0899e84 viewNotificationCategory 未改 -->
- [ ] 4.3（低优先）`browse/notification-monitor.ts`：reconcile 入口红点 count 与首页 per-tab 计数口径（探针实测入口 4 vs 三栏 2），使触发信号与清零终止信号一致归零 <!-- 待真机 DOM 校准；当前两者最终都归 0 故非阻塞，不盲改扫描判据以免引入回归 -->

## 5. 测试与真机校准

- [x] 5.1 cloud：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全过（安全红线 AC-* 不破） <!-- aidcp-cloud f9b2092 acceptance 26/26 + full 665/665 + typecheck clean -->
- [x] 5.2 edge：`npm run typecheck` + 相关 `npm test` <!-- aidcp-edge 0899e84 typecheck clean + full 326/326 -->
- [ ] 5.3 真机复跑 `aidcp-edge/scripts/notification-clear-probe.ts`：在「评论/@」有未读时确认该类也清零（赞/关注已验证）；并验证「滚到底」对未读多于一屏的清零 <!-- gated：需真机 + 评论/@ 未读；滚到底需新 edge 跑起来 -->
- [ ] 5.4 真机：处理一波→再制造新未读→确认仍触发新巡视（去 epoch 行为）；巡视中来新消息不开并发、由循环吸收 <!-- gated：需真机 E2E（部署 cloud + 跑 edge） -->

## 6. 部署与收尾

- [x] 6.1 dry-run 暴露随附 master 增量范围（ECS 全量快照口径），向用户确认后再部署 <!-- 06-25 ECS 实测处于 a38fb96（pre-change：lastHandledEpoch×6/categoryAttempts×0）→ 生产代码增量恰为 f9b2092 一笔（我的 5 src）；其余皆滞后 test/ 文件，不被 tsx src/server.ts 加载、无害 -->
- [x] 6.2 部署 cloud（先备份 → rsync `--exclude .env/node_modules/.git` → 重启 `aidcp-cloud.service` → healthcheck） <!-- 06-25 备份 cloud.bak.20260625-104620.tar.gz + .env.bak.20260625 → rsync(az,excl env/nm/git/dist) → restart(ActiveEnter 10:47:54) → healthcheck 全绿：active running + :8787 监听 + 飞书长连接已建立 + PG(锚点缓存/RiskController PgRiskStore)就绪 + 无 error；isales 未碰 -->
- [x] 6.3 部署后 grep 关键文件内容确认新码生效 + 看新启动日志（非仅信 rsync 回执） <!-- 06-25 grep 实测：session-context/gatekeeper lastHandledEpoch=0、triage incrementCategoryAttempts=1、categoryAttempts=7（新码已生效）；启动日志干净 -->
- [ ] 6.4 归档顺序：本 change 的 spec delta 依赖 `notification-monitor` 先归档；`openspec validate notification-clear-to-zero --strict` 通过后再 archive <!-- gated：notification-monitor 仍 active；且等真机验收 5.3/5.4 后再归档 -->
