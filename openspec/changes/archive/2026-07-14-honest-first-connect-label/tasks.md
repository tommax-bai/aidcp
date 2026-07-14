# Tasks

## 1. aidcp-edge — 状态投影：记住「这轮核心连上过云端没有」

- [x] 1.1 `src/electron/main.cjs` `makeStatus()`：新增 `cloudEverConnected: false`（默认未连过）。 <!-- aidcp-edge 416ed94 -->
- [x] 1.2 `src/electron/main.cjs` `startEdge()`：spawn 新核心时写 `cloudEverConnected: false`。新核心 = 没连过，哪怕上一个核心连上过。 <!-- aidcp-edge 416ed94 -->
- [x] 1.3 `src/electron/main.cjs` `stopAndRestart()`：复位 `cloudEverConnected: false`（正要换核心）。 <!-- aidcp-edge 416ed94 -->
- [x] 1.4 `src/electron/main.cjs` 日志投影：命中「已连接云端 / 已握手 / 云端已重连」时写 `cloudEverConnected: true`（与既有 `cloud: 'connected'` + `settleLaunchReady` 同一处）。 <!-- aidcp-edge 416ed94 -->
- [x] 1.5 冷待机唤醒路径**不复位**该位（云端连接全程未断）。 <!-- aidcp-edge 416ed94 已确认 onColdStandbyWoken 不写该字段；唤醒只重建浏览器，云端连接自始未断 -->

## 2. aidcp-edge — 呈现层：两处判定按事实分流

- [x] 2.1 `src/electron/renderer/ui-logic.js` `synthesizeHealth()`：断连分支拆两路——没连过 → 启动态（`ready`／「正在启动…」）；连过 → 「正在重新连接」（`attention`）。 <!-- aidcp-edge 416ed94 -->
- [x] 2.2 `src/electron/renderer/ui-logic.js` `fleetLevel()`：同样拆两路——没连过 → `launching` /「启动中」/ `needsAction: false`；连过 → `attention` /「正在重新连接」/ `needsAction: true`。 <!-- aidcp-edge 416ed94 -->

## 3. aidcp-edge — 回归

- [x] 3.1 `test/electron/ui-logic.test.ts` + `test/electron/fleet-console.test.ts`：冷启动窗口（edge=running + session=running + cloud=disconnected + 没连过）→ 两处都必须是启动态、`needsAction: false`。 <!-- aidcp-edge 416ed94 已验证这两条在修复前的代码上必失败（把 ui-logic.js stash 掉重跑：fail 2） -->
- [x] 3.2 同上两文件：连过之后断连 → 两处都必须是「正在重新连接」+ `needsAction: true`（守住不把真断线也一起吞掉）。 <!-- aidcp-edge 416ed94 这两条在修复前后都通过——它们钉的是本就正确、不许被改坏的行为 -->
- [x] 3.3 `npm run typecheck` + `npm test` 全过。 <!-- aidcp-edge 416ed94 land 时 rebase 到最新 master 重跑：1272 pass / 0 fail；test:acceptance 19 pass -->

## 4. 真机验收（已解耦登记 backlog，不在本 change 内闭环）

- [x] 4.1 登记 `docs/real-machine-acceptance-backlog.md` **簇 66**（66.1–66.5：冷启动全程只见「启动中」/ 环境栏不浮顶不染琥珀 / 真断线仍如实报重连 / 崩溃重起不冒充重连 / 冷待机唤醒不退回首次连接窗口）。

## 备注

- 未部署项：本 change 只改边缘桌面客户端呈现层，**不涉及云端、不需要部署**。生效条件是**重启桌面客户端**。
- 集成时 canonical `aidcp-edge` checkout 正被并发 session 占用（未提交 WIP + 一个未推送的本地 chore 提交 `bd3bc59`），与 `origin/master` 分叉、无法 ff。**未触碰其工作区**（CLAUDE.md §7：绝不抹他人 WIP）；本 change 已在 `origin/master` 上，该 checkout 待并发 session 收工后自行同步。
