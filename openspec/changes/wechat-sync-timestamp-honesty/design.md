## Context

视频号互动链目前有三种不同时间：

1. Edge 完成一次平台读取时写入同步批次 `observedAt`；
2. Cloud 在事务内持久化批次时写入 `received_at`，并把该值放进 sync ack 的 `receivedAt`；
3. customer API 在每次 list/detail 请求时生成 `meta.asOf`，用作稳定分页快照边界。

Cloud 已在 `interaction_sync_batches` 保存前两种时间，但 customer API 没有投影它们。Electron 因而把第三种时间显示为“数据时间”，并用 `Boolean(meta.asOf)` 判断“同步正常”。该判断只证明 HTTP 读请求成功，不能证明 Edge 执行过平台读取或 Cloud 接收过同步批次。

另一个重要约束是 Edge 的 `stableBatchId` 故意排除 `requestId` 与 `observedAt`。新一轮读取若内容和游标完全不变，会生成与旧轮次相同的 batchId；Cloud 当前把它当普通重放并返回旧 `receivedAt`。因此只新增一个读查询仍不足以证明“空结果/无变化但刚刚同步成功”，还需要区分同一批次的网络重放与更新的真实观察时间。

本变更跨 control contract、Cloud customer API/store 和 Edge renderer；不改变 WS v2 字段、风险控制、发送状态机或账号凭证边界。

## Goals / Non-Goals

**Goals:**

- 以已提交的同步批次为唯一成功证据，同时保留“Edge 观察时间”和“Cloud 接收时间”两种语义。
- 让 comment 与 dm 各自拥有可空、env/account-scoped、单调不回退的新鲜度投影。
- 让内容未变化或空批次的真实新观察可以推进新鲜度，而网络重放不能伪造推进。
- 让客户端明确区分 API 页面快照、同步请求受理和同步成功，不再以 `meta.asOf` 或 HTTP 2xx 推断健康。
- 保持 customer API 加性兼容，并用 fixtures/schema 锁定字段。

**Non-Goals:**

- 不修改平台私有接口、同步轮询频率、WS v2 payload、batchId 算法或 cursor 推进原则。
- 不以“时间较新”替代 auth、runtime controls、effective capability 或 Cloud connectivity 门禁。
- 不承诺真实账号读写、自动回复合规或生产启用；这些仍受父级变更的人工/合规门禁约束。
- 不新增 Console 页面，也不从 renderer 直接访问平台或数据库。

## Decisions

### 1. API 投影同时返回 observedAt 与 receivedAt

list/detail 的 `data.syncFreshness` 使用固定双渠道形状：

```json
{
  "comment": { "observedAt": 1784044802000, "receivedAt": 1784044802100 },
  "dm": null
}
```

`observedAt` 表示 Edge 完成平台读取的设备时间，回答“数据是在什么时候观察到的”；`receivedAt` 表示 Cloud 成功提交该证据的服务端时间，回答“系统什么时候确认收到了这次同步”。从未成功提交的渠道必须为 `null`，不能回落到 auth checkedAt、HTTP request time、thread message time 或当前时间。

备选方案是只返回 `lastSuccessAt`。这会重新混淆数据观察与服务端接收，无法诚实呈现队列延迟或设备时钟异常，因此不采用。

### 2. 最新证据来自 interaction_sync_batches，不重新解释 meta.asOf

Cloud 按授权后的 `(accountId, envKey)` 查询每个 channel 最新已接受批次，排序键为 `observed_at DESC, received_at DESC, id DESC`。该表同时包含两种原始时间，也包含零 thread/零 message 的成功批次；比从 thread 行聚合更完整。查询结果在 list/detail 响应内复用同一严格类型。

`meta.asOf` 保持原样，仅用于响应快照与分页 cursor。renderer 不显示它为数据时间，也不把它用于同步状态。这样不破坏既有分页签名和兼容客户端。

### 3. 同 batchId 的更新观察只推进证据，不重复业务写

