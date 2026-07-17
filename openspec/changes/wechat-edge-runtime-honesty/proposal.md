## Why

视频号边缘运行时绕过了通用生命周期契约：底层浏览器 provider 在无法确认浏览器真死时会如实回报「未确认」，但视频号的 sidecar 在确认杀死之前就丢弃了句柄、运行时又把这个诚实信号原地吞掉并无条件退出进程——结果是「明知没关掉却上报已关闭」，装着已登录会话的浏览器继续运行、槽位被误判空出、云端墓碑照常推进到清除数据。

同一处运行时还有三个同源缺口：解绑标记只挡住了连接器、没挡住浏览器授权，重启后会为已解绑环境弹二维码并把凭据重新落盘（且因 profile cookie 未清，常见路径下连扫码都不需要，形成「浏览器一直重开 → AdsPower 删除永远失败 → 游标永远回不到 purged」的自维持环）；解绑不取消在途的授权循环，循环恢复后会把刚删掉的凭据原样写回；回复发送的早退路径构造了失败结果却从不落投递箱，云端拿到彻底的沉默，attempt 永卡 dispatched、撞账号级唯一索引让该账号此后所有回复 409，且下次对账会把「压根没发过」写成 ambiguous（禁止重试、要人工去平台肉眼核对）——而边缘明确知道没发。

此外解绑在本机留下永久墓碑：云端支持 purge 后重新绑定同一环境，边缘却单方面钉死连接器永不启动，日志还报成「云端没协商能力」，把排查引向完全错误的方向。当前 welcome 只有 `offboardPending` 与普通 runtime-controls version，无法证明「这是同一解绑已经 purged 后的新归属」；若 Edge 仅凭 capability 或 `offboardPending=false` 清墓碑，会在旧解绑刚完成时立即错误复活。

## What Changes

- **关闭必须凭实证**：sidecar 只在确认浏览器真死之后才丢弃句柄；未确认即如实保持不可用态并向上抛出，第二次关闭必须真的重试关闭，MUST NOT 直接报成功。
- **运行时接住关闭失败**：shutdown / terminate 改成两阶段关闭——先停 connector、保持 Cloud 连接，再确认 sidecar 真死；只有确认成功才关闭 Cloud 并退出。未确认时清除本次关闭闩、回落到可重试暂停态并发送既有 `lifecycle.close_failed`，外壳的「关闭失败」分支从死代码变为真正接线。
- **解绑闸覆盖授权**：登录闸与连接器闸查同一组前提（含持久化的解绑标记）；已解绑环境重启后 MUST NOT 弹二维码、MUST NOT 重新落盘凭据。
- **解绑作废在途授权**：引入解绑代次标记，清除时作废在途授权；浏览器授权和 legacy binding migration 等每一个凭据写点都必须在写前复查代次，代次已过期即丢弃而非写回。
- **早退结果必须落投递箱**：connector / reply sender 用内部判别联合类型显式区分「已持久化」「无 claim 的确定判决」「fail-closed 拒写」，不得让 runtime 仅凭相同的 `invalid_command` payload 猜来源。前两类按既定规则投递；`invalid_scope` 与幂等命名空间冲突保持拒写并留可检索日志。
- **墓碑必须有权威回拨证据**：Cloud 在 welcome 的 `interactionRecovery` 可选下发 exact-scope `rebindProof(accountId, envKey, purgedOffboardId)`；只有 active ownership 已重新建立且对应 offboard 已 `purged` 才能生成。Edge 仅在 proof 与本地墓碑逐字段匹配时清墓碑；缺失、错 scope、旧 Cloud 或查询失败全部保持 fail closed。

本 change 会触碰 Edge/Cloud 两份 `protocol.ts` 和 `docs/protocol.md`，属于协议单写热点；不得与其他协议变更并行写同一文件。它不改变 message type 计数、不新增 active command、也不触碰 `command-bridge` 动作映射、`RoleName` / `role-catalog` 或 `risk-state-machine.ts`。Edge 与 Cloud 可在各自隔离 worktree 开发，但协议冻结、集成和 dev 部署必须串行。

## Capabilities

### Modified Capabilities

- `wechat-channels-real-runtime`: 边缘视频号运行时的关闭、解绑、授权与回执必须实证诚实，且每个不可用态都有明确的回拨路径。

## Impact

- `aidcp-edge`：视频号 sidecar / runtime / auth / reply outbox / 本地墓碑，以及 Edge protocol type、validation、fixtures 和聚焦测试。
- `aidcp-cloud`：welcome recovery provider、exact rebind proof 查询、Cloud protocol type/fixtures/tests；不放宽 offboard、purge 或 ownership guard。
- `aidcp`：`docs/protocol.md`、本 change 的设计/任务账本与真机验收 backlog。
- 不构建 Edge 安装包；Cloud 运行时代码完成后按规范部署 `dev`，真实写入仍保持 gated。
