## 1. 协议三处同步 — NoteDetailPayload.authorFollowed

- [ ] 1.1 `aidcp-cloud/src/comm/protocol.ts`：`NoteDetailPayload` 加可选 `authorFollowed?: boolean`
- [ ] 1.2 `aidcp-edge/src/comm/protocol.ts`：同上，与 cloud **逐字一致**
- [ ] 1.3 `docs/protocol.md`：`NoteDetailPayload` 字段说明同步
- [ ] 1.4 两仓 `npm run typecheck`；`test:acceptance` 确认 AC-PROTO 消息总数仍 44（仅加字段、不增消息类型）

## 2. aidcp-edge — note.open 探测关注态

- [ ] 2.1 `src/browse/browse-session.ts` `openCard`（~600-676）：上报 `note.detail` 前探测 modal 作者区关注按钮（复用 `executeFollow` 选择器 + `已关注/互关/aria-pressed` 判定），得 `authorFollowed`
- [ ] 2.2 在 `NoteDetailPayload` 上回填 `authorFollowed`；探测不到时缺省（falsy）
- [ ] 2.3 edge 单测：note.detail 携带 `authorFollowed`（已关注→true、未关注→false/缺省）

## 3. aidcp-cloud — NoteData 透传 + AuthorEvaluator 提前 skip

- [ ] 3.1 `src/orchestrator/role-dispatcher.ts`：`NoteData` 加 `authorFollowed?: boolean`；`updateNoteData` 从 `note.detail` 透传
- [ ] 3.2 `src/agents/author-evaluator.ts` `onInteractionCompleted`：取到 `noteData` 后、调 LLM 前，若 `authorFollowed===true` → `emit profile.skipped`（reason `already_followed`）并返回
- [ ] 3.3 cloud 单测：`authorFollowed=true` → AuthorEvaluator 不调 LLM、emit profile.skipped(already_followed)、不产 profile.worth_visiting；`false/缺省` → 原评估流程

## 4. 验证与归档

- [ ] 4.1 两仓 `npm run typecheck` → `test:acceptance`（AC-PROTO 不漂移）→ `test`
- [ ] 4.2 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <commit-sha> 备注 -->`）
- [ ] 4.3 `openspec validate skip-profile-visit-if-followed --strict` 通过
- [ ] 4.4 cloud 改动按 §5 安全序列部署 ECS（含 healthcheck/回滚），部署后追加 `<!-- <date> deployed -->`
- [ ] 4.5 真机确认：打开一篇已关注作者的笔记 → 互动后不再进主页/不再尝试关注（日志无 profile.open / follow）
- [ ] 4.6 `/opsx:archive` 归档（delta 合并进 `openspec/specs/author-profile-visit`）
