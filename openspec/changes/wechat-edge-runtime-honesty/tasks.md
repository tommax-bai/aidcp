# Tasks — wechat-edge-runtime-honesty

> 仓：`aidcp-edge` + `aidcp-cloud`；协议/账本：`aidcp`。Edge 独占 `src/wechat-channels/runtime.ts`、`browser-sidecar.ts`、`state-store.ts`，`src/cdp/browser-provider.ts` 只读。Cloud 改动收窄到 recovery provider / welcome mapping 与测试。
> 两份 `protocol.ts` 与 `docs/protocol.md` 是单写热点：先冻结合同，再分别实现，集成/部署串行。不得与其他协议 change 同时写这些文件。
> 每条 task 完成后按 `<!-- <repo> <commit-sha> 备注 -->` 标注；sha 必须取自已推送提交，不要编造。实现阶段使用匹配隔离 worktree，禁止混入 canonical checkout 的其他脏改动。

## 1. 前提与合同重验

- [ ] 1.1 在当前 Edge/Cloud master 上按行为重验 H3/H4/H5/H8/M7；已被他人修复或失去前提的项目登记「已失效 + commit/测试依据」并跳过，绝不重复实装。
  - H3：sidecar 是否在确认真死前丢句柄；runtime 是否先断 Cloud、吞 close error、永久置 `shuttingDown` 并无条件 exit。
  - H4：connector gate 与 auth initialize gate 是否仍未共用含本地 tombstone 的判定。
  - H5：`clear()` 是否仍不作废在途 auth；legacy migration 与 browser candidate 两处 `store.save` 是否都无 generation 复查。
  - H8：connector 未启动、invalid command、invalid scope、飞行/durable idempotency conflict 是否仍收敛成无法供 runtime 判别的普通 result；runtime catch 是否仍为空。
  - M7：Edge tombstone 是否永久为真；welcome 是否仍只有 `offboardPending` / runtime controls、没有 exact purge + rebind proof。
- [ ] 1.2 在 `docs/protocol.md`、Cloud/Edge protocol types 与 fixtures 冻结可选 `interactionRecovery.rebindProof { accountId, envKey, purgedOffboardId }`、old/new peer、缺失/查询失败 fail-closed 语义；确认 message type 计数与 active-command routing 不变。

## 2. aidcp-edge — H3 关闭生命周期闭合

- [ ] 2.1 `browser-sidecar.ts`：close 只对 `closed` 早退；确认真死后才清 session/browser，未确认保留句柄、置 `unavailable` 并抛具名错误；并发 close 复用单个 in-flight attempt。
- [ ] 2.2 `browser-sidecar.ts`：`unavailable` 再 close 必须复用保留 browser handle 真实重试；已关闭 CDP session 不得冒充 browser 已死。
- [ ] 2.3 `runtime.ts`：实现两阶段 close——先 stop/drain connector、保持 Cloud client，再确认 sidecar；成功后才 `client.closeAndWait()` 与 exit。
- [ ] 2.4 `runtime.ts`：未确认时发送既有 `lifecycle.close_failed`、保持进程/Cloud 存活、清除本次 close 闩；重复 IPC close 或 SIGINT/SIGTERM 可重新尝试，不因 `once`/永久布尔闩空转。
- [ ] 2.5 对齐 `CoreLifecycleController` 与 Electron 外壳既有 IPC/状态文案，但不直接复用其“先 deactivate Cloud”的实现；视频号关闭失败必须真正命中外壳的 paused/close_failed 分支且槽位不记为空出。
- [ ] 2.6 测试：sidecar 确认真死、未确认保留句柄、unavailable 重试、并发 close；runtime 未确认时不 close Cloud/不 exit/上报失败，第二次确认后才 close Cloud + exit。

## 3. aidcp-edge — H4 解绑闸覆盖授权

- [ ] 3.1 `runtime.ts`：提取 account-scoped start decision，统一覆盖 connector start 与 auth initialize，至少含 build/kill switch、Cloud capability/runtime controls、Cloud offboard barrier、本地 tombstone。
- [ ] 3.2 本地 tombstone 时走 `auth.disable()`，不得打开 sidecar、弹二维码、读取 profile candidate 或写凭据；日志明确 tombstone/offboardId，不冒充 Cloud 未协商。
- [ ] 3.3 测试：已解绑环境启动与重连均不触发 auth initialize/sidecar open/store save；Cloud 未协商与本地 tombstone 日志可区分。

## 4. aidcp-edge — H5 解绑作废全部在途授权

