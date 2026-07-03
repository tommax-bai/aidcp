## Why

返回 feed 后"卡片已出来却干等才滚动"，希望缩短。实测 ECS 日志（两个完整返回周期）厘清了耗时构成：

- `back` 命令 → `back` 完成（**边缘返回执行**：`~2.5s humanPause` + 刚读笔记 dwell 兜底 + `0.8s sleep` + feed 重新水合）≈ **7~8s**；
- `back` 完成（卡片出现）→ 首个 `scroll`（**云端 LLM 评估**）≈ **~1s**；之后每次 评估→`scroll` ≈ **~1s**。

即：**云端决策已经很快（~1s），返回周期里"秒级"等待几乎全在边缘返回执行**（humanPause + dwell + sleep）。`history.back` 渲染卡片后，边缘还要跑完这些固定停顿才继续，观感就是"卡片在了却迟迟不滚"。

拟人化原则（已与用户对齐）：**熟悉的内容人思考更快**。返回 feed 必然回到刚刚看过的同一批卡片；对**近期已评估过**（如最近 30 个）的内容，应把可调的"思考 / 犹豫"时长降到约**常规的 1/3**。同时**保留二次评估**（返回后仍能点开下一个值得看的卡片），且**不削减刚读笔记的 dwell**（红线，治秒退）。

## What Changes

- **cloud**：`SessionContext` 维护**有界近期已评估集合**（约最近 30 个 noteId，按 recency，超出淘汰最旧）+ `markEvaluated(noteId)` / `isRecentlyEvaluated(noteId)`。`ContentEvaluator` 在每次评估时把候选 `markEvaluated`（**候选过滤不变 → 二次评估照常发生**，不跳过、不复用旧判定）。
- **cloud**：`computeThinkMs`（`pacing.ts`）支持"熟悉"折扣——目标内容近期已评估时，thinkMs 中心值 ×≈1/3（带非零下限）。`thinkNow(familiar)` 透传；`open_note` 等动作在目标卡 `isRecentlyEvaluated` 时按折扣下发。**dwellMs 不受影响**。
- **edge**：`navigation.back` 当 `reason==='back_to_feed'`（必然返回到刚看过的 feed）时，把返回手势 `humanPause(actionTiming)` 降到约 1/3（带非零下限），并缩短 `history.back` 之后的固定 `sleep(800)` 与冗余等待（feed 已水合时）。**保留非零下限，不秒退**。
- **不动协议**：thinkMs 已是既有协议字段；back 的 `reason` 已透传到边缘——两处折扣都无需新协议字段。

## Capabilities

### New Capabilities
<!-- 无新增 capability -->

### Modified Capabilities
- `command-pacing`: 新增「熟悉内容的思考时间按近期已评估折扣」（thinkMs ×≈1/3，有界 recency，dwell 不变）与「返回熟悉 feed 的手势与落地更快但不秒退」（back_to_feed 手势停顿与返回后 settle ×≈1/3，带非零下限）两条要求。

## Impact

- **cloud（aidcp-cloud）**：`src/agents/session-context.ts`（有界 recency 集合）；`src/agents/content-evaluator.ts`（仅 `markEvaluated`，候选过滤不变）；`src/risk/pacing.ts`（`computeThinkMs` 熟悉折扣 + 非零下限）；`src/orchestrator/role-dispatcher.ts`（`thinkNow(familiar)` + `open_note` 等按 `isRecentlyEvaluated` 折扣）。
- **edge（aidcp-edge）**：`src/browse/browse-session.ts`（`navigateBack` 的 back_to_feed 手势停顿与返回后 settle 折扣，带下限）。
- **协议 / docs**：无改动。
- **保留 / 红线**：二次评估（LLM）保留，不跳过/不复用；刚读笔记 dwell 不折扣；所有折扣保留非零下限，杜绝零延迟秒退（不触 command-pacing 既有"杜绝秒退"红线）。
