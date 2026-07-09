## 1. aidcp-edge — 壳层纯逻辑模块

- [x] 1.1 新增 `src/electron/ui-state.cjs`：`envKeyFromSettings(settings)`（`self` | `ads:<adsProfileId>`）、`adoptStoredLastPublish(parsed, currentEnvKey)`（同键采纳，异键/缺键返回 null）、`serializeUiState(envKey, lastPublish)` <!-- aidcp-edge 9c5991e -->
- [x] 1.2 新增 `test/electron/ui-state.test.ts`：同键采纳 / 异键丢弃 / 缺键丢弃（升级路径）/ 序列化带键往返，约 4 例（按测试克制惯例） <!-- aidcp-edge 9c5991e 4 例全绿 -->

## 2. aidcp-edge — main.cjs 接线

- [x] 2.1 `loadUiState`：读文件后经 `adoptStoredLastPublish` 按当前设置键判定采纳；`saveUiState` 落盘改用 `serializeUiState`（带 `envKey`） <!-- aidcp-edge 9c5991e -->
- [x] 2.2 `startEdge`：spawn 时刻快照 `runningEnvKey`；内存历史态归属键 ≠ 本次环境键时，在既有重启补丁那次 `updateStatus` 并入 `lastPublish: null`（同环境重启不动） <!-- aidcp-edge 9c5991e -->
- [x] 2.3 两处 `lastPublish` 写入点（发布成功 / 云端快照回填）以 `runningEnvKey` 记归属后再落盘 <!-- aidcp-edge 9c5991e 兜底 envKeyFromSettings(settings)（runningEnvKey 未设时） -->

## 3. 验证与收口

- [x] 3.1 `cd ../aidcp-edge && npm test && npm run typecheck` 全过（含既有 companion-ui / ui-logic / renderer-smoke 无回归） <!-- aidcp-edge 9c5991e worktree 内 rebase 到最新 master 后 test 759 绿 + acceptance 15 绿 + typecheck 干净 + node --check main.cjs -->
- [x] 3.2 真机验收项登记 `docs/real-machine-acceptance-backlog.md`：切环境重启后发布卡回空态 / 切回有记录账号被快照回填 <!-- 控制仓 簇 22 -->
- [x] 3.3 edge 集成合入 master 并推送；tasks.md 回写 commit sha；`openspec validate env-switch-last-publish-reset --strict` 后归档 <!-- aidcp-edge 9c5991e 经 land-change ff 推 origin/master，主 checkout 已同步；纯客户端改动、无 ECS 部署项 -->
