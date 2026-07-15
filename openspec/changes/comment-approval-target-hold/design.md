## Context

浏览闭环内触发评论、进入人审时，账号本应停在待评论帖上等审批。经多 agent 对抗性核验（跨 `aidcp-cloud` / `aidcp-edge`），结论：

- **根因全在云端**。边缘 FB 会话 100% 命令驱动、一命令一回执，静默期完全静止（无自主滚动 / 看门狗 / 心跳）；hot-lead 解耦路径对 FB 结构性不触发（其热度闸依赖只有小红书才上报的发布相对时刻文本）。故账号任何位移必对应云端下发的一条命令。
- **实现漂移**。现有 `comment-interaction` Requirement 106 已要求"等待期间进入被看门狗认得的暂停态、复用按-edge 暂停通道、暂停期间不发其他浏览/互动命令"。但当前实现是一个进程内布尔 `RoleDispatcher.approvalInFlight`：① 全仓只在 idle-nudge 翻译器一处被查（`role-dispatcher.ts:1787`），不进命令统一出口 `sendCommand`（`690-726`）；② 只在 `comment.cleared` 才置位，评估/撰写/去 AI 味三次 LLM 的"撰写窗"完全无保护。
- **两条真实滚走源**（已确证）：撰写窗内并行点赞回 `no_target` → 云端立即 `sendScrollCommand('rescan_after_stale_target')`（`2223-2234`）把目标帖滚走；审批窗内任何 stray 边缘上报驱动 `open_note`/`scroll`/`refresh`，且一条点赞回执可能触发 `session.should_end`→`session.end`（`2049`）废掉在审评论。

现成机制与先例：`sendCommand` 已 honor 软暂停通道 `SessionContext.browseSuspended`（`697`），暂停期扣住 browse 命令、放行 `session.end`/bypass；`SessionMonitor.pauseClock()`（`session-monitor-role.ts:153`）把 idle 看门狗按"有意暂停"冻结；`nickname-enricher.ts:104/155-159` 是"`setBrowseSuspended(true)` → 做事 → 严格顺序先解除暂停再 emit 续场命令"的成熟先例。

## Goals / Non-Goals

**Goals:**
- 让评论支线在途成为真正的暂停态：覆盖支线全程（互动完成/评估起 → `comment.done`/`comment.skipped` 止），经统一命令出口生效，扣住一切会离开待评论帖的命令。
- 一个机制同时治住两条滚走源（撰写窗 no_target 重扫、审批窗 stray 命令）与"提前结束会话废掉在审评论"。
- 严格保持 AC-PUB 红线与 `session.end` 可达性；跨平台（XHS / FB 两步迁移）一致。

**Non-Goals:**
- 不改边缘（`aidcp-edge` 无改动）。
- 不改评论两步 surface 迁移逻辑与其 fail-closed 双验证（读评 surface 不等时先 `open_note{navigate}` 再评论，保持不变）。
- 不放松"未授权不发"、不改评论准入门槛 / 每日上限 / 风控闸。
- 不引入新协议消息、不新增角色。

## Decisions

### D1：复用 `browseSuspended` 软暂停通道，而非扩展 `approvalInFlight` 的检查点
**选择**：进入评论支线时 `ctx.setBrowseSuspended(true)`，终局 `setBrowseSuspended(false)`。
**理由**：`sendCommand` 是所有翻译块的唯一出口且已 honor `browseSuspended`——复用它，一切离开待评论帖的命令（重扫滚屏、idle_nudge 滚屏、`open_note` 换帖、`refresh`、feed 续滚）自动被扣住，无需在每个出口逐一加 `approvalInFlight` 判断（那正是当前漏洞的形态：单点补丁必然漏点）。`session.end` 与 bypass 命令天然放行，满足 spec"`session.end` 仍可达"。
**备选（弃）**：在 `sendCommand` 里新增独立的 `approvalInFlight` 闸——等价于再造一个 `browseSuspended`，重复且易与巡视/配额闸交互出错。

