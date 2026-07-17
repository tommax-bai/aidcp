# Tasks — wechat-edge-runtime-honesty

> 仓：`aidcp-edge`（master）。本 change 独占 `src/wechat-channels/runtime.ts`、`browser-sidecar.ts`、`state-store.ts`；`src/cdp/browser-provider.ts` **只读参考、不要改**（那层已经是诚实的）。
> 少量改动会落到 `src/wechat-channels/auth-session.ts`（解绑代次）与 `connector.ts` / `reply-sender.ts`（早退结果的判别口径）——这两个文件本批无他人认领，但改动务必收窄。
> 每条 task 完成后按 `<!-- <repo> <commit-sha> 备注 -->` 标注；**sha 必须取自已推送的提交**，不要编造。

## 1. aidcp-edge — 前提重验

- [ ] 1.1 在当前 aidcp-edge master 上重验本 change 每条发现的前提是否仍成立（文件/行号可能已漂移，按行为而非行号核对）。任一条已被他人修复或已失去前提 → 在本文件如实登记「已失效 + 依据」并跳过，**绝不为了勾选而重复实装**。

  重验锚点（2026-07-17 在 `eb1f077` 上已核，五条均仍成立）：
  - **H3**：`browser-sidecar.ts` 的 `close()` 是否在 `killAndConfirmDead()` **之前**就把 `this.session` / `this.browser` 置空；失败分支是否把状态置为 `unavailable`，而函数开头的早退守卫是否只认 `closed`（→ 第二次 close 无句柄可杀、直接置 `closed` 报成功）。
  - **H3 上层**：`runtime.ts` 的 `shutdown()` 是否 `await sidecar.close().catch(() => undefined)`，`terminate()` 是否在 `finally` 里无条件 `process.exit(0)`。
  - **H4**：`runtime.ts` 末尾的登录闸是否只查 `flags.interactionEnabled` 与 `flags.accountKillSwitch` 两个本地开关，而不查 `state.isOffboarded()`（连接器闸查了三项、含解绑）。
  - **H5**：`auth.clear()` 是否只清 store / 置状态，而不作废在途的 `authenticateThroughBrowser()` 循环；该循环末尾是否无条件 `store.save(...)`。
  - **H8**：`connector.send()` 的 `!this.started` 早退与 `reply-sender.ts` 的 `scopeMatches` / `commandValid` / 飞行中 attempt / `claim.status==='conflict'` 五条早退，是否都直接 `Promise.resolve(resultFor(...))` 而从不进 outbox；`runtime.ts` 里 `state.completeReplyExecution(...)` 的 catch 是否为空（吞掉 `reply_execution_not_claimed`）。
  - **M7**：`state-store.ts` 的 `isOffboarded()` 是否只要有 `completed` + `cleared`/`already_cleared` 就永远返回 true、无任何期满或云端重绑的回拨；以及未启动时打的日志是否措辞为「Cloud did not negotiate interaction_inbox_v1」。

## 2. aidcp-edge — H3 关闭生命周期闭合

- [ ] 2.1 `browser-sidecar.ts`：把句柄丢弃移到**确认真死之后**。`close()` 先 `killAndConfirmDead()`，确认为真才置空 `session`/`browser`、状态置 `closed`；未确认则保留句柄、状态置 `unavailable` 并抛出未确认信号。
- [ ] 2.2 `browser-sidecar.ts`：早退守卫只对 `closed` 生效；`unavailable` 态再次调用 `close()` SHALL 真的重新发起关闭并重新确认（不得空转报成功）。
- [ ] 2.3 `runtime.ts`：`shutdown()` 不再吞掉 sidecar 的未确认信号——移除 `.catch(() => undefined)`，让未确认向上传播。
- [ ] 2.4 `runtime.ts`：`terminate()` 改为按结果分流——确认关闭才 `process.exit(0)`；未确认则向外壳上报「关闭失败 / 浏览器仍在运行」、**保持进程存活于暂停态**（保留云端连接以便下一次关闭指令重试）。注意 `process.exit(0)` 挂在 `finally` 上，只删 catch 无效。
- [ ] 2.5 对齐通用生命周期契约：读小红书 / FB 核心的关闭路径，确认「未确认关闭时拒绝退出、回落暂停并如实上报」的消息形状与外壳既有的「关闭失败」分支一致，使该分支对视频号不再是死代码。
- [ ] 2.6 测试：sidecar 三态用例（确认真死→closed+成功；未确认→unavailable+抛出且句柄保留；unavailable 再 close→真的重试）+ runtime 一条（关闭未确认时不 exit、上报关闭失败）。

