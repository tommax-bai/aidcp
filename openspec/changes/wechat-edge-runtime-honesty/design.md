## Context

当前实现的五条发现均在 `aidcp-edge` master 上成立，但原任务清单对三个关键机制描述不足：

1. `shutdown()` 在 sidecar 关闭前先断 Cloud，且 `shuttingDown` 永久置真；只删 catch / finally 仍无法保留连接或重试。
2. `invalid_command` 同时承载真正的命令校验失败、飞行中不同 attempt 冲突和 durable claim 冲突；runtime 只看结果 payload 无法决定是否落 outbox。
3. welcome 没有权威的新绑定证据；`interaction_inbox_v1`、`offboardPending=false` 或 runtime-controls version 都不能单独证明本地墓碑已被新归属取代。

本设计优先复用既有事实：浏览器 provider 的 `killAndConfirmDead()`、外壳的 `lifecycle.close_failed`、Edge durable outbox、Cloud durable offboardId / `purged` 状态和 active ownership。不会在 Edge 自行计算 30 天，也不会把错误/缺失快照当成授权。

## Goals

- 关闭成功只能来自浏览器真死证据；失败后进程、Cloud 连接和浏览器句柄仍可被观察与重试。
- 解绑同时挡住新授权并作废所有在途凭据写盘，包括 legacy binding migration。
- 无平台调用的确定判决能够 durable 投递，外来 scope / 幂等冲突仍拒绝污染本账号命名空间。
- 本地解绑墓碑只能被 Cloud 的 exact-scope purge + 新归属证明解除。

## Non-goals

- 不改变底层 `browser-provider.ts` 的关闭算法。
- 不放宽 Cloud 的 ownership、offboard、29/30 天 purge 或真实写开关。
- 不新增 protocol message type、active command 或 Edge 安装包。
- 不让 Edge 依据本地时钟自动过期墓碑；旧 peer 或缺证明时保持 fail closed。

## Decisions

### 1. Sidecar 保留句柄直到确认真死

`CdpWechatChannelsBrowserSidecar.close()` 只对 `closed` 早退。它先进入 `closing`，保留 `session` / `browser` 字段，停止 request capture 并关闭 CDP session，然后调用同一个 browser handle 的 `killAndConfirmDead()`。

- 返回 true：清空句柄，进入 `closed`，返回成功。
- 返回 false 或抛错：保留 browser/session 引用，进入 `unavailable`，向上抛出具名未确认错误。
- `unavailable` 再次 close：复用保留的 browser handle 再次真实关闭和确认，不把 session 已关闭误当成浏览器已死。

并发 close 通过单个 in-flight promise 串行化，避免 offboard 与外壳 close 同时杀同一 browser。

### 2. Runtime 使用两阶段、可重试的关闭状态机

视频号 runtime 采用 `running -> closing -> close_failed | closed` 的本地状态和一个只覆盖当前尝试的 `closeAttempt` promise：

1. 停止 connector / drain 平台动作，但暂不调用 `client.closeAndWait()`。
2. 调用 sidecar close 并等待真死结论。
3. 未确认：状态转 `close_failed`，通过现有 child IPC 发送 `lifecycle.close_failed`，保留 Cloud client 与进程，不调用 `process.exit`；当前 attempt settled 后清除闩，下一次 `lifecycle.close` 或信号可重新进入第 1 步。
4. 确认成功：再关闭 Cloud client，记录停止原因并 `process.exit(0)`。

信号监听不得因第一次失败永久失效；重复信号和 IPC close 共用同一串行入口。通用 `CoreLifecycleController` 的状态/IPC 语义作为合同参考，但它当前会在 close confirmation 前执行 deactivate，因此本 change 不直接复用其实现，也不扩大成通用生命周期重构。

offboard 关闭复用同一个 sidecar close 证据，但不退出进程：未确认时 durable 回 `failed`，Cloud 让该 offboard 回到 pending 并重试；确认成功时才回 `cleared`。

### 3. 同一道 gate 控制 connector 与授权

runtime 提取一个 account-scoped start decision，至少包含：本地 build flag、account kill switch、Cloud capability/runtime controls、Cloud offboard barrier、本地 offboard tombstone。connector start 与 `auth.initialize()` 读取同一份判定。

本地墓碑为真时调用 `auth.disable()`，不打开 sidecar、不读 profile candidate、不落凭据。原因日志必须区分本地 tombstone（含 offboardId）、Cloud offboard pending、Cloud 未协商和其他本地开关。

### 4. 授权代次覆盖所有凭据写点

`WechatAuthCoordinator` 维护单调 `authGeneration`。每次 initialize/reopen/browser-auth 尝试捕获 generation；`clear()` 先推进 generation，使所有旧尝试立即失效，再清内存与 encrypted store。

