## 1. aidcp-cloud — seen 集合与重访感知中心值

- [ ] 1.1 `src/agents/session-context.ts`：新增 `_seenCardIds:Set<string>` + `markCardSeen(noteId)` / `isCardSeen(noteId)` / `seenFractionOf(cards)`；保留 `_visitedNoteIds` 不变（D2）
- [ ] 1.2 `src/orchestrator/role-dispatcher.ts` `page.cards.arrived`（:393-396）：对每张可见卡片 `markCardSeen`（D2）
- [ ] 1.3 `src/risk/pacing.ts`：新增 feed-scroll `thinkMs` 中心值计算，按 `seenFraction` 单调调小 + 非零 floor（K 默认 0.6，可调）（D3）
- [ ] 1.4 `src/orchestrator/role-dispatcher.ts` `feed.scrolled`（:296-298）：用当前可见卡片 `seenFractionOf` 计算 `thinkMs`，挂到 `scroll` 指令 `params.thinkMs`（全新页则全量/不挂）（D3）
- [ ] 1.5 `src/comm/command-bridge.ts:22-23`：`scroll` 映射改为 `{ reason: command.reason, ...command.params }`，转发 params（D4）

## 2. 协议三处同步 — PageScrollPayload.thinkMs

- [ ] 2.1 `aidcp-cloud/src/comm/protocol.ts`：`PageScrollPayload` 加可选 `thinkMs?:number`
- [ ] 2.2 `aidcp-edge/src/comm/protocol.ts`：同上，与 cloud **逐字一致**
- [ ] 2.3 `docs/protocol.md`：`PageScrollPayload` 字段说明同步（协议三处同步之一）
- [ ] 2.4 两仓 `npm run typecheck` 通过（`Record<MessageType,true>` 穷举不漂移，AC-PROTO-* 绿）

## 3. aidcp-edge — 返回手势 + page.scroll honor thinkMs

- [ ] 3.1 `src/browse/browse-session.ts` `navigateBack()` 的 `back_to_feed` 路径：移除 `ensureDetailDwell` 之后的全量 `humanPause(actionTiming)`，改轻量手势停顿（非零、带 jitter）（D1）
- [ ] 3.2 `src/browse/browse-session.ts` `page.scroll` handler（:425-431）：若 `payload.thinkMs` 存在则 `thinkBefore(jitter(thinkMs))` 再 `scrollNext`；缺失按现状（D6）
- [ ] 3.3 确认非 back_to_feed 的返回路径（如回搜索结果）行为未被误改

## 4. 验证与归档

- [ ] 4.1 cloud 单测：seen 集合标记/比例、feed-scroll thinkMs 随 seenFraction 调小且有 floor、bridge 转发 params；`npm run test:acceptance` → `npm test`
- [ ] 4.2 edge 单测/acceptance：page.scroll honor thinkMs（叠抖动、缺失不劣化）、back_to_feed 仍非零手势停顿、详情页不秒退（红线不回归）；`npm run test:acceptance` → `npm test`
- [ ] 4.3 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <commit-sha> 备注 -->`）
- [ ] 4.4 `openspec validate revisit-aware-feed-pacing --strict` 通过
- [ ] 4.5 cloud 改动按 §5 安全序列部署 ECS（含 healthcheck/回滚），部署后追加 `<!-- <date> deployed -->`
- [ ] 4.6 `/opsx:archive` 归档（delta 合并进 `openspec/specs/command-pacing`）
