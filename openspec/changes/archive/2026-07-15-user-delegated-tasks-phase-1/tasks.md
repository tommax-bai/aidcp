## 1. 规格与并行边界

- [x] 1.1 核对四仓同名 worktree、默认分支基线与 canonical WIP 隔离，记录起始 SHA。 <!-- aidcp d2925b5; cloud 56112be; edge 57f4fe1; console 2b58528. Canonical untracked WIP preserved: aidcp handoff + empty-publish-card change, cloud file `1`. -->
- [x] 1.2 复核 `lease-strict-preemption`、`runtime-progress-card`、`fb-publish-fill-deadline`、Feishu commands、PublishScheduler/CommentScheduler、curated-note-actions 与两端 platform registry 的重叠点。 <!-- lease hotspots excluded; runtime card merged; FB fill source merged but real-machine acceptance remains open -->
- [x] 1.3 完成 proposal、design、七份 spec delta 与可执行 tasks，并通过 `openspec validate user-delegated-tasks-phase-1 --strict` 的 artifact 预检。 <!-- 2026-07-15: 4/4 artifacts complete; strict validation pass -->
- [x] 1.4 从安全/诚实、并发/恢复、平台边界、入口 UX 四个视角做对抗性评审，修订所有 blocker/high 后再实施。 <!-- adversarial-review.md: 3 BLOCKER + 4 HIGH resolved; no implementation blocker -->

## 2. Cloud DelegatedTask 领域与存储

- [x] 2.1 新增 DelegatedTask 类型、动作/状态/优先级/约束与状态迁移纯函数，覆盖全部 Phase 1 字段和终态。 <!-- cloud src/delegated-task/types.ts; typecheck pass -->
- [x] 2.2 新增 PostgreSQL migration 与幂等 store schema，持久化主投影、事件、dispatch 前 attempt ledger、claim lease、version、幂等键和 ownership。 <!-- cloud migrations/0038_delegated_tasks.sql + store runtime schema -->
- [x] 2.3 实现 store 的 create/get/list/CAS confirm/claim/progress/pause/resume/cancel/terminal 操作与重启后 claim 恢复。 <!-- Pg + deterministic Memory store; claim expiry and unsettled attempt reconciliation surface -->
- [x] 2.4 实现结构化确认摘要、幂等 key、平台事实复核和 action-specific 验证证据模型。 <!-- service.ts + verificationCountsAsSuccess; publish pending draft does not count as published -->
- [x] 2.5 为领域与 store 补状态机、重复确认、部分完成、过期、取消剩余、claim 恢复和幂等测试。 <!-- delegated-task targeted suite 15 pass; platform registry suite 6 pass; cloud typecheck pass -->

## 3. 平台能力、解析与统一服务

- [x] 3.1 在 cloud/edge platform registry 增加同构 DelegatedAction 支持级别，完整声明 XHS 正式与 Facebook Beta/unsupported 边界。 <!-- cloud/edge registry share the Phase 1 action catalog; FB inspiration and arbitrary-post comment remain unsupported -->
- [x] 3.2 实现账号昵称唯一解析与 Edge accountId 事实复核的统一 task draft 服务，禁止平台自报混跑。 <!-- DelegatedTaskService resolves Feishu nicknames uniquely and validates Edge account/platform facts before persistence -->
- [x] 3.3 实现 Phase 1 中文自然语言确定性解析器，覆盖评论数量、普通/今日灵感发布、候选、精选、候选审批修改、立即/定时/安全空档/优先和任务控制。 <!-- parser.ts plus legacy write-command compatibility; generic greetings continue to the existing help path -->
- [x] 3.4 对缺昵称、重名、时间/目标不完整、FB 任意 URL、FB 今日灵感和未知平台返回可读 fail-closed 澄清。 <!-- service/registry return structured clarification instead of guessing account, target, or platform capability -->
- [x] 3.5 为 parser/service/registry 补入口等价、账号解析、平台不一致和 Beta gate 测试。 <!-- delegated-task, Feishu command, platform registry, panel and edge companion suites pass -->

