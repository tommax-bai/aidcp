## 1. aidcp-cloud — 迁移与记录落库（account_id + post_url）

- [ ] 1.1 新增迁移 `migrations/0014_publish_post_url.sql`：`ALTER TABLE publish_log ADD COLUMN IF NOT EXISTS post_url TEXT`（additive、可重入；`account_id` 列已存在，本期开始真正写入）
- [ ] 1.2 `PublishRecord` 增 `accountId` 与 `postUrl`；`publish-log-store.ts:insert()` 把 `account_id` 写进 INSERT（取自触发上下文，缺省 `default`，不再依赖列默认值）
- [ ] 1.3 新增/扩展按 id 回写 `post_url` 的存储方法（扩展 `updatePostId` 或新增 `updatePostUrl`）

## 2. aidcp-cloud — 触发链路携带真实账号

- [ ] 2.1 飞书 `/publish [accountId]`：`feishu/commands.ts` 解析可选账号参，省略时回落 `DEFAULT_ACCOUNT_ID`（向后兼容）
- [ ] 2.2 `publish-scheduler.ts` `triggerManual(accountId?)` / `checkAndMaybeTrigger` 携带账号；`resolveSoul(accountId)`/`getSoul(accountId)` 按账号解析人设
- [ ] 2.3 `TriggerInput` 增 `accountId`，穿到 `PublishExecutor`，落库时写入 `account_id`
- [ ] 2.4 `server.ts` 发布触发动作把 `accountId` 传进 scheduler（手动与自动两条路径）

## 3. aidcp-cloud — 发布命令定向下发

- [ ] 3.1 `comm/ws-server.ts`（`EdgeCloudServer`）增 account→edgeId 解析：扫 `edges` 匹配 `session.accountId`；同账号多连接取确定性单目标并记日志
- [ ] 3.2 `command-sequencer.ts` `sendAndWaitResult(cmd, edgeId)` 与 `publish-executor.ts` 的 `pushToEdges(env, edgeId)` 定向到目标账号节点（不再广播）
- [ ] 3.3 目标账号无在线节点 → 诚实判 `failed`（`no_edge_for_account`），MUST NOT 退回广播、MUST NOT 假成功；补一条「无目标不广播」回归断言

## 4. aidcp-edge — 详情页链接抓取与回报

- [ ] 4.1 发帖成功路径（`flows/publish-post.ts` 等）额外抓取带 `xsec_token` 的完整笔记分享 URL；抓不到诚实回 `null`（不用裸 id 拼链接）
- [ ] 4.2 把捕获到的完整分享 URL 随发布结果回执上报云端
- [ ] 4.3 若回执 URL 字段属协议新增：按 CLAUDE.md §2「四处同步」核对两份 `protocol.ts` + `command-bridge` + `docs/protocol.md`（优先复用现有 publish 结果回执通道，避免新增消息类型）

## 5. aidcp-cloud — 写回 post_url + 面板接口扩展

- [ ] 5.1 收到 edge 回报的分享 URL → 写入 `publish_log.post_url`（抓不到则存 NULL）
- [ ] 5.2 `panel-store.ts` `publishedHistory`：SELECT 增 `account_id`/`content`/`post_url`，`LEFT JOIN accounts` 取展示名（`nickname ?? label ?? account_id`）；`PanelPublish` 增 `accountId`/`content`/`postUrl`/展示名
- [ ] 5.3 `panel-server.ts` `GET /api/content/published` 增可选 `?accountId` 过滤（镜像 `/api/monitor/interactions` 的写法，走 `account_id` 索引）

## 6. aidcp-console — 展示

- [ ] 6.1 `types/api.ts` `PanelPublish` 增 `accountId`/`content`/`postUrl`（+展示名）
- [ ] 6.2 `api/queries.ts` `usePublished` 支持可选 `accountId` 过滤参（透传到 `?accountId`）
- [ ] 6.3 `ContentPage.tsx` 加「账号」列（显示昵称/label）+ 账号筛选（复用 `useAccounts`/账号选择器）
- [ ] 6.4 加「查看」入口（抽屉/弹窗）展示完整正文 + 「打开小红书详情页」链接按钮（`postUrl` 为空则禁用并标「无链接」，不给坏链）

## 7. 测试与回归

- [ ] 7.1 cloud：触发带账号→落真实 `account_id`、定向下发、无在线节点诚实失败 的单测/验收；安全红线 `AC-PUB-*`/`AC-PROTO-*` 全过
- [ ] 7.2 cloud：`/api/content/published` 返回 `accountId`/`content`/`postUrl` 与 `?accountId` 过滤 的测试
- [ ] 7.3 edge：分享 URL 抓取（抓到→上报、抓不到→诚实置空）测试；若动协议则 `AC-PROTO` 两份 protocol.ts 不漂移
- [ ] 7.4 三仓 `npm run typecheck` 全过

## 8. 部署与真机验证

- [ ] 8.1 cloud 迁移 `0014` + 按 §5 安全序列部署（备份→rsync→restart→healthcheck→失败回滚）；部署后 grep 关键文件确认新码生效、看新启动日志
- [ ] 8.2 真机：以非 `default` 账号发帖 → 历史显示真实账号 + 完整正文 + 可点开的小红书详情页链接；无在线节点账号触发 → 诚实失败
- [ ] 8.3 进度回写本仓 tasks.md（HTML 注释标 `<repo> <commit-sha>`，部署后追加 `<date> deployed`）
