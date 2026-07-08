<!-- 进度按 sub-repo 分节回写；代码落 aidcp-cloud (25f765d) / aidcp-console (b3970cc)，2026-07-09 部署 dev 并验证。 -->

> **实装偏差与决策（务必先读）**
> - **出站路由范围收窄**：读代码后判定——只有 `notifyComments`（账号入站「评论 / @」通知 = 各团队要收的"消息"）按账号路由；**审批卡 / 运维告警（persona / captcha / config-error）/ 排期回执 / 命令结果卡刻意保留默认（管理）群**。理由：外部客户群按对外共享模型是客户所在群，不应让客户点审批卡、也不应看到内部运维/编排告警。resolver/store/panel/入站闸机制全建齐，将来若要更多站点按账号路由，扩展调用点即可。spec R4 已据此改写。
> - **管理群 = env 白名单**：`FEISHU_MANAGEMENT_CHAT_IDS`（逗号分隔），**不复用 `is_default`、不由 `/bind` 授予**。白名单为空 → 放行全部（零回归 ramp）。比"面板独立标志 + is_default"更简、无耦合、显式 opt-in。
> - **入站闸做在命令入口**（`CommandRouter.handle` 解析后、派发前），对所有非 help 命令统一生效——比"逐 action 改 `CommandActions` 接口 + 逐处穿 chatId"更简且无绕过缝。显式 accountId / 单账号短路天然被入口闸覆盖。spec CR3 已据此改写。
> - **命令结果卡未改**：同步结果卡今天已回源群（ws-receiver），未新增 async 卡的 sourceChatId 穿线（保持既有目标，且绝不按账号路由 = 满足红线）。

## 1. aidcp-cloud — 存储与解析基座

- [x] 1.1 新建 `src/cache/group-route-store.ts` + 表 `group_route`（`init()` 自建 CREATE TABLE IF NOT EXISTS；单写者 upsert/清除/读回真态；`getRoute` 精确相等、42P01 回落 null；`listRoutes`）。 <!-- aidcp-cloud 25f765d -->
- [x] 1.2 接入 `src/server.ts` 启动 init 链（仿 notification-contact-store：init 失败退化留 undefined + 日志，不崩启动）。 <!-- aidcp-cloud 25f765d；dev 已验证 group_route 表随启动自建 -->
- [x] 1.3 `src/account-store.ts` 新增 `getGroupLabel(accountId)` 纯读（异步直读 PG，读异常上抛由解析器兜底）。 <!-- aidcp-cloud 25f765d -->
- [x] 1.4 `src/feishu/chat-target.ts` 新增 `resolveChatIdForAccount(accountId?, deps)`：叠在不动的 `resolveDefaultChatId` 上；每层读各自 try/catch 向下穿透、绝不外抛；config-gap 日志。 <!-- aidcp-cloud 25f765d -->

## 2. aidcp-cloud — 出站按账号路由

- [x] 2.1 `notifyComments`（`src/server.ts`）换用 `resolveChatIdForAccount(ctx.accountId)`（核心投递点）。 <!-- aidcp-cloud 25f765d -->
- [x] 2.2 **刻意不改**：评论审批卡 / persona / captcha / 排期回执 / config-error / 参照创作 等**面向运营方**发送点保留默认（管理）群（见顶部偏差说明）。captcha-coordinator / handler.ts 均未改。 <!-- 决策：非账号入站消息不按账号路由 -->

## 3. aidcp-cloud — 命令回执 / 审批走源群

- [x] 3.1 **保持现状**：同步命令结果卡已回源群（`ws-receiver.ts`）；未新增 async 卡穿线（既有目标不变，且不按账号路由 = 满足"命令卡不走账号映射"红线）。 <!-- 决策：见顶部偏差说明 -->
- [x] 3.2 `resolveApprovalCardTarget`（publish-executor）保持 `manualApprovalChatId → 默认群`、不插账号层（本 change 未触碰）。 <!-- 无改动，语义符合 spec -->

## 4. aidcp-cloud — 入站作用域安全闸

