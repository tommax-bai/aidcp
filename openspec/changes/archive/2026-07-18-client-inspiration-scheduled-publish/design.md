## Context

客户端当前依赖 `ui.snapshot.publishPreview` 获取某账号最新一条 `pending_approval` 草稿，并在 Electron `renderer.js` 中渲染单稿审核页。Cloud `PublishLogStore.pendingPublishPreviewForAccount` 固定 `ORDER BY id DESC LIMIT 1`，所以多稿并行生成后只有最新稿可达。客户端批准通过 `publish.approval_action` 携带 `requestId/approved/contentVersion`；Cloud 比对账号、状态与版本后写审批信号，但客户端不能在这个授权点编辑 `publish_metadata.mode/publishTime`。

灵感库已经有成熟的 customer-auth 账号绑定读边界、具名 IPC、卡片列表/详情和陈旧响应隔离。本变更复用这些交互模式承载多稿审核，但不会把内部 panel API 或账号选择权开放给 renderer。

## Goals / Non-Goals

**Goals:**

- 当前账号的所有待审稿在客户端可分页到达，多条时以卡片列表进入详情。
- 列表/详情读取按 `envKey → 持久账号绑定` 隔离，离线时仍可读；批准/取消仍要求目标 Edge 活会话。
- 批准时允许选择立即发布或合法的小红书定时发布，并使审批签名绑定计划修改后的真实内容版本。
- 单条处理成功后保留剩余待审队列与页面上下文。
- 旧 Cloud/旧 Edge 仍可沿用单稿 `ui.snapshot.publishPreview` 与不带计划的批准动作。

**Non-Goals:**

- 不在灵感参考创作入口提前设置发布时间。
- 不让客户编辑标题、正文、话题或配图以外的新字段；本变更只在批准时编辑发布模式与时间。
- 不为 Facebook/视频号开放平台内定时发布。
- 不绕过人工审批，不做批量一键批准，不新增数据库字段。
- 不在本变更中构建 Electron 安装包。

## Decisions

### 1. 多稿读取走 customer-auth 列表/详情，不把整队列塞进 ui.snapshot

新增只读端点：

```text
GET /publish-drafts?envKey=<profile>&limit=<1..50>&offset=<0..1000000>
GET /publish-drafts/:id?envKey=<profile>
```

两者先用客户 JWT 鉴权，再调用既有 `resolveBoundAccountForEnv` 得到唯一账号。Cloud 查询 `publish_log` 时把 `account_id` 与 `status='pending_approval'` 写进 SQL WHERE；详情以 `id + account_id + status` 查询，跨账号与不存在返回同形 404。列表返回一致 total 与分页 items；DTO 只含审核所需的标题、正文/摘要、话题、配图、版本、更新时间、来源类型、平台与发布计划，不含来源原稿快照、内部 provider 诊断、审批文件或其它账号信息。

Electron main 新增固定路径的 `publish-draft:list/get` 具名 IPC，renderer 只能传 limit/offset/id，`envKey/token/path` 继续由 main 注入。相比把数组加入 `ui.snapshot`，此方案有界分页、可按需取详情、支持刷新并避免每次状态心跳重复推送大正文/多图。现有单稿 snapshot 保留为旧 Cloud 或读接口失败时的可用回落。

### 2. 审核工作区采用“列表 → 详情”，单条自动进详情

打开“稿件审核”时先请求第一页（每页 12 条）。两条及以上渲染与灵感池一致的卡片网格：封面、标题、正文摘要、更新时间、立即/定时标签；点击进入详情。仅一条时直接显示详情，零条显示真实空态。详情返回列表保留页码与滚动位置；账号切换使请求 epoch 失效并清空所有旧稿状态。

批准/取消在途只锁当前详情。成功后从当前内存页移除该稿并重新读取权威列表；若仍有稿件回到列表/下一条，只有队列确实为空才显示空态。失败保留详情、选择与错误文案，绝不乐观染绿。

### 3. 发布计划属于批准动作，并通过同一稿件 CAS 后授权新版本

新 Edge 批准请求携带：

