## Why

后台「发布历史」当前把所有账号混在一起看不出区分，且只能看到标题/状态/回执/时间——看不到真正发出去的正文，也没有任何能点开真实笔记的入口。更深的问题是：发帖这条链路根本没带账号——发帖记录的 `account_id` 列虽在（迁移 0005），但落库语句从不写它、触发恒为 `default`、命令向所有边缘广播，所以「按账号看历史」在数据层就是空话。本变更把发帖做成真正的按账号闭环，并让后台能查看正文与一个可点开的小红书详情页链接。

## What Changes

- **发帖全链路带真实账号**：触发时指定目标账号 → 按该账号解析人设 → 以该账号落 `publish_log.account_id` → 发布命令**定向**下发到绑定该账号的在线边缘节点（不再广播）。目标账号无在线节点时**诚实失败**，绝不广播、绝不假成功。
- **发布成功时捕获可用的详情页链接**：边缘在发帖成功后额外抓取带 `xsec_token` 的完整笔记分享 URL 并回报；云端新增列持久化。抓不到则存空、后台显示「无链接」，**绝不**用裸 id 拼一个打不开的假链接糊弄。
- **面板接口暴露按账号 + 正文 + 详情链接**：`GET /api/content/published` 的返回增 `accountId` / `content` / `postUrl`，并新增可选 `?accountId` 过滤（镜像 `/api/monitor/interactions` 已有写法）。
- **后台展示**：发布历史加「账号」列 + 按账号筛选；加「查看」入口展示完整正文与「打开小红书详情页」链接按钮（链接为空则禁用并标注，不给坏链）。
- 数据库 additive 迁移 `0014_publish_post_url.sql`：`publish_log` 增 `post_url TEXT`（`account_id` 列已存在，本变更只是开始真正写入它）。

## Capabilities

### New Capabilities
- `publish-account-attribution`: 发帖触发→人设解析→记录落库→命令下发全链路携带并固化**真实账号**；下发定向到绑定该账号的在线边缘节点，目标账号无在线节点时诚实失败。
- `publish-post-link-capture`: 发布成功时捕获并持久化一个**可用的**小红书笔记详情页链接（带 `xsec_token` 的完整分享 URL）；不可得时诚实置空、绝不伪造打不开的链接。

### Modified Capabilities
- `console-panel-api`: 已发布历史只读接口 `GET /api/content/published` 增 `accountId` / `content` / `postUrl` 字段与可选 `?accountId` 过滤；其「归因待补时不冒充按账号数字」的前提随发帖真实带账号而落地为真实按账号切片。

## Impact

- **aidcp-cloud**：迁移 `0014_publish_post_url.sql`；`PublishRecord` / `publish-log-store.ts`（insert 写 `account_id`+`post_url`，新增/扩展按 id 回写 `post_url`）；触发链路穿 `accountId`（`feishu/commands.ts` `/publish [accountId]`、`publish-scheduler.ts` `triggerManual`、`server.ts` 触发动作、`resolveSoul/getSoul(accountId)`、`TriggerInput`、`publish-executor.ts`）；定向路由（`comm/ws-server.ts` 增 account→edgeId 解析、`command-sequencer.ts`/`publish-executor.ts` 定向 `pushToEdges(env, edgeId)`）；面板层 `panel-server.ts`（`?accountId` 过滤）+ `panel-store.ts`（`publishedHistory` 的 SELECT 与 `PanelPublish` 增列、可 join `accounts` 取展示名）。
- **aidcp-edge**：发帖成功路径（`flows/publish-post.ts` 等）额外抓取带 token 的完整分享 URL 并随结果回报；若涉及回执字段新增，按 CLAUDE.md §2「协议 v2 四处同步」核对两份 `protocol.ts` + `command-bridge` + `docs/protocol.md`。
- **aidcp-console**：`ContentPage.tsx` 加账号列 + 账号筛选（复用 `useAccounts`）+ 查看正文/详情链接的抽屉或弹窗；`types/api.ts` 的 `PanelPublish` 增 `accountId`/`content`/`postUrl`。
- **依赖与并行**：定向发帖仅依赖**已存在**的 hello 期 `EdgeSession.accountId` 绑定，**不**依赖 `multi-account-node-support`（多租户浏览内核，在途）的每租户上下文，可相对独立推进；与其软共享连接注册表。预留迁移号 `0014` 避免与并发会话撞号。
- **安全红线**：沿用 MUST NOT 静默假成功——无在线节点 / 抓不到链接均诚实失败或显式置空，绝不派生假值（与 `publish-submit-integrity`、`edge-no-strategy-honest-failure` 一致）。
