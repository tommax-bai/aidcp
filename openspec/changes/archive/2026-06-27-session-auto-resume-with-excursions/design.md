## Context

现役浏览闭环是事件驱动多 Agent：`feed.entered` 启动，互动/返回后再次 `feed.entered` 往复，由 `SessionMonitorRole` 判结束。单场结束的全部条件只在收到 `action.completed` 时核（`session-monitor-role.ts:130-176`：时长 / 动作数 / 配额）；另有一条独立 wall-clock 空闲看门狗（`checkIdle` `:142-154`，idle-nudge 130s / idle-end 240s）。结束经 `session.should_end → role-dispatcher.ts:885-888` 下发 `session.end` + `endSession()`（`:649-656` 拆全部角色订阅）。

**坐实的现状约束（已用多 agent workflow 勘察，file:line 为准）：**
- 结束后**云端无任何自动重启**：唯一永久监听是 `edge.hello`（`role-dispatcher.ts:505-507`，注册在 `setup()`、不在 `commandUnsubscribers` 内）→ `onHelloEvent → restartSession()`（`:514-518/619-646`）；另有 `tryStartSession()`（`:538`，`sessionActive` 为真早退）唯一现实调用方是面板 `dispatch` 开关（`server.ts:1096-1102 → connection-runtime.ts:152-159`，且有 `if (changed)` 闸，已 active 再点是 no-op）。飞书 `/resume` 只解 `pausedEdges`、不调 `tryStartSession`。
- **发布**走独立全局编排器 `PublishOrchestrator`（`server.ts:425`，`pipelineTimeoutMs≈18min :427`，人审窗口 `approvalWaitMs=900s=15min`），**不往每连接私有总线 emit 任何事件**（`publish.command.result` 只路由给 `commandSequencer`，`handler.ts:290-293`）。其 `trigger()` 有 try/finally（`publish-orchestrator.ts:63-82`）覆盖所有终止路径；`status==='running'` 时于 `:34-44` 提前 return。
- **通知巡视**是会话内 excursion：起 `excursion.requested`（`notification-gatekeeper.ts:53`），止 `excursion.ended`（`excursion-resumer.ts:56-62`，把 triage_done / classify_failed / 巡视命令 `action.completed{ok:false}` 三条终止幂等收敛成一次）。软暂停闸 `browseSuspended` 在 `role-dispatcher.ts:324-330` 扣 browse 命令。巡视上报刷新空闲看门狗判活基线（`session-monitor-role.ts:98-100`）。
- 多租户红线：preview dispatcher 看门狗曾向**所有** edge 误广播 `session.end`（已修 `a38fb96`）——任何续场/暂停 MUST 每连接私有、绝不广播。

## Goals / Non-Goals

**Goals:**
- 单场正常结束后自动「歇 N%（默认 10%、抖动）再续场」，带活跃时段窗口 + 每日上限 + 撞风控不续三道护栏；续场资格按结束原因区分；休息计时器每连接私有、有界取消、绝不广播。
- 发布与巡视**不计入单场时长**、**不被单场时限/看门狗打断**。
- 续场护栏与看门狗两段阈值落库、按账号可改、热加载、缺值绝不 brick、空配置严格零回归。
- 守红线：不动协议、不动边缘、不碰风控状态单写、不碰发布审批链。

**Non-Goals:**
- 不删除空闲看门狗（它是事件驱动闭环唯一的「还活着吗」探测器，见 D4）。
- 不引入「单场总动作硬顶」等新行为（与 session-limits 同界，超出本 change）。
- 不动 v1 兼容路径（plan/select、`SessionBudget`）。
- 不接「真实平台封号/限流信号→风控状态迁移」（既有缺口，正交）。

## Decisions

### 决策 1：发布用「让位」（结束当前会话 → 发布独占 → 结束后起新场），不在监测体里冻结时钟

- **选择**：`/publish` 触发即按 accountId 定向**结束**该账号浏览会话（标记不可续场、不安排休息）；发布经 try/finally 的保证终止点回调 `onPublishEnd` → 起一场全新浏览会话（过续场各闸）。`onPublishStart` 在 `trigger()` 真正开始处（`status='running'` 之后、try 之前）调，被忽略的触发（`:34-44` 早退）不 arm。
- **理由**：一边缘一 Chrome，发布期物理上不可能并发浏览；把发布当「接管边缘」而非「并发活动」最贴现实。这样**发布期根本没有浏览会话、没有看门狗在跑**——无需冻结、无需封顶、无需心跳。「不计时」天然满足（旧会话已结束）、「不被打断」天然满足（无并发浏览命令撞页）。且**最坏故障是诚实暂停**（终止信号丢→停在无会话态等重连/运营），而非冻死/撞页。
- **否决的替代**：
  - *冻结监测体时钟（pause clock + freeze idle + maxPause 封顶）*：能work，但要在 delicate 的监测体里加引用计数暂停+封顶，且为「发布期静默」承重；让位把这套全省了。
  - *看门狗消费发布事件来刷新判活（feed-events）*：发布人审窗口最长 ~15min **全程静默无事件**，喂不到东西，5min 看门狗仍误杀；要补救得加审批期心跳，且**只解决「不被打断」、不解决「不计时」**（时长那本账动不到），反而更复杂。
