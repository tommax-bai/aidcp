# Tasks — standby-covers-idle-waits

> 目标：**停工就让位**。把「让账号停下来的闸」和「让它关浏览器的闸」接上线，使一台机器的账号天花板从约 6 抬到约 14。
>
> 前置事实（已由 `browser-slot-scheduling` 落地，本 change 的收益算式依赖它）：**唤醒是原地重开浏览器、不重启核心进程、云端连接不断**（`aidcp-edge/src/electron/main.cjs:2069`），成本约 30–45s，且经全局串行启动队列削峰。

## 0. 前置核实（已完成 —— 三条结论改写了设计）

- [x] 0.1 **`ui.snapshot` 已有一条约 60s 的心跳链**，且**带 browserStandby**。链由 hello 起头（`ui-snapshot.ts:136`），此后 `pushDailyUsageSnapshot` 自己续自己（`:215`、`:241`）；周期来自 minute 窗的 `refreshAt = now + 60s`（`server.ts:1612`），**与配额是否将释放无关**、恒定约 60s。冷待机期间核心进程与云端 WS 不断 → 心跳继续 → **提示照常送达**。
- [x] 0.2 **风控状态迁移今天不触发任何推送**（`risk-controller.ts` 的 `applySignal` / `setQuotaLevel` 只改内存 + 落库，无 emitter / callback / EventBus）。**但因 0.1 的 60s 心跳，无需新建推送**——解冻后最坏 60s 内下一跳即带 `eligible=false`，边缘据此唤醒。**原计划的「状态变化推送」由此取消（YAGNI）。**
- [x] 0.3 恢复时刻：
      **(a) 周历** —— **已有现成函数** `msUntilNextActive(mask, now)`（`risk/session-limits.ts:104`），直接复用，**不新写**。整周全关 → 返回 `null`（无恢复时刻 → 走「回访」语义）。掩码 168 位、**周一起头、服务器本地时区、小时粒度**。
      **(b) 活跃时段窗口** —— 无现成函数，需新写；规则：下一次出现 `startMin` 的本地时刻，已过则 +24h（**该规则对跨午夜 `start>end` 同样正确**）。
      **(c) 每日场数 / 分钟** —— 恢复时刻 = 下一个**服务器本地**日界。**坑：两套日界并存**——续场计数 `dailyTally` 按 `localDayKey`（服务器本地时区，`role-dispatcher.ts:1495`），而风控 day 窗口与 dailyUsage 按**上海**日界（`time/shanghai-day.ts`）。**MUST NOT 复用 `nextShanghaiDayStartMs`**，否则进程 TZ ≠ Asia/Shanghai 时算错。
      **(d) 风控 frozen / restricted** —— **没有任何自动恢复**：状态机里虽有恢复常量与 `recoverIfEligible`，但**全仓无人调用、也从不发 `recovered` 信号**；唯一出口是运营手动改状态。故**MUST NOT 编造 `wakeAt`**——只能走「回访」语义。
- [x] 0.4 **从 server.ts 拿不到续场计数**：`RoleDispatcher.dailyResume` / `dailyTally` / `canAutoResume` 全私有、每连接一实例，`ConnectionRuntimeRegistry` 无 `dispatcherForAccount`。最小改动三处（照抄现成的 `sessionUsageForAccount` 形状）：dispatcher 加只读裁决快照 → registry 加按账号取用 → server 接线。
      **约束**：`dailyResume` 是每连接内存 Map，**边缘重连即清零**（既有行为，不在本 change 范围）。冷待机**不重连**（核心与 WS 不断），故待机期间计数不丢。

## 1. aidcp-cloud — 待机提示的产出侧

