# 视频号互动存储：失败语义与写熔断复位（wechat-store-and-circuit）

## Why

视频号互动的云端存储层把四处「暂时做不到」实现成了「永远做不到」，且没有任何机制把它们拨回来。最严重的是账号写熔断：跳闸后全仓唯一的清除语句只在「发送成功确认」时执行，而门禁在熔断态拒绝一切发送——没有发送就没有确认，闭环死锁；运营唯一的写入口不碰熔断字段，关掉写暂停也解不开，接口返回 200、后台显示「允许写入」，实际每次发送仍失败——界面与真实行为相反。同期还有三处同源问题：收件箱摄取把已处理会话无条件打回待审、卡在分类中的 job 只在进程启动时恢复一次、解绑后正文的清理硬等边缘回执（边缘永不回来则正文永久留存，spec 明写的 30 天 purge 形同虚设）。

发布侧的同类熔断早已成文：「熔断清除 MUST 接通人工确认路径且不得死锁」（`publish-dispatch-resilience`）。本 change 是对该既有不变量的复刻违反的修复，措辞复用那份 spec。

## What Changes

- **H10 写熔断可复位**：运营显式解除写暂停即视为人工确认，在同一次 UPDATE 内清零连续失败计数与熔断时间戳；熔断状态透出到运行控制的对外视图与后台，与「运营暂停」分开渲染，不得两者共用一个开关。
- **M4 摄取不打回已处理会话**：只有真正新建了回复 job 的入站消息才把会话置为待审；已 ignored/escalated/replied 的会话不因整页重摄取而复活。
- **M5 分类中 job 周期恢复**：周期恢复扫描纳入卡住的 classifying job（不再只在进程启动时扫一次），消除「永久处理中、既不出草稿也不报错、手动重生成被 409 拒」与部署重启的 40s 盲区。
- **M6 云端清理与边缘回执解耦**：云端那份正文/昵称/头像/会话标题的清除不再等边缘回执，到期即执行；边缘清理结果单独记账，不阻塞云端的时间兜底。

## Capabilities

### Modified Capabilities

- `wechat-channels-interaction`: 写熔断的复位路径、摄取的会话状态语义、分类中 job 的周期恢复、解绑清理的时间兜底。
- `console-panel-api`: 运行控制视图透出熔断状态，后台不得把熔断渲染成「允许写入」。

## Notes

- **并行安全**：本 change 不触碰四个热点文件（两份 `protocol.ts`、command-bridge 动作映射、`RoleName` + role-catalog、`risk-state-machine.ts`），可与本批其余 change 全并行开发；集成仍串行（合回前 rebase + `test:acceptance` + `typecheck`）。
- **文件边界**：本 change 拥有 `aidcp-cloud/src/interactions/interaction-store.ts`、`src/interactions/interaction-internal-api.ts` 的运行控制视图、`src/server.ts` 的互动恢复段，以及 console 的运行控制展示。并行的 `wechat-send-failure-semantics` 拥有 `send-orchestrator.ts`——H10 的**门禁**在那个文件里，本 change **只改复位侧、不动门禁**。若实装中发现必须调整门禁判据（例如门禁需要区分「熔断」与「运营暂停」的拒绝原因），标为跨 change 协调项，先与该 change 的 session 对齐再动，绝不双方各改一半。