- **桥接**：`ConnectionRuntimeRegistry` 加按 accountId 的 `endSessionForAccount` / `startSessionForAccount`（仿 `startAll/endAll`）；`OrchestratorDeps` 加 `onPublishStart/onPublishEnd`；`server.ts` 装配处接线（`runtimes` 前向引用安全，仿 `commandSequencer.pusher`）。

### 决策 2：巡视用「轻离」（暂停时限 + 扣时长，看门狗保持活着）

- **选择**：`SessionMonitor` 订阅 `excursion.requested → pauseClock('patrol')`、`excursion.ended → resumeClock('patrol')`。pause 只暂停**时限判定**，**不冻空闲看门狗**。
- **理由**：巡视频繁且短、是会话内「离开一下」，端到端 end+restart 会频繁重置预算（可被滥用绕预算），故必须保持同一会话。巡视上报本就刷新看门狗判活基线（`:98-100`），健康巡视不误触；卡死巡视由看门狗有界兜底——故巡视**不需要单独封顶**。但巡视命令仍发 `action.completed` 会触发 `checkSession`，故时限 early-return 守卫**必需**，否则会用「含巡视时间的 elapsed」误判超限当场掐断巡视。
- **与发布的不对称是有根的**：巡视持续上报、无长静默 → 看门狗喂得到、不冻；发布有人在环长静默、且要扣时长 → 让位（结束会话）。

### 决策 3：可暂停时钟 = 多原因引用计数 early-return + 末次解除前移 `startedAt`

- **选择**：`SessionMonitorRole` 加 `pauseReasons: Map<string,…>` + `pauseStartedAt`。`pauseClock(reason)`：0→1 转换记 `pauseStartedAt`、`set(reason)`；`resumeClock(reason)`：未持有则 no-op（陌生 token 安全），末次 `size→0` 时 `startedAt += clock()-pauseStartedAt`（前移＝排除暂停窗口）并补调一次 `checkSession()`（把「延期的结束」补发）。`checkSession()` 顶部 `if pauseReasons.size>0 return`（单点守卫同时延期时长/动作数/配额三出口）。`subscribe()/unsubscribe()` 清 `pauseReasons`，绝不跨场残留。
- **理由**：引用计数（非布尔）正确处理「发布让位时若仍有巡视暂停」「嵌套」等并集；末次前移使观测 elapsed 自然排除暂停段、`getStats()` 可复用；陌生 token no-op 守卫使 restartSession 后在途回调误调 resume 不产生负泄漏。
- **注意**：本 change 下发布走让位（结束会话）而非 pauseClock，故 `pauseClock` 的现役使用方仅巡视一个 reason；引用计数是为「将来若有第二类暂停」留干净缝 + 防 restartSession 错配，非过度设计。

### 决策 4：看门狗保留并两段阈值可配，放弃结束默认 1h；不删

- **选择**：保留两段看门狗；轻推（idle-nudge）保持 ~2min 频繁（须 > 详情页停留上限 90s）、放弃结束（idle-end）默认 **1h**；两段阈值进按账号配置层、热加载、缺值回落默认。
- **理由（为何不删，用户曾提议删）**：所有其它结束条件都只在 `action.completed` 时核——边缘一旦静默（命令发了无回执 / 页面卡 / CDP 悄断不报错），云端会永等不来的事件，无别的计时器能发现（真发生过：notification-monitor 6.5.1 卡死，看门狗 240s 收掉）。加了自动续场后更糟：卡住会话永不结束→永不休息→永不续场→自动化静默死。看门狗是唯一 liveness 网，删它踩「不许静默装死」红线。轻推还在不结束会话前提下救活多数瞬时卡顿。
- **代价（写进 Risks）**：1h 放弃阈值＝真死锁最多等 1h 才回收；但经 D1 让位 + D2 巡视自喂后正常浏览从不空闲超几分钟，故 1h 不比 5~10min 多挡误杀、只是回收更慢——用户已知并接受，且阈值可配可随时缩短。

### 决策 5：自动续场资格 + 三护栏 + 每连接计时器

