> 范围：Phase 1，只做定时自动发帖。评论 / 群评排期是后续独立变更。落地前先满足 §0 前置。

## 0. 前置（不写排期代码）

- [ ] 0.1 确认在途 WIP（`editable-account-group-label` / `account-group-chat-injection` / `role-thinking-mode-config`）在云端 `account-store` / `panel-server` / `panel/types` / `server` 那摊已解结、提交、测试通过；本变更再落云端，避免加深交织
- [ ] 0.2 迁移文档编号确认：用 `migrations/0028_content_schedule.sql`（0026/0027 已占）

## 1. aidcp-cloud — 内容排期数据层

- [x] 1.1 全局单例表 `content_schedule_global`（`content_active_mask TEXT` 168 格 '0'/'1' + 审计列），`CREATE TABLE IF NOT EXISTS` 于 store `init()` 自建（幂等、单例行守卫） <!-- aidcp-cloud (branch content-schedule-cloud) a35a8ed 待合并；src/config/content-schedule-store.ts -->
- [x] 1.2 旁挂 1:1 侧表 `account_content_schedule`（PK `account_id`；`auto_enabled`/`post_enabled` 默认 false、`post_daily_cap INTEGER` 默认 0、`content_active_mask TEXT` null=继承全局、审计列），`CREATE TABLE IF NOT EXISTS` 自建 <!-- a35a8ed 待合并 -->
- [x] 1.3 单写方法 `setGlobal(patch)`：掩码非 168 位 '0'/'1' 整块拒、`RETURNING` 回读真态、诚实结果联合 <!-- a35a8ed 待合并；方法名 setGlobal（非 setContentScheduleGlobal） -->
- [x] 1.4 单写方法 `setAccount(accountId, patch)`：UPSERT-only、UPSERT 前 `SELECT 1 FROM accounts` 校验存在（无行→`account_not_found`、绝不造幽灵行）、退役 `default` 拒、非法整块拒、`RETURNING` 回读、诚实联合、绝不 raw UPDATE / 乐观 <!-- a35a8ed 待合并；reason=account_not_found（非 unknown_account） -->
- [x] 1.5 读方法 `getGlobal()` / `getAccount(accountId)` / `listCatalog()`（`LEFT JOIN accounts`，缺行合成默认全 false/0/继承、`configured=false`；派生 `effectiveMask`=override??global、`maskSource`）+ 调度器现读 `effectiveScheduleFor(accountId)` <!-- a35a8ed 待合并；hasGroupCode 归 Phase 3 群评、本期未派生 -->
- [x] 1.6 掩码判定 fail-closed：调度器 tick 用 `isValidWeekActiveMask(mask) && isWeekActiveAt(mask, now)`，非法 / 缺失一律「不活跃、跳过」；**绝不**复用 `isWeekActiveAt` 的非法→全天活跃兜底 <!-- a35a8ed 待合并；落在 content-scheduler.ts onTick -->
- [ ] 1.7 人审文档 `migrations/0028_content_schedule.sql`（两表 DDL，与 store 建表逐字对齐）

## 2. aidcp-cloud — 发帖多账号泛化 + 日上限计数

- [x] 2.1 发帖触发加孪生入口 `triggerScheduled(accountId)`：复用 `doTrigger`/`buildTriggerInput`、`forced=false`（`ContentScout` 可诚实判无素材跳过）、绕开 `checkAndMaybeTrigger` 的 `resolveSingleAccountId` 单账号闸；persona 绑定 + 风控 `status==='normal'` + `canDo('publish')` + 发布前人审全部不变 <!-- aidcp-cloud (branch content-schedule-cloud) 787a9cc 待合并 -->
- [x] 2.2 `isBusy()` 真全局忙闲闸（无 accountId，`publishing` flag 环绕 doTrigger）；调度器侧再加 `postFiring` 同步闸防同 tick 双 fire（load-bearing：发帖必须全局串行、禁按账号并行，除非先消灭 publishAccountRef 全局槽） <!-- 787a9cc 待合并；+1 全局串行测试 -->
- [x] 2.3 `countPublishedTodayForAccount(accountId)` 从 `publish_log`（已账号感知）按服务器本地日历日派生；日上限判定 = 今日已发 + `hasPendingApprovalForAccount(accountId)`（在途草稿计入，堵 TOCTOU） <!-- 787a9cc 待合并 -->

## 3. aidcp-cloud — 内容调度器（ContentScheduler）

- [ ] 3.1 `ConnectionRuntimeRegistry` 加 `onlineAccountIds(): string[]` 访问器（遍历取有 edgeId 的 distinct accountId） <!-- 调度器已把它作为注入 dep（onlineAccounts）；真实访问器待 §4 装配时加 -->
- [x] 3.2 `ContentScheduler`（新文件、纯控制流、全 I/O 注入、可脱边端单测）：每 tick 遍历在线账号，闸序 `enabled ∧ fail-closed(effectiveMask,now) ∧ 分钟命中偏移 ∧ 风控 normal ∧ 非全局忙 ∧ 未达日上限` <!-- aidcp-cloud (branch content-schedule-cloud) a35a8ed 待合并；src/orchestrator/content-scheduler.ts -->
- [x] 3.3 分钟错峰 `offset = hash(accountId + localDayKey(now) + 'post') % 60`（纯函数无状态可复现） <!-- a35a8ed 待合并；自带 localDayKey（不导出 dispatcher 的、避开热点文件）+ djb2 hash -->
- [x] 3.4 幂等键 `(account, 小时格)`（同格不重触发）+ tick 重入护栏（上轮未完跳过）+ 每账号 single-flight 集合（本 Phase 只发帖，预留背板） <!-- a35a8ed 待合并 -->
- [x] 3.5 触发**发帖全局串行 + fire-and-forget**：下发前过 `isPublishBusy()`、忙则本槽顺延；心跳「发起即返回」绝不 `await` 生成管线 <!-- a35a8ed 待合并 -->
- [ ] 3.6 每次触发回诚实结果卡：已发起待审 / 本槽无新素材本次不发 / 失败带原因；绝不静默假成功 <!-- 归 triggerPost 注入实现（§4 装配）异步补卡，调度器只 fire -->


