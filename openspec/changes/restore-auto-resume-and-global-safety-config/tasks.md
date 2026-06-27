> **协调与红线（动手前必读）**
> - **行号以代码为准**：所有 `文件:行` 为 2026-06-27 复核值，动手前再核一遍。
> - **两条线分别成 commit**：stream A（续场回归修复，紧急、可先部署）与 stream B（安全配置全局化、大改 + 迁移）**分开提交**，A 不被 B 拖住。
> - **不触协议**：A 复用既有 `scroll`→`page.scroll` 通道（`command-bridge.ts:22-23`，边端白名单 `edge-client.ts:353` 已放行），**MUST NOT 新增协议消息类型**；B 是云端内部配置不经 WS v2。两份 `protocol.ts` / `command-bridge.ts` / `docs/protocol.md` 一律不动。
> - **不触风控状态单写**：`setQuotaLevel` / `applySignal` / 状态机 / `risk_state` 不动；provider 只读，配置只写自己的表。
> - **迁移号**：现有最高 `0021`（`0012/0017` 缺号）。动前 `ls ../aidcp-cloud/migrations/` 复核取号、与并发会话错峰。
> - **`role-dispatcher.ts` 是多 change 热点**（A①/A②/B 都改它；`multi-account-node-support` 35/36 正穿 `currentAccountId` 多租路由）。B 改动严格限定 7 个 provider 调用点；共享文件（`role-dispatcher.ts` / `server.ts` / `panel-server.ts` / `panel/types.ts` / console `types/api.ts`）**只 `git add` 自己的 hunk、绝不 `-A`**（见 memory `precise-git-add-concurrent-sessions`）。
> - **绝不 brick**：B 全局配置缺失/字段非法 → 逐项回落写死默认（`risk/*.ts` 写死常量保留作 builtin）；保「写库成功才刷镜像 / 逐字段回落 / 永不抛」。
> - **归档前置（D6）**：B 的 `interaction-risk-gating` delta 现为 `## ADDED`（全局），归档前须按 §10.5 与 `session-limits-to-quota-layer` 的「按账号」delta 协调，baseline 最终只留全局一条。

## 1. aidcp-cloud — stream A①：消除会话结束双调（治「续场完全不触发」，必做且优先）

- [x] 1.1 `src/orchestrator/role-dispatcher.ts` `session.should_end` 处理器（约 :1080-1084）：删去其中的 `this.endSession(payload.reason, {autoResumeEligible:true})`（约 :1083），**只保留** `sendCommand({action:'session.end', reason})`；由注入的结束回调（:532 `onSessionEnd`）作**唯一**结束入口 <!-- aidcp-cloud 90a03cf -->
- [x] 1.2 复核 `src/agents/session-monitor-role.ts` `triggerEnd`（:247-255）顺序保持「先 emit 发结束命令、后走 `onSessionEnd` 回调」不变（顺序正确：结束命令先到边端，再武装续场） <!-- aidcp-cloud 90a03cf 复核：triggerEnd 顺序 emit→onSessionEnd 确认正确、未改 -->
- [x] 1.3 复核 `endSession`（:729-744）现只被调一次：第一次即过守卫 → 置 `sessionActive=false` → `armRestTimer`（:743）武装续场计时器且不再被同次取消；`cancelRestTimer`（:750）/`armRestTimer`（:757）内部逻辑**不动** <!-- aidcp-cloud 90a03cf 复核：endSession/restTimer 内部逻辑未改；§4 回归断言锁定 cleared==0 -->

## 2. aidcp-cloud — stream A②：续场后主动重新驱动边端（云端半）

