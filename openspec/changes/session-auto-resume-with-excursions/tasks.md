## 1. aidcp-cloud — 配置层（按账号续场护栏 + 看门狗阈值）

- [ ] 1.1 `ls ../aidcp-cloud/migrations/` 复核最高迁移号，取未用号；新增迁移：扩 `session_config` 加列 `rest_ratio_pct` / `active_window_start_min` / `active_window_end_min` / `daily_max_sessions` / `daily_max_minutes` / `idle_nudge_ms` / `idle_end_ms`（均 nullable 或带默认，缺行/缺列回落写死默认）
- [ ] 1.2 在 `session-config-store.ts`（或新 `resume-config-store.ts`）扩展按账号提供者：`restRatioFor` / `activeWindowFor` / `dailyCapsFor` / `idleNudgeMsFor` / `idleEndMsFor`，逐项缺/非法回落写死默认、永不抛；store init 失败装配处吞错退化默认
- [ ] 1.3 集中导出写死默认常量（`DEFAULT_REST_RATIO_PCT=10`、`DEFAULT_IDLE_NUDGE_MS≈130_000`、`DEFAULT_IDLE_END_MS=3_600_000`、活跃窗口默认全天不限、每日上限默认很宽/不限）+ 校验上限，供回落与 facade 校验复用
- [ ] 1.4 新增 facade（复刻 `quota-config-facade` / `session-config-facade`）：getView（库缺行以写死默认合成）+ 非乐观 setX（先校验、写库成功才刷镜像回真态；任一字段非法整块拒、绝不部分落库）

## 2. aidcp-cloud — 会话监测体：可暂停时钟 + 看门狗阈值可配

- [ ] 2.1 `session-monitor-role.ts`：加 `pauseReasons: Map` + `pauseStartedAt`；公有 `pauseClock(reason)` / `resumeClock(reason)`（0→1 记起点；末次 size→0 时 `startedAt += clock-pauseStartedAt` 并补调 `checkSession()`；陌生 token no-op）
- [ ] 2.2 `checkSession()` 顶部加 `if (this.pauseReasons.size>0) return`（单点守卫延期时长/动作数/配额三出口）；`subscribe()`/`unsubscribe()` 清 `pauseReasons`+`pauseStartedAt`，绝不跨场残留
- [ ] 2.3 看门狗两段阈值改读注入的可配提供者（`getIdleNudgeMs`/`getIdleEndMs` thunk，按当前账号现读），缺省回落写死默认；idle-end 默认 1h、idle-nudge 保持 ~2min 且 > 90s 详情页停留上限
- [ ] 2.4 单测：巡视期 `action.completed` 不触发时限结束 + `resumeClock` 后补发结束；末次解除前移 startedAt 正确扣除暂停段；`restartSession` 后 pause 态已清；看门狗阈值缺值回落默认；idle-nudge 仍 > 90s

## 3. aidcp-cloud — 调度器：休息计时器 + 续场闸 + 巡视暂停接线

- [ ] 3.1 `role-dispatcher.ts`：`endSession` 带可续场资格入参（来源决定）；新增每连接 `unref` 休息计时器：`rest = maxDurationMsFor(account) × restRatio + lognormal 抖动`，仅「可续场」结束才 arm
- [ ] 3.2 续场闸 `canAutoResume(account)`：依次过 `canStartSession`（dispatchActive+人设）+ 活跃时段窗口 + 每日上限（每账号 `{date/windowEpoch,count,accMs}` 内存计数、按界重置）+ 风控状态非 restricted/frozen；不过则诚实不续
- [ ] 3.3 休息计时器触发 → 过 `canAutoResume` → `tryStartSession()`（已 active 早退处理边缘先自连竞态）；计时器在 `dispatch stop` / 账号暂停 / 掉线拆除 / 边缘先自连（hello→restartSession）时立即取消
- [ ] 3.4 在会话级订阅（`commandUnsubscribers` 内、随 endSession 拆除）接 `excursion.requested → sessionMonitor.pauseClock('patrol')`、`excursion.ended → resumeClock('patrol')`；持 `sessionMonitor` 引用
- [ ] 3.5 单测：正常结束 arm 计时器、运营停/暂停/掉线不 arm；护栏任一不过不续；计时器只 `tryStartSession` 本连接、绝不广播；idle-end 续场受每日上限封顶

