## Context

实测（ECS journald，两个返回周期）耗时构成：
- `back` 命令→完成 ≈ 7~8s（边缘返回执行：`humanPause(actionTiming)` 中位 ~2.5s + 刚读笔记 dwell 兜底 + `sleep(800)` + feed 重新水合）。
- `back` 完成→首个 `scroll` ≈ ~1s（云端 `ContentEvaluator` 一次 LLM 评估，`content.no_valuable → FeedScroller → feed.scrolled → scroll` 即时）。
- 后续 评估→scroll ≈ ~1s/次。

结论：**云端决策快（~1s）；返回周期的"秒级"等待几乎全在边缘返回执行**。`content.no_valuable → scroll` 无 dwell/thinkMs；`open_note` 带 `thinkMs = thinkNow() = computeThinkMs({status, progress})`（`pacing.ts:102` = `THINK_BASE_MS(700)·tempo·fatigue`）。返回 feed 必然回到打开笔记前的同一批可见卡片（feed 未滚动）→ 这批卡片是"刚刚评估过的熟悉内容"。

`SessionContext` 现有 `_visitedNoteIds`（打开过的笔记）+ `markVisited/isVisited`，`reset()` 不重置。缺"近期已评估"的有界 recency 概念。

## Goals / Non-Goals

**Goals:**
- 拟人化：熟悉内容（近期已评估，约最近 30 个）→ 思考更快 → 可调"思考/犹豫"时长 ×≈1/3。
- 覆盖两条返回后分支：滚动分支（缩边缘返回执行的 humanPause + sleep）、点开分支（缩 open_note 的 thinkMs）。
- 保留二次评估（返回后仍能点开下一个值得看的卡片）。
- 节奏中心值收口云端（thinkMs 折扣在云端算）；边缘手势时序折扣是边缘自带层。

**Non-Goals:**
- **不跳过 / 不复用 LLM 评估**（用户明确要保留二次评估）。
- **不削减刚读笔记 dwell**（红线，治秒退）。
- 不动协议、不动 command-bridge。
- 不改 `search.scrolled`（同构，留待后续）。

## Decisions

### D1：SessionContext 有界近期已评估集合
加 `markEvaluated(noteId)` / `isRecentlyEvaluated(noteId)`，底层为**有界 recency**（约最近 30 个 noteId，超出淘汰最旧；如保序数组 + Set，或带序号的 Map 取末 N）。`reset()` 不清（跨轮保持，进程级生命周期）。
- **为何**：state 单写云端（边轻云重）。有界=模型"近期记忆"，老内容"淡忘"后不再享折扣，符合用户"最近 30 个"语义。

### D2：ContentEvaluator 只标记、不改候选过滤（保留二次评估）
`_evaluate` 在评估候选时对其 `markEvaluated(noteId)`；**候选过滤保持 `!isVisited` 不变**（不加 `isEvaluated` 排除）→ 返回后 LLM 仍正常评估、能点开下一个值得看的卡片。
- **为何**：用户要保留二次评估。recency 集合仅用于"算折扣"，不用于"跳过评估"。

### D3：computeThinkMs 增"熟悉"折扣
`ThinkInput` 加可选 `familiar?: boolean`（或 `discount?: number`）；familiar 时 `thinkMs ×= FAMILIAR_DISCOUNT(≈1/3)`，并夹一个非零下限 `THINK_FLOOR_MS`。`role-dispatcher.thinkNow(familiar)` 透传；`content.valuable → open_note` 时按 `ctx.isRecentlyEvaluated(payload.noteId)` 决定 familiar。其余带 thinkMs 的动作（profile_open / interaction / scroll_comments / follow）可同口径按目标 noteId 判 familiar（有 noteId 才判）。
- **为何**：中心值收口云端；熟悉→快、全新→全量。下限杜绝秒退。
- **dwellMs 不变**：`computeDwellMs` 不接 familiar，刚读笔记停留不被折扣。

### D4：edge 返回 back_to_feed 的手势 + settle 折扣
`navigateBack` 当 `reason==='back_to_feed'`：`humanPause(actionTiming)` 改用 ≈1/3 的折扣停顿（带非零下限）；`history.back` 之后的固定 `sleep(800)` 缩短（feed 已水合时）/ 冗余等待收敛。仍保留非零手势停顿与"返回后健康校验"（坏页兜底不动）。
- **为何**：back_to_feed 必然返回刚看过的熟悉 feed → 等价于"近期已评估"，可直接按 reason 判定，无需新协议字段。停留已由 dwell 治理（在 navigateBack 之前的 `ensureDetailDwell`），返回手势不必再全量犹豫。
- **红线**：保留非零下限；不动 `ensureDetailDwell`（笔记 dwell）、不动 404/坏页兜底。

## Risks / Trade-offs

- [折扣到 1/3 后返回过快、像脚本] → 各处保留非零下限（thinkMs floor + 手势 floor）；叠 lognormal 抖动；停留仍由 dwell 守。可按上线日志校准 FAMILIAR_DISCOUNT 与下限。
- [familiar 误判：同 noteId 在 recency 窗口内外] → 有界 recency 命中即折扣，未命中按全量——最坏退化为现状（不会更慢）；幂等 Set。
- [edge 折扣误伤非 back_to_feed 返回（如回搜索结果）] → D4 严格只在 `reason==='back_to_feed'` 生效；其他返回路径不变。
- [削错对象→秒退回归] → 严格不碰 `computeDwellMs` / `ensureDetailDwell`；acceptance 保留 command-pacing"杜绝秒退"红线用例。
- [LLM 评估 ~1s 仍在] → 这是保留二次评估的固有成本（用户接受）；本 change 不动它，只压边缘返回执行与动作 thinkMs。

## Migration Plan

1. cloud：D1（session-context）→ D2（content-evaluator 标记）→ D3（pacing computeThinkMs + role-dispatcher thinkNow/open_note）；`npm run typecheck`。
2. edge：D4（navigateBack back_to_feed 折扣 + settle）；`npm run typecheck`。
3. 回归：两仓 `npm run test:acceptance`（含 command-pacing 秒退红线、AC-PROTO 不漂移）→ `npm test`。
4. 部署：cloud 按 §5 安全序列上 ECS；edge 本地运行。回滚：还原各处，无数据迁移（recency 仅内存）。

## Open Questions

- `FAMILIAR_DISCOUNT`（默认 1/3）与各下限（thinkMs floor、手势 floor）取值，依上线日志校准。
- recency 窗口大小（默认 ~30）是否合适？
- 是否对 `search.scrolled` / 回搜索结果路径同样应用（本次 Non-Goal）。
- 除 open_note 外，profile_open/interaction/follow 的 thinkMs 是否也按 familiar 折扣？（默认一并，按目标 noteId 判定；follow/profile 以 authorId 为主，可暂不折扣——实装时定。）
