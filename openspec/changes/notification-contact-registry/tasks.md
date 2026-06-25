> **并发协调（多流并行，本流 = notification-contact-registry）**
> - **迁移号 0016**：现盘最高 `0015_session_config`；0009–0015 已被各流占。本流取 **0016**。动前 `ls ../aidcp-cloud/migrations/` 复核、与并发会话错峰。
> - **协议四处归属冲突（动前必读）**：`account-real-nickname` 声明独占协议四处。本流需改两份 `protocol.ts`（`NotificationItem` 扩 kind + `fromUserId?`）+ `docs/protocol.md`，**不新增 MessageType**（复用 `notification.items`，故 `command-bridge.ts` / `edge-client.ts` onMessage 预期不动，实装核对）。**与 `account-real-nickname` 排序后再落协议**（其一先、另一 rebase）。
> - **巡视协调**：点赞/关注抽取与 `notification-monitor`（巡视编排）、`notification-clear-to-zero`（清零，已部分部署）协调；抽取为清零旁路只读输出，绝不改变清零结果。
> - **共享 chokepoint 只 APPEND**：`../aidcp-cloud/src/panel/panel-store.ts`、`panel/types.ts`、`src/server.ts`、`src/orchestrator/role-dispatcher.ts`（仅订阅 APPEND）、`../aidcp-console/src/api/queries.ts`、`src/types/api.ts`、`src/App.tsx`、`src/pages/AppShell.tsx`。
> - 部署 = 显式发布动作，按 CLAUDE.md §5 安全序列；同机多会话错峰（见 [[deploy-verify-content-after-rsync]] / [[precise-git-add-concurrent-sessions]]）。
>
> **实装实测注记**：实装期三仓工作树均洁净（无并发 WIP）；协议未新增 MessageType，故未与 `account-real-nickname` 撞号（两份 protocol.ts 的 NotificationItem 改动逐字一致、git diff 实证）。对抗评审报告的 isVideo / 注释漂移为**既有 master 债务、非本流引入**（见 §7 注）。

## 1. aidcp-edge — 抽取主页ID + 点赞/关注发送者（红线：只读上报、保清零）

- [x] 1.1 `src/browse/notification-monitor.ts`：`buildNotificationItemsJs`（评论/@）增 `fromUserId` —— 从行内头像 `a[href*="/user/profile/"]` 解析 `<id>`，取不到留空（不抛、不瞎猜） <!-- aidcp-edge 521dff0 -->
- [x] 1.2 `src/browse/notification-monitor.ts`：新增「赞和收藏」抽取（kind=like/collect、fromUser、fromUserId、目标笔记标题/note 锚点若有），并入 `buildNotificationCategoryItemsJs('likes')` <!-- aidcp-edge 521dff0；选择器 best-effort，真机校准见 8.3 -->
- [x] 1.3 `src/browse/notification-monitor.ts`：新增「新增关注」抽取（kind=follow、fromUser、fromUserId），`buildNotificationCategoryItemsJs('follows')` <!-- aidcp-edge 521dff0；真机校准见 8.3 -->
- [x] 1.4 `src/browse/browse-session.ts`：`viewNotificationCategory('likes'|'follows')` 升级为「清未读 + 抽取发送者 + 经 `notification.items` 上报」；**保留清零行为**（仍滚动/看一眼清至 0）；抽取失败不阻断清零回执 <!-- aidcp-edge 521dff0 -->
- [x] 1.5 `src/comm/protocol.ts`：`NotificationItem.kind` 扩为 `comment|mention|like|collect|follow`、增 `fromUserId?: string`（与云端逐字一致） <!-- aidcp-edge 521dff0 -->
- [x] 1.6 edge `npm run typecheck` + `npm test`（notification-monitor 既有断言不回归） <!-- aidcp-edge 521dff0：typecheck 绿 / acceptance 11/11 / full 326/326 -->

## 2. aidcp-cloud + docs — 协议同步（四处纪律）

- [x] 2.1 `src/comm/protocol.ts`：`NotificationItem` 扩 kind + `fromUserId?`（与 edge 逐字一致；两份 protocol.ts 的 NotificationItem byte-identical 实证） <!-- aidcp-cloud 5118a0b -->
- [x] 2.2 `docs/protocol.md`：更新 `NotificationItem` 字段说明 + 点赞/关注现经 `notification.items` 报 items 的说明（未增 MessageType，头部计数不变） <!-- aidcp 本仓（本次提交）-->
- [x] 2.3 核对 `command-bridge.ts` 动作映射与 `edge-client.ts` onMessage 白名单：`notification.browse_*` 既有命令已生效、`notification.items` edge→cloud 无需白名单 → 不动；AC-PROTO 26/26 绿确认无漂移 <!-- 5118a0b：未新增 MessageType，四处仅 2 份 protocol.ts + docs 改动 -->

