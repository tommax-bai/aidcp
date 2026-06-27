<!-- 进度（2026-06-27）：§1-§6 + §7.2 实装完成、已 commit+push（cloud 472a2f8 / console 0d4308a / 本仓进度 70d7e59→本次）。代码级验证绿：acceptance 26/26（AC-PROTO/PUB/RISK 全过）+ 自有新测 23/23 + 我方改动文件 tsc 零错。§7.1 全量 npm test/typecheck 被并发 publish-multi-image WIP（其 M types.ts 令 imageUrls/imagePrompts 必填、role 实装未跟上）阻塞，非本 change 代码——待并发 land 后全量复跑。cloud types.ts 经 surgical HEAD-blob+my-hunk 提交（仅含 OrchestratorDeps 回调、不裹挟 multi-image WIP，已验工作树 multi-image WIP 完好保留）。§8.1 **已部署 ECS 2026-06-27 healthcheck 全绿**（cloud 472a2f8 + console 0d4308a，resume_config 表 0 行零回归，isales 未碰；生产即 feature ON=24/7 默认）；§8.2 真机校准 + §8.3 归档 = operator-driven gated。 -->

## 1. aidcp-cloud — 配置层（按账号续场护栏 + 看门狗阈值）

- [x] 1.1 迁移号取 0020（现有最高 0019_interaction_feed）；新增 `migrations/0020_resume_config.sql` **独立表** `resume_config`（非扩 session_config，零改动已部署文件）：`rest_ratio_pct` / `active_window_start_min` / `active_window_end_min` / `daily_max_sessions` / `daily_max_minutes` / `idle_nudge_ms` / `idle_end_ms`（均 nullable，缺列回落写死默认） <!-- aidcp-cloud 472a2f8 偏离: 独立表而非扩 session_config（task 1.2 留的latitude，降已部署文件回归风险） -->
- [x] 1.2 新增 `src/config/resume-config-store.ts`（`ResumeConfigStore implements ResumeConfigProvider`）：`restRatioFor`/`activeWindowFor`/`dailyCapsFor`/`idleNudgeMsFor`/`idleEndMsFor`，逐项缺/非法回落写死默认、永不抛；init 失败装配处吞错退化 <!-- aidcp-cloud 472a2f8 -->
- [x] 1.3 `src/risk/resume-limits.ts`：写死默认常量（`DEFAULT_REST_RATIO_PCT=10`、`DEFAULT_IDLE_NUDGE_MS=130_000`、`DEFAULT_IDLE_END_MS=3_600_000`、`DEFAULT_ACTIVE_WINDOW=全天`、每日不限 0）+ 校验上限 + `isWithinActiveWindow` 纯函数 + `ResumeConfigProvider` 接口 <!-- aidcp-cloud 472a2f8 -->
- [x] 1.4 新增 `src/config/resume-config-facade.ts`（复刻 session-config-facade）：getCatalog（库缺行以写死默认合成）+ 非乐观 set（逐字段校验、任一非法整块拒、写库成功才刷镜像回真态） <!-- aidcp-cloud 472a2f8 -->

## 2. aidcp-cloud — 会话监测体：可暂停时钟 + 看门狗阈值可配

- [x] 2.1 `session-monitor-role.ts`：加 `pauseReasons: Set` + `pauseStartedAt`；公有 `pauseClock(reason)` / `resumeClock(reason)`（0→1 记起点；末次 size→0 时 `startedAt += clock-pauseStartedAt` 并补调 `checkSession()`；陌生 token no-op） <!-- aidcp-cloud 472a2f8 -->
- [x] 2.2 `checkSession()` 顶部 `if (clockPaused()) return`（单点守卫延期时长/动作数/配额）；`subscribe()`/`unsubscribe()` 清暂停态，绝不跨场残留 <!-- aidcp-cloud 472a2f8 -->
- [x] 2.3 看门狗两段阈值改读注入的 `getIdleNudgeMs`/`getIdleEndMs` thunk（按账号现读、热加载），缺省回落写死默认（放弃结束默认 1h、轻推 ~2min）；**空闲看门狗不受 pause 影响**（巡视期保持活着兜底） <!-- aidcp-cloud 472a2f8 -->
- [x] 2.4 单测 10/10 绿（test/agents/session-monitor-role.test.ts）：巡视期不触发时限结束 + resume 补发；扣除暂停段；陌生 token no-op；重订阅清暂停态；暂停期 idle 看门狗仍兜底；阈值经 thunk 热加载 <!-- aidcp-cloud 472a2f8 -->

