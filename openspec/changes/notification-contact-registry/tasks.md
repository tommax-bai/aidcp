> **并发协调（多流并行，本流 = notification-contact-registry）**
> - **迁移号 0016**：现盘最高 `0015_session_config`；0009–0015 已被各流占。本流取 **0016**。动前 `ls ../aidcp-cloud/migrations/` 复核、与并发会话错峰。
> - **协议四处归属冲突（动前必读）**：`account-real-nickname` 声明独占协议四处。本流需改两份 `protocol.ts`（`NotificationItem` 扩 kind + `fromUserId?`）+ `docs/protocol.md`，**不新增 MessageType**（复用 `notification.items`，故 `command-bridge.ts` / `edge-client.ts` onMessage 预期不动，实装核对）。**与 `account-real-nickname` 排序后再落协议**（其一先、另一 rebase）。
> - **巡视协调**：点赞/关注抽取与 `notification-monitor`（巡视编排）、`notification-clear-to-zero`（清零，已部分部署）协调；抽取为清零旁路只读输出，绝不改变清零结果。
> - **共享 chokepoint 只 APPEND**：`../aidcp-cloud/src/panel/panel-store.ts`、`panel/types.ts`、`src/server.ts`、`src/orchestrator/role-dispatcher.ts`（仅订阅 APPEND）、`../aidcp-console/src/api/queries.ts`、`src/types/api.ts`、`src/App.tsx`、`src/pages/AppShell.tsx`。
> - 部署 = 显式发布动作，按 CLAUDE.md §5 安全序列；同机多会话错峰（见 [[deploy-verify-content-after-rsync]] / [[precise-git-add-concurrent-sessions]]）。

## 1. aidcp-edge — 抽取主页ID + 点赞/关注发送者（红线：只读上报、保清零）

- [ ] 1.1 `src/browse/notification-monitor.ts`：`buildNotificationItemsJs`（评论/@）增 `fromUserId` —— 从行内头像 `a.user-avatar[href*="/user/profile/"]` 解析 `<id>`，取不到留空（不抛、不瞎猜）
- [ ] 1.2 `src/browse/notification-monitor.ts`：新增「赞和收藏」抽取器（kind=like/collect、fromUser、fromUserId、目标笔记标题/note 锚点若有）——行结构**真机校准**，以评论栏为模板，code-point 安全截断
- [ ] 1.3 `src/browse/notification-monitor.ts`：新增「新增关注」抽取器（kind=follow、fromUser、fromUserId）——真机校准
- [ ] 1.4 `src/browse/browse-session.ts`：`viewNotificationCategory('likes'|'follows')` 升级为「清未读 + 抽取发送者 + 经 `notification.items` 上报」；**保留清零行为**（仍滚动/看一眼清至 0）
- [ ] 1.5 `src/comm/protocol.ts`：`NotificationItem.kind` 扩为 `comment|mention|like|collect|follow`、增 `fromUserId?: string`（与云端逐字一致）
- [ ] 1.6 edge `npm run typecheck` + `npm test`（含 notification-monitor 既有断言不回归）

## 2. aidcp-cloud + docs — 协议同步（四处纪律）

- [ ] 2.1 `src/comm/protocol.ts`：`NotificationItem` 扩 kind + `fromUserId?`（与 edge 逐字一致；两份 `Record<MessageType,true>` 穷举不漂移）
- [ ] 2.2 `docs/protocol.md`：更新 `NotificationItem` 字段说明 + 点赞/关注现经 `notification.items` 报 items 的说明（头部计数不变=未增 MessageType）
- [ ] 2.3 核对 `command-bridge.ts` 动作映射与 `edge-client.ts` onMessage 主动命令白名单：`notification.browse_*` 为既有命令已生效、`notification.items` 为 edge→cloud 无需白名单 → 预期不动；逐一确认无遗漏

## 3. aidcp-cloud — 存储（迁移 0016，两表 + store）

- [ ] 3.1 `migrations/0016_notification_contacts.sql`：`notification_event`（PK `(account_id, dedup_key)` + `(account_id, seen_at DESC)`/`(account_id, from_user_id)` 索引）+ `notification_contact_meta`（PK `(account_id, sender_key)`、`tags TEXT[] NOT NULL DEFAULT '{}'`、`wechat`/`note`/`updated_at`/`updated_by`）；幂等；表头注明第三方 PII 留存理由
- [ ] 3.2 `src/cache/notification-contact-store.ts`（新，模仿 `valuable-comment-store.ts`：自带池 + `init()` 内嵌同源 DDL + ON CONFLICT）：`appendEvents(accountId, items)` —— 按 kind 算 `dedup_key`（评论/@ 含内容判别、点赞/收藏含 note 锚点、关注按人；红线：同人不同评论不撞键）、`from_user`/`from_user_id` 空串归一为 NULL、多行 `INSERT ... ON CONFLICT DO NOTHING`
- [ ] 3.3 store：`listContacts(accountId, limit, offset)` 跑读时投影（只左连 meta 1:1、`COUNT(*)`、原因/时间聚合）；缺表回落空
- [ ] 3.4 store：`setManual(accountId, senderKey, {wechat, note, tags}, updatedBy)` upsert meta（仅人工字段）；每账号留存上限（`appendEvents` 后删最旧，对齐 valuable-comment 口径）
- [ ] 3.5 store 单测：50锚点=1联系人/次数50、同人同篇两评论=两行（D3 防丢）、重扫与重启幂等、空昵称归一、按账号隔离、加标签不放大计数

