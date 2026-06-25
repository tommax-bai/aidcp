## Why

后台需要一个**按账号维度**的「通知联系人」页：把所有**给本账号发过通知的人**（评论 / @ / 点赞 / 收藏 / 关注）沉淀成一份可人工运营的联系人名册，记录**昵称、加入原因、微信（预留）、标签（人工）、添加时间**。坐实现状（带 `文件:行`）：

- **评论 / @ 的发送者边缘端已抓、已回传**：`../aidcp-edge/src/browse/notification-monitor.ts:134-158`（`buildNotificationItemsJs` 扫「评论和@」栏的列表行）抽出 `{kind, fromUser(昵称), content, itemKey}`，经 `notification.items` 上报（`browse-session.ts:1444`），云端 `comm/handler.ts:253-260` 翻成每连接事件 `notification.items.arrived`。
- **点赞 / 收藏 / 关注的发送者在通知页里看得到，但边缘端目前不抽取**：`browse-session.ts:1457` 的 `viewNotificationCategory('likes'|'follows')` 只「进分类看一眼清未读（v1 不抽取）」，回执 `action.completed`，不报任何人。协议里 `NotificationBrowseLikesPayload`/`FollowsPayload`（`protocol.ts:660-667`）也没有 items 回报字段。**所以这两类要做，需补边缘抽取 + 协议带回**。
- **当前没有稳定的「人」标识**：每条通知行的头像链接里其实带着对方主页ID（`a.user-avatar[href=/user/profile/<id>]`），但边缘端为了评论去重**故意没用它**（`notification-monitor.ts:148-149` 抽 itemKey 时显式跳过 `/user/profile/` 链）。结果系统只有昵称可用 —— 同名会被并成一个人、改名会被拆成两个人。
- **现在没有任何通知发送者的持久化**：去重只有内存水位 `notifiedItemKeys`（`../aidcp-cloud/src/agents/notification-deduper.ts:39-43` 计算 key、按主页链接显式排除以保评论各自独立），进程重启即丢；全仓无通知发送者表。
- **多租户内核已就位**：`multi-account-node-support` 已实装 —— 每连接私有 EventBus + RoleDispatcher + RiskController，`accountId` 经 `edge.hello` 穿透为连接真实账号。记录天然可按账号隔离、定向不广播。
- **存储 / 面板 / console 三层有现成同形先例**：`migrations/0013_llm_token_usage.sql`（按账号预聚合表）、`src/cache/valuable-comment-store.ts`（自带池 + 自建表 + ON CONFLICT + 留存上限存第三方评论 PII）、`src/panel/`（JWT 闸只读 BFF + 写端点）、console `src/pages/TokenUsagePage.tsx`/`PersonaPage.tsx`（按账号筛选表格 + 写表单）。

结论：把通知发送者在**事件到达处统一记成一份按账号的事件流水**（评论/@ 零边缘改动即可；点赞/收藏/关注补边缘抽取后同一通道带回），**人工字段（微信/标签/备注）独立存到侧表**，「联系人列表」按人**读时聚合**算出。识别「人」用边缘新抽的主页ID（取不到再退回昵称）。

## What Changes

- **edge —— 抽取主页ID + 点赞/关注发送者**（红线：纯结构化只读上报，不做任何决策/持久化）：
  - `notification-monitor.ts`：评论/@ 抽取增 `fromUserId`（从头像 `/user/profile/<id>` 解析；取不到留空）；新增「赞和收藏」「新增关注」两栏的发送者抽取（行结构需**真机校准**，以评论栏为模板）。
  - `browse-session.ts`：`viewNotificationCategory('likes'|'follows')` 从「只看一眼清未读」升级为「**看一眼清未读 + 抽取发送者并经 `notification.items` 上报**」；**保留** notification-clear-to-zero 的清零行为不变。
  - 截断沿用既有 code-point 安全 `cut()`；缺字段诚实留空，绝不回退整行 textContent。
- **协议 v2（四处同步纪律）**：`NotificationItem`（两份 `protocol.ts` 逐字一致）`kind` 联合扩为 `'comment'|'mention'|'like'|'collect'|'follow'`、增 `fromUserId?`；`docs/protocol.md` 同步 NotificationItem 文档 + 点赞/关注现报 items 的说明。**不新增 MessageType**（复用 `notification.items`），故 `command-bridge.ts` 动作映射与 `edge-client.ts` onMessage 主动命令白名单**预期不动**（`notification.browse_*` 为既有命令、已生效；实装时核对确认）。
- **cloud —— 记录（事件到达处统一钩，与飞书解耦）**：订阅每连接 `notification.items.arrived`（`comm/handler.ts:255`），按**连接真实账号**追加事件。**红线**：记账被 try/catch 包住、失败只吞并打**准确**日志（绝不冒充飞书失败、绝不阻塞/拖垮巡视）；幂等追加，下轮安全重试。
- **cloud —— 存储（迁移 0016，两表）**：
  - `notification_event`（只追加 = 真相）：`account_id` + `dedup_key`（按 kind 计算，**含内容判别 / note 锚点，绝不把同人不同评论撞成一条**）+ `kind` + `from_user`(可空) + `from_user_id`(可空) + `content` + `note_title` + `seen_at`，主键 `(account_id, dedup_key)`、`ON CONFLICT DO NOTHING`。带**每账号留存上限**（对齐 `valuable-comment-store` 存第三方 PII 的留存口径）。
  - `notification_contact_meta`（人工字段唯一落点）：`account_id` + `sender_key` + `wechat`(预留可空) + `tags TEXT[]`(人工) + `note` + `updated_at` + `updated_by`，主键 `(account_id, sender_key)`。**巡视写入绝不碰本表；人工编辑绝不碰事件流水。**