## 4. aidcp-cloud — 发布「让位」

- [ ] 4.1 `connection-runtime.ts`：`ConnectionRuntimeRegistry` 加 `endSessionForAccount(accountId, reason)` / `startSessionForAccount(accountId)`（遍历 `bySession` 匹配 `rt.accountId`，仿 `startAll/endAll`），结束标记不可续场
- [ ] 4.2 `publish-agent/types.ts`：`OrchestratorDeps` 加可选 `onPublishStart?(accountId)` / `onPublishEnd?(accountId)`
- [ ] 4.3 `publish-orchestrator.ts`：`trigger()` 在 `status='running'` 之后、try 之前调 `onPublishStart(accountId)`；`finally` 调 `onPublishEnd(accountId)`；`:34-44` 早退路径不调（不动会话）
- [ ] 4.4 `server.ts`：装配 `onPublishStart=(a)=>runtimes?.endSessionForAccount(a,'publish_takeover')`、`onPublishEnd=(a)=>runtimes?.startSessionForAccount(a)`（前向引用 `runtimes` 安全，仿 `commandSequencer.pusher`）
- [ ] 4.5 单测：发布触发结束并发浏览会话且不安排休息；发布各终止路径（成功/跳过/超时/中止/异常）均经 finally 起新场；被忽略触发（已 running）不动会话；起新场过续场各闸

## 5. aidcp-cloud — 面板 API

- [ ] 5.1 `panel-server.ts` + `panel/types.ts`：APPEND JWT 守卫的 `GET /api/resume-config`（回显按账号续场护栏 + 看门狗阈值，库缺行以写死默认合成）与 `PUT`（非乐观写、`verified.payload.sub` 作 updatedBy、未注入 503）
- [ ] 5.2 装配 `server.ts`：config store/facade init（与其余 config store 同 try/catch 吞错退化）+ 注入监测体/调度器提供者 + 面板依赖（仅 APPEND，不与并发流抢同处）

## 6. aidcp-console — 配置编辑区

- [ ] 6.1 `src/types/api.ts` + `src/api/queries.ts`：APPEND 续场护栏 + 看门狗阈值 DTO 与取数/写回 hook
- [ ] 6.2 `/quotas`（或等价配置页）加「续场与看门狗」编辑区（按账号：rest_ratio / 活跃时段窗口 / 每日上限 / idle-nudge / idle-end），前端即时校验 + 服务端校验为准 + 保存后回显刷新（非乐观）；console build/typecheck 绿

## 7. 验证（代码级，落 sub-repo 执行）

- [ ] 7.1 cloud：`npm run test:acceptance` 先过安全红线（`AC-PROTO-*` 无协议漂移 / `AC-PUB-*` 发布审批链零改 / `AC-RISK-*` 不写风控终态），再全量 `npm test`，再 `npm run typecheck`
- [ ] 7.2 `openspec validate session-auto-resume-with-excursions --strict` 通过

## 8. 部署与归档（显式动作，gated）

- [ ] 8.1 按 §5 安全序列部署 ECS（先备份 → `rsync --dry-run` 摸范围 → rsync 排除 .env/node_modules/.git → restart → healthcheck：8787 / PG `select 1` / 迁移已建列 / 面板 8090 / isales 未碰）；部署后 grep ECS 文件内容 + 看启动日志确认新码生效
- [ ] 8.2 真机校准：正常结束→歇 10%→续场；过活跃窗口/达每日上限/风控受限不续；发布触发→会话结束→发布跑完→新场起、无撞页；巡视耗时不计入单场、巡视不被时限掐断；看门狗 1h 生效 + 后台改阈值下场即生效
- [ ] 8.3 `openspec validate --strict` 终检 → archive（delta 合并进 `openspec/specs/`，归档目录 `<YYYY-MM-DD>-session-auto-resume-with-excursions/`）