- [ ] 4.1 `auth-session.ts`：引入单调 auth generation；initialize/reopen/browser-auth 捕获 generation，`clear()` 先推进代次并使旧 attempt 可识别地失效。
- [ ] 4.2 在所有跨 await 的候选发布点及每个 `store.save(...)` 前复查 generation，明确覆盖 stored legacy binding migration 与 browser candidate save；旧代次不得更新内存 active session。
- [ ] 4.3 `runtime.ts` offboard：先 stop/drain connector，再 `auth.clear()` 并等待旧 attempt settled/invalidated，最后关闭 sidecar；未确认 durable 回 `failed`，不得回 `cleared`。
- [ ] 4.4 测试：解绑命中 browser auth 网络等待与 legacy migration 等待时，恢复后均零 save/零 active-session publish；未解绑路径两处 save 正常。

## 5. aidcp-edge — H8 早退结果的可判别持久化

- [ ] 5.1 `connector.ts` / `reply-sender.ts`：引入内部 `ReplySendOutcome`，显式区分 `persisted_or_replayed`、`persist_without_claim`（connector 未启动/真正 invalid command）和 `reject_without_persist`（invalid scope/飞行或 durable idempotency conflict）；wire payload 不变。
- [ ] 5.2 `state-store.ts`：增加无 claim result-outbox 入口；写前校验 exact runtime scope、attemptId/idempotencyKey 未绑定到其他值，相同结果幂等，任何 namespace 冲突拒写。
- [ ] 5.3 `runtime.ts`：仅按 outcome.kind 分流，禁止解析 error message 或只按 `invalid_command` 猜来源；确定判决 durable 后 flush，拒写具名记录，移除空 catch，其余异常如实记录。
- [ ] 5.4 测试：connector 未启动/真正 invalid command 入 outbox 并投递；invalid scope、飞行中不同 attempt、durable claim conflict 不落 outbox且有日志；同 attempt 继续复用原 promise。

## 6. Cloud + Edge — M7 exact rebind proof

- [ ] 6.1 `aidcp-cloud`：新增 recovery snapshot provider。仅当 `offboardPending=false`、active ownership 已重新建立、Cloud 可证明 exact logical `accountId + envKey`，且同 scope 最近一次 offboard 已 `purged` 时返回 `rebindProof`；不得信任 hello 自报来补缺失绑定。
- [ ] 6.2 `aidcp-cloud`：welcome mapping/fixtures/tests 接入 proof；pending、tombstoned、purged 但未归属、active 但 scope mismatch、legacy override 无权威映射、查询失败均省略 proof 并 fail closed。
- [ ] 6.3 `aidcp-edge`：Edge protocol validation/accessor 接受可选 proof；old Cloud、缺失或 malformed proof 不改变 tombstone。
- [ ] 6.4 `state-store.ts`：本地 tombstone 保留 exact offboardId；仅当 proof 的 accountId/envKey/purgedOffboardId 与当前 runtime scope 和 completed cleared/already_cleared tombstone 全匹配时，在一次 durable mutation 中清除。
- [ ] 6.5 `runtime.ts`：welcome/reconnect 先校验并应用 proof，再重跑统一 start decision；proof 不匹配、本地 tombstone、Cloud pending、未协商分别记录真实原因。
- [ ] 6.6 两端测试：旧 peer/无 proof/错三元组/仅 tombstoned 都不启动；exact purge + 新 active ownership proof 清墓碑并恢复 connector/auth；重复 proof 幂等。

## 7. 验证、集成与交付

- [ ] 7.1 在 Edge 匹配 worktree 先跑新增聚焦测试，再跑 `npm run test:acceptance && npm test && npm run typecheck`；保留通过计数与失败边界。
- [ ] 7.2 在 Cloud 匹配 worktree跑 recovery/provider/handler/protocol 聚焦测试、acceptance、全量测试与 typecheck；确认无数据库真实客户写入。
- [ ] 7.3 rebase 到最新默认分支，按 Cloud → Edge 串行 fast-forward 集成并 push；协议 types/fixtures/docs 做最终 drift check，不 force-push。
- [ ] 7.4 运行 `scripts/deploy-target dev --check`，从 clean Cloud master 备份并部署 dev；验证 service/listener/health/Feishu/PostgreSQL 与 old/new Edge welcome。Edge 不构建安装包。
- [ ] 7.5 更新 `docs/real-machine-acceptance-backlog.md`：浏览器占用导致关闭未确认、已解绑重启不弹码/profile 最终 purge、重连窗口诚实 reply failure、purge 后同环境重新归属 proof/清墓碑；未执行真实写必须保持开放。
- [ ] 7.6 更新本 task ledger 的 repo/SHA/验证/部署/偏差，运行 `openspec validate wechat-edge-runtime-honesty --strict`；仅在所有必需任务完成后 archive。