## 3. aidcp-cloud — 存储（迁移 0016，两表 + store）

- [x] 3.1 `migrations/0016_notification_contacts.sql`：`notification_event`（PK `(account_id, dedup_key)` + `(account_id, seen_at DESC)`/`(account_id, from_user_id)` 索引）+ `notification_contact_meta`（PK `(account_id, sender_key)`、`tags TEXT[]`、`wechat`/`note`/`updated_at`/`updated_by`）；幂等；表头注明 PII 留存理由 <!-- aidcp-cloud 5118a0b -->
- [x] 3.2 `src/cache/notification-contact-store.ts`（自带池 + 内嵌同源 DDL + ON CONFLICT）：`appendEvents` —— 按 kind 算 `dedup_key`（评论/@ 含内容哈希、点赞/收藏含 note 锚点、关注按人；红线：同人不同评论不撞键）、空串归 NULL、多行 `INSERT ... ON CONFLICT DO NOTHING`、同批次去重 <!-- aidcp-cloud 5118a0b -->
- [x] 3.3 store：`listContacts` 读时投影（只左连 meta 1:1、`COUNT(*)`、原因/时间聚合）；缺表（42P01）回落空 <!-- aidcp-cloud 5118a0b -->
- [x] 3.4 store：`setManual` upsert meta（仅人工字段）；每账号留存上限（`appendEvents` 后删最旧，按 account_id scoped，非全局） <!-- aidcp-cloud 5118a0b -->
- [x] 3.5 store 单测：50锚点=1联系人/同人同篇两评论=两行（红线防丢）、重扫幂等、空昵称归一、按账号删旧、setManual 只动侧表（test/notification-contact-store.test.ts 14 用例全绿） <!-- aidcp-cloud 5118a0b -->

## 4. aidcp-cloud — 记录接线（notification.items.arrived，APPEND）

- [x] 4.1 `src/server.ts`：构造 `NotificationContactStore` + `await init()`（接既有 store-init 之后；init 失败留 undefined 退化不崩） <!-- aidcp-cloud 5118a0b -->
- [x] 4.2 `buildDispatcher` 内订阅每连接 `ctx.bus` 的 `notification.items.arrived` → `appendEvents(ctx.accountId, items)`，try/catch 吞+准确日志（不冒充飞书失败、不阻塞巡视）；每连接订阅一次（buildDispatcher 每连接调一次，非 setup/restart） <!-- aidcp-cloud 5118a0b -->
- [x] 4.3 最小有效性闸：无身份且内容/昵称/锚点皆空的行丢弃；预览 dispatcher 无边缘会话天然不触发（对抗评审 wiring 维度 PASS 确认） <!-- aidcp-cloud 5118a0b -->

## 5. aidcp-cloud — 面板 API（JWT 闸，APPEND）

- [x] 5.1 `src/panel/types.ts`：`PanelDeps.notificationContact?`（listContacts/setManual）+ 复用 store 导出 `NotificationContact`/`NotificationContactManual` DTO <!-- aidcp-cloud 5118a0b -->
- [x] 5.2 `src/panel/panel-server.ts`：`GET /api/notification/contacts?accountId&limit&offset`（accountId 必填→缺 400、绝不默认 default；缺表→空；未注入→503；未鉴权→401 继承） <!-- aidcp-cloud 5118a0b -->
- [x] 5.3 `src/panel/panel-server.ts`：`PUT /api/notification/contacts/:accountId/:senderKey`（严格校验 wechat/note/tags≤20×≤40；accountId/senderKey 取自 path 非 JWT；updatedBy=sub；非法→400 不落库；未注入→503；只动侧表） <!-- aidcp-cloud 5118a0b -->
- [x] 5.4 `src/server.ts`：panel deps 注入 `notificationContact`（与记录同一 store 实例） <!-- aidcp-cloud 5118a0b -->
- [x] 5.5 panel 校验：缺 accountId 400、按账号隔离、token 不可越权指定账号、写只动侧表、非法标签整块拒（对抗评审 red-lines 维度 PASS 确认；端到端 401/400 真机连通见 8.x） <!-- aidcp-cloud 5118a0b -->

## 6. aidcp-console — 通知联系人页（按账号 + 人工编辑）

