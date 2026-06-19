## 1. aidcp-cloud — 已评估卡片集合 + 跳过重复评估

- [ ] 1.1 `src/agents/session-context.ts`：新增 `_evaluatedNoteIds:Set<string>` + `markEvaluated(noteId)` / `isEvaluated(noteId)`；`reset()` 不重置（与 `_visitedNoteIds` 同口径，跨轮保持）（D1）
- [ ] 1.2 `src/agents/content-evaluator.ts` 候选过滤（:74-76）：改为 `!c.noteId || (!isVisited(c.noteId) && !isEvaluated(c.noteId))`（D2）
- [ ] 1.3 `src/agents/content-evaluator.ts`：在 `candidates.length===0` 早退之后、`decide(prompt)` 之前，对本批候选逐个 `markEvaluated(noteId)`（有 noteId 才标记）（D2）
- [ ] 1.4 保留候选空时 `no_valuable` 的 reason 字符串 `all_cards_visited`（含义扩展为「全已看过/已评估」，兼容现有断言）（D2）

## 2. 验证

- [ ] 2.1 content-evaluator 单测：已 `markEvaluated` 的卡片被排除 → 空候选 → `no_valuable`，且**断言未调用 LLM**（mock `llm.complete` 调用计数为 0）
- [ ] 2.2 content-evaluator 单测：连续两次 `evaluate` 同一批卡片 → 第二次走快路径（无 LLM）、立即 `no_valuable`
- [ ] 2.3 content-evaluator 单测：第二批含新卡片 → 仅新卡片进入候选并触发 LLM 评估
- [ ] 2.4 既有用例不回归（含 `已访问卡片被过滤 → all_cards_visited`）；`npm run typecheck` → `npm run test:acceptance` → `npm test`

## 3. 收尾与归档

- [ ] 3.1 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <commit-sha> 备注 -->`）
- [ ] 3.2 `openspec validate skip-revisited-feed-reeval --strict` 通过
- [ ] 3.3 cloud 改动按 §5 安全序列部署 ECS（含 healthcheck/回滚），部署后追加 `<!-- <date> deployed -->`
- [ ] 3.4 上线后用日志确认返回 feed 后是「立即滚动」（page.cards 后无 content_evaluator LLM 判定行即出 scroll）
- [ ] 3.5 `/opsx:archive` 归档（delta 合并进 `openspec/specs/browse-loop-resilience`）
