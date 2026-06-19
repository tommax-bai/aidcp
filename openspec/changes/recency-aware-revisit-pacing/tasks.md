> ⚠️ **阻塞（并发开发）**：实装期间发现 **edge 与 cloud 两仓均有他人未提交的 captcha WIP**（edge: overlay-monitor/login-modal-watcher/protocol/executeFollow 复检；cloud: ws-server `pauseEdge/resumeEdge`、protocol Captcha payload、role-dispatcher `canInteract` 风控闸、protocol-contract.test）。cloud WIP 当前**令 `npm run typecheck` 失败**（`test/like-command.test.ts` 的 `FakePusher` 未实现新 `pauseEdge/resumeEdge`），非本 change 所致。故本 change 代码已落地+我的文件 typecheck 干净+定向测试全过，但**未提交**（避免与并发 WIP 纠缠 / 不在 broken 树上提交）。

- [x] 1.1 `src/agents/session-context.ts`：有界近期已评估集合（cap 30，淘汰最旧）+ `markEvaluated` / `isRecentlyEvaluated`；`reset()` 不重置（D1）<!-- aidcp-cloud uncommitted（并发 WIP 同树）-->
- [x] 1.2 `src/agents/content-evaluator.ts`：`_evaluate` 在 emit 之后对本批候选 `markEvaluated`；**候选过滤 `!isVisited` 不变**（二次评估保留）（D2）<!-- aidcp-cloud uncommitted -->
- [x] 1.3 `src/risk/pacing.ts`：`ThinkInput.familiar?`；familiar 时 `×FAMILIAR_DISCOUNT(1/3)` 夹 `THINK_FLOOR_MS(150)`；`computeDwellMs` 不接 familiar（D3）<!-- aidcp-cloud uncommitted -->
- [x] 1.4 `src/orchestrator/role-dispatcher.ts`：`thinkNow(familiar)` + `content.valuable → open_note` 按 `isRecentlyEvaluated(noteId)` 传 familiar（emit 同步 → 首开全量、返回再开 1/3）（D3）<!-- aidcp-cloud uncommitted -->

## 2. aidcp-edge — 返回 back_to_feed 手势 + 落地折扣

- [x] 2.1 `src/browse/browse-session.ts` `navigateBack(targetPage, reason)`：`reason==='back_to_feed' && !wantSearch` 时手势用 `cardGapTiming`（≈action 的 1/3、带抖动非零）+ `history.back` 后 sleep 800→300（D4）<!-- aidcp-edge uncommitted（并发 WIP 同树）-->
- [x] 2.2 未碰 `ensureDetailDwell`（笔记 dwell）与 404/坏页兜底；非 back_to_feed / 回搜索路径时序不变（D4）<!-- aidcp-edge uncommitted -->

## 3. 验证

- [x] 3.1 cloud 单测：`computeThinkMs` familiar→≈1/3 且 ≥150 下限、全新→全量、`computeDwellMs` 不受 familiar 影响（pacing 11/11）；定向跑 pacing+content-evaluator+role-dispatcher 30/30 全过 <!-- 我的文件 typecheck 干净；全量 typecheck 被并发 cloud WIP（FakePusher）阻塞 -->
- [ ] 3.2 cloud 单测：返回后二次评估仍发生（候选过滤未排除 evaluated）<!-- 结构上已保留（仅新增 markEvaluated，未改 filter）；待补显式断言 -->
- [ ] 3.2b 待并发 WIP 落定（FakePusher 修复、typecheck 恢复绿）后补 edge navigateBack 测试 + 全量回归
- [ ] 3.3 edge 单测/acceptance：back_to_feed 手势停顿 ≈1/3 且非零、非 back_to_feed 不变、笔记 dwell/坏页兜底不回归；command-pacing「杜绝秒退」红线全过
- [ ] 3.4 两仓 `npm run typecheck` → `npm run test:acceptance` → `npm test`

## 4. 收尾与归档

- [ ] 4.1 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <commit-sha> 备注 -->`）
- [ ] 4.2 `openspec validate recency-aware-revisit-pacing --strict` 通过
- [ ] 4.3 cloud（+edge 若需）改动按 §5 安全序列部署 ECS，部署后追加 `<!-- <date> deployed -->`
- [ ] 4.4 上线后用 ECS 日志校准 `FAMILIAR_DISCOUNT` / 下限 / recency 窗口，并确认返回后续刷更快
- [ ] 4.5 `/opsx:archive` 归档（delta 合并进 `openspec/specs/command-pacing`）