- [x] 6.1 `src/types/api.ts`：`PanelNotificationContact` DTO（与 cloud 逐字对齐，APPEND） <!-- aidcp-console 00bd821 -->
- [x] 6.2 `src/api/queries.ts`：`useNotificationContacts(accountId)`（accountId 为空不查）+ 页面内保存 mutation（apiPut，非乐观、成功 invalidate） <!-- aidcp-console 00bd821 -->
- [x] 6.3 `src/pages/NotificationContactsPage.tsx`（新）：必选账号选择器（无全账号视图）+ 诚实口径 Alert + 表格（昵称含「昵称缺失」/ 原因中文标签 / 标签 / 微信 / 次数可排序 / 添加时间 / 最近时间 / 操作）+ 编辑弹窗（标签多选 + 微信 + 备注）+ 空态 <!-- aidcp-console 00bd821 -->
- [x] 6.4 `src/App.tsx` 加 `/notification-contacts` 路由；`src/pages/AppShell.tsx` 导航加「通知联系人」（ContactsOutlined，APPEND） <!-- aidcp-console 00bd821 -->
- [x] 6.5 console `npm run typecheck` + 生产 `npm run build` 绿 <!-- aidcp-console 00bd821 -->

## 7. 验证（红线 + 回归）

- [x] 7.1 edge：`npm run test:acceptance`（AC-PROTO 不漂移）11/11 + 全量 `npm test` 326/326 + `npm run typecheck` 绿 <!-- aidcp-edge 521dff0 -->
- [x] 7.2 cloud：`npm run test:acceptance` 26/26（AC-PROTO/PUB/RISK 不受影响）+ 全量 `npm test` 679/679（含 14 新用例）+ `npm run typecheck` 绿 <!-- aidcp-cloud 5118a0b -->
- [x] 7.3 `openspec validate notification-contact-registry --strict` 通过 <!-- 见本次提交 -->
<!-- 对抗评审（4 路：协议漂移 / SQL fan-out / 运行时接线 / 红线隔离）：wiring + red-lines 两维 PASS 零问题；
     SQL 维确认投影只 1:1 连 meta 无放大、按账号留存、去重键防丢；协议维报告的 isVideo + 注释漂移为
     **既有 master 债务、非本流引入**（本流 protocol.ts diff 仅 NotificationItem，两仓逐字一致，git diff 实证）。 -->

## 8. 部署 + 真机（gated，显式发布才做）

- [x] 8.1 ECS 跑迁移 0016；cloud 按 §5 安全序列部署 <!-- 2026-06-25 deployed。备份 /opt/aidcp/cloud.bak.20260625-155258.tar.gz(252K,code)+.env.bak.20260625-155258；部署范围实证=本流单 commit 5118a0b（git log f9b2092..5118a0b 仅一条、rsync itemize 仅 7 文件+0016）；rsync src/migrations(no --delete, exclude .env/node_modules/.git)；显式跑 0016（node_modules/.bin/tsx run-migration，status ok）；restart aidcp-cloud(新 pid 1527361)；healthcheck 全绿：active+8787/8090 LISTENING+「NotificationContactStore 已就绪」+「连接运行时多租户就绪」+飞书长连接已建立+面板路由 GET/PUT 401(route+proxy+JWT 闸通,非404)；内容校验非仅信回执(grep server.ts NotificationContactStore=11 + store 文件 12KB 在 ECS)；psql \d 确认两表+列(tags TEXT[] DEFAULT '{}'/wechat/sender_key/account_id)；投影 SQL 真机执行 0 行无错(GROUP BY/array_agg/LEFT JOIN 语法在该 PG 版本有效)。isales 4 服务 active+:80=200 全程未碰。[[deploy-verify-content-after-rsync]] -->
- [x] 8.2 console 构建 + 部署到 8088（与 isales 隔离） <!-- 2026-06-25 deployed。fresh build→index-BXxMrUS9.js；rsync --delete(删旧 index-CxyWaiW9.js)；nginx 8088 root=200 / /notification-contacts SPA=200；served bundle==on-disk bundle==index-BXxMrUS9.js -->
- [ ] 8.3 真机校准（gated，需真机浏览器/账号）：点赞/关注两栏 DOM 行结构 + 主页ID 解析校准（评论栏已校准、这两栏 best-effort 待真机 dump 收口）；验「同人同篇两评论 = 两行事件」
- [ ] 8.4 真机 E2E（gated，需本地 edge 连 ECS + 真实账号浏览）：触发真实 评论/点赞/关注 → 联系人页对应账号出现该人、原因/昵称/时间正确、加标签不改次数

## 9. 收尾

- [x] 9.1 按 sub-repo 分节回写本 tasks.md 进度（cloud 5118a0b / edge 521dff0 / console 00bd821 / 本仓 docs） <!-- 本次提交 -->
- [ ] 9.2 `/opsx:archive`（待 8.4 真机出数后；delta 合并进新 capability `openspec/specs/notification-contact-registry`）
