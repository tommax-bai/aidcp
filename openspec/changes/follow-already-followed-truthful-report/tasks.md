## 1. aidcp-edge — executeFollow 如实上报 + 检测增强

> ⚠️ edge 工作树存在**既有未提交 WIP**（反验证码 overlay watcher + follow 提交前复检，~572 行 / 2 个新文件 / protocol.ts 改动）。本 change 的 edge 改动已落入工作树并验证通过，但**尚未提交**（避免把 WIP 混进本 change 提交），待用户决定提交方式。

- [x] 1.1 `src/browse/browse-session.ts` `executeFollow()`：探测 JS 在文案 `已关注 / 互关` 判定基础上叠加 `aria-pressed==='true'`（OR），命中返回 `{already:true}`（D3）<!-- aidcp-edge uncommitted（WIP 同树）-->
- [x] 1.2 `executeFollow()` already 分支改为良性 no-op 成功：`reportActionCompleted({ action:'follow', ok:true, reason:'already_followed' })`，日志 `[browse] ✓ 已关注（无需重复关注）`（D1）<!-- aidcp-edge uncommitted -->
- [x] 1.3 真实新关注成功路径上报 **不带 `reason`**（`{ action:'follow', ok:true }`）—— 现状已如此，未改（D2 衔接点）<!-- aidcp-edge 现状 -->
- [x] 1.4 真失败路径如实：`no-btn` → `{ ok:false, reason:'btn_no-btn' }`、异常 → `{ ok:false, reason: message }`（红线不破）<!-- aidcp-edge uncommitted -->
- [x] 1.5 edge 单测：补「already_followed → ok:true + reason」「no-btn → ok:false + btn_no-btn」；`typecheck` 通过、`test:acceptance` 11/11、`test` 251/251 全绿 <!-- aidcp-edge uncommitted -->

## 2. aidcp-cloud — 配额依真实回执扣减

- [x] 2.1 `src/orchestrator/role-dispatcher.ts` `profile.done`：移除无条件 `consumeBudget('follow')`（D2）<!-- aidcp-cloud 900f085 -->
- [x] 2.2 `action.completed`：当 `action==='follow' && ok===true && reason!=='already_followed'` 才 `consumeBudget('follow')`；already_followed 与失败均不扣（D2）<!-- aidcp-cloud 900f085 -->
- [x] 2.3 follow 仍属 `noRecoverScroll`、返回由 `BackToFeed` 接管的控制流未改（不回归）<!-- aidcp-cloud 900f085 -->
- [x] 2.4 cloud 单测：「真实关注扣 1 / already_followed 不扣 / 失败不扣」（+ `remainingFollows` getter）；`typecheck` 通过、`test:acceptance` 11/11、`test` 173/173 <!-- aidcp-cloud 900f085 -->

## 3. 收尾与归档

- [x] 3.1 两仓回归全绿（含 AC-PROTO/PUB/RISK），按 sub-repo 分节回写本 tasks.md 进度 <!-- 2026-06-19 -->
- [ ] 3.2 `openspec validate follow-already-followed-truthful-report --strict` 通过
- [ ] 3.3 cloud 侧改动按 §5 安全序列部署 ECS（备份 → rsync → restart → healthcheck → 失败回滚），部署后追加 `<!-- <date> deployed -->`（**待确认**：cloud 半与旧 edge 也兼容，可独立部署）
- [ ] 3.4 edge 半提交并随 edge 本地运行生效（**待用户决定**：与既有 WIP 的提交方式）
- [ ] 3.5 `/opsx:archive` 归档（delta 合并进 `openspec/specs/follow-decision`）

## 旁现（out of scope，建议后续 change）

- like / collect 的"已点赞/已收藏"也走相同**假失败**模式：`executeLikeOrCollect` 命中已完成态时报 `ok:false, reason:'already_liked'/'already_collected'`（见 edge `browse-session.test.ts` 既有断言），且其配额在 `interaction.completed` 下发时即扣（role-dispatcher.ts:316），与 follow 修复前同病。本 change 仅治 follow；建议另起 change 一并修 like/collect 的假失败 + 配额计账。
