## Context

节奏系数收口云端：内容/状态相关时长由云端算**中心值**，随指令以 `thinkMs`/`dwellMs` 下发；边缘只叠 lognormal 抖动 + 保证停留达标 + 断连兜底（command-pacing spec）。当前缺口经代码核实：

1. **返回手势双重犹豫**：`navigation.back` 的 edge 处理先 `ensureDetailDwell()`（满足该笔记停留下限，治秒退），随后 `navigateBack()` 又 `humanPause(actionTiming)`（`TIMING_PRESETS.action` 中位 ~2.5s）才 `history.back()`。停留已被 dwell 治理，这第二段全量 action 犹豫是重复计费，构成返回链路主要固定延迟。
2. **feed 重扫无重访感知**：`feed.scrolled` → `sendCommand({action:'scroll', reason:'feed_scroll'})`（`role-dispatcher.ts:296-298`）不带 `thinkMs`。`SessionContext._visitedNoteIds` 仅记「打开过的笔记」、仅供 ContentEvaluator 决定要不要打开；`computeDwellMs`/`computeThinkMs`（`pacing.ts`）纯按内容量+风控算，无「seen-before」入参。返回到一页全是刚看过的卡片时，仍按首见全量节奏。

两个**会让天真修法失效**的硬约束（已核实）：
- `command-bridge.ts:22-23`：`scroll` 映射**只转发 `{reason}`、丢弃 `params`**（与 `note.open`/`interaction.*` 转发 `command.params` 不同）。在云端给 feed scroll 挂 `params:{thinkMs}` 会被**静默丢弃**，必须同时改 bridge。
- `PageScrollPayload`（edge/cloud `protocol.ts:350`）当前仅 `{reason?}`。加 `thinkMs` 是**协议 v2 改动，须三处同步**（两份 `protocol.ts` 逐字一致 + `docs/protocol.md`），`npm run typecheck` 用 `Record<MessageType,true>` 穷举把关。

## Goals / Non-Goals

**Goals:**
- 返回 feed 更快：`back_to_feed` 路径去掉返回手势的二次全量犹豫，改轻量手势停顿（停留仍由 dwell 治理）。
- 已看过的 feed 卡片扫得更快：云端按「可见卡片已看过比例」调小 feed-scroll `thinkMs` 中心值；全新卡片仍给全量。
- 节奏中心值仍收口云端；边缘只叠抖动（不新增系数）。

**Non-Goals:**
- **不削减刚读笔记的 dwell**（你确实读了它，削它=秒退回归，违反红线）。
- 不改 `search.scrolled` 的搜索结果重扫（同构问题，留待后续）。
- 不引入「跨会话/持久化已读」——seen 集合仅会话内（`SessionContext` 生命周期）。
- 不动子动作运动时序（逐帧滚动/鼠标轨迹，edge 自带）。

## Decisions

### D1：返回手势改轻量停顿（edge 层）
`navigateBack()` 的 `back_to_feed` 分支移除 `humanPause(this.actionTiming)`，改用一段显著更小的手势停顿（如 `scroll` 量级 jitter，中位 ~0.6–0.8s）。
- **为何**：停留时长由 `ensureDetailDwell()`（接云端 `dwellMs`）治理；返回手势是「已决定离开后的一次回退动作」，真人是快速 flick，不再全量deliberation。这是 edge 执行层的手势时序，属边缘自带范畴，**不破坏「中心值收口云端」**。
- **备选（否决）**：让云端给 back 指令再下发一个「gesture think」字段——多一个协议字段、收益小；手势时序本就归边缘。
- **保留红线**：`ensureDetailDwell()` 与「详情页非零停留」不变；本决策只动 dwell **之后**那段冗余 action 犹豫。

### D2：云端卡片级 seen 集合（state 单写在云端）
`SessionContext` 增 `_seenCardIds:Set<string>` + `markCardSeen(noteId)` / `isCardSeen(noteId)` / `seenFractionOf(cards)`；`role-dispatcher.ts` 在 `page.cards.arrived`（:393-396）对每张可见卡片 `markCardSeen`。保留 `_visitedNoteIds`（打开过的笔记）不变。
- **为何**：state 单写在云端（边轻云重）。「滑过但没打开」的卡片也要算「看过」，故需独立于 visited-notes 的 card-seen 集合。
- **备选（否决）**：让 edge 在 `page.cards` 里带 `seen` 标记——把状态判断下沉边缘，违反单写；且 edge 无跨轮记忆。