## 3. aidcp-cloud — 调度器：休息计时器 + 续场闸 + 巡视暂停接线

- [x] 3.1 `role-dispatcher.ts`：`endSession(reason, {autoResumeEligible})`；每连接 `unref` 休息计时器：`rest = maxDurationMs × restRatio × lognormal抖动`，仅「可续场」结束才 arm；记当日 browseMs <!-- aidcp-cloud 472a2f8 -->
- [x] 3.2 续场闸 `canAutoResume(account)`：`canStartSession`（dispatchActive+人设）+ 风控非 restricted/frozen + 活跃时段窗口 + 每日上限（每账号 `{dayKey,sessions,browseMs}` 内存计数、按本地日界重置） <!-- aidcp-cloud 472a2f8 -->
- [x] 3.3 计时器到点 `onRestElapsed` → 过闸 → `tryStartSession`（已 active 早退）；`cancelRestTimer` 在 (re)startSession / endSession 调（dispatch stop/暂停/掉线/边缘先自连均经此取消） <!-- aidcp-cloud 472a2f8 -->
- [x] 3.4 `setupEdgeEventSubscriptions` 接 `excursion.requested → pauseClock('patrol')`、`excursion.ended → resumeClock('patrol')`（随 endSession 拆除）；setup 捕获 `sessionMonitor` 引用 <!-- aidcp-cloud 472a2f8 -->
- [x] 3.5 单测 10/10 绿（test/integration/role-dispatcher-resume.test.ts）：eligible arm≈10%、运营停不 arm、到点续场、frozen/dispatch-off/每日上限不续、isWithinActiveWindow 纯函数（普通/跨午夜/全天） <!-- aidcp-cloud 472a2f8 -->

## 4. aidcp-cloud — 发布「让位」

- [x] 4.1 `connection-runtime.ts`：`endSessionForAccount(accountId, reason)`（不可续场）/ `resumeSessionForAccount(accountId)`（经续场各闸 `tryAutoResume`），遍历 `bySession` 匹配 `rt.accountId` <!-- aidcp-cloud 472a2f8 -->
- [x] 4.2 `publish-agent/types.ts`：`OrchestratorDeps` 加 `onPublishStart?(accountId)` / `onPublishEnd?(accountId)`（与并发 multi-image 改动 disjoint，append 在 OrchestratorDeps 尾） <!-- aidcp-cloud 472a2f8 -->
- [x] 4.3 `publish-orchestrator.ts`：`trigger()` `status='running'` 之后调 `onPublishStart(accountId)`；`finally` 调 `onPublishEnd(accountId)`；早退（已 running）路径不调 <!-- aidcp-cloud 472a2f8 -->
- [x] 4.4 `server.ts`：装配 `onPublishStart=(a)=>runtimes?.endSessionForAccount(a,'publish_takeover')`、`onPublishEnd=(a)=>runtimes?.resumeSessionForAccount(a)`（runtimes 前向引用，同 commandSequencer.pusher 模式） <!-- aidcp-cloud 472a2f8 -->
- [x] 4.5 单测 3/3 绿（test/publish-agent/publish-stepaside.test.ts）：trigger→start 然后 end；accountId 缺省 default；被忽略触发（已 running）不调 start/end <!-- aidcp-cloud 472a2f8 -->

## 5. aidcp-cloud — 面板 API