- [x] 1.1 `src/risk/resume-limits.ts`：新增纯函数 `nextActiveWindowStartAt(now, win)`（活跃时段下一个窗口开始，**含跨午夜**）与 `nextLocalDayStartAt(now)`（**服务器本地日界，MUST NOT 用上海日界**——见 0.3c）。纯函数、可单测。 <!-- aidcp-cloud 33934d6 nextActiveWindowStartAt / nextLocalDayStartAt（本地日界，非上海） -->
- [x] 1.2 ~~新写周历 helper~~ **取消**：复用现成的 `msUntilNextActive`（`risk/session-limits.ts:104`）。 <!-- 取消：复用现成的 msUntilNextActive -->
- [x] 1.3 `src/orchestrator/role-dispatcher.ts`：新增只读公开方法 `resumeGateSnapshot(now)`，返回 `{ blocked, reason: 'week'|'active_window'|'daily_sessions'|'daily_minutes'|'risk'|'not_ready'|null, resumeAt?: number }`；**`canAutoResume()` 改为基于它实现**，使两套判据不可能漂移（零行为回归）。 <!-- aidcp-cloud 33934d6 resumeGateSnapshot；canAutoResume 已改为基于它实现 -->
- [x] 1.4 `src/orchestrator/connection-runtime.ts`：加 `resumeGateForAccount(accountId, edgeId?)`，照抄 `sessionUsageForAccount`（:280）的 edgeId 命中 / fallback 形状。 <!-- aidcp-cloud 33934d6 resumeGateForAccount -->
- [x] 1.5 `src/comm/browser-standby.ts`：判据从「reason 是否以 `quota:` 开头」改成「**解除阻塞需不需要浏览器**」，并吃第二个来源（续场闸裁决）： <!-- aidcp-cloud 33934d6 判据换成「解除阻塞需不需要浏览器」+ 回访语义 -->
      - 验证码 / 登录 / 需人工介入 / 未知 → `eligible=false`（**保持不变**）
      - 风控配额窗口未释放 → `source='risk'`（**保持不变**）
      - 续场闸阻塞且算得出 `resumeAt` → `source='session'`，`eligible = (resumeAt − now) ≥ minWaitMs`
      - 风控 `frozen` / `restricted`、周历整周全关 → **无恢复时刻** → `eligible=true` + **回访 `wakeAt`**（默认 6h）。回访语义 = 「多久后回来再问一次」，**MUST NOT 当作恢复承诺**（见 0.3d）。
- [x] 1.6 `src/comm/browser-standby.ts`：默认门槛 `DEFAULT_BROWSER_STANDBY_MIN_WAIT_MS` **20min → 5min**（与边缘 2.1 同改，缺一不可）。 <!-- aidcp-cloud 33934d6 20min→5min -->
- [x] 1.7 `src/server.ts`：把续场闸裁决接进 `buildBrowserStandbyForAccount`（`:1718`，`runtimes` 在该闭包已可用，见 `:1609` 的先例）。 <!-- aidcp-cloud 33934d6 -->
- [x] 1.8 **加固 60s 心跳链**（本 change 的唤醒地基）：`src/comm/ui-snapshot.ts:215` 现在只在 `sent > 0 && dailyUsage` 时重排下一跳——**dailyUsage 一旦为空，链就永久断**，即使待机提示仍在。改为 `sent > 0 && (dailyUsage || browserStandby)`。**不改这条，冻结账号的唤醒路径就悬在一个可能断的链上。** <!-- aidcp-cloud 33934d6 心跳链两条断裂路径都堵上（用量缺失 / 无窗口刷新时刻） -->
- [x] 1.9 单测：各来源 eligible / 门槛边界 / 跨午夜窗口 / **本地日界（非上海）** / 冻结与整周全关走回访 / `canAutoResume` 零行为回归 / 心跳链在 dailyUsage 为空时不断。 <!-- aidcp-cloud 33934d6 browser-standby 14 例 + resume-limits-next-at 7 例 + ui-snapshot 心跳链 2 例 -->
      **台账更正（d83cb45）**：33934d6 里那三条号称「验证码 / 登录 / 未知状态不让位」的用例是**假覆盖**——它们喂给桩的 `explain()` 理由（`captcha_required` / `login_required` / `unknown_scheduler_state`）真实风控对 `view` 动作**永远不会返回**（只会返回 allowed / `state:frozen` / `quota:*`）。它们守的是一段到不了的代码，而**真实的验证码路径当时没有任何测试、也没有任何实现**（见 1.11）。已删除，换成走真实可达路径的用例。
