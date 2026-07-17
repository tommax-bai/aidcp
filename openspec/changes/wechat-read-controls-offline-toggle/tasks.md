## 1. aidcp-edge — 渲染层读取开关闸与 edgeDelivery 呈现

> 本 change 的**全部**代码改动只落 `src/electron/renderer/interaction-workspace.js` 与 `test/electron/interaction-workspace.test.ts` 两个文件。
> 红线：MUST NOT 改任何 Cloud 文件；MUST NOT 在 `main.cjs` 新增浏览器 / 环境闸；MUST NOT 动 `connectivityWriteBlocked()`（`:277-279`）及其覆盖的回复写闸。

- [ ] 1.1 读 `design.md`「被推翻的假设」四条，确认不去 Cloud 侧排查（`interaction-customer-api.ts:319` 的 503 是不可达死代码，错误文案与症状同形、极易被重新「修」一遍）。
- [ ] 1.2 从 `renderReadSettings()` 的 `editable` 判定（`interaction-workspace.js:411-412`）里删除 `env && env.connectivity === 'connected'` 一项，保留 `stored`、`state.auth.status === 'active'`、`!state.stale`、`typeof api.interactionUpdateReadControls === 'function'` 四项；就地写注释说明这次写入经主进程直发 Cloud HTTP、不经过该环境核心子进程，Cloud 无 Edge 在线时按 CAS 落库并回 `deferred`、下次 hello 由欢迎信封快照收敛（cloud `handler.ts:663-669`）。`updateReadControls()`（`:1169`）的 `!env` 守卫保持不变。
- [ ] 1.3 **必须与 1.2 同批**：把 `edgeDelivery.status` 存入 state（如 `state.readDelivery`），在 `renderReadSettings()` 里驱动 `dom.readApply`（`:422-427`）——未应用且本次为 `deferred` 时持久显示「待该环境下次连接后生效（需要启动该环境）」，`applied` 与其余未应用分支的现有文案不动。`:1187-1189` 已有的 `actionNotice` 分档**保留、不重写**（它是即时反馈，与持久态互补）。只做 1.2 不做 1.3 = 用假成功换假阻断，同一条红线的另一面。
- [ ] 1.4 补渲染层回归测试（`test/electron/interaction-workspace.test.ts`，jsdom）：① `connectivity='disconnected'` + `status='active'` + stored 已取到 → 三个开关 `disabled===false`，切换真的调到 `interactionUpdateReadControls`；② `edgeDelivery.status='deferred'` → 持久区出现待生效文案且**不含**「已应用」；③ `deferred` 与 `enqueued` 文案可区分；④ 冷待机（`connectivity='connected'` + `browserState='closed'` + `status='active'`）可编辑——**防 1.2 顺手把 `status` 也摘了**；⑤ `status!=='active'` 与 `state.stale===true` 仍禁用；⑥ 钉死决策 3 的暗路：停止态环境在一次成功 `loadList` 之后 `state.stale===false` 且开关可编辑（`:1422` 设 stale、`:927` 无条件清——若哪天 `:927` 改成有条件清除，这条测试当场红，而不是让开关悄悄变回灰的）。
- [ ] 1.5 跑 `cd ../aidcp-edge && npm run test:acceptance && npm test && npm run typecheck`，全绿。
- [ ] 1.6 提交并推送到 edge `master`（worktree 开发、集成串行、遇 non-ff 一律 rebase 不 force）。**不打安装包**（CLAUDE.md §6）。

## 2. aidcp-cloud — 无改动（显式确认）

- [ ] 2.1 确认零改动：`git -C ../aidcp-cloud status` 干净。Cloud 侧已经离线正确（`server.ts:1981-1995` 无 Edge 时 `{delivered:0}` 不抛错、`interaction-customer-api.ts:326` 如实回 `edgeDelivery`、`handler.ts:663-669` hello 收敛、`:70-72` 的 `applicationStatus` 结构上不可能把离线保存报成 `applied`）。本 change 无 Cloud 部署项。

## 3. aidcp — 契约回写与验收登记

- [ ] 3.1 `openspec validate wechat-read-controls-offline-toggle --strict` 通过。
- [ ] 3.2 把 A1–A5 五条真机验收项登记进 `docs/real-machine-acceptance-backlog.md`（见 `design.md` 验收节），归入视频号真机簇。**必须写明：复现只能用「已停止 / 从未启动」的环境——冷待机今天是好的（`main.cjs:2212/2221` 进冷待机时显式置 `cloud:'connected'`），用应用内「关闭浏览器」按钮去试会看到开关正常，从而得出「无法复现」的错误结论。**
- [ ] 3.3 把 A1（停止态环境确实呈现 `connectivity !== 'connected'`）标注为本 change **唯一未经真机观测的推断**：由 `main.cjs:1030` 默认 `disconnected` + `main.cjs:2794` 核心退出置 `disconnected` + `renderer.js:231` 推出，代码闭合但未真机确认。若真机上停止态环境居然报 `connected` → 根因另有其人，修法仍正确但症状不消失，须回头重新定位。
- [ ] 3.4 登记「`loadDetail` 的 stale 不对称」（`interaction-workspace.js:1011` 只在 connected 时清 stale，`loadList:927` 无条件清）为**已知、已分析、本 change 故意不改**的残留：它同时喂 `connectivityWriteBlocked()` → 回复草稿 / 发送写闸，动它会放开本 change 未分析过的写入。当前实际影响为零（`loadList` 先跑并已清 stale，该条件是死条件）。
- [ ] 3.5 用 HTML 注释回写 1.x 的 commit-sha（`<!-- aidcp-edge <sha> 备注 -->`），sha 必须取自**已推送**的提交。
- [ ] 3.6 真机 A1–A5 跑通后 archive 本 change，清理 worktree / 分支。