- [x] 4.1 管理群 = env `FEISHU_MANAGEMENT_CHAT_IDS` 白名单（不复用 is_default）；`isCommandChatAuthorized` 注入 `CommandRouter`（白名单空 → 放行全部，零回归，启动日志说明）。 <!-- aidcp-cloud 25f765d；dev 启动日志确认"作用域未启用→放行全部" -->
- [x] 4.2 `CommandRouter.handle` 入口闸：非 help 命令来自非白名单群 → 诚实拒（黄卡「本群无权下达账号命令」），MUST NOT 执行。 <!-- aidcp-cloud 25f765d -->
- [x] 4.3 `/bind` 越权：`/bind` 归入受闸命令，白名单启用后非管理群不可自助提权；管理权来自 env 白名单、非 is_default。 <!-- aidcp-cloud 25f765d -->
- [x] 4.4 显式 accountId / 单账号短路由**入口闸统一覆盖**（先判权限后解析账号），无绕过缝——比逐 action 改接口更简。 <!-- aidcp-cloud 25f765d -->

## 5. aidcp-cloud — 面板路由

- [x] 5.1 `bot-chat-store` 加 `listActive()` 只读（列活跃所在群，无 DDL，42P01 回落空）。 <!-- aidcp-cloud 25f765d -->
- [x] 5.2 `panel-server.ts` + `types.ts`：`GET/PUT /api/notification/routes`（写者 `notificationRoutes` 注入 PanelDeps；未注入 503；body 守卫；读回真态）+ `GET /api/bot-chats`（复用 botChatStore）。目标 opaque chat_id（非枚举）。 <!-- aidcp-cloud 25f765d；dev 三路由 401 已连线（非 404）-->

## 6. aidcp-console — 配置界面

- [x] 6.1 新增「通知路由」页 `/notification-routes`（`NotificationRoutesPage`）：team(group_label)→群映射表，目标从 `GET /api/bot-chats` 下拉、未知群显式列出可清除；读写 `/api/notification/routes`；无新枚举、opaque chat_id。注册进 `routes.tsx`（顶部导航「通知路由」）。 <!-- aidcp-console b3970cc；dev 已部署新 bundle -->

## 7. 测试

- [x] 7.1 `resolveChatIdForAccount` 单测：已绑定→团队群 / 未绑定 / 空表 / 读抛异常仍落默认（不外抛）/ config-gap 日志。 <!-- aidcp-cloud 25f765d test/feishu-notification-routing.test.ts -->
- [x] 7.2 `group-route-store` 单测：空键 invalid_key / 空 chat 清除 / upsert 读回 / 42P01 回落。 <!-- aidcp-cloud 25f765d 同上文件 -->
- [x] 7.3 入站作用域单测：非管理群账号命令拒 / 管理群执行 / help 放行 / 未注入零回归放行。 <!-- aidcp-cloud 25f765d 同上文件 -->
- [x] 7.4 面板路由单测：503 未注入 / PUT 校验 + 读回 / GET 列表 / bot-chats 列表。 <!-- aidcp-cloud 25f765d test/panel-notification-routes.test.ts -->
- [x] 7.5 全量绿：cloud test:acceptance(46) + test(1635) + typecheck；console test(18 files) + build + typecheck。 <!-- 25f765d / b3970cc -->

## 8. 文档与运营 runbook

- [x] 8.1 运营 runbook 要点写入 `design.md`（Migration Plan §3：对外共享认证 + 逐客户建外部群 / 拉人 / 加机器人 / 指定群主 / 面板绑定）。 <!-- design.md -->
- [x] 8.2 外部群 API 支持清单核对项写入 design 备注（`im/v1/messages` text+card+reaction；机器人不可当群主；外部成员仅 open_id）。 <!-- design.md Risks 段 -->
- [x] 8.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md` 簇 20（真外部群收发 / 错映射防线 / 外部群命令拒绝 / 对外共享认证前置 / 零回归）。 <!-- 簇 20 -->


## 9. 部署与验收

- [x] 9.1 dev 部署（探 ECS 无并发在写 → 干净 git archive 快照 → 备份 cloud.bak+.env.bak → rsync 排除 .env/node_modules/.git → restart → healthcheck；console 干净 worktree build → 备份 → rsync 无 --delete；未碰 isales）。 <!-- 2026-07-09 deployed dev：cloud 25f765d / console b3970cc -->
- [x] 9.2 部署后验证：service active + 8787 + PG select 1 + **group_route 表随 init 自建（列齐）** + 启动日志（GroupRouteStore 就绪 / 作用域未启用零回归 / 飞书长连接）+ 面板三路由 401 已连线 + console 新 bundle 上线。 <!-- 2026-07-09 dev 全绿 -->