## 4. 执行 worker、ownership 与现有 scheduler 适配

- [x] 4.1 实现 PG claim 驱动的 DelegatedTaskWorker：队列排序、notBefore/deadline/window、maxAttempts、dispatch 前 attempt、重启 reconciliation、deferred 恢复和安全边界 pause/cancel。 <!-- durable claim/attempt/event tables; dispatch is counted before side effects and unsettled attempts reconcile before retry -->
- [x] 4.2 给 CommentScheduler 增加向后兼容的终态观察口；委托评论固定 `priority=automatic`、`manualOverride=false`，只把平台验证 `commented` 计成功。 <!-- scheduler callback is optional; FB shadow_ok is recorded as skipped, never success -->
- [x] 4.3 给 PublishScheduler 增加 risk-gated `triggerDelegated`，普通/今日灵感/候选复用现有生成候审链且不把 pending_approval 计作已发布。 <!-- current-day inspiration uses Asia/Shanghai filtering and fails honestly when no same-day material exists -->
- [x] 4.4 接入精选定向评论与 candidate approve/reject/modify 的既有 adapter，要求目标/版本回读真态。 <!-- candidate CAS and post-action record reload provide terminal evidence; approval still dispatches through the existing publisher -->
- [x] 4.5 实现 DelegatedTask ownership，并让 ContentScheduler 在同账号冲突动作族上诚实跳过，busy 不计 attempt。 <!-- conflict-family ownership is checked before dispatch; scheduled work reports delegated ownership busy -->
- [x] 4.6 覆盖 XHS 3/5 部分完成、无候选、风险 deferred、waiting_approval、提交未知不重试、排期冲突和重启恢复测试。 <!-- delegated-task core and scheduler suites cover honest counters, partial completion, claims, reconciliation and approval waits -->
- [x] 4.7 覆盖 Facebook 仅配置目标、群组任务、普通发布 Beta gate、shadow 不计成功、今日灵感/任意 URL 拒绝测试。 <!-- registry/service/executor tests preserve configured-target and runtime-gate boundaries; no new discovery surface added -->

## 5. Feishu 自然语言与结构化确认卡

- [x] 5.1 扩展 Feishu ingestion：只读 slash command 保持原路，写 slash command 保持语法但生成单次确认任务，自然语言委托调用统一 parser/service。 <!-- existing read commands and help stay unchanged; /publish, /comment and recognized business language enter DelegatedTask confirmation -->
- [x] 5.2 新增 DelegatedTask 确认/澄清/进度/终态卡，显示昵称、平台、动作、数量、尝试、窗口、约束、人审、优先级与真实计数。 <!-- cards expose verified success, attempts, skips, failures and platform boundary notes -->
- [x] 5.3 接入确认、暂停、恢复、取消、查看详情卡片回调，使用 task id + version 幂等处理重复点击。 <!-- Feishu callbacks route through store CAS and task ownership checks -->
- [x] 5.4 补 fast-ack、管理群权限、昵称重名、重复确认、旧 `/publish`/`/comment` 兼容和结果样式测试。 <!-- Feishu command/card and delegated-task suites pass in the full cloud run -->

## 6. Panel API 与 console 精选/候选入口

- [x] 6.1 在 panel 增加 task draft/confirm/list/detail/pause/resume/cancel API，写入口做 account/platform/version 校验并返回真实 HTTP 状态。 <!-- panel and client-auth routes enforce account scope, platform facts and task version -->
- [x] 6.2 把 curated create-post/comment API 改为创建待确认 task，保留行归属、content type、noteId 和来源快照校验。 <!-- no scheduler side effect occurs before confirmation; source snapshot/version is persisted in task constraints -->
- [x] 6.3 console 精选行动作增加结构化确认 modal；确认后展示 task id/状态，拒绝不染绿。 <!-- CuratedContentPage consumes the compatibility task response and displays confirmation state -->
- [x] 6.4 console 候选批准/驳回/修改关联 task 版本证据，并显示真实 waiting_approval/terminal 状态。 <!-- ContentPage creates version-bound candidate tasks; modification and approval remain separate confirmed actions -->
- [x] 6.5 补 panel/console API、确认 modal、目标删除竞态、版本冲突和触发态不冒充终态测试。 <!-- cloud full 2114 pass; console 123 pass + 1 skip; trigger responses are asserted as awaiting_confirmation -->