- [x] 1.10 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿。 <!-- aidcp-cloud 33934d6 acceptance 50/50 · test 2017/2017 · typecheck 0 -->

### 1.11–1.13 验证码安全回归修复（对抗性评审发现，d83cb45）

> **这是 33934d6 上线到 dev 之后才发现的一条真实安全回归。** 本 change 把判据换成「解除阻塞需不需要浏览器」，却**只接了「不需要」那一半的证据**——「需要浏览器」那一半没有任何输入，于是判据只剩半边。
> **失败链**：边缘上报验证码 → 风控信号把账号迁到 `restricted` → 续场闸据此判停工 → 待机闸判「可以让位」→ 而 `ui.snapshot` **有意豁免**验证码暂停闸（它是界面数据、不是页面命令，`ws-server.ts:213-224`）→ 提示照常送达 → **运营正被要求去解验证码的那个浏览器被关掉**。边缘侧的浮层标志不是防线（会被「浏览循环结束」等无关事件清掉，`main.cjs:3186`）。
> **波及面不止 restricted**：验证码期间账号同样可能排期外 / 每日上限满 / 配额耗尽，那几支照样让位——故闸必须压在**所有**来源之前。

- [x] 1.11 `src/comm/browser-standby.ts`：新增 `needsBrowserToUnblock` 输入，命中即 `eligible=false` / `reason='hard_blocker'`，且**短路在所有来源判定之前**（不能只补在受限那一支）。 <!-- aidcp-cloud d83cb45 一票否决闸压在全部来源之前 -->
- [x] 1.12 `src/server.ts`：该输入由**云端权威**填充（`server.isEdgePaused(edgeId)` = 该边缘是否正处于验证码暂停态），**MUST NOT 依赖边缘自报的浮层标志**。 <!-- aidcp-cloud d83cb45 buildBrowserStandbyForAccount 接入 isEdgePaused -->
- [x] 1.13 单测：验证码期间四类来源（受限 / 排期外 / 每日上限 / 配额）**全部**不让位；验证码解除后恢复正常让位（该闸 MUST NOT 永久禁用让位）。附带修复 `resumeGateSnapshot` 的副作用——它原会调用 `canStartSession()`（含两次告警 + 会话拒绝回调），被 60s 心跳链每分钟触发一次，使未绑人设的账号每分钟误发一次「会话被拒」；已拆出纯判定函数，`canAutoResume` 仍保留告警。 <!-- aidcp-cloud d83cb45 acceptance 50/50 · test 2020/2020 · typecheck 0 -->

## 2. aidcp-edge — 门槛与抗抖动

- [x] 2.1 `src/electron/browser-cold-standby.cjs`：默认门槛 `DEFAULT_BROWSER_COLD_STANDBY_MIN_WAIT_MS` **20min → 5min**。 <!-- aidcp-edge 5b9b5b9 20min→5min，回归测试钉死两端一致 -->
      **红线**：边缘取 `Math.max(本地门槛, 云端门槛)`（`browser-cold-standby.cjs:62`）——只改云端不生效、且无任何报错。回归测试须断言两端默认值一致。
