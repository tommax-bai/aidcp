## Context

返回 feed 的浏览闭环（已核实）：edge `navigation.back(back_to_feed)` → `history.back` + 等待水合 → 上报 `page.cards` → cloud `page.cards.arrived`（`role-dispatcher.ts:393-396`）→ `updateVisibleCards` + `ContentEvaluator.evaluate()` → 评估出 `content.valuable`（点开）或 `content.no_valuable`（不值得）→ `FeedScroller.handleNoValuable`（`feed-scroller.ts:42-66`）即时 `feed.scrolled` → `role-dispatcher.ts:296` 即时 `sendCommand(scroll)`。

`content.no_valuable → scroll` 全程**无 dwell / 无 thinkMs**（page.scroll handler 也是 lean 路径）。所以「返回后干等才滚动」的**唯一**成因是 `ContentEvaluator._evaluate` 里那次 LLM 往返（`content-evaluator.ts:88-91 this.decide(prompt)`）。

`_evaluate` 已有快路径：候选为空时 `emit no_valuable('all_cards_visited')` **不调 LLM**（:78-85）。但候选过滤只看 `isVisited`（:74-76），而 `isVisited` 仅 `note.detail.arrived` 时标记（只覆盖**打开过**的笔记）。返回后那批「看过但没打开」的卡片仍是候选 → 走 LLM → 等待。

`SessionContext`（`session-context.ts`）已有 `_visitedNoteIds` + `markVisited`/`isVisited`，`reset()` 不重置（跨轮保持）。缺一个「已评估」概念。

## Goals / Non-Goals

**Goals:**
- 消除返回 feed 后那段 LLM 重复评估等待：可见卡片若都已评估过 → 立即滚动。
- 新出现的卡片仍照常 LLM 评估（不牺牲对新内容的判断）。
- 纯 cloud、零协议改动、零 edge 改动。

**Non-Goals:**
- 不改滚动节奏（thinkMs/dwell）、不改返回手势——它们不是这次等待的成因。
- 不改 edge、不动协议、不动 command-bridge。
- 不引入跨会话持久化（evaluated 集合仅会话内，`reset()` 保持但进程级生命周期）。

## Decisions

### D1：SessionContext 增「已评估卡片集合」
加 `_evaluatedNoteIds:Set<string>` + `markEvaluated(noteId)` / `isEvaluated(noteId)`；`reset()` 与 `_visitedNoteIds` 同口径**不重置**（跨轮保持）。
- **为何**：state 单写在云端（边轻云重）。需要一个区别于「打开过的笔记」的「已评估卡片」集合，覆盖「看过没打开」的卡片。

### D2：ContentEvaluator 候选过滤排除 evaluated + 评估前标记
- 候选过滤（`content-evaluator.ts:74-76`）：`!c.noteId || (!isVisited(c.noteId) && !isEvaluated(c.noteId))`。
- 在 `candidates.length===0` 早退**之后**、调用 LLM **之前**，对本批候选逐个 `markEvaluated(noteId)`（有 noteId 才标记）。
- **为何**：先判空再标记，保证**首次**评估仍会跑；标记后，任何后续重现（返回、滚动重叠）都被排除 → 候选空 → 即时 `no_valuable` → 即时滚动。每张卡片整会话至多触发一次 LLM 评估。
- **reason 字符串**：候选空时仍 emit `no_valuable('all_cards_visited')`（含义扩展为「全已看过/已评估」），**保留字符串**以兼容现有测试断言（`content-evaluator.test.ts:179`）。

### D3：无 noteId 的卡片回退现状
无 `noteId` 的卡片（`!c.noteId`）继续始终作为候选（无法标记/识别）。
- **为何**：安全回退，最坏退化为现状（仍评估），不会更差。绝大多数 feed 卡片有 noteId。

## Risks / Trade-offs

- [行为变化：一屏卡片至多被评估一次 → 返回后不再回头从同屏挑第二张可点开的笔记] → 这是**有意**的，契合「读完一篇、返回后滚到新内容」的真人直觉，也正是用户诉求（返回别再等/再挑）。代价：若一屏恰有两篇都值得点开，第二篇本次不会被点开（滚动后会有新内容补上）。若日后要保留「同屏二次点开」，可改为「仅在 `no_valuable`（skip）时 markEvaluated、`valuable`（点开）那批不标记」——列 Open Questions。
- [标记时机：在 LLM 之前标记，若 LLM/打开失败这批仍被标记为已评估、不再重评] → 可接受且更稳（避免对同一失败批次反复重评/卡死）；失败后由现有 recovery-scroll / 看门狗推进。
- [evaluated 集合无限增长] → 单会话内卡片量有限（Set of noteId 字符串），内存可忽略；`reset()` 不清是为跨轮保持，进程重启自然清空。
- [并发评估] → `_evaluating` 守卫（`content-evaluator.ts:63`）已防一批 page.cards 触发多次并发评估，标记逻辑在 `_evaluate` 内不引入新竞态。

## Migration Plan

1. cloud：D1（session-context）→ D2（content-evaluator）；`npm run typecheck`。
2. 测试：content-evaluator 单测——已 evaluated 的卡片被排除、空候选即时 no_valuable（断言**不调 LLM**：mock llm.complete 计数为 0）、新卡片仍评估、保留 `all_cards_visited` reason；`npm run test:acceptance` → `npm test`。
3. 部署：cloud 按 §5 安全序列上 ECS。回滚：还原两文件即可，无数据迁移。

## Open Questions

- 是否要保留「同屏二次点开」？（改为仅在 skip 分支 markEvaluated）。默认按「一屏至多一次点开」推进，更快更像真人。
- evaluated 与 visited 是否合并为单一集合？当前分开更语义清晰（visited=打开过、evaluated=评估过，visited⊆evaluated），实现上 isVisited 已被 evaluated 覆盖，但保留两者便于未来分级。