- [x] 2.1 续场重开后下发一次 `scroll(resume_redrive)` 重驱边端。**偏离原计划落点**：未改 `feed.entered{session_start}` 翻译分支（那会在每次 fresh start / hello 也发、且与本人昵称采集的 `feed.entered{session_start}` 监听竞争），改落在 `doAutoResume`（:785-796）`tryStartSession()` 之后——**仅续场路径发**、最小面、零 fresh-start 冗余；且即便误发，`sendCommand` 软暂停闸（`browseSuspended`）在采集期本就会扣住 scroll，二者不相扰 <!-- aidcp-cloud 90a03cf 落点 doAutoResume 而非 feed.entered handler，设计 D3 列为允许的备选 -->
- [x] 2.2 复核 `scroll`→`page.scroll` 映射（`comm/command-bridge.ts:22-23`）与 `server.ts:828-830` 出口不变；**不新增协议消息类型** <!-- aidcp-cloud 90a03cf 复核：复用既有 scroll→page.scroll，协议四点未动 -->
- [x] 2.3 复核 `startSession`/`restartSession`（:635-662 / :693-722）emit `feed.entered{trigger:'session_start'}` 不变 <!-- aidcp-cloud 90a03cf 复核：两处 emit 未改 -->

## 3. aidcp-edge — stream A②：边端浏览循环唤醒重启

- [x] 3.1 `src/browse/browse-session.ts` 云端命令入口（`onCloudCommand`）：当 `!this.running` 且收到**浏览类命令**（`isWakeCommand` = 非 `session.end`）时 `void this.start()`（幂等守卫）重启循环；`session.end` 仍只置 `stopRequested` <!-- aidcp-edge c1591ab onCloudCommand 新增 !running 唤醒分支 + isWakeCommand 帮助函数 -->
- [x] 3.2 处理 `start()` 清空命令队列（:280 `commandQueue=[]`）：唤醒分支**不 push 触发命令**，靠重启后 `ensureExplore→…→reportVisibleCards` 重报 `page.cards` 驱动云端；不依赖排队命令存活 <!-- aidcp-edge c1591ab !running 分支 return、不入队 -->
- [x] 3.3 shutdown 守卫：新增终态 `close()` + `closing` 标记（`onCdpUnrecoverable` 也置 `closing`），主动关闭/CDP 死局期间迟到命令 MUST NOT 复活循环；`main.ts` 关机由 `browse?.stop()` 改 `browse?.close()`；identity 重连仍用非终态 `stop()`、云端 `session.end` 也不置 closing（故仍可续场唤醒） <!-- aidcp-edge c1591ab browse-session.ts close()/closing + main.ts shutdown close() -->
- [x] 3.4 回归：保留 AC-PROTO 白名单断言（`page.scroll` 仍在白名单）；新增 `test/browse/browse-session.test.ts` 两用例「循环已停→收 page.scroll→重启→重报 page.cards」「close() 后迟到命令不复活」 <!-- aidcp-edge c1591ab 复用既有 makeHarness 追加 2 用例 -->
- [x] 3.5 `npm run typecheck` + `npm test` + `npm run test:acceptance` 全绿 <!-- aidcp-edge c1591ab typecheck 0 / acceptance 11 pass / full test 全绿（含新 2 用例，browse-session 50 pass） -->

## 4. aidcp-cloud — stream A 回归断言

- [x] 4.1 新增 `test/integration/role-dispatcher-end-dedup.test.ts`：经真实 `SessionMonitorRole.triggerEnd`（emit + onSessionEnd）驱动时长超限结束 → 断言休息计时器「已武装且未被取消」（faithful 计时器桩：`getCleared()===0`）、到点 `fire()` 真续场 <!-- aidcp-cloud 90a03cf 用 d.bus.emit('action.completed') 驱真实监测体；bug 路径下 cleared==1 + fire no-op 会如实失败 -->
- [x] 4.2 同文件：续场重开后断言云端下发 `scroll(reason='resume_redrive')` <!-- aidcp-cloud 90a03cf 在 dedup 测试 A② 用例断言 -->