- [x] 2.2 `src/electron/browser-cold-standby.cjs`：`shouldEnterColdStandby` 新增**最短持有时长**闸（默认 3 分钟，可经设置 / env 覆盖）：唤醒后不足最短持有时长 → `skip('min_hold')`。需要一个「上次唤醒完成时刻」的输入（外壳在 `onColdStandbyWoken` 处记录）。 <!-- aidcp-edge 5b9b5b9 minHoldMs 默认 3min，回传 holdRemainingMs -->
- [x] 2.3 `src/electron/main.cjs`：记录 `lastWokenAt`，传入 `shouldEnterColdStandby`；`min_hold` skip 时**不清除**待机提示，持有时长满足后按最新提示重新判定（不能把提示丢了）。 <!-- aidcp-edge 5b9b5b9 coldStandbyLastWokenAt + coldStandbyHoldTimer；min_hold 排到点重判、绝不丢提示 -->
- [x] 2.4 处理无 `wakeAt` 的提示（冻结）：关浏览器但**不排到点唤醒定时器**，只等云端推新快照唤醒（既有 `applyBrowserStandbyHint` 在 `!decision.ok` 且 `coldStandbyActive` 时已会 `wakeColdStandby`，确认该路径对「提示变 ineligible」成立）。 <!-- aidcp-edge 5b9b5b9 回访 wakeAt 由云端赋值，边缘按普通提示处理（零协议改动） -->
- [x] 2.5 单测：门槛 5 分钟 / 最短持有时长拦截 / 持有满足后恢复判定 / 无 wakeAt 不排定时器 / 两端默认门槛一致。 <!-- aidcp-edge 5b9b5b9 browser-cold-standby 13 例 -->
- [x] 2.6 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿。 <!-- aidcp-edge 5b9b5b9 acceptance 19/19 · test 1283/1283 · typecheck 0 -->

## 3. 集成与部署

- [x] 3.1 cloud 合回 master，按 CLAUDE.md §5 安全序列部署 `dev`（备份 → rsync → restart → healthcheck）。 <!-- aidcp-cloud 33934d6 2026-07-14 deployed(dev) 备份 cloud.bak.20260714-203023.tar.gz → git archive 快照 rsync → restart → healthcheck 全过（NRestarts=0 / 8787 / 飞书长连接 / panel 8090 / isales 三服务未受影响） --> <!-- aidcp-cloud d83cb45 2026-07-14 deployed(dev) 验证码修复补部署；部署前已核 ECS 上跑的确为 33934d6（md5 比对）；备份 cloud.bak.captchafix-20260714-211739.tar.gz；healthcheck 全过 -->
- [x] 3.2 edge 合回 master；**不出安装包**（CLAUDE.md §6：打包需用户显式要求）。本机验证走 `npm run build:dist` + 重启客户端。 <!-- aidcp-edge 5b9b5b9 已合 master + 主 checkout 已 build:dist；按 CLAUDE.md §6 不出安装包 -->
- [x] 3.3 观测：dev 上确认「排期外 / 时长满 / 冻结」三类各至少产出一次 `source='session'` 或冻结让位，且槽位真的空出来（客户端左栏可见环境进入「浏览器已关闭，云端连接保持中」）。 <!-- aidcp 2026-07-14 解耦到真机 backlog 簇 80.2/80.4（需真账号跑满一天才观测得到，桩测证明不了；不阻塞归档） -->

## 4. 真机验收（解耦收拢，不阻塞归档）

- [x] 4.1 登记 `docs/real-machine-acceptance-backlog.md`：① 冻结账号让位后**人工解冻能自动醒来**（这是本 change 最危险的一条，桩测只能证明推送发出、证明不了端到端醒来）；② 5 分钟门槛下实测**一天的开关次数**，确认「不频繁」；③ 实测**单账号日均真实占用时长**（天花板公式的分母，与 `browser-slot-scheduling` task 0.2 同源，合并做）。 <!-- aidcp 2026-07-14 簇 80（6 条，80.1 为红线：冻结让位后必须能被解冻唤醒） -->

## 5. 明确不做

- [x] 5.1 **不做需求驱动的「让位 / 槽位借调」**（决策已记录，非待办）（请一个休息中的账号提前腾位子）。理由见 `browser-slot-scheduling` task 5.8：它在**任何**密度下都错——会掐掉正在跑的会话、绕过唯一那道安全闸（暂停 / 验证码 / 稿件待审 / 未登录），且合格供体仅占约 3% 的时间。本 change 是纯供给侧的，密度越高越管用。
