# Tasks — session-start-quota-honest-sleep

> 范围：**aidcp-cloud 单仓两处 + 本仓 spec/台账**。edge / console / 协议零改动。不出安装包。

## 1. aidcp-cloud — 会话启动现问配额

- [ ] 1.1 `src/orchestrator/role-dispatcher.ts` `restartSession()`：在 `this.sessionStartedAt = this.clock();` 之后、`this.eventBus.emit('feed.entered', ...)` **之前**插入现问一次 + 被拒即 `sleepForViewQuota(decision)`
      🔴 **红线：必须在 `emit` 之前**。EventBus 进程内同步派发，下游角色链可能在该 emit 内同步走到 `sendCommand` ⇒ 装在 emit 之后 = 首批命令漏过刹车，且间歇性、测试可全绿。仓内同族判例见 memory `fb-like-gate-sync-emit-race`
      🔴 **红线：不区分窗口，一律现问 + 按 `decision.retryAfterMs` 睡**。minute/hour 被拒睡 60s 后自动重驱（净行为同今日、只是提前），day 被拒睡到明天。加窗口分支＝无收益的额外分叉
      🔴 **红线：MUST NOT 拒签会话**。会话照开、刹车踩死；`sleepForViewQuota` 内部自带 `if (this.viewQuotaSleeping) return` 幂等
      **不要动 `:1556` 的 `cancelViewQuotaSleep(false)`**——它在事故路径（重连、对象重造）上确是 no-op，但在同连接重启路径（续场 / 面板 / 绑人设自启）上是真取消。**先清后问**，见 design §3

- [ ] 1.2 复核插入点前置条件：`sleepForViewQuota` 会调 `this.sessionMonitor?.pauseClock('view_quota')`，而 `SessionMonitor.startedAt` 在 `:1581` 的 `roles.forEach(r => r.subscribe())` 才重置 ⇒ 插入点必须在 `:1581` 之后。选定点（`sessionStartedAt` 赋值后）同时满足「在 subscribe 之后」与「在 emit 之前」，无第二个合法位置

## 2. aidcp-cloud — 休眠闸补日志（红线）

- [ ] 2.1 `src/orchestrator/role-dispatcher.ts:765-767`：休眠支现为裸 `return false`、**无日志**。补节流日志，格式照抄同函数 `:778-782`（`comment_inflight` 支）：`[RoleDispatcher] command.suppressed reason=view_quota_sleep action=... account=...`
      🔴 **必须节流**：日窗休眠 ≈8h、存活探针每 240s 一条 ⇒ 约 120 条/夜/账号 × 车队规模。节流键 `(account, reason)`；同一轮休眠至少留首条
      🔴 **节流 MUST NOT 退化成不打**——本 change 让这道闸从边角升为主刹车，不打日志＝把「静默丢弃」红线从偶发扶正成常态

## 3. aidcp-cloud — 测试（克制）

- [ ] 3.1 单测（**少数用例即可**，见 memory `test-case-restraint`）：
      ① **核心**：`explainView` 桩返回 `{allowed:false, reason:'quota:day', retryAfterMs:X}` → `restartSession()` → 断言 `viewQuotaSleeping` 为真、且**首个 emit 之后零条浏览命令下发**（这条即红线三本身，typecheck 抓不到）
      ② **反向不变量**：同上场景断言**未下发 `session.end`**、会话仍 `sessionActive`
      ③ **先清后问**：对象上先置陈旧休眠标记 + `explainView` 返回 allowed → `restartSession()` → 断言休眠已清、会话正常开跑（钉住「保留 `:1556`」不被误删）
      ④ 日志节流：同一轮休眠内多次被扣命令 → 断言记录条数被节流且 ≥1
- [ ] 3.2 `npm run test:acceptance` → `npm test` → `npm run typecheck`
      🔴 `typecheck` **不得接 `| tail`**，退出码须取自 tsc 本身（见 archive `cooldown-as-backstop-not-quota` 1.4 的守则）

## 4. 可选（同文件顺手，不扩范围）

- [ ] 4.1 `explain()` 对 `state:frozen` / `state:restricted` 不返回 `retryAfterMs` ⇒ 回落 `VIEW_QUOTA_RECHECK_FALLBACK_MS`(60s) 重判，且日志把风控终态贴成「view 配额暂不可用」——**标签不诚实**。**是既有行为**（`:2269` 那道闸今天就这样），非本 change 引入。若顺手改：日志按 `decision.reason` 前缀分流（`quota:*` 才说配额），**MUST NOT** 改判定逻辑

## 5. aidcp（本仓）— spec 与台账

- [ ] 5.1 spec delta：`interaction-risk-gating` **ADDED ×2**（会话启动现问 + 休眠期扣命令可观测）。既有要求 `:501-506`「临时 view 配额不阻止会话启动」**不改**——它显式限定 `quota:minute` / `quota:hour`，与新要求互补不冲突
      ⚠️ **`validate --strict` 抓不到 delta 语义错**（不校验 MODIFIED 目标是否存在、不校验整条替换是否丢内容）。本 change 全 ADDED、风险低，但仍须人肉对着主 spec 确认无重名要求
- [ ] 5.2 `openspec validate session-start-quota-honest-sleep --strict` → valid
- [ ] 5.3 tasks.md 回写 sha（**须取自已推送提交**，见 memory `tasks-md-sha-must-be-pushed`）
- [ ] 5.4 部署 dev（`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck）。🔴 绝不碰同机 isales

## 6. 后续（不在本 change 内，须登记）

- [ ] 6.1 **另起 change D（边缘侧、要出包）**：唤醒带原因 / 认租约。
      内容：`main.ts:1412` `wakeFromStandby` 不带唤醒原因；`:1456-1463` 唤醒后无条件 `browse.start()`（而 `:1114` / `:1184` 两处装配点都有 `taskCoordinator.blocksBrowse` 守卫，`:1463` 是唯一漏的）；FB 首屏 feed 上报未计入写者记账（违反 `facebook-session.ts:357` 自己的注释）；`session.end` 打到停放的浏览器应为 no-op
      🔴 **陷阱（务必写进 D 的 tasks）**：**不要直接复用 `blocksBrowse`**——`edge-task-coordinator.ts:324-326` 与 `:275-277` 口径不同，**不覆盖「正在唤醒」中间态** ⇒ 守卫静默失效且测试全绿
- [ ] 6.2 **backlog 登记**：`sliding-window-counter.ts:38` 的 `quota <= 0 → retryAfterMs undefined` 潜在雷（本 change 打不到：FB 慢启动第 1 天 view 上界 `[10,20]` 非 0）
- [ ] 6.3 **backlog 登记（真机观测）**：边缘约每 5 分钟断连 / 重连 churn —— **根因未查**，可能是独立缺口。它会重置空闲时钟 ⇒ 看门狗 1h 结束会话这条尾巴今天可能从未触发过。本 change 上线后需观测一夜：churn 仍在则行为收敛不变；churn 停了则 1h 尾巴首次现形（→ endSession → `:1604` 取消休眠 → 休息 → 续场闸六道判据无配额 → restartSession → **本 change 重新现问 → 再睡**，闭环安全）
