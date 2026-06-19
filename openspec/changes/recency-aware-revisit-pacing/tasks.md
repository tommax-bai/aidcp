## 1. aidcp-cloud — 有界近期已评估集合 + thinkMs 熟悉折扣

- [ ] 1.1 `src/agents/session-context.ts`：新增**有界近期已评估集合**（约最近 30，超出淘汰最旧）+ `markEvaluated(noteId)` / `isRecentlyEvaluated(noteId)`；`reset()` 不重置（跨轮保持）（D1）
- [ ] 1.2 `src/agents/content-evaluator.ts`：在 `_evaluate` 评估候选时对其 `markEvaluated(noteId)`；**候选过滤保持 `!isVisited` 不变**（保留二次评估，不加 isEvaluated 排除）（D2）
- [ ] 1.3 `src/risk/pacing.ts`：`computeThinkMs` 的 `ThinkInput` 增 `familiar?:boolean`（或 discount）；familiar 时中心值 ×`FAMILIAR_DISCOUNT(≈1/3)`，夹非零下限 `THINK_FLOOR_MS`；`computeDwellMs` 不接 familiar（dwell 不折扣）（D3）
- [ ] 1.4 `src/orchestrator/role-dispatcher.ts`：`thinkNow(familiar?)` 透传；`content.valuable → open_note`（:374）按 `ctx.isRecentlyEvaluated(payload.noteId)` 传 familiar；评估批标记由 ContentEvaluator 负责（D3）

## 2. aidcp-edge — 返回 back_to_feed 手势 + 落地折扣

- [ ] 2.1 `src/browse/browse-session.ts` `navigateBack`：当 `reason==='back_to_feed'` 时，返回手势 `humanPause(actionTiming)` 用 ≈1/3 折扣停顿（带非零下限），并缩短 `history.back` 后的固定 `sleep(800)` / 冗余等待（D4）
- [ ] 2.2 确认不碰 `ensureDetailDwell`（笔记 dwell）与 404/坏页健康校验兜底；非 back_to_feed 返回时序不变（D4）

## 3. 验证

- [ ] 3.1 cloud 单测：`computeThinkMs` familiar → ≈1/3 且 ≥ 下限；全新 → 全量；`computeDwellMs` 不受 familiar 影响；SessionContext 有界 recency（淘汰最旧 / isRecentlyEvaluated 命中与失效）；open_note 对近期已评估卡片下发折扣 thinkMs
- [ ] 3.2 cloud 单测：返回后二次评估仍发生（候选过滤未排除 evaluated，content-evaluator 仍对未 visited 候选评估）
- [ ] 3.3 edge 单测/acceptance：back_to_feed 手势停顿 ≈1/3 且非零、非 back_to_feed 不变、笔记 dwell/坏页兜底不回归；command-pacing「杜绝秒退」红线全过
- [ ] 3.4 两仓 `npm run typecheck` → `npm run test:acceptance` → `npm test`

## 4. 收尾与归档

- [ ] 4.1 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <commit-sha> 备注 -->`）
- [ ] 4.2 `openspec validate recency-aware-revisit-pacing --strict` 通过
- [ ] 4.3 cloud（+edge 若需）改动按 §5 安全序列部署 ECS，部署后追加 `<!-- <date> deployed -->`
- [ ] 4.4 上线后用 ECS 日志校准 `FAMILIAR_DISCOUNT` / 下限 / recency 窗口，并确认返回后续刷更快
- [ ] 4.5 `/opsx:archive` 归档（delta 合并进 `openspec/specs/command-pacing`）