## 4. aidcp-cloud — 装配与旧扳机互斥

- [ ] 4.1 `server.ts` 在 PublishScheduler / CommentScheduler 构造后装配 `ContentScheduler`（注入 onlineAccounts / scheduleFor / triggerScheduled / isPublishBusy / countToday / 结果卡发送），`setInterval(60_000)` 守卫在 `AIDCP_CONTENT_SCHEDULE_AUTO`
- [ ] 4.2 内容调度器开启时**无条件、启动期确定性关闭**旧 `AIDCP_PUBLISH_AUTO` 单账号定时器；二者 MUST NOT 并存、**不留 fallback**；启动日志明示走哪条

## 5. aidcp-cloud — 面板 API

- [ ] 5.1 新 panel dep `PanelContentSchedule` / `PanelContentScheduleGlobal`（不复用 `accountAttr`）+ DTO（`ContentScheduleRow` / 全局 view），`panel/types` 定义 + 校验（掩码 168 位、日上限非负整数）
- [ ] 5.2 端点 `GET /api/content-schedule` / `PUT /api/content-schedule/:accountId` / `GET,PUT /api/content-schedule/global`（JWT 保护；写经 §1 单写方法、诚实非乐观）

## 6. aidcp-console — 前端「内容排期」页

- [x] 6.1 抽出共用周历网格组件（从 `QuotasPage` 的浏览掩码网格控件抽到 `src/components/`），安全页与内容排期页共用 <!-- aidcp-console 7c99529 偏离：新建 src/components/WeekActiveGrid.tsx（从 QuotasPage 忠实复制 + 导出 helper），内容排期页已用；为避免并发 session 改动期碰 QuotasPage，QuotasPage 改用共享组件的去重留后续 -->
- [x] 6.2 新页「内容排期」Card1=全局「内容可自动时段」网格（复用组件；文案区分「治自动发帖」vs 浏览页那张「治浏览会话」、点破「格子=何时允许自动尝试、非保证发出」） <!-- aidcp-console 7c99529 -->
- [x] 6.3 新页 Card2=每账号策略表（账号 | 总开关默认关 | 发帖开关 + 日上限 | 时段=跟随全局）；账号变多只加行；每账号自定义时段编辑入口 v1 不做 <!-- aidcp-console 7c99529 -->
- [x] 6.4 `types/api.ts` 镜像 DTO（两处防漂移）；`queries` 读写 `/api/content-schedule[/:accountId]` 与 `/global`；路由 / 菜单入口 <!-- aidcp-console 7c99529 前端先照 spec DTO 契约建；cloud 端点待云端仓安静后落 -->

## 7. 测试与回归

- [x] 7.1 cloud 调度器单测：闸序 / 错峰偏移确定性 / 幂等键 / 重入护栏 / 日上限原子（已发+在途）/ fail-closed 掩码 / 全局串行 / fire-and-forget 不阻塞 <!-- aidcp-cloud (branch content-schedule-cloud) a35a8ed 待合并；test/content-scheduler.test.ts 10/10 通过。「开新关旧扳机互斥」待 §4 装配后补断言 -->
- [ ] 7.2 cloud 存储单测：UPSERT 校验账号存在 / 退役拒 / 非法整块拒 / 写后回读真态 / 未配=不自动
- [ ] 7.3 面板写诚实非乐观断言（拒绝与成功可区分、绝不 raw UPDATE）
- [ ] 7.4 全局回归：`npm run test:acceptance` → `npm test` → `npm run typecheck`（AC-PROTO / AC-PUB / AC-RISK 全过；本变更不动协议 / 风控单写 / 发布发送，人审铁红线不破）
- [x] 7.5 console `npm run typecheck` + `npm run build` <!-- aidcp-console 7c99529 typecheck 干净 + vite build 通过（chunk-size 告警为既有、非本变更引入） -->

## 8. 部署（按需、安全序列）

- [ ] 8.1 前置：§0 WIP 解结提交后再部署
- [ ] 8.2 cloud 面板层按安全序列（备份 → rsync `--exclude .env/node_modules/.git` → `systemctl restart` → healthcheck `active(running)`+8787+飞书长连接+PG `select 1`）；失败即回滚；绝不碰同机 isales
- [x] 8.3 console 构建产物发 nginx root（**不 `--delete`**） <!-- aidcp-console 7c99529 2026-07-03 deployed：rsync dist/ → /opt/aidcp/console（无 --delete，intro.* 保留）；nginx 8088 HTTP 200、/api 反代 200、isales 端口未动。注：前端为 shell，/api/content-schedule 端点待云端实现前进页面为空/存不了 -->
- [ ] 8.4 先建表 + 上界面、`AIDCP_CONTENT_SCHEDULE_AUTO` 保持关，验证配置读写诚实后再开自动扳机