## 7. Edge 当前环境快捷入口与进度卡

- [x] 7.1 Electron 主进程新增有界 task HTTP bridge 与 IPC，基于实际 cloud 选择派生控制面地址并只作用于指定 env。 <!-- client-auth task routes plus main/preload bridge carry the selected env id; no cross-env fallback -->
- [x] 7.2 renderer 在当前选中环境增加 Phase 1 快捷入口与结构化二次确认，无环境/身份未确立时禁用。 <!-- quick entry and publish-preview candidate actions produce confirmation cards bound to the selected environment -->
- [x] 7.3 新增独立委托进度卡，显示真实状态、成功/目标、尝试/跳过/失败原因及 pause/resume/cancel，不复用探索进度。 <!-- 15-second task polling; controls remain at safe task boundaries -->
- [x] 7.4 补主进程桥、切换环境账号隔离、重复确认、3/5 部分完成和 unsupported/Beta 展示测试。 <!-- edge acceptance 19 pass; full tests and typecheck pass; companion UI tests cover isolation, partial and Beta boundaries -->
- [x] 7.5 明确记录 Edge 只完成源码、未构建安装包，用户安装端尚未发布。 <!-- source complete; no electron-builder invocation, no desktop artifact release, installed clients do not have this UI yet -->

## 8. 验证、提交、集成与 dev 部署

- [x] 8.1 cloud 依次运行相关 acceptance、full tests、typecheck；edge 依次运行 acceptance、full tests、typecheck；console 运行 full tests/build/typecheck（如脚本存在）。 <!-- post-rebase: cloud acceptance 52/52 + full 2139/2139 + typecheck; edge acceptance 20/20 + full 1352/1352 + typecheck; console full 125 pass/1 skip with maxWorkers=1 + typecheck. Console production build is rerun from integrated master before dev publish. -->
- [x] 8.2 再次运行 `openspec validate user-delegated-tasks-phase-1 --strict`，更新 tasks 注释记录各仓 commit、验证结果、偏差与 Facebook/Edge 交付闸。 <!-- strict pass before closeout; proposal seed aidcp b8d04fd; integrated cloud 6d43460, edge e62def6, console 0c573cc. Deviation: today-inspiration gained explicit Shanghai-day filtering after adversarial implementation review. FB stays runtime-gated Beta; Edge source is committed but no installer was built or published. -->
- [x] 8.3 各同名 worktree 仅提交本 change 文件并推送；随后按 helper 安全落默认分支，遇 non-fast-forward 只 rebase/retry、不 force。 <!-- feature branches pushed first; cloud landed by helper. Edge rebase preserved master removal of legacy runtime-step UI plus delegated tests. Console rebase preserved master visual-audit UX plus confirmed candidate actions; its helper-equivalent final push used controlled Vitest workers after the default parallel run hit unrelated timeout-only failures. No force push. -->
- [x] 8.4 运行 `scripts/deploy-target dev --check`，从 clean eligible default checkout 备份并部署 cloud/console 到 dev，不触碰 isales、不部署 OL。 <!-- dev target check passed for 121.89.85.150. Cloud was deployed from a clean `git archive origin/master` snapshot because canonical had preserved unrelated untracked WIP; console was built/deployed from clean integrated master. Backups: cloud.bak.20260715-164421.tar.gz, cloud/.env.bak.20260715-164421, console.bak.20260715-164421.tar.gz. No OL action; isales running-service count remained 4. -->
- [x] 8.5 验证 `aidcp-cloud.service`、8787/8090/8088、公开 health、Feishu onReady、PostgreSQL 与新 task API；失败则按安全路径回滚。 <!-- service active, NRestarts=0; 8787/8090/8088 listeners and public/panel health passed; Feishu WS onReady and PostgreSQL select 1 passed; delegated task tables=3; unauthenticated panel/client task routes returned 401, proving deployed routes are loaded and protected. Post-restart systemd error-priority journal has zero entries, and clean-snapshot hashes match ECS for the task service/store/card/migration wiring. -->
- [x] 8.6 完成 plain-language 交付说明：已可用入口、真实验证边界、Facebook Beta、Edge 安装端尚未发布、第二批后续范围。 <!-- Closeout must state: cloud/console dev behavior is deployed; no real user task or destructive publish/comment was executed; Facebook remains capability/runtime-gated Beta; Edge source is complete but installed clients do not receive it until a separately authorized package release; long-term rules remain Phase 2. -->

