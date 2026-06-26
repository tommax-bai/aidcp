## 1. 协议三处同步 — NoteDetailPayload.authorFollowed

- [x] 1.1 `aidcp-cloud/src/comm/protocol.ts`：`NoteDetailPayload` 加可选 `authorFollowed?: boolean` <!-- aidcp-cloud d84de12 -->
- [x] 1.2 `aidcp-edge/src/comm/protocol.ts`：同上，与 cloud **逐字一致** <!-- aidcp-edge d6fb112 NoteDetailPayload 块两仓 diff 验证逐字一致 -->
- [x] 1.3 `docs/protocol.md`：`NoteDetailPayload` 字段说明同步 <!-- aidcp (中控) 本次提交 -->
- [x] 1.4 两仓 `npm run typecheck`；`test:acceptance` 确认 AC-PROTO 消息总数仍 44（仅加字段、不增消息类型） <!-- edge typecheck 全绿；cloud 仅加字段 my-files 全部 type-clean（cloud 全量 typecheck 失败项均为并发 WIP publish-multi-image/session-limits，非本改动）。AC-PROTO 现役断言为 56（非 44，协议自 06-19 已增长）；仅加字段→保持 56 不变、AC-PROTO 5/5 绿、无漂移 -->

## 2. aidcp-edge — note.open 探测关注态

- [x] 2.1 `src/browse/browse-session.ts` `openCard`（~600-676）：上报 `note.detail` 前探测 modal 作者区关注按钮（复用 `executeFollow` 选择器 + `已关注/互关/aria-pressed` 判定），得 `authorFollowed` <!-- aidcp-edge d6fb112 抽出共享常量 FOLLOW_BUTTON_SELECTORS；新增 probeAuthorFollowed 逐字镜像 executeFollow 扫描，检测口径完全一致 -->
- [x] 2.2 在 `NoteDetailPayload` 上回填 `authorFollowed`；探测不到时缺省（falsy） <!-- aidcp-edge d6fb112 openCard 总置布尔（未探到=false=falsy）；note.detail 日志带 [已关注] 便于真机核验 -->
- [x] 2.3 edge 单测：note.detail 携带 `authorFollowed`（已关注→true、未关注→false/缺省） <!-- aidcp-edge d6fb112 新增 2 测；edge full 362/362 绿 -->

## 3. aidcp-cloud — NoteData 透传 + AuthorEvaluator 提前 skip

- [x] 3.1 `src/orchestrator/role-dispatcher.ts`：`NoteData` 加 `authorFollowed?: boolean`；`updateNoteData` 从 `note.detail` 透传 <!-- aidcp-cloud d84de12 两份 NoteData（role-dispatcher.ts + content-curator-role.ts）均加字段；updateNoteData(payload.detail) 同对象透传，无需额外代码 -->
- [x] 3.2 `src/agents/author-evaluator.ts` `onInteractionCompleted`：取到 `noteData` 后、调 LLM 前，若 `authorFollowed===true` → `emit profile.skipped`（reason `already_followed`）并返回 <!-- aidcp-cloud d84de12 偏离说明：现役入口非 onInteractionCompleted 而是 onCommentResolved（订阅 comment.done/comment.skipped）；闸加在 author_unknown 之后、buildPrompt 之前；并修正文件头过期注释 -->
- [x] 3.3 cloud 单测：`authorFollowed=true` → AuthorEvaluator 不调 LLM、emit profile.skipped(already_followed)、不产 profile.worth_visiting；`false/缺省` → 原评估流程 <!-- aidcp-cloud d84de12 新增 2 测（true→skip 无 LLM；false→走 LLM）；既有「缺省」由原有用例覆盖 -->

## 4. 验证与归档

- [x] 4.1 两仓 `npm run typecheck` → `test:acceptance`（AC-PROTO 不漂移）→ `test` <!-- edge: typecheck 绿 + acceptance 11/11 + full 362/362。cloud: 受并发 WIP（publish-multi-image/session-limits 未编译）阻塞、无法全量绿；本改动 my-files type-clean，scoped 全绿：AC-PROTO 5/5、author-evaluator + role-dispatcher 集成 + profile-opener + back-to-feed 42/42、agents+integration 全量 185/185 -->
- [x] 4.2 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <commit-sha> 备注 -->`） <!-- 本次 -->
- [x] 4.3 `openspec validate skip-profile-visit-if-followed --strict` 通过 <!-- "Change 'skip-profile-visit-if-followed' is valid" -->
- [x] 4.4 cloud 改动按 §5 安全序列部署 ECS（含 healthcheck/回滚），部署后追加 `<!-- <date> deployed -->` <!-- aidcp-cloud d84de12 2026-06-26 deployed：ECS 原在 c1e00b0，仅本改动为运行时 delta；外科 rsync 4 src 文件（clean export，未带并发 WIP，ECS sessionLimitProvider=0 已验）；备份 cloud.bak.20260626-094923.tar.gz + .env.bak.20260626-094923；healthcheck 全绿（active/NRestarts=0/8787/飞书长连接 onReady/PG select 1/无启动错误）；新码 grep 实测生效（role-dispatcher authorFollowed=1） --> <!-- 2026-06-26 deployed -->
- [ ] 4.5 真机确认：打开一篇已关注作者的笔记 → 互动后不再进主页/不再尝试关注（日志无 profile.open / follow）
- [ ] 4.6 `/opsx:archive` 归档（delta 合并进 `openspec/specs/author-profile-visit`）