- **选择**：`endSession` 带可续场资格标记（来源决定，非猜 reason）：时长/动作数/配额=可续；运营 stop / 风控-验证码暂停 / 掉线=不可续。可续则在该连接 dispatcher 上 arm 一个 `unref` 的休息计时器（`rest = maxDurationMsFor(account) × rest_ratio` + 抖动）；触发时过续场闸（`canStartSession` + 活跃时段 + 每日上限 + 风控）后 `tryStartSession()`（已 active 早退，处理「边缘先自连」竞态）。计时器在 stop/暂停/掉线/先自连时取消。
- **idle-end 是否续场**：**eligible**（卡死→杀掉重开正是恢复路径），但受每日上限封顶防死循环（连续卡死会被当日上限止住）。
- **每日计数**：每账号 `{date/windowEpoch, count, accumulatedMs}` 内存计数，按日界/窗口界重置；续场前查。单租户下即 `default` 一行。

### 决策 6：配置复刻 session-limits-to-quota-layer 的 `session_config` 范式

- **选择**：新增按账号配置（`rest_ratio`、活跃时段窗口、每日上限场数/时长、看门狗 idle-nudge/idle-end 两阈值）——优先**扩 `session_config` 加列**（同主键 `account_id`、同 store 时序：先写库成功再刷镜像、缺行/非法回落、永不抛），避免新表。新增 store/facade（复刻 `quota-config-*` / `session-config-*`）+ 面板 JWT GET/PUT（非乐观写）+ console 编辑区。**需 DB 迁移**：迁移号实装前 `ls ../aidcp-cloud/migrations/` 复核取未用号（现 0017_images，0018 可能被并发 model-config/interaction-feed 占用，按实际取）。
- **理由**：单场上限已在 `session_config`、按账号、never-brick，续场护栏与看门狗阈值同源治理最一致、最小惊讶；扩列 vs 新表——项集稳定、YAGNI 不需窄表可扩展性。

## Risks / Trade-offs

- **[1h 放弃阈值→真死锁最多等 1h 才回收]** → 轻推保持 ~2min 快速自愈、只有戳不活才等满；阈值可配可缩短；活跃窗口内若开头死锁会丢约 1h（用户接受）。
- **[发布让位的终止信号丢失→自动化停在无会话态]** → try/finally 是覆盖全路径的唯一保证终止点，丢失概率极低；即便发生也是**诚实暂停**（安全），靠边缘重连/运营恢复，远好于「冻死/撞页」。
- **[暂停态跨 restartSession 残留→时钟永冻]** → `subscribe/unsubscribe` 清 `pauseReasons`、`resumeClock` 陌生 token no-op；巡视事件挂会话级 `commandUnsubscribers`、随 endSession 拆除。
- **[续场死循环（卡死→杀→续→又卡死）]** → 每日上限封顶；活跃时段窗口；风控闸。
- **[每连接计时器误广播]**（a38fb96 类）→ 计时器每 dispatcher 私有、只 `tryStartSession()` 自己；按 accountId 定向桥，绝不 `startAll`。
- **[并发会话抢同一批文件]**（server.ts / panel-server.ts / panel/types.ts / connection-runtime.ts 同机重度并发）→ 一律 APPEND、只 `git add` 自己具体文件、绝不 `-A`、共享文件用 git plumbing 只暂存自己 hunk；迁移取未用号。
- **[ECS 部署=全量 master 快照]** → 部署前 `rsync --dry-run` 摸范围、部署后 grep ECS 文件内容 + 看启动日志确认新码生效、同机 isales 绝不碰。

## Migration Plan

1. 合「配置 store/facade + 迁移（扩 `session_config` 列）+ 监测体可暂停时钟与看门狗阈值可配 + 调度器休息计时器/续场闸/巡视暂停接线 + 发布让位回调 + 注册表按账号桥 + 面板 GET/PUT」提交；cloud `npm run typecheck` + `test:acceptance`（AC-RISK/AC-PUB/AC-PROTO 红线）+ 全量 `npm test` 绿。
2. console build/typecheck 绿（配置编辑区）。
3. 按 §5 安全序列部署 ECS（先备份 → `rsync --dry-run` → rsync → restart → healthcheck：8787 / PG `select 1` / 迁移已建列 / 面板 8090）；与并发会话错峰。
4. 真机校准：正常结束→歇 10%→续场；过活跃窗口/达每日上限/风控受限不续；发布触发→浏览会话结束→发布跑完→新场起；巡视耗时不计入单场、巡视不被时限掐断；看门狗 1h 生效、阈值后台改即生效。
5. 回滚：失败即回滚备份；表为空/未注入提供者时回落写死默认（never-brick 保证回滚安全）。

## Open Questions

- 活跃时段窗口与每日上限的**默认值**（窗口默认全天不限 + 每日上限默认很宽？还是给一组保守默认）——倾向「默认不限（零回归），运营按账号收紧」，实装时定。
- 看门狗阈值默认：idle-nudge 沿用 ~130s、idle-end 默认 3600s（用户拍板）——确认 idle-nudge 是否随之微调（保持 > 90s 即可）。
- 续场休息抖动幅度（lognormal σ）取值——实装时给一组温和默认，可后续调。