### D3：feed-scroll `thinkMs` 按已看过比例缩放（云端中心值）
`pacing.ts` 增 feed-scroll 节奏：`thinkMs_center = THINK_BASE * (1 - K*seenFraction) * tempo * fatigue`，floor 保底（如 ≥150ms），`K≈0.6`（可调，列 Open Questions）。`feed.scrolled` 处理据当前可见卡片的 `seenFractionOf` 计算并挂到 `scroll` 指令 `params.thinkMs`。
- **为何**：中心值收口云端；重访比例高→扫得快，全新页→全量。
- **依赖**：必须配 D4（bridge 转发 params）+ D5（协议字段）+ D6（edge honor），否则 thinkMs 到不了边缘。

### D4：修 command-bridge 让 scroll 转发 params
`command-bridge.ts:22-23` 改为 `createEnvelope('page.scroll', { reason: command.reason, ...command.params })`（对齐 `navigation.back` 的写法）。
- **为何**：当前丢 params，D3 的 thinkMs 会被静默吞掉。这是必修接缝。

### D5：协议 `PageScrollPayload.thinkMs`（三处同步）
edge/cloud 两份 `protocol.ts` 给 `PageScrollPayload` 加可选 `thinkMs?:number`（逐字一致）+ `docs/protocol.md` 同步说明。
- **为何**：协议 v2 铁律；`npm run typecheck` 穷举校验，漂移即失败。

### D6：edge `page.scroll` honor `thinkMs`
`browse-session.ts:425-431` 在 `scrollNext` 前，若 `payload.thinkMs` 存在则 `thinkBefore(jitter(thinkMs))`；缺失按现状（无额外等待，向后兼容）。
- **为何**：边缘只叠抖动消费中心值；旧云端不带字段时行为不劣化。

## Risks / Trade-offs

- [手势提速可能让返回过快、像脚本] → D1 仍保留轻量 jitter 手势停顿（非零），且停留下限仍由 dwell 守；实际感知是「读够了→快速返回」，符合真人。可在 acceptance 钉「back_to_feed 仍有非零手势停顿」。
- [seenFraction 误判：卡片顺序/虚拟列表导致同 noteId 重复或漏标] → 以 noteId 去重；`markCardSeen` 幂等（Set）；seenFraction 只驱动「调小」方向，最坏退化为全量节奏（不会更慢于现状）。
- [协议三处漂移] → 严格三处同步 + `npm run typecheck` + AC-PROTO-* 必过。
- [削错对象：误把刚读笔记 dwell 也缩了 → 秒退回归] → D1/D3 严格只动 feed-scroll think 与返回手势，**不碰 `dwellForCurrentNote('read')` / `ensureDetailDwell`**；acceptance 保留「带 dwellMs 的无价值详情页不秒退」。
- [K 折扣曲线未校准] → 先用保守 `K=0.6` + floor，依真实日志的返回-重扫节奏迭代；列 Open Questions。

## Migration Plan

1. cloud：D2（session-context）→ D3（pacing）→ D4（bridge）→ D5（cloud protocol.ts）→ role-dispatcher 挂 thinkMs；`npm run typecheck`。
2. edge：D5（edge protocol.ts，与 cloud 逐字一致）→ D6（page.scroll honor）→ D1（navigateBack 手势）；`npm run typecheck`。
3. docs：`docs/protocol.md` 同步 `PageScrollPayload.thinkMs`。
4. 回归：两仓 `npm run test:acceptance`（含 AC-PROTO-* / 秒退红线）→ `npm test`。
5. 部署：cloud 改动按 §5 安全序列上 ECS；edge 本地运行。回滚：还原各处改动，无数据迁移（seen 集合仅内存）。

## Open Questions

- 折扣系数 `K` 与 floor 的取值，依真实返回-重扫日志校准。
- 「滑过未打开」与「打开过」是否应有**不同**折扣力度（打开过的折扣更狠）？当前 D2 单一 seen 集合，可后续分级。
- `search.scrolled` 是否同样接入重访感知（同构，本次 Non-Goal）。
- D1 轻量手势停顿是否需要可配置/接云端 tempo（当前定为纯 edge 手势层）。
