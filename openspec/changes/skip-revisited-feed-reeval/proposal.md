## Why

返回 feed 后，卡片已经出来了却要**干等一段时间才开始滚动**——这段等待没必要。

经代码核实：返回 feed 时 edge 上报 `page.cards` → cloud `page.cards.arrived` → `ContentEvaluator.evaluate()` 跑**一次 LLM 评估**判断要不要点开某张卡片，之后才（对全不值得的情况）`content.no_valuable → feed.scrolled → scroll`。`content.no_valuable → 滚动` 这一段本身是即时的（无 dwell / thinkMs）；**唯一的等待就是那次 LLM 评估往返**。

而这次评估是**重复**的：`ContentEvaluator` 的候选过滤只排除 `isVisited`（真正**打开过**的笔记，`content-evaluator.ts:74-76`），`isVisited` 仅在 `note.detail.arrived` 时标记（`note-opener.ts`）。所以返回后，那几张「之前在 feed 上可见、但没点开」的卡片**仍是候选** → `candidates.length>0` → 又跑一遍完整 LLM。可这批卡片在你点开笔记**之前就已经评估过一次**了。

仅当候选为空（全 `isVisited`）时 `_evaluate` 才会**不调 LLM** 立即 `no_valuable`（`content-evaluator.ts:78-85`）——这正是我们想要的快路径，但它今天只覆盖「打开过的笔记」，覆盖不到「只看过、没打开」的卡片。

## What Changes

- **cloud**：`SessionContext` 新增**已评估卡片集合** `_evaluatedNoteIds` + `markEvaluated(noteId)` / `isEvaluated(noteId)`（跨轮次保持，与 `_visitedNoteIds` 一致）。
- **cloud**：`ContentEvaluator._evaluate` 的候选过滤在排除 `isVisited` 之外**同时排除 `isEvaluated`**；并在确认候选非空、即将评估时，把这批候选 `markEvaluated`（保证每张卡片整个会话**至多触发一次** LLM 评估）。
- **效果**：返回 feed 后可见卡片若都已评估过（典型情况）→ 候选为空 → **立即 `no_valuable` → 立即滚动，零 LLM 等待**；滚动后出现的**新卡片**仍照常 LLM 评估。
- **不动协议、不动 edge、不动 bridge、不改节奏（thinkMs/dwell）**——返回慢的成因是 LLM 重复评估，不是滚动节奏，也不是返回手势。

## Capabilities

### New Capabilities
<!-- 无新增 capability -->

### Modified Capabilities
- `browse-loop-resilience`: 新增「返回 feed 后不重复评估已看过的卡片」要求——返回 feed 的续刷在可见卡片均已评估过时 SHALL 立即滚动而不重跑 LLM 评估；新出现的卡片仍照常评估。

## Impact

- **cloud（aidcp-cloud）**：`src/agents/session-context.ts`（`_evaluatedNoteIds` + markEvaluated/isEvaluated）；`src/agents/content-evaluator.ts`（候选过滤排除 evaluated + 评估前标记 evaluated）。
- **edge / 协议 / docs**：无改动。
- **行为变化（须知会）**：一屏 feed 卡片整个会话**至多被 LLM 评估一次**；即「同一屏只产出至多一次点开决策」，返回后不再回头从同屏挑第二张，而是滚动到新内容。这与「返回后快速移动到新内容」的拟人直觉一致（见 design 的 trade-off）。
- **风险面**：纯 cloud 决策侧；不触红线（不静默假成功/失败、不改风控、不改协议）；`all_cards_visited` 这个 no_valuable reason 含义扩展为「全已看过/已评估」，保留字符串不变以兼容现有断言。
