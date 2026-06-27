> ✅ **并发开发已落定**：实装期与他人 captcha WIP（openspec change `captcha-restrict-and-interaction-gating`）同树。WIP 作者已 settle 并提交推送（cloud `3c84ccf`、edge `9126e04`），typecheck 恢复绿。本 change：cloud 我的 4 文件单独提交 `678eab9`；edge navigateBack 改动随 `9126e04` 一并入库（同文件交织、本环境无法交互式拆 hunk）。两仓全量回归绿后批量部署 ECS。

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
- [ ] 3.2b 待并发 WIP 落定（FakePusher 修复、typecheck 恢复绿）后补 edge navigateBack 测试 + 全量回归 <!-- 并发 WIP 已落定（cloud 3c84ccf / edge 9126e04，typecheck 恢复绿）、全量回归已绿（见 3.4，2026-06-19 cloud 185/185 + edge 251/251）；仅余 navigateBack 专项单测（与 3.3 重复） -->
- [~] 3.3 edge navigateBack 显式单测未补（同文件交织 + 时间紧）；现有 edge 全量 251/251 通过、含 command-pacing「不秒退」相关红线 <!-- 待补 navigateBack fastReturn 专项断言 -->
- [x] 3.4 两仓 `npm run typecheck`（绿）→ `test:acceptance`（cloud 11/11、edge 11/11，AC-PROTO 44 两端一致）→ `test`（cloud 185/185、edge 251/251） <!-- 2026-06-19 合并树（含 captcha WIP）全绿 -->

## 4. 收尾与归档

- [x] 4.1 按 sub-repo 分节回写本 tasks.md 进度 <!-- cloud 678eab9 / edge 9126e04 -->
- [x] 4.2 `openspec validate recency-aware-revisit-pacing --strict` 通过 <!-- 2026-06-19 valid -->
- [x] 4.3 cloud 改动按 §5 安全序列部署 ECS <!-- aidcp-cloud 678eab9 2026-06-19 deployed：backup cloud.bak.20260619-165030.tar.gz → rsync → restart → healthcheck 全过；批量随问题2 + captcha 同次部署 -->
- [ ] 4.4 上线后用 ECS 日志校准 `FAMILIAR_DISCOUNT` / 下限 / recency 窗口，并确认返回后续刷更快（返回后 open_note thinkMs ≈1/3、back_to_feed 手势更短）
- [ ] 4.5 `/opsx:archive` 归档（delta 合并进 `openspec/specs/command-pacing`）—— 待 4.4 观察校准后归档