## 3. aidcp-edge — H4 解绑闸覆盖授权

- [ ] 3.1 `runtime.ts`：把连接器启动闸的前提提取为一处判定（含 `state.isOffboarded()`），登录闸复用同一处；已解绑时走 `auth.disable()` 路径、不调用 `auth.initialize()`。
- [ ] 3.2 `runtime.ts`：已解绑时确保不拉起浏览器 sidecar、不弹二维码，且不从存活 profile 读回候选凭据落盘。
- [ ] 3.3 测试：已解绑环境启动 → 不触发授权初始化、无凭据写盘（用桩 store 断言零 `save`）。

## 4. aidcp-edge — H5 解绑作废在途授权

- [ ] 4.1 `auth-session.ts`：引入解绑代次标记（单调递增计数）；`clear()` 推进代次。
- [ ] 4.2 `auth-session.ts`：授权循环在每次 `store.save(...)` 前复查代次；代次已推进 → 丢弃该次写盘并如实记录（不静默）。
- [ ] 4.3 `runtime.ts` offboard 分支：`auth.clear()` 之后 SHALL 等待/作废在途授权，再进入 sidecar 关闭；关闭结果按第 2 节口径如实回报（未确认 → `failed`，不得报 `cleared`）。
- [ ] 4.4 测试：解绑命中授权等待中 → 恢复后 `save` 被丢弃、磁盘无凭据；未解绑路径 `save` 正常。

## 5. aidcp-edge — H8 早退结果落投递箱

- [ ] 5.1 判别口径：把五条早退分成两类——**确定判决**（连接器未启动 `INTERACTION_FEATURE_DISABLED`、命令校验不过 `invalid_command`）SHALL 落投递箱；**fail-closed 拒写**（`invalid_scope` 外来 scope、幂等键已绑定到另一 attempt 的冲突）SHALL 不落投递箱，但 SHALL 打可检索日志。飞行中同 attempt 复用既有 promise、不属于早退结果，保持原样。
- [ ] 5.2 `state-store.ts`：新增一条「无 claim 也能把结果写进 result outbox」的持久化入口（按 attemptId 定位），并在写入前校验结果 scope 与本运行时绑定一致；scope 不符即拒写并抛出。
- [ ] 5.3 `runtime.ts`：`interaction.reply.send` 分支——`completeReplyExecution` 抛 `reply_execution_not_claimed` 时，若结果属于确定判决则改走 5.2 的入口持久化，再 `flushReplyResultOutbox()`；属于 fail-closed 拒写则记日志后返回。**移除那个空 catch**，其余异常照常如实记录。
- [ ] 5.4 测试：连接器未启动时收到 reply.send → outbox 有一条 `failed`+`not_verified` 结果且被投递；`invalid_scope` → outbox 为空且有拒写日志。

## 6. aidcp-edge — M7 墓碑回拨路径

- [ ] 6.1 `state-store.ts`：解绑墓碑不再永久为真——以云端权威判定为准。云端重新协商并按新绑定派发该环境时，本机墓碑 SHALL 被清理、连接器恢复启动。实现从简（YAGNI）：不在边缘自行计时 30 天，只保留「云端重新绑定 → 清墓碑」这一条回拨。
- [ ] 6.2 `runtime.ts`：区分两类不可用原因的日志——本机解绑墓碑（写明 offboardId）vs 云端未协商 interaction 能力，措辞不得互相冒充。
- [ ] 6.3 测试：墓碑期内不启动且日志指向墓碑；云端重新绑定后连接器启动且墓碑被清。

## 7. 收尾

- [ ] 7.1 `cd /Users/baitianxing/codes/aidcp-edge && npm run test:acceptance && npm test && npm run typecheck` 全绿。
- [ ] 7.2 合回 edge master（rebase 到最新 master、解冲突后 ff）；push。
- [ ] 7.3 把桩验不了的真机项登记到 `docs/real-machine-acceptance-backlog.md`（建议并入视频号真机簇）：① 运营机上强制制造「关闭未确认」（浏览器被占用），确认核心不退出、槽位不被记为空出、云端墓碑不推进到 purge；② 已解绑环境重启客户端，确认不弹二维码且 AdsPower profile 能被真正删除、游标走到 purged；③ 重连窗口内下发回复命令，确认云端收到诚实失败回执而非沉默、该账号后续回复不再 409。
- [ ] 7.4 `cd /Users/baitianxing/codes/aidcp && openspec validate wechat-edge-runtime-honesty --strict` 通过后 archive。
