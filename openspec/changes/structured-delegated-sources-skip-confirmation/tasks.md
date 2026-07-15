# Tasks

## 1. aidcp-cloud — createDraft 按 source 分流直接入队

- [ ] 1.1 `DelegatedTaskService.createDraft`：`source !== 'feishu'` 时创建后直接确认入队并返回 `autoQueued`；`feishu` 仍 `awaiting_confirmation`。`createFromText` 简化为透传（旧 slash 直接排队由此统一决定） <!-- aidcp-cloud <sha> -->
- [ ] 1.2 单测：console source `createDraft` → `queued` + `autoQueued`（人审 review 不变）；feishu 仍 `awaiting_confirmation`；panel 精选行级动作 + `/api/delegated-tasks/draft` 均 `queued`、执行前零副作用；控制操作仍需 version <!-- aidcp-cloud <sha> -->
- [ ] 1.3 回归：`npm run typecheck` + `npm run test:acceptance`（AC-PUB / AC-RISK 绿）+ 全量 `npm test` 全绿 <!-- aidcp-cloud <sha> -->

## 2. aidcp-console — 移除确认 Modal

- [ ] 2.1 `CuratedContentPage`：移除「请确认用户委托任务」Modal + `pendingTask` + `confirmTask`；洗稿 / 定向评论直接入队 + 成功 toast；「生成确认」文案改诚实动作名 <!-- aidcp-console <sha> -->
- [ ] 2.2 `ContentPage`：移除确认 Modal + `pendingTask` + `confirmTask`；候选稿批准 / 驳回 / 修改、待审删图直接入队 + 成功 toast <!-- aidcp-console <sha> -->
- [ ] 2.3 两页测试改写到新契约（无确认卡、无 /confirm、诚实 toast、错误路径、CAS 版本、执行前零副作用）；`npm run typecheck` + `npx vitest run` 全绿 <!-- aidcp-console <sha> -->

## 3. aidcp-edge — 快捷入口直接入队

- [ ] 3.1 `renderer.js` `draftDelegatedTask`：结构化精确入口 `autoQueued` → 直接入队 + 已排队消息 + 刷新任务列表，不弹确认卡（源码改动；不打包） <!-- aidcp-edge <sha> -->

## 4. aidcp（中控）— spec delta

- [ ] 4.1 `user-delegated-tasks` 需求 RENAMED + MODIFIED（确认卡收窄到自然语言、结构化精确入口直接入队）
- [ ] 4.2 `openspec validate structured-delegated-sources-skip-confirmation --strict` 通过

## 5. 部署

- [ ] 5.1 部署 cloud `dev` 并 healthcheck <!-- <date> deployed -->
- [ ] 5.2 部署 console `dev`（构建 + rsync + 无 --delete） <!-- <date> deployed -->