Cloud 命中已有 batchId 时继续验证 env/channel/scope/cursor 一致性：

- `payload.observedAt <= stored.observed_at`：视为旧网络重放，保持原证据时间与业务数据不变；
- `payload.observedAt > stored.observed_at`：视为对相同内容/游标的一次更新平台观察，只把该 batch 的 `observed_at` 推进到新值、把 `received_at` 更新为本次事务服务端时间，并推进同 scope cursor 的成功时间；仍返回 `duplicate`，不重复创建 message/job 或推进业务 cursor 内容。

这样保持 batch 内容幂等，同时让“没有新消息但确实重新读过平台”产生可见证据。较旧的延迟包不能让时间倒退。新 batch 的 thread `last_synced_at` 使用该批次 `observedAt`；Electron 的全局/分渠道状态不再依赖 thread 时间。

备选方案是把 `observedAt` 纳入 batchId。它会改变 Edge 的重放身份和产生更多批次行，不是本次所需的最小契约变化，因此不采用。

### 4. 客户端状态由渠道门禁与 syncFreshness 联合决定

InteractionWorkspace 保存 `syncFreshness` 而非把 `meta.asOf` 保存为数据状态：

- comment/dm tab 只读取对应渠道；综合 tab 分别展示两者，不能用其中一个替另一个背书；
- stored/applied/effective read gate 未通过时继续优先显示真实阻断原因；
- 门禁通过但证据为 null 时显示“尚未成功同步”，空列表不能写成“当前没有互动”；
- 有证据时显示最近 `observedAt`，Cloud 离线时保留该时间并明确为上次成功数据；
- 局部刷新 2xx 后显示“请求已受理，等待同步结果”，只有后续 list/detail 的目标渠道 `receivedAt` 比点击前基线推进，才显示本次已有成功结果。

如果 `observedAt` 明显晚于 `receivedAt`（容忍最多 5 分钟设备时钟偏差），客户端显示设备时间待校准并以 Cloud 接收时间作辅助证据，不能展示未来的“同步正常”。

### 5. Contract-first，加性部署

先更新 control contract 的 schema/fixtures，再实现 Cloud 和 Edge。字段只加在 interaction list/detail 的 `data` 内；旧客户端会忽略加性字段，新客户端在 Cloud 尚未升级或返回非法形状时按 unknown/fail-closed 显示“同步状态待确认”。不需要协议 v2 command mapping 变更。

## Risks / Trade-offs

- [每次 list/detail 多一次同步证据查询] → 使用单条按双渠道取最新记录的查询；先检查现有索引与查询计划，只有证据表规模证明需要时才加 additive index migration。
- [设备时钟偏差导致 observedAt 不可信] → 同时返回 Cloud `receivedAt`，客户端检测明显未来时间并停止“正常”宣称。
- [相同 batchId 的 observedAt 更新可能被误当重放] → 只在 observedAt 严格增加时推进证据，业务 message/job 写仍完全幂等；聚焦测试覆盖相等、较旧和较新三种情况。
- [父级 interaction-management 尚未归档] → 新建独立 additive capability；实现只依赖已在 edge/cloud 默认分支存在的代码，不修改父 change 的两项人工验收结论。
- [新 Edge 先于 Cloud 部署] → 缺失 `syncFreshness` 按 unknown 展示，不用 `meta.asOf` 回退；避免兼容窗口内继续假成功。

## Migration Plan

1. 合入并校验 control contract/schema/fixtures。
2. 在 Cloud 实现证据推进、读取投影和聚焦测试；部署 `dev` 后检查 list/detail 的 null/双渠道形状。
3. 在 Edge 实现 fail-closed 展示与 renderer 测试；无需构建安装包，除非用户另行要求。
4. 回滚时先回滚 Edge 展示，再回滚 Cloud additive 投影；既有 batch/thread/cursor 数据不删除。若增加索引，保留索引也不改变语义。

## Open Questions

无。真实账号是否允许读写与父级变更的 OQ/人工验收门禁保持不变，不由本 change 放宽。