```ts
{
  requestId: `publish-${recordId}`;
  approved: true;
  contentVersion: number;
  publishMode: 'immediate' | 'scheduled';
  publishTime: number | null;
}
```

取消只携带既有字段，发布计划字段缺省。审核详情从 Cloud 草稿真态初始化选择；scheduled 以北京时间显示。新批准若选择 immediate 必须传 null；scheduled 必须传有限 epoch ms。

Cloud 闸序：解析 requestId → 校验活会话账号 → 读取稿件 → account/status/现有审批/客户端版本 → `validatePublishSchedule(draft.platform, mode, time, now)` → 发布 preflight → 如计划变化则调用既有 `PublishLogStore.editDraft(recordId, expectedVersion, {publishMode,publishTime}, 'client')` 并使用其事务写后真态 → 用真实 `contentVersion` 写审批信号 → 触发 dispatcher。预检必须位于计划 CAS 前，避免预检失败留下部分计划修改；CAS 冲突或时间非法时整体不授权；绝不先写批准再改稿。计划未变化时不无谓增版本。

旧 Edge 未带新字段时，Cloud 沿用稿件当前 `metadata.mode/publishTime` 并按既有动作批准；因此 Cloud 可先部署。新 Edge main 对枚举、null/有限数与 approved=false 不带计划做窄校验。

### 4. 不新增发布状态，列表可暂时本地排除刚处理稿

审批信号与 `publish_log.status` 现有设计分离，批准后 dispatcher 才推进状态。客户端收到批准/取消成功后将该 recordId 记入按环境分桶的进程内 `handled` 集合，并在权威列表刷新结果中暂时过滤，避免 dispatcher 极短延迟内让已处理稿闪回。Cloud 后续状态变化自然把它从 `pending_approval` 查询中移除；账号切换不会跨桶污染，应用重启后集合自然清空。

### 5. 协议只扩展审批动作，不扩展大快照

Cloud/Edge 两份 `PublishApprovalActionPayload` 同步增加可选 `publishMode/publishTime`，结果增量返回 `contentVersion` 供 UI 记录实际授权版本。`docs/protocol.md` 记录：新字段仅在 approved=true 使用，scheduled 必须满足权威策略；旧发送方缺字段沿用稿件真态。其它 protocol v2 类型和主动路由不变。

## Risks / Trade-offs

- [待审列表读接口与审批 RPC 走两条通道] → 读只需持久绑定，写仍由活 Edge 会话校验；所有写入以 Cloud 重新加载稿件为准，renderer 列表不是授权凭据。
- [批准后 DB 状态短暂仍为 pending] → 页面会话 handled 集合过滤刚处理稿，随后以 Cloud 状态自然收敛；不会把过滤当平台成功证据。
- [计划修改使内容版本增加] → Cloud 以 CAS 修改后重读，并把新版本写入同一审批信号；任何并发编辑使旧请求失败而不是批准错版。
- [定时时间在操作途中越过 1 小时下限] → Cloud 在批准动作内最后权威校验，失败保留详情供客户重新选择。
- [分页期间新增/处理稿导致页漂移] → 每次返回使用同一 WHERE 的 total，处理后回到第一页/当前可用页重新读取；不承诺快照隔离。
- [Cloud/Edge 分批升级] → Cloud 先支持新端点/可选字段；新 Edge 对端点不可用时回落单稿 snapshot，旧 Edge 审批沿用稿件当前计划。

## Migration Plan

1. 合并并部署 Cloud：新增只读端点，兼容旧审批 payload。
2. 合并 Edge：启用多稿列表与批准时计划控件；未发布新安装包前线上客户端无行为变化。
3. 不做数据库迁移。回滚 Edge 后继续使用单稿 snapshot；回滚 Cloud 前先回滚尚未发布的新 Edge 包。
4. Electron 安装包仍需用户显式要求后再构建/发布。

## Open Questions

- 无。多稿列表使用 12 条分页；批准位置默认回显稿件当前模式，定时范围沿用小红书 1 小时至 14 天权威策略。