## 4. aidcp-cloud — 记录接线（notification.items.arrived，APPEND）

- [ ] 4.1 `src/server.ts`：构造 `NotificationContactStore`、`await init()`（接既有 store-init 之后）
- [ ] 4.2 订阅每连接 `notification.items.arrived`（`role-dispatcher.ts` setupEdgeEventSubscriptions 或 server 连接装配处，APPEND）→ `store.appendEvents(连接真实accountId, items)`，`try/catch` 包住、失败吞+准确日志（不冒充飞书失败、不阻塞巡视）；钩子注释点明「记录==边缘抽到上报，与飞书无关」
- [ ] 4.3 最小有效性闸：无身份且内容/昵称皆空的结构异常行丢弃；预览调度器（无边缘会话）天然不触发，加回归断言

## 5. aidcp-cloud — 面板 API（JWT 闸，APPEND）

- [ ] 5.1 `src/panel/types.ts`：`PanelDeps.notificationContact?`（注入 store：listContacts/setManual）+ `PanelNotificationContact` DTO（camelCase mapper、时间戳 epoch ms）
- [ ] 5.2 `src/panel/panel-server.ts`：`GET /api/notification/contacts?accountId&limit&offset`（accountId 必填→缺则 400；缺表→空；未注入→503；未鉴权→401）
- [ ] 5.3 `src/panel/panel-server.ts`：`PUT /api/notification/contacts/:accountId/:senderKey`（严格校验 wechat/note/tags；accountId/senderKey 取自 path 非 JWT；updatedBy=sub；非法→400 不落库；未注入→503）
- [ ] 5.4 `src/server.ts`：panel deps 注入 `notificationContact`（与记录同一 store 实例）
- [ ] 5.5 panel 单测：缺 accountId 400、按账号隔离、token 不可越权指定账号、写只动侧表、非法标签 400

## 6. aidcp-console — 通知联系人页（按账号 + 人工编辑）

- [ ] 6.1 `src/types/api.ts`：`PanelNotificationContact` DTO（与 cloud 逐字对齐，APPEND）
- [ ] 6.2 `src/api/queries.ts`：`useNotificationContacts(accountId)`（accountId 为空不查）+ 保存 mutation（apiPut，非乐观、成功 invalidate，APPEND）
- [ ] 6.3 `src/pages/NotificationContactsPage.tsx`（新）：必选账号选择器（无全账号视图）+ 诚实口径 Alert + 表格（昵称含「昵称缺失」标记 / 原因中文标签 / 标签 / 微信 / 次数可排序 / 添加时间 / 最近时间 / 操作）+ 编辑弹窗（仅 标签多选 + 微信 + 备注）+ 空态
- [ ] 6.4 `src/App.tsx` 加 `/notification-contacts` 路由；`src/pages/AppShell.tsx` 导航加「通知联系人」（APPEND）
- [ ] 6.5 console `npm run typecheck` + 生产 `npm run build` 绿

## 7. 验证（红线 + 回归）

- [ ] 7.1 edge：`npm run test:acceptance`（AC-PROTO 两份 protocol.ts 不漂移）+ 全量 `npm test` + `npm run typecheck`
- [ ] 7.2 cloud：`npm run test:acceptance`（AC-PROTO/PUB/RISK 不受影响——不碰发布/风控单写）+ 全量 `npm test` + `npm run typecheck`
- [ ] 7.3 `openspec validate notification-contact-registry --strict` 通过

## 8. 部署 + 真机（gated，显式发布才做）

- [ ] 8.1 ECS 跑迁移 0016；cloud 按 §5 安全序列部署（备份→rsync→restart→healthcheck，grep 新码确认生效，非仅信 rsync 回执）
- [ ] 8.2 console 构建 + 部署到 8088（与 isales 隔离）
- [ ] 8.3 真机校准：点赞/关注两栏 DOM 行结构 + 主页ID 解析校准；验「同人同篇两评论 = 两行事件」
- [ ] 8.4 真机 E2E：在某绑定账号触发真实 评论/点赞/关注 → 联系人页对应账号出现该人、原因/昵称/时间正确、加标签不改次数

## 9. 收尾

- [ ] 9.1 按 sub-repo 分节回写本 tasks.md 进度（commit-sha + 偏离说明）
- [ ] 9.2 `/opsx:archive`（待 8.4 真机出数后；delta 合并进新 capability `openspec/specs/notification-contact-registry`）