> §1–§4 备注（stream A）：committed cloud `90a03cf` + edge `c1591ab`，**尚未 push**（推 master 被安全分类器拦下，待用户授权）。验证：cloud typecheck 0、全量 test 仅 `AC-PUB-01` 失败（Windows `\tmp\` vs POSIX `/tmp/` 路径分隔符的既有环境问题，与 stream A 无关、云端 Linux 上为绿，本 change 未碰发布路径）；edge typecheck 0 / acceptance 11 pass / 全量含新 2 用例全绿。precise git add：cloud 只提 role-dispatcher.ts + 新测试（未裹挟并发 WIP nickname-enricher.ts）；edge 只提 browse-session.ts / main.ts / browse-session.test.ts（未裹挟 feed-scroller 等 WIP）。

## 5. aidcp-cloud — stream B：存储收敛全局单例 + 迁移

- [ ] 5.1 `ls ../aidcp-cloud/migrations/` 复核取号；新增 `migrations/00XX_global_safety_config.sql`：把 `session_config` + `resume_config` 收敛为单行全局表（`id INTEGER PRIMARY KEY DEFAULT 1 CHECK(id=1)`），把现有 `account_id='default'` 行值**迁入全局行**（保 30min）；幂等；旧维度数据保留至 §10.4 验证后再清理
- [ ] 5.2 `src/config/session-config-store.ts`：内存镜像 `Map<accountId,Row>` → 单个全局 `Row|null`；`get()`/`set(patch, updatedBy)` 去 accountId；SCHEMA 改单行 `ON CONFLICT(id)`；保「写库成功才刷镜像 / 逐字段非法回落写死默认 / 永不抛」
- [ ] 5.3 `src/config/resume-config-store.ts`：同上单例化；保留 `idleEndMs()` 的 `end > nudge` 不变量
- [ ] 5.4 default 行确认（部署前在 ECS 实证）：`session_config`/`resume_config` 是否有 `default` 行及其值（确认 30min 被带走）；无行→表空回落写死默认（零回归）；存在多个非 default 账号行→迁移取 `default` 行值、其余废弃并 `log` 记录

## 6. aidcp-cloud — stream B：provider 去 accountId + 调用点

- [ ] 6.1 `src/risk/session-limits.ts`（`SessionLimitProvider` :63）：`sessionDurationMsFor`/`sessionBudgetFor` 去 accountId（→ `sessionDurationMs()`/`sessionBudget()`）；`DEFAULT_*` 常量保留作 builtin fallback
- [ ] 6.2 `src/risk/resume-limits.ts`（`ResumeConfigProvider` :60）：5 方法（`restRatio`/`activeWindow`/`dailyCaps`/`idleNudgeMs`/`idleEnd`）去 accountId；`DEFAULT_*` / `isWithinActiveWindow` 不变
- [ ] 6.3 `src/orchestrator/role-dispatcher.ts` 7 个调用点去 `currentAccountId` 实参：:345, :536, :537, :621, :761, :799, :801（仅这 7 处，勿动多租路由）
- [ ] 6.4 复核 `src/agents/session-monitor-role.ts` thunk（`()=>number`，:24/:39/:40）**无需改**（已无账号维度，交接 B.7 列它是误）
- [ ] 6.5 每日上限语义复核：阈值全局共用、计数仍**按账号按日**（`dailyCaps` 用法不变，避免误读成所有账号共享一个计数）

## 7. aidcp-cloud — stream B：facade + 面板 API 去账号

- [ ] 7.1 `src/config/session-config-facade.ts`：去 `buildCatalog` 账号目录（`Set(['default']) ∪ getAll()`），改单个全局 `getView()/set(patch)`（无 accountId）；GET 返回全局生效值 + `override/builtin` 来源态
- [ ] 7.2 `src/config/resume-config-facade.ts`：同上去账号目录、改全局读写
- [ ] 7.3 `src/panel/panel-server.ts`：`/api/session-limits`（:645/:653）、`/api/resume-config`（:705/:713）请求/响应去 accountId、去必填账号校验（:667-670 / :726-730）；保 JWT 守卫 / 非乐观写 / 整块拒 / 未注入 503
- [ ] 7.4 `src/panel/types.ts`：`SessionLimitRowView`/`SessionLimitCatalogView`/`SessionLimitPatchInput`/`PanelSessionLimits` + `ResumeConfig*` 去 accountId、改单全局形态
- [ ] 7.5 `src/server.ts`：store 装配 + provider 注入随接口微调（**仅必要改动**，与他流共享块不裹挟）

## 8. aidcp-cloud — stream B：测试

- [ ] 8.1 `test/session-config-store.test.ts`：重写为全局（空库→全局取值=写死默认；写全局→生效；非法字段逐项回落）；删一切「按账号/缺行回落」语义断言
- [ ] 8.2 `test/resume-config-store.test.ts`：**新建**（全局单例 + 看门狗 `end > nudge` 不变量 + 迁移迁入 `default` 值用例）
- [ ] 8.3 `test/session-config-facade.test.ts`：fakeStore / 断言改全局；删账号目录相关
- [ ] 8.4 `test/session-effective-limits.test.ts` + `test/integration/role-dispatcher-resume.test.ts`：注入的 mock provider 改无参（无 accountId）接口
- [ ] 8.5 `npm run test:acceptance`（AC-PROTO/AC-PUB/AC-RISK 红线）先过 → 全量 `npm test` → `npm run typecheck`

## 9. aidcp-console — stream B：全局表单

- [ ] 9.1 `src/types/api.ts`：`SessionLimitRow`/`ResumeConfigRow` 去 accountId；`Catalog{limits[]/configs[]}` 数组壳收敛为单个全局对象（保 `SessionInteractionBudget` 不变）；与 `account-real-nickname` 共享本文件但改不相交接口
- [ ] 9.2 `src/api/queries.ts`：`useSessionLimits`（:66）/`useResumeConfig`（:74）返回类型改全局对象；端点 `/api/session-limits`、`/api/resume-config` 与 queryKey 可不变
- [ ] 9.3 `src/pages/QuotasPage.tsx`：两张按账号表格（Card :309 / :329）→ 两张**全局表单卡片**；去账号列（:183/:270）、去编辑弹窗里的账号（:388/:435）、去 `slRows/rcRows` 排序 useMemo；mutate payload 去 accountId（`saveSL` :153-171 / `saveRC` :231-251）
- [ ] 9.4 文案：Alert（:314/:334）改「对**所有账号**生效的全局安全限制；未配置时用系统内置默认」；`来源` 从每行 Tag 改为每卡单个 `override/builtin` 徽标
- [ ] 9.5 共享文件 `types/api.ts` 只暂存本 change hunk（precise-git-add）；`npm run build` 绿

## 10. 验证 · 部署 · 归档协调

- [ ] 10.1 cloud `test:acceptance`→`test`→`typecheck` 全绿；edge 全绿；console `build` 绿
- [ ] 10.2 部署（CLAUDE.md §5 安全序列、§0 私钥与 sub-repo 前置检查）：ECS 备份（`cloud.bak.<ts>.tar.gz` + `.env.bak`）→ 迁移 `00XX` 在 PG 执行（迁入 `default` 值）→ rsync（排除 `.env/node_modules/.git`）→ `systemctl restart aidcp-cloud.service` → healthcheck（active + 8787 + 飞书长连 + `select 1`）→ 失败即回滚。**绝不碰同机 isales**
- [ ] 10.3 真机验证 A：会话结束 → 边端收 `session.end` 停 loop → 云端 ~1min 后续场 → 云端发引导 `scroll` → 边端 loop 重启重报 `page.cards` → 闭环恢复；期间新未读被新会话通知巡视处理
- [ ] 10.4 真机验证 B：后台设全局单场 30min → **任意/所有账号**单场按 30min 结束（不再 10min）；改全局续场/看门狗参数对所有账号即时生效（热加载）；确认旧 per-account 表数据已无用后清理
- [ ] 10.5 spec 归档协调（D6）：待 `session-limits-to-quota-layer` 先跑完真机校准并归档（其「按账号单场上限」并入 baseline）后，把本 change `specs/interaction-risk-gating/spec.md` 由 `## ADDED`（全局）改为 `## REMOVED`（按账号，注明 Reason/Migration）+ `## ADDED`（全局）或等价 `## MODIFIED`；`openspec validate restore-auto-resume-and-global-safety-config --strict` 通过
- [ ] 10.6 `/opsx:archive`（待 10.1–10.5 全部完成后）
