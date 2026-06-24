## Context

发帖链路今天是**单账号 + 广播**：

- 触发恒为 `default`——飞书 `/publish` 写死 `DEFAULT_ACCOUNT_ID`（`feishu/commands.ts:78-79`），`publishScheduler` 是全局单例（`server.ts:471`），`resolveSoul()` 不带账号（`publish-scheduler.ts:88-92`，回落 `default`）。
- 命令广播——`command-sequencer.ts:247` 与 `publish-executor.ts:219` 的 `pushToEdges(env)` 不传 `edgeId`，发给所有在线边缘。
- 账号列在、从不写——`publish_log.account_id` 存在（迁移 0005，默认 `default`），但 `publish-log-store.ts:insert()` 的 INSERT 根本没这列。
- 历史展示薄——`GET /api/content/published`（`panel-server.ts:153-155`）只回 `{id,title,status,platformPostId,publishedAt}`，无账号、无正文、无链接、无过滤；正文 `content` 其实全文存着（`publish_log.content`，TEXT）。
- 详情链接现取不到——边缘发帖成功只抓**裸 note id**（`flows/publish-post.ts:138-156`），存进 `platform_post_id`；现代小红书 explore 链接需 `xsec_token` 动态参，裸 id 拼的 URL 不一定打得开。

关键发现：**按账号定向下发的底座已经在**——每条边缘连接 hello 时已把账号绑到 `EdgeSession.accountId`（`comm/handler.ts:274-280`、`ws-server.ts:23-40`），`pushToEdges(env, edgeId?)` 已支持按 `edgeId` 定向（`ws-server.ts:154-168`）；缺的只是 account→edgeId 解析 + 把 `accountId` 穿过触发链路。人设也已能按账号取（`account-persona-config` 已部署，`getSoul(accountId)` 可用）。

## Goals / Non-Goals

**Goals:**
- 发帖记录承载并固化**真实账号**：触发选账号 → 人设按账号解析 → `publish_log.account_id` 落真实值 → 发布命令定向到该账号的在线边缘节点。
- 目标账号无在线节点 / 链接抓不到时**诚实失败或诚实置空**，绝不广播、绝不伪造打不开的链接。
- 后台「发布历史」可按账号筛选、看完整正文、点开一个可用的小红书详情页链接。

**Non-Goals:**
- 不做 console 端「按账号发帖」按钮（本期触发仍走飞书 `/publish [accountId]`，console 触发留 follow-up）。
- 不实现「目标账号当前离线 → 排队等节点上线再发」的离线队列（无节点即诚实失败）。
- 不做同账号多节点（N:1）的下发去重/选节点策略——那是 `multi-account-node-support` Change B 的职责；本期对同账号多连接只取确定性的单一目标并记日志。
- 不渲染图片（用户已定：改成详情页链接）。
- 不重建多租户浏览内核——只用已存在的连接级账号绑定。

## Decisions

### D1：定向下发复用已存在的 hello 期账号绑定，不依赖多租户内核
新增一个 account→edgeId 解析（扫 `EdgeCloudServer.edges`，匹配 `session.accountId`），把解析出的 `edgeId` 一路传到 `pushToEdges(env, edgeId)`。
- **为什么**：绑定与定向 `push` 的原语都已存在，发帖定向不需要 `multi-account-node-support` 的每租户浏览上下文，可独立交付、软共享连接注册表。
- **诚实失败**：解析不到在线节点 → 不发、判 `failed`、带明确原因（`no_edge_for_account`），MUST NOT 退回广播。
- **同账号多连接（N:1）**：若多条连接同 `accountId`，本期取确定性单目标（如最早连接）并记日志；完整 N:1 协调留给 Change B。

### D2：触发携带账号，默认 `default` 保持向后兼容
飞书 `/publish [accountId]` 省略即 `default`；`accountId` 经 `triggerManual(accountId?)` → `resolveSoul(accountId)`/`getSoul(accountId)` → `TriggerInput.accountId` → `PublishExecutor` → `insert({account_id})` → 定向 `push`。
- **为什么**：单参最小改动即可端到端带账号；现役单账号路径零回归（不传账号 = 老行为）。
- **备选**：console 触发按钮——更顺手但牵涉 console 写操作鉴权与 UI，留 follow-up，避免本期膨胀。

