## 1. aidcp-edge — executeFollow 如实上报 + 检测增强

- [ ] 1.1 `src/browse/browse-session.ts` `executeFollow()`：探测 JS 在文案 `已关注 / 互关` 判定基础上叠加 `aria-pressed==='true'`（OR 关系，不替换文案判定）作为 already 命中条件（D3）
- [ ] 1.2 `executeFollow()` already 分支改为良性 no-op 成功：`reportActionCompleted({ action:'follow', ok:true, reason:'already_followed' })`，日志改为 `[browse] ✓ 已关注（无需重复关注）`（D1）
- [ ] 1.3 确认真实新关注成功路径上报 **不带 `reason`**（`{ action:'follow', ok:true }`），作为与 no-op 的区分契约（D2 衔接点）
- [ ] 1.4 确认真失败路径不变：`no-btn` → `{ ok:false, reason:'btn_no-btn' }`、异常 → `{ ok:false, reason: message }`（红线：不得把真失败报成成功）
- [ ] 1.5 edge 单测/acceptance：补「already_followed → ok:true + reason」「真实关注 → ok:true 无 reason」「no-btn → ok:false」三态用例；`npm run typecheck` → `npm run test:acceptance` → `npm test`

## 2. aidcp-cloud — 配额依真实回执扣减

- [ ] 2.1 `src/orchestrator/role-dispatcher.ts` `profile.done` 处理：移除无条件 `consumeBudget('follow')`，仅保留 `sendCommand({ action:'follow', ... })`（D2）
- [ ] 2.2 `action.completed` 处理：当 `payload.action==='follow' && payload.ok===true && payload.reason!=='already_followed'` 时 `consumeBudget('follow')`；already_followed 与失败均不扣（D2）
- [ ] 2.3 确认 follow 仍属 `noRecoverScroll`、返回由 `BackToFeed` 接管的控制流未被破坏（不回归）
- [ ] 2.4 cloud 单测/acceptance：补「already_followed no-op 不扣额」「真实关注扣 1」「真失败不扣额」用例；`npm run typecheck` → `npm run test:acceptance` → `npm test`

## 3. 收尾与归档

- [ ] 3.1 两仓回归全绿（含红线 `AC-*`）后，按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <commit-sha> 备注 -->`）
- [ ] 3.2 `openspec validate follow-already-followed-truthful-report --strict` 通过
- [ ] 3.3 cloud 侧改动按 CLAUDE.md §5 安全序列部署 ECS（备份 → rsync → restart → healthcheck → 失败回滚），部署后追加 `<!-- <date> deployed -->`
- [ ] 3.4 `/opsx:archive` 归档（delta 合并进 `openspec/specs/follow-decision`）