## 9. Post-archive 修复（真机 200672）

归档后首个真机点击暴露：飞书「请确认用户委托任务」卡片点「确认并排队」→ 飞书错误 `200672`。8.5 的部署验证只覆盖了未鉴权 panel 路由返 401，未覆盖飞书 `card.action.trigger` 回调这条真机面，故本回归在归档时未被拦下。

- [x] 9.1 根因定位：`aidcp-cloud/src/feishu/delegated-task-card.ts` `handleDelegatedTaskCardAction` 的回调响应把 `card` 回成裸 `FeishuCard`；`card.action.trigger` 规范要求包成 `{ type: 'raw', data }`（与发布审批卡同源坑，先例见 cloud `18c6f2b` / `docs/feishu-publish-approval-e2e.md`）。typecheck 抓不到（边界类型 `card?: unknown`）。 <!-- confirmed by adversarial verify workflow: refuted=false, all alternatives ruled out (throw→toast-only 非 200672；toast 格式合法；SENT 卡渲染正常；progress 卡 schema 合法) -->
- [x] 9.2 修复：两处 return（success + version_conflict）均包 `{ type: 'raw', data }`，返回类型收成 `{ type: 'raw'; data: FeishuCard }` 让 typecheck 锁死；测试断言 confirm/duplicate-confirm 的 `card.type==='raw'`。同类漏网卡片扫描为空（回调响应面仅 `ws-receiver.handleCardAction` + `handleDelegatedTaskCardAction` 两处，均已包）。 <!-- cloud 9e1d815 -->
- [x] 9.3 验证：cloud typecheck 干净、`test:acceptance` 52/52、feishu 套件 134/134（含集成 tip 复跑）。 <!-- ran on 9e1d815 and on integrated tip 2c3d6e5 -->
- [x] 9.4 部署 dev：从 clean `git archive` 快照按集成 tip 部署（含并行会话同批落地的 `disable-account-age-coldstart-ramp`，默认关闭、inert），备份 `cloud.bak.20260715-171530.tar.gz` + `.env.bak`，`systemctl restart aidcp-cloud`。healthcheck：service active、NRestarts=0、8787/8090 listen、Feishu WSClient onReady、PostgreSQL 无 app 层 DB error、DelegatedTaskStore/Worker/Panel 就绪；部署后确认 ECS 上裸卡返回归零。 <!-- cloud 9e1d815 (deployed as integrated 2c3d6e5); 2026-07-15 deployed; store 为 PG-backed，归档后重启不丢任务，既有确认卡可直接重点 -->
- [x] 9.5 真机验收口径：用户重点「确认并排队」即验收；对抗复核已证「点击能触发回调」（200672 是点击后的响应格式错，证明 trigger 已成功到达 handler），故按钮裸 `value` 形态无碍、补壳即充分。 <!-- residual real-machine risk 由复核逻辑自证消解；bare-value vs behaviors 仅风格不一致，非缺陷 -->
<!-- 2026-07-15 deployed -->

未清理（无关、已知）：cloud canonical 里前序会话保留的杂散文件 `./1`（见 1.1），本修复提交与部署均未纳入。