### D2：暂停窗从"评论支线开始"起，而非 `comment.cleared`
**选择**：在评论支线确立要处理该笔记的最早点进入暂停态（评估阶段 / `interaction.completed` 派生的评论链起点），覆盖撰写窗。
**理由**：撰写窗内并行点赞回 `no_target` 的重扫是最主要的真实滚走源；`comment.cleared` 太晚。浏览闭环本就串行 hold 在此（返回 feed 必等 `comment.done`/`comment.skipped` → AuthorEvaluator），因此对"不评论的多数笔记"短暂进入暂停态无副作用——期间本就不该有前进命令，暂停只是把 stray 的重扫/nudge 滚屏挡掉。
**备选（弃）**：仅覆盖 `comment.cleared` 之后——漏掉撰写窗竞态（H1），不达标。
**实现取舍**：进入点优先取能覆盖撰写窗竞态的最早稳定信号；若评估阶段为纯确定性早判、其 `comment.skipped` 与进入点同 tick 同步返回，需保证"进入→同步 skip→解除"顺序不把标志卡死（参照现有对 `comment.cleared` 同步 skip 卡死的防御）。

### D3：人审窗内推迟 `session.should_end`，用同一 `pauseClock` 语义
**选择**：暂停期间冻结 idle 计时（`pauseClock`），并把动作数/时长/配额触发的 `should_end` 推迟到评论支线终局后再评估。
**理由**：一条点赞回执在人审窗内触发 `should_end` 会连评论一起废掉；窗口 ≤ 硬短超时（数十秒到 ~90s），推迟评估对限流账面影响可忽略。终局后仍会评估，真正超限照常结束。`session.end` 在终局解除暂停后可达，不破坏红线。
**备选（弃）**：窗内照常允许 `should_end` 结束会话——符合"`session.end` 仍可达"字面，但会真的杀掉已人审通过的评论，与本 change 目的相悖。

### D4：终局严格顺序——先解除暂停，再下发评论/迁移命令
**选择**：`comment.approved`/`comment.skipped` 处理器内先 `setBrowseSuspended(false)` + resume clock，再走 approved 评论下发 / `open_note{navigate}` 迁移。
**理由**：评论命令与迁移 `open_note` 都经 `sendCommand`，若暂停未解除会被自己扣住而静默丢弃。镜像 `nickname-enricher` 的严格顺序先例。

## Risks / Trade-offs

- **[进入点过早误伤正常前进命令]** → 浏览闭环在评论支线在途期间本就不发前进命令（串行 hold）；暂停只挡 stray 的重扫/nudge/换帖，无正常命令被误扣。终局 D4 保证评论/迁移放行。以 acceptance 用例覆盖"终局命令必达"。
- **[同步 skip 卡死暂停标志]** → 复用现有对 `comment.cleared` 同步 skip 的防御思路：仅在真正进入支线时置位，终局订阅者清位；桩测覆盖"评估即 skip"的同 tick 路径不残留暂停。
- **[与巡视/配额软暂停叠加]** → `browseSuspended` 已被巡视/`nickname-enricher` 复用，可能同时置位。采用引用计数或"评论支线独立标志 + 出口取并集"避免一方解除误放另一方（实现期定；优先最小改动：若无并发场景则单标志，若有则引用计数）。以 typecheck + acceptance 保证。
- **[热点单写文件冲突]** → `role-dispatcher.ts` 与活跃 change `lease-strict-preemption` 同区。集成串行：合入前 rebase 最新 master、解冲突、跑 `test:acceptance` + `typecheck`。
- **[`should_end` 推迟掩盖真实超限]** → 仅推迟 ≤ 硬短超时一个窗口，终局后立即复评；不改变最终结束语义，只避免"废掉在审评论"。

## Migration Plan

1. 在 `aidcp-cloud` 开发分支 / worktree 实装（cloud-only）。
2. `npm run test:acceptance`（AC-PUB / AC-PROTO / 评论闸全过）→ 全量 `npm test` → `npm run typecheck`。
3. 合入 master 前 rebase 到最新、解 `role-dispatcher.ts` 冲突、复跑闸。
4. 默认部署 `dev`（安全序列：备份 → rsync → restart → healthcheck）。
5. 真机灰度（评论触发→人审期账号停在帖上→审后继续）归 `docs/real-machine-acceptance-backlog.md`（并入 FB 灰度簇）。
- **回滚**：cloud-only、无协议/DB 变更，回滚即还原 `role-dispatcher.ts` 相关块；无迁移数据。

## Open Questions

- 暂停进入点的确切事件锚（评估阶段起点 vs `interaction.completed` 派生锚）——取"能覆盖撰写窗竞态且不与串行 hold 冲突"的最早稳定点，实装时以代码现状定，acceptance 用例锁行为。
- `browseSuspended` 并发复用是否需引用计数——按实现期是否存在"评论支线与巡视/昵称采集同窗"决定；无并发则单标志最小改。
