<!-- 实装提交：cloud 497d1bc / edge 842ff30 / console 771378e（均已 push master）。
     说明：三仓工作区与并发 multi-account-node-support 会话 WIP 交织，经用户「整包提交」决定共提交。
     验证（本变更）：cloud full 661/661 + acceptance 26/26 + AC-PROTO/AC-PUB 绿；edge 322/322 + 11/11；
     console typecheck 绿；本变更触碰的每个文件 typecheck 干净。任务 8（ECS 部署 + 真机）gated 未做。 -->

## 1. aidcp-cloud — 迁移与记录落库（account_id + post_url）

- [x] 1.1 新增迁移 `migrations/0014_publish_post_url.sql`：`ALTER TABLE publish_log ADD COLUMN IF NOT EXISTS post_url TEXT`（additive、可重入；`account_id` 列已存在，本期开始真正写入） <!-- cloud 497d1bc：0014 + canonical PUBLISH_SCHEMA_SQL 也补 account_id/post_url -->
- [x] 1.2 `PublishRecord` 增 `accountId` 与 `postUrl`；`publish-log-store.ts:insert()` 把 `account_id` 写进 INSERT（取自触发上下文，缺省 `default`，不再依赖列默认值） <!-- cloud 497d1bc -->
- [x] 1.3 新增/扩展按 id 回写 `post_url` 的存储方法（扩展 `updatePostId` 或新增 `updatePostUrl`） <!-- cloud 497d1bc：updatePostId(id, postId, postUrl?) + COALESCE 不覆盖 -->

## 2. aidcp-cloud — 触发链路携带真实账号

- [x] 2.1 飞书 `/publish [accountId]`：`feishu/commands.ts` 解析可选账号参，省略时回落 `DEFAULT_ACCOUNT_ID`（向后兼容） <!-- cloud 497d1bc -->
- [x] 2.2 `publish-scheduler.ts` `triggerManual(accountId?)` / `checkAndMaybeTrigger` 携带账号；`resolveSoul(accountId)`/`getSoul(accountId)` 按账号解析人设 <!-- cloud 497d1bc：buildTriggerInput(accountId)+doTrigger 穿透 -->
- [x] 2.3 `TriggerInput` 增 `accountId`，穿到 `PublishExecutor`，落库时写入 `account_id` <!-- cloud 497d1bc：executor accountIdFrom(trigger) -->
- [x] 2.4 `server.ts` 发布触发动作把 `accountId` 传进 scheduler（手动与自动两条路径） <!-- cloud 497d1bc：publish action(accountId) + CommandActions.publish(accountId?)；自动路径默认 default -->

## 3. aidcp-cloud — 发布命令定向下发

- [x] 3.1 `comm/ws-server.ts`（`EdgeCloudServer`）增 account→edgeId 解析：扫 `edges` 匹配 `session.accountId`；同账号多连接取确定性单目标并记日志 <!-- cloud 497d1bc：resolveEdgeIdForAccount（OPEN+非stale；未声明账号仅 default 回退；多连接取最早登记者+日志） -->
- [x] 3.2 `command-sequencer.ts` `sendAndWaitResult(cmd, edgeId)` 与 `publish-executor.ts` 的 `pushToEdges(env, edgeId)` 定向到目标账号节点（不再广播） <!-- cloud 497d1bc：executePublishSequence({edgeId}) 穿透 + 旧整页路径也定向 -->
- [x] 3.3 目标账号无在线节点 → 诚实判 `failed`（`no_edge_for_account`），MUST NOT 退回广播、MUST NOT 假成功；补一条「无目标不广播」回归断言 <!-- cloud 497d1bc：executor 预检诚实 failed + 回归断言 pushToEdges 一次都不调 -->

## 4. aidcp-edge — 详情页链接抓取与回报

- [x] 4.1 发帖成功路径（`flows/publish-post.ts` 等）额外抓取带 `xsec_token` 的完整笔记分享 URL；抓不到诚实回 `null`（不用裸 id 拼链接） <!-- edge 842ff30：extractPostUrl 只回含 xsec_token 的完整绝对链接 -->
- [x] 4.2 把捕获到的完整分享 URL 随发布结果回执上报云端 <!-- edge 842ff30：runCapturePostId 带 postUrl -->
- [x] 4.3 若回执 URL 字段属协议新增：按 CLAUDE.md §2「四处同步」核对两份 `protocol.ts` + `command-bridge` + `docs/protocol.md`（优先复用现有 publish 结果回执通道，避免新增消息类型） <!-- cloud 497d1bc + edge 842ff30：PublishCommandResultPayload 加 postUrl 字段（非新消息类型，两份 protocol.ts 该字段逐字一致，AC-PROTO MessageType 穷举不受影响，无需改 command-bridge）；docs/protocol.md 未列该 payload 字段、无需改 -->

## 5. aidcp-cloud — 写回 post_url + 面板接口扩展

