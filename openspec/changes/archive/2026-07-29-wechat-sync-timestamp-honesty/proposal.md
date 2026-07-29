## Why

视频号互动 workspace 当前把 customer API 的 `meta.asOf`（本次 HTTP 快照/分页边界）显示为“数据时间”，并仅凭该字段存在就宣称“评论/私信同步正常”。因此即使 Edge 从未成功同步、同步已经停滞，或用户点击“局部刷新”后 Cloud 只受理了请求，客户端也会把一次成功读 API 冒充成平台数据刚刚同步。

Cloud 已持久化每个成功同步批次的 Edge `observed_at` 与 Cloud `received_at`，应把这份真实证据投影给客户界面，并明确区分页面读取、请求受理和同步成功。

## What Changes

- customer-auth 的互动 list/detail 回包新增按 `comment`、`dm` 分渠道的只读同步新鲜度投影；每个渠道只有在成功持久化过批次时才返回该批次的 `observedAt` 与 `receivedAt`，否则明确为 `null`。
- `meta.asOf` 保留为 API 快照和分页一致性字段，但不再被客户端解释或展示为互动数据时间，也不得用来推断同步健康。
- Electron InteractionWorkspace 使用真实分渠道同步证据展示“尚未成功同步”或最近数据观察时间；读取能力、空列表和 HTTP 2xx 均不能单独触发“同步正常”。
- 用户发起局部刷新后先显示“请求已受理/等待结果”；只有后续读回的成功同步证据推进，才能显示本次同步已有新成功结果。
- 补齐 contract fixtures/schema、Cloud API/store 测试和 Edge renderer 测试，覆盖从未同步、历史同步停滞、空批次成功、请求受理未完成及分渠道时间不同的情况。

## Capabilities

### New Capabilities

- `wechat-sync-timestamp-honesty`: 定义视频号互动成功同步时间的权威来源、customer-auth 投影，以及客户端不得以 HTTP 快照或请求受理冒充同步成功的展示规则。

### Modified Capabilities

<!-- None. The parent interaction-management change is not archived yet, so this follow-up is kept as an additive capability instead of a delta against a non-baseline spec. -->

## Impact

- Control contract: `docs/contracts/wechat-channels-interaction/v1` 的 customer API schema/fixtures，以及本 change 的新 capability spec。
- Cloud: `InteractionStore` 的同步证据读取、`InteractionCustomerApi` list/detail 投影与聚焦测试；不改变 WS v2 payload、Edge command routing 或风险状态写入边界。
- Edge: `interaction-workspace.js` 的状态模型、空态/状态文案和 renderer 测试；不改变凭证、任意 fetch、发送门禁或浏览器生命周期语义。
- 数据库：优先复用 `interaction_sync_batches(observed_at, received_at)`；若查询计划需要索引，只允许 additive migration，不重写或删除既有同步数据。