- **cloud —— 面板 API**：JWT 闸 `GET /api/notification/contacts?accountId=&limit=&offset=`（**accountId 必填、缺则 400，绝不默认 default**；不提供全账号合并视图 = 防把运营自己各账号粉丝交叉关联的 PII 泄露）；`PUT /api/notification/contacts/:accountId/:senderKey`（只改 wechat/note/tags，严格校验、accountId 取自 path 不取自 JWT、updatedBy=JWT sub）。缺表回落空、未注入 503、未鉴权 401。
- **console —— 新「通知联系人」页（`/notification-contacts`）**：必选账号（无全账号视图）；表格列 昵称（缺失显式「昵称缺失」不留白）/ 加入原因 / 标签 / 微信 / 互动次数 / 添加时间 / 最近时间 / 操作；编辑弹窗只改 标签 + 微信 + 备注；顶部**诚实口径 Alert**（只记通知里可直接取到的人；无历史回填；添加时间=云端首次扫到时间）。

**口径（用户已确认）**：① 记录范围 = 评论 + @ + 点赞 + 收藏 + 关注，**全部来自通知页可直接取到的人**，一次性做全；② 身份标识 = **抽主页ID作稳定身份**（取不到退回昵称）。

## Capabilities

### New Capabilities
- `notification-contact-registry`: 通知发送者的诚实捕获（含主页ID稳定身份）→ 按账号事件流水落库（幂等 + 留存）→ 人工字段侧表 → 面板只读查询 + 人工编辑 → console 按账号联系人页。

### Modified Capabilities
<!-- 无既有已合并 spec 被改：点赞/关注的边缘抽取行为归入本新 capability。`notification-monitoring` 尚未合并（仍在活跃 change `notification-monitor` 内），故不在此 MODIFY，仅在 Impact 注明协调。 -->

## Impact

- **edge（aidcp-edge）**：`src/browse/notification-monitor.ts`（`fromUserId` 解析 + 赞/关注两栏抽取器，真机校准）、`src/browse/browse-session.ts`（`viewNotificationCategory` 升级为抽取+上报、保清零）、`src/comm/protocol.ts`（`NotificationItem` 扩 kind + `fromUserId?`，与云端逐字一致）。
- **cloud（aidcp-cloud）**：`src/comm/protocol.ts`（同上，逐字一致）；`migrations/0016_notification_contacts.sql`（新，两表，幂等）+ 同源内嵌 DDL；`src/cache/notification-contact-store.ts`（新，自带池 + 自建表 + appendEvents/listContacts/setManual + 按 kind 去重键 + 留存上限）；`src/orchestrator/role-dispatcher.ts` 或 `src/server.ts`（订阅 `notification.items.arrived` 记录，**APPEND**，按连接 accountId）；`src/panel/panel-server.ts` / `panel-store.ts` / `types.ts`（读/写端点 + DTO，**APPEND**）。
- **console（aidcp-console）**：`src/pages/NotificationContactsPage.tsx`（新）、`src/App.tsx`（路由）、`src/pages/AppShell.tsx`（导航 APPEND）、`src/api/queries.ts`（hook APPEND）、`src/types/api.ts`（DTO APPEND）。
- **docs**：`docs/protocol.md`（NotificationItem + 点赞/关注报 items）。
- **不涉及**：风控状态单写（本变更不碰 RiskController / risk_* 表）、发布链、isales。
- **并发协调（多流并行，关键）**：
  - **迁移号 0016**（现盘最高 0015_session_config；0009–0015 已被各流占；本流取 0016，动前 `ls ../aidcp-cloud/migrations/` 复核）。
  - **协议四处归属冲突**：活跃 change `account-real-nickname` 声明**独占协议四处**（`protocol.ts`/`command-bridge.ts`/`docs/protocol.md`/`edge-client.ts` onMessage）。本变更也需改 `protocol.ts`（NotificationItem）+ `docs/protocol.md`。两者均早期，**实装前须与 `account-real-nickname` 排序**（建议其一先落、另一 rebase），避免协议文件互踩。
  - **巡视行为协调**：点赞/关注抽取须与活跃的 `notification-monitor`（巡视编排）、`notification-clear-to-zero`（已部分部署，清零语义）协调 —— 抽取是清零过程中的旁路只读输出，**绝不改变「分诊到三栏未读全 0」的清零结果**。
  - 共享 chokepoint（`panel-store.ts` / `panel/types.ts` / `server.ts` / console `queries.ts` / `types/api.ts` / `App.tsx` / `AppShell.tsx`）**只 APPEND**；同机多会话部署错峰、精确 per-path staging（见 [[precise-git-add-concurrent-sessions]] / [[deploy-verify-content-after-rsync]]）。
- **红线 / 保留**：边轻云重（边缘只抽取上报、零决策零持久化）；绝不静默假成功（缺昵称如实留空、点赞/关注当前不可得部分由 UI 明示、互动次数读时 `COUNT` 实算不存计数列、同人不同评论绝不撞键丢失）；按账号隔离（主键账号在先、读写强制账号、写端点 accountId 取自 path）；记账绝不阻塞/拖垮巡视；第三方 PII 有留存上限。