旧尝试在每个可能跨越解绑的 await 返回后以及每个 `store.save(...)` 前复查 generation，至少覆盖：

- stored legacy binding migration 的 save；
- browser candidate identity/probe 完成后的 save；
- 将 candidate 发布为内存 active session 前。

代次不匹配使用内部可识别的 revoked outcome，记录不含凭据的日志，不转成普通 auth failure，也不再写盘。offboard 在 `clear()` 后等待旧 auth attempt settled / invalidated，再关闭 sidecar，避免授权循环继续触碰已关闭浏览器。

### 5. Reply sender 返回内部判别结果

不修改 Cloud wire payload。connector / reply sender 的内部返回值改成判别联合：

```ts
type ReplySendOutcome =
  | { kind: 'persisted_or_replayed'; result: InteractionReplyResultPayload }
  | { kind: 'persist_without_claim'; reason: 'connector_not_started' | 'invalid_command'; result: InteractionReplyResultPayload }
  | { kind: 'reject_without_persist'; reason: 'invalid_scope' | 'idempotency_conflict'; result: InteractionReplyResultPayload };
```

- 同 attempt 飞行复用和已有 completed/executing 结果属于 `persisted_or_replayed`。
- connector 未启动、结构/期限等平台调用前的确定非法判决属于 `persist_without_claim`。
- scope 不匹配、飞行中不同 attempt、attempt/idempotency durable conflict 属于 `reject_without_persist`。

runtime 只按 `kind` 分流，不解析 error message，也不凭相同的 `invalid_command` 猜来源。新的无 claim outbox 入口同时校验 exact runtime scope、attemptId/idempotencyKey 未绑定到其他值，并对相同结果幂等；任何冲突拒写并记录可检索 reason。

### 6. Cloud 生成 exact rebind proof

`WelcomePayload.interactionRecovery` 向后兼容地增加：

```ts
rebindProof?: {
  accountId: string;
  envKey: string;
  purgedOffboardId: string;
};
```

Cloud 只有同时证明以下条件时才下发：

1. `offboardPending=false`；
2. `envKey` 已重新存在 active customer ownership；
3. `accountId + envKey` 是 Cloud 可证明的当前视频号逻辑绑定（标准路径 `accountId === envKey`；显式迁移必须由 Cloud 自有映射证明，不能信任 hello 自报）；
4. 相同 `accountId + envKey` 的 exact offboard 已处于 `purged`，且该 ID 是这次重新归属所跨越的最近一次 purge。

仅 tombstoned、仅已 purge 但未重新归属、active ownership 但 scope 不匹配、查询失败都不发 proof。旧 Cloud/Edge 忽略可选字段；缺失永远不能清本地墓碑。

Edge 在完成 welcome validation 后，把 proof 与本地 completed cleared/already_cleared tombstone 比较。只有 `accountId + envKey + purgedOffboardId` 全匹配才在同一次 durable mutation 中清墓碑；随后重新运行统一 start decision。proof 不匹配只记录摘要 reason，不删除状态、不启动 connector/auth。

### 7. 协议与集成顺序

该可选 welcome 字段需要同步更新 Cloud/Edge protocol types、Cloud welcome mapping/provider、Edge welcome validation/accessor、fixtures、合同测试和 `docs/protocol.md`。不增加 message type 数量或 active-command routing。

协议冻结后先集成/部署 Cloud，再集成 Edge，确保新 Edge 遇到旧 Cloud 时只是缺 proof 并 fail closed。Cloud/Edge 开发可在匹配 worktree 并行，但两份 protocol hotspot 与最终集成必须单写、串行。

## Failure handling

- sidecar close false/throw：保留句柄、IPC close_failed、Cloud 保持连接、允许重试。
- auth generation stale：丢弃写盘与 active-session publish，日志只含 generation/reason。
- reply outcome/scope 冲突：不写 outbox，具名日志；确定判决写盘失败则不声称已投递。
- rebind proof provider/validation failure：proof 缺失，墓碑继续生效。

## Validation

- Edge：sidecar 三态/并发 close、runtime 关闭失败后 Cloud 未关闭且第二次成功退出、offboard failed retry、授权两处 save 竞态、reply 三类 outcome、墓碑 exact proof/mismatch/old peer。
- Cloud：proof 仅在 active ownership + exact logical binding + matching purged offboard 时出现；pending/tombstoned/no ownership/mismatch/query error 均不出现。
- 合同：两端 type/fixture/docs 一致，message type 计数不变，旧 peer 兼容。
- 真机：只登记未执行的浏览器占用、解绑重启/profile purge、回复重连窗口与 purge 后重新绑定验证；不伪造真实写成功。