### D3：详情页链接由边缘在成功时抓「带 token 的完整分享 URL」，诚实置空兜底
边缘发帖成功后，除裸 id 外额外尝试抓取带 `xsec_token` 的完整笔记分享 URL（如从分享面板/页面 DOM），随发布结果回报；云端新增 `publish_log.post_url` 持久化。
- **为什么**：裸 id 拼的 explore 链接缺 `xsec_token` 不一定能打开；要「可点开」必须抓真实分享 URL。
- **诚实置空**：抓不到则 `post_url` 存 NULL、后台显示「无链接」，MUST NOT 用裸 id 拼一个假链接（红线：不派生假值）。
- **协议**：回执里加一个可空 URL 字段属协议字段新增——按 CLAUDE.md §2 核对两份 `protocol.ts` + `command-bridge` + `docs/protocol.md` 是否需要同步（优先复用现有 publish 结果回执通道，避免新增消息类型）。

### D4：在既有 `/api/content/published` 上扩展，不另起详情接口
返回增 `accountId` / `content` / `postUrl`；新增可选 `?accountId` 过滤，写法镜像 `/api/monitor/interactions`（`panel-server.ts:172-180`）。
- **为什么**：历史只取最近 50 条、`content` 是有界 TEXT，随列表带回正文成本可忽略；少一个端点、少一次往返、与现有只读聚合约束（走索引、不全表扫）一致。`account_id` 已有索引（迁移 0005）支撑过滤。
- **展示名**：`publishedHistory` 可 `LEFT JOIN accounts` 取 `nickname ?? label ?? account_id`，让后台显示真实昵称而非裸 id。

### D5：后台展示 = 账号列 + 账号筛选 + 查看抽屉
`ContentPage` 加「账号」列与账号筛选（复用 `useAccounts`/账号选择器）；加「查看」入口（抽屉/弹窗）展示完整正文 + 「打开小红书详情页」链接按钮（`postUrl` 为空则禁用并标「无链接」，不给坏链）。

### D6：迁移 additive、单列
`0014_publish_post_url.sql` 仅 `ALTER TABLE publish_log ADD COLUMN IF NOT EXISTS post_url TEXT`（`account_id` 列已存在，本期只是开始写它）。预留 `0014`（0012 被 `account-real-nickname` 预留、0013 已用）。

## Risks / Trade-offs

- **分享 URL 本身可能有时效/会话性** → 缓解：发帖成功当下抓取并固化即为「最佳可得」；对该账号登录态下通常可打开；抓不到诚实置空。本期不做服务端代理/重托管（用户已确认不渲染图、只给链接）。
- **目标账号发帖时不在线** → 缓解：诚实 `failed`（`no_edge_for_account`），不广播、不假成功；离线排队明确划为 Non-Goal。
- **同账号多连接歧义** → 缓解：本期确定性单目标 + 日志；完整 N:1 留 Change B，proposal/Non-Goals 已点明。
- **历史旧行仍为 `default`** → 影响可接受：additive 回填即此意；新行起携带真实账号，按账号筛选对新数据生效；后台对「全部账号」视图无回归。
- **与 `multi-account-node-support` 软耦合** → 缓解：只用已存在的连接级绑定与定向 push 原语，account→edgeId 解析保持极薄、不复制其内核；若该内核后续提供统一路由再收敛到一处。
- **协议字段新增遗漏同步** → 缓解：优先复用现有 publish 结果回执通道；如确需新字段，按四处同步清单核对，`npm run typecheck` 兜前三处漂移。

## Migration Plan

1. cloud：跑迁移 `0014`（additive，可重入 `IF NOT EXISTS`）；改 store/触发/路由/面板层；`npm run test:acceptance` → 全量 `npm test` → `npm run typecheck`（安全红线 `AC-PUB-*`/`AC-PROTO-*` 必过）。
2. edge：加分享 URL 抓取 + 回报；`npm run typecheck` + 测试；若动协议则核对四处同步。
3. console：加列/筛选/抽屉 + 类型；build。
4. 部署按 §5 安全序列（先备份 → rsync → restart → healthcheck → 失败回滚）。**回滚低风险**：`post_url` 可空、`?accountId` 可选、不传账号即老行为，新码可平滑回退。

## Open Questions

- console 端「按账号发帖」触发按钮是否本期就做？默认**否**（飞书 `/publish [accountId]` 先行，console 触发留 follow-up）。
- 边缘能否稳定抓到带 `xsec_token` 的完整分享 URL？若实测多数抓不到，是否接受「多数无链接」并把抓取健壮性作为后续硬化项？（红线不变：抓不到诚实置空，不伪造。）