- [x] 5.1 `panel/types.ts`（`PanelResumeConfig`+DTO）+ `panel-server.ts`：APPEND JWT 守卫 `GET /api/resume-config`（库缺行以写死默认合成）+ `PUT`（非乐观写、`verified.payload.sub` 作 updatedBy、未注入 503、非法整块拒） <!-- aidcp-cloud 472a2f8 -->
- [x] 5.2 `server.ts`：`ResumeConfigStore` init（与其余 config store 同 try/catch 退化）+ 注入 `resumeConfigProvider` 给 dispatcher + 看门狗 thunk + 面板 `resumeConfig: createResumeConfigPanel`（APPEND，不抢并发流同处） <!-- aidcp-cloud 472a2f8 -->

## 6. aidcp-console — 配置编辑区

- [x] 6.1 `src/types/api.ts`（`ResumeConfigRow`/`ResumeConfigCatalog`）+ `src/api/queries.ts`（`useResumeConfig`）APPEND <!-- aidcp-console 0d4308a -->
- [x] 6.2 `QuotasPage.tsx` 加「自动续场与看门狗」Card + 编辑 Modal（按账号：rest_ratio / 活跃时段窗口 / 每日上限 / 看门狗轻推·放弃以分钟编辑），即时校验 + 非乐观回显；`tsc --noEmit` + `vite build` 绿 <!-- aidcp-console 0d4308a -->

## 7. 验证（代码级，落 sub-repo 执行）

- [~] 7.1 cloud：`test:acceptance` **26/26 绿**（AC-PROTO 56 类无漂移 / AC-PUB 审批链零改 / AC-RISK 不自残 全过）+ 自有新测 **23/23 绿** + 我方改动文件 `tsc` **零错**；**全量 `npm test` / `npm run typecheck` 被并发 publish-multi-image WIP 阻塞**（content-assembler/cover-selector/image-generator/image-planner + 其 tests 因 M types.ts 未跟上），非本 change 代码 <!-- BLOCKED by concurrent WIP, not ours; 待并发 land 后全量复跑 -->
- [x] 7.2 `openspec validate session-auto-resume-with-excursions --strict` 通过

## 8. 部署与归档（显式动作，gated）

- [x] 8.1 **已部署 ECS（2026-06-27）**：cloud（pristine origin/master worktree 472a2f8 + 内容级 checksum dry-run 仅本变更 15 文件零co-ship → 备份 → rsync 排除 .env/node_modules/.git 无 --delete → restart）healthcheck 全绿（active + 8787/8090 listening + 面板 /api/health ok + 启动日志「续场配置存储已就绪 resume_config」无错 + resume_config 表已建 0 行=零回归 + grep server.ts resumeConfig=5 新码生效 + types.ts imageUrls=0 未带 multi-image WIP + isales 4/4 未碰）；console（pristine master 0d4308a build → 备份 → rsync dist，served index-DN-LhXrz.js + 8088→200 + nginx ok）。**console 从 master HEAD 构建，附带co-ship 已提交但他会话 deploy-gated 的 prompt-preview 人设选择 UI（4e35cbf）+ nav 改名（a5e35d2），纯加性无回归** <!-- cloud 472a2f8 deployed / console 0d4308a deployed 2026-06-27 -->
<!-- 部署后生产即 feature ON：缺配置默认 rest10%/全天窗口/不限/轻推~2min/放弃1h = 24/7 连刷，运营须经 console「自动续场与看门狗」设活跃时段窗口才不连轴转 -->
- [~] 8.2 真机校准（operator-driven）—— **DEFERRED：用户拍板「先归档，真机验收后续统一做一次全面的」（归档≠已验证，[[archived-unverified-2026-06-21]] 同纪律）**：正常结束→歇 10%→续场；过活跃窗口/达每日上限/风控受限不续；发布触发→会话结束→发布跑完→新场起、无撞页；巡视耗时不计入单场、巡视不被时限掐断；看门狗 1h 生效 + 后台改阈值下场即生效
- [x] 8.3 `openspec validate --strict` 通过 → `openspec archive -y`（3 delta 合并进 `openspec/specs/`：新 session-auto-resume + browse-loop-resilience MODIFIED看门狗+ADDED excursion扣时 + publish-pipeline ADDED让位；归档目录 `2026-06-27-session-auto-resume-with-excursions/`）
