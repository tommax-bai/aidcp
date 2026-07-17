## Context

视频号入站互动有三层会阻止同一平台样本重复出现：Cloud 的 thread/message 数据，Cloud 的 sync batch/cursor 去重状态，以及 Edge 按账号加密落盘的 channel checkpoint/thread source。现有 offboarding 会同时删除授权、运行控制和回复配置，范围远大于测试重置，不能复用。现有人工同步只沿当前游标继续读取，也不能重放旧样本。

该能力跨 Cloud、Edge 协议和 Electron 客户端，并包含开发数据删除，因此必须默认关闭、按账号/环境/渠道收口、保留审计且保持写入 fail-closed。

## Goals / Non-Goals

**Goals:**

- 让开发人员用同一条真实评论或私信反复验证列表、详情和只读处理流程。
- 只清当前客户拥有的当前 env/account、且只清显式选择的 `comment` 或 `dm`。
- 在同一渠道同步锁内清 Edge 检查点并从空 cursor 重读，同时清 Cloud batch 去重记录。
- 所有拒绝、部分完成和成功状态均可解释、可审计，不把投递当成重读完成。

**Non-Goals:**

- 不删除、隐藏或修改微信平台上的评论/私信。
- 不发送回复，不重置发送幂等历史，不用此能力测试已有发送记录的渠道。
- 不清授权/session、runtime controls、reply config、风险计数、客户绑定或 offboarding 状态。
- 不在 `ol` 或未显式启用的 Cloud 开放，不提供 Console 批量删除，不自动执行真实账号重置。

## Decisions

### 1. 独立 customer-auth 路由，双重开发环境开关

新增 `POST /environments/:envKey/interactions/test-reset`，请求严格为 `{ "channel": "comment" | "dm" }` 并要求 `Idempotency-Key`。路由继续复用 `withAuthorizedInteractionScope`，不能传 accountId，也不能跨环境。

Cloud 只有同时满足 `AIDCP_DEPLOY_ENV=dev` 与 `AIDCP_INTERACTION_TEST_DATA_RESET=true` 时才返回 `testTools.dataResetEnabled=true` 并接受路由；其余环境返回 feature-disabled。选择显式双开关而不是只看 `NODE_ENV`，因为生产构建也可能以 production Node 模式运行在 dev。

### 2. Cloud 在已确认唯一新 Edge 在线后执行单渠道事务

新增协议 capability `interaction_test_data_reset_v1`。Cloud 先完成读取开关、有效授权、读取 capability 和具备该 capability 的唯一 Edge 在线检查，再进入回调事务：

1. `FOR UPDATE` 锁定当前账号 runtime controls，校验 envKey 与 `write_paused=true`；
2. 若所选渠道存在任意 `interaction_send_attempts`，整次拒绝；
3. 删除当前 account/env/channel 的 `interaction_threads`（级联 message/job/attempt）、`interaction_sync_batches` 和 `interaction_sync_cursors`；
4. 在同一事务写入不含正文的 `interaction_audit_events`，仅记录 actor、channel 和删除计数；
5. 提交后立即下发既有 `interaction.sync.request`，reason 扩展为 `test_reset`。

这样已知 Edge 离线、旧版或读取门禁不满足时不会先清 Cloud。若事务已提交但 WebSocket 在最后投递时断开，API 返回明确的“Cloud 已清空但重新拉取未送达”错误并追加失败审计；客户端保留重试入口，不能显示完成。

未选择先让 Edge 重置并读取再删 Cloud，因为稳定 batchId 会被 Cloud 现有批次表判为 duplicate；也未复用 offboarding，因为它会清除超出测试范围的客户与授权数据。

### 3. Edge 在渠道同步锁内原子切换到空检查点

`InteractionSyncRequestPayload.reason` 增加 `test_reset`，并由协议 validator 严格接受。Connector 收到该 reason 后，在既有 channel sync lock 内先调用 `WechatRuntimeStateStore.resetReadState(channel)`，删除该渠道所有 checkpoint 和 `threadSources`，再执行正常 comment/DM sync。回复执行、结果 outbox、offboarding 和加密 session 均保留。

该顺序保证同渠道不会有普通同步夹在“清检查点”和“从头读取”之间。Cloud 只向声明新 capability 的 Edge 下发，避免旧 Edge 因未知 reason 拒绝而造成已清空但无法自动重读。

### 4. 客户端只在开发工具可用时展示，并要求二次确认

互动列表回包增加只读 `testTools.dataResetEnabled`。Electron 视频号工作区增加“测试数据”折叠卡；仅该值为 true 时显示评论/私信两个按钮。点击后先展示人话说明，再要求输入固定确认词 `重置评论` 或 `重置私信`。

确认文案明确：会删 Cloud 当前渠道副本并重新拉取；不会删微信平台数据；不会发送回复。请求接受后客户端清除当前本地选中态并刷新列表，显示“已清空，正在重新拉取”；只有后续列表真实出现或明确返回空态才更新结果，不伪造读取数量。

## Risks / Trade-offs

- [Risk] Cloud 提交后 WebSocket 恰好断开，形成只清空未自动重读。 → 返回专门的部分完成错误、写审计并允许相同渠道重新执行；不回滚或伪造 Edge 已处理。
- [Risk] 重置一个已有发送记录的渠道可能让回复工作流重复面向同一平台消息。 → 发现所选渠道任意 send attempt 就永久拒绝测试重置，改用无发送历史的测试账号/渠道。
- [Risk] 重读可能受平台只返回有限历史窗口影响。 → 客户端只展示实际回来的数据，不承诺平台仍可返回已存在的旧样本。
- [Risk] 新旧 Cloud/Edge 短暂版本不一致。 → capability 协商先于删除；Cloud 未看到新 capability 就拒绝。
- [Trade-off] 单次只重置一个渠道，比“一键全清”多一步。 → 删除范围更容易确认，失败与审计也更清楚。

## Migration Plan

1. 先发布 Edge 协议、状态重置和客户端代码，但保持 Cloud 功能关闭；旧 Cloud 不会发送 `test_reset`。
2. 发布 Cloud 代码；只在 `dev` 设置两个显式开关，确认新 Edge capability 在线后入口才可用。
3. 用单元/集成测试构造隔离数据验证删除范围、拒绝门禁、批次重放和 UI 二次确认；不操作当前真实账号数据。
4. 回滚时先关闭 `AIDCP_INTERACTION_TEST_DATA_RESET`，再回滚 Cloud/Edge；已重读的数据按正常入站记录保留。

## Open Questions

- 无。若后续需要对有发送历史的账号反复测试，应另建专用测试账号或设计独立的不可发送 replay sandbox，不能放宽本能力的拒绝规则。