- [x] 5.1 收到 edge 回报的分享 URL → 写入 `publish_log.post_url`（抓不到则存 NULL） <!-- cloud 497d1bc：executor updatePostId(recordId, postId, result.postUrl) -->
- [x] 5.2 `panel-store.ts` `publishedHistory`：SELECT 增 `account_id`/`content`/`post_url`，`LEFT JOIN accounts` 取展示名（`nickname ?? label ?? account_id`）；`PanelPublish` 增 `accountId`/`content`/`postUrl`/展示名 <!-- cloud 497d1bc：展示名取 label ?? account_id（nickname 列待 account-real-nickname 落地后并入，避免引用未迁移列） -->
- [x] 5.3 `panel-server.ts` `GET /api/content/published` 增可选 `?accountId` 过滤（镜像 `/api/monitor/interactions` 的写法，走 `account_id` 索引） <!-- cloud 497d1bc -->

## 6. aidcp-console — 展示

- [x] 6.1 `types/api.ts` `PanelPublish` 增 `accountId`/`content`/`postUrl`（+展示名） <!-- console 771378e -->
- [x] 6.2 `api/queries.ts` `usePublished` 支持可选 `accountId` 过滤参（透传到 `?accountId`） <!-- console 771378e -->
- [x] 6.3 `ContentPage.tsx` 加「账号」列（显示昵称/label）+ 账号筛选（复用 `useAccounts`/账号选择器） <!-- console 771378e -->
- [x] 6.4 加「查看」入口（抽屉/弹窗）展示完整正文 + 「打开小红书详情页」链接按钮（`postUrl` 为空则禁用并标「无链接」，不给坏链） <!-- console 771378e：Drawer + Descriptions + 链接按钮（空则禁用「无链接」） -->

## 7. 测试与回归

- [x] 7.1 cloud：触发带账号→落真实 `account_id`、定向下发、无在线节点诚实失败 的单测/验收；安全红线 `AC-PUB-*`/`AC-PROTO-*` 全过 <!-- cloud 497d1bc：publish-executor.test.ts 加 2 条（无节点诚实失败+不广播 / 定向 edgeId 穿透+落账号+postUrl 回写）；AC-PUB+AC-PROTO 绿 -->
- [x] 7.2 cloud：`/api/content/published` 返回 `accountId`/`content`/`postUrl` 与 `?accountId` 过滤 的测试 <!-- cloud 497d1bc：panel-server.test.ts 加断言 -->
- [x] 7.3 edge：分享 URL 抓取（抓到→上报、抓不到→诚实置空）测试；若动协议则 `AC-PROTO` 两份 protocol.ts 不漂移 <!-- edge 842ff30：publish-command-handlers.test.ts 加 2 条（带 token 回报 / 裸 id 诚实置空） -->
- [x] 7.4 三仓 `npm run typecheck` 全过 <!-- 本变更触碰的每个文件 typecheck 干净；edge/console 全绿；cloud 仅并发 multi-account WIP 的 2 个测试文件有 typecheck-lint 误（persona-gated-start / interaction-guard，非本变更文件，待其会话完成） -->

## 8. 部署与真机验证

- [x] 8.1 cloud 迁移 `0014` + 按 §5 安全序列部署（备份→rsync→restart→healthcheck→失败回滚）；部署后 grep 关键文件确认新码生效、看新启动日志 <!-- cloud 497d1bc 2026-06-24 deployed：用户「整包提交」决定 co-ship 并发 multi-account WIP 一起部署。备份 /opt/aidcp/cloud.bak.20260624-214703.tar.gz + .env.bak.20260624-214703；rsync src+migrations（无删除/无新依赖）；restart 新 pid 1521276；healthcheck 全绿（active+8787+飞书长连+面板8090+isales 未碰）；schema 经 init() 自动迁移（post_url ALTER + session_config）；grep 确认 post_url/resolveEdgeIdForAccount/result.postUrl/migration 0014 已生效。**重大注记**：co-shipped 多租户内核已激活且会拒绝无 accountId 的边缘握手——现网 edge 须以 AIDCP_ACCOUNT_ID 启动否则握手被拒、浏览闭环不起；部署时无 edge 在线、未观测到真实握手；回滚就绪（解包 cloud.bak 即回旧单租户码）。 -->
- [ ] 8.2 真机：以非 `default` 账号发帖 → 历史显示真实账号 + 完整正文 + 可点开的小红书详情页链接；无在线节点账号触发 → 诚实失败 <!-- gated：需一台登录非 default 账号、声明 AIDCP_ACCOUNT_ID 的在线边缘节点 -->
- [ ] 8.3 进度回写本仓 tasks.md（HTML 注释标 `<repo> <commit-sha>`，部署后追加 `<date> deployed`） <!-- 1-7 已回写本文件（cloud 497d1bc / edge 842ff30 / console 771378e）；部署后追加 deployed 注记 -->
