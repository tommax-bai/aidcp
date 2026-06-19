## Why

返回 feed 后的操作慢，且与「这页内容是否刚刚看过」无关——拟人化在**时长维度**上没有「看过没看过」的概念。实测：打开一篇笔记、返回后，可见卡片与打开前是**同一批**，系统却按「第一次见」的全量节奏重新扫读。

慢的两个可优化来源（经代码核实）：
1. **返回手势的重复全量犹豫**：edge `navigateBack()` 在 `ensureDetailDwell()` 已满足该笔记停留下限**之后**，又叠一段固定 `humanPause(actionTiming)`（中位 ~2.5s）才 `history.back()`。停留时长已由 dwell 治理，这第二段全量犹豫属重复计费——是返回链路的**主要固定成本**。
2. **feed 重扫无重访感知**：`feed.scrolled → scroll(feed_scroll)` 指令**不带任何 thinkMs**；而真人对**已看过**的卡片会快速扫过、只在**新出现**的卡片上慢下来。系统虽有「已访问笔记」集合（`SessionContext._visitedNoteIds`），但只用于**要不要打开**的决策，从不参与节奏，且只记「打开过的笔记」、不记「feed 上滑过的卡片」。

注意保留的合法停留：刚读过那篇笔记的 dwell 补足（治「无价值秒退」）**不在削减范围**——你确实读了它。

## What Changes

- **edge**：`navigateBack()` 的 `back_to_feed` 路径**不再**在 `ensureDetailDwell()` 之后叠加全量 `humanPause(actionTiming)`；改用一段**轻量手势停顿**（小幅 jitter），因为停留已由 dwell 治理，避免二次全量犹豫。其他返回路径（如回搜索结果）按现状保留或单独评估。
- **cloud**：`SessionContext` 新增**卡片级 seen 集合**（区别于「打开过的笔记」），每次 `page.cards.arrived` 标记可见卡片 noteId；新增「这批卡片已看过比例」查询。
- **cloud**：`pacing.ts` 为 **feed 滚动**引入重访维度——按「即将划走的可见卡片已看过比例」把 `thinkMs` 中心值**调小**（全新卡片仍给全量）。`feed.scrolled` 处理（`role-dispatcher.ts:296-298`）据此给 `scroll` 指令挂上 `thinkMs`。
- **cloud**：修 `command-bridge.ts:22-23`——`scroll` 当前**只转发 `{reason}`、静默丢弃 `params`**；改为同时转发 `params`（否则上面挂的 `thinkMs` 到不了边缘）。
- **协议（BREAKING-ish，需三处同步）**：`PageScrollPayload` 增加可选 `thinkMs`（edge/cloud 两份 `protocol.ts` 逐字一致 + `docs/protocol.md`），`npm run typecheck` 把关。
- **edge**：`page.scroll` handler（`browse-session.ts:425-431`）读取可选 `payload.thinkMs`，执行滚动前 `thinkBefore(thinkMs)` 叠 lognormal 抖动；缺失则按现状（无额外等待）。中心值仍在云端，边缘只叠抖动。

## Capabilities

### New Capabilities
<!-- 无新增 capability -->

### Modified Capabilities
- `command-pacing`: 扩展「决策指令携带可选时间指令」以纳入 feed `page.scroll` 的可选 `thinkMs`；新增「重访 feed 的节奏感知（已看过卡片更快扫过）」与「已满足停留的返回手势不重复全量犹豫」两条要求。

## Impact

- **edge（aidcp-edge）**：`src/browse/browse-session.ts`（`navigateBack` 的 back_to_feed 路径、`page.scroll` handler）；`src/comm/protocol.ts`（`PageScrollPayload.thinkMs`）。
- **cloud（aidcp-cloud）**：`src/agents/session-context.ts`（seen-card 集合）；`src/orchestrator/role-dispatcher.ts`（`page.cards.arrived` 标记 seen、`feed.scrolled` 挂 thinkMs）；`src/risk/pacing.ts`（feed-scroll 重访感知中心值）；`src/comm/command-bridge.ts`（scroll 转发 params）；`src/comm/protocol.ts`（`PageScrollPayload.thinkMs`，与 edge 逐字一致）。
- **docs**：`docs/protocol.md`（`PageScrollPayload` 字段说明，协议三处同步之一）。
- **风险面**：协议改动须 AC-PROTO-* 不漂移；feed 重扫提速不得波及「刚读笔记 dwell」与「详情页非零停留」既有红线；`search.scrolled` 类似但本次默认不改（列 Non-Goal）。
