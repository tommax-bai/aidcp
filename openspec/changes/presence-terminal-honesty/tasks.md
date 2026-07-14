# Tasks

## 1. aidcp-edge — 在场感终态与诚实等待

- [x] 1.1 在场感行改为「终态优先」：当日浏览额度已跑满时先出终态文案，不再被新鲜期内的中途动作文案盖住（`src/electron/renderer/ui-logic.js` 的 `presenceView`）。额度未满时不得自行推断今日完成。 <!-- aidcp-edge 84267f2 -->
- [x] 1.2 新鲜度分段：1 分钟内保留动效 + 「刚刚更新」；超过 1 分钟、不足 5 分钟时保留动作文案但停动效、标签改为「已等待 · N 分钟」。 <!-- aidcp-edge 84267f2 新增 PRESENCE_LIVE_MS=60s 与 waitedText() -->
- [x] 1.3 云端连接断开时改写在场感为连接中断实情文案（`src/electron/main.cjs` 断连分支），不再让中途动作文案继续演。 <!-- aidcp-edge 84267f2 顺带补重连回来的翻回（'云端已重连' 无翻译规则、不会自己被顶掉） -->

## 2. aidcp-edge — 测试

- [x] 2.1 `test/electron/ui-logic.test.ts`：补「会话仍报运行中 + 动作文案新鲜 + 当日额度已满 → 在场感必须是终态文案（且与探索进度卡同口径）」与「额度未满 + 动作文案 2 分钟前 → 保留文案、无动效、标签为已等待、绝不自称今日完成」两条。 <!-- aidcp-edge 84267f2 -->
- [x] 2.2 断连改写的契约断言落在 `test/electron/lifecycle-contract.test.ts`（偏离：Electron 起不来，`main.cjs` 按本仓既有做法设源码契约，不走 companion-ui 的 DOM 桩）。 <!-- aidcp-edge 84267f2 -->
- [x] 2.3 `npm run test:acceptance`（19 ✓）+ `npm test`（1339 ✓）+ `npm run typecheck` 全绿。 <!-- aidcp-edge 84267f2 -->

## 3. 收口

- [x] 3.1 `openspec validate presence-terminal-honesty --strict` 通过。
- [x] 3.2 提交 + 推送（edge master `84267f2`，已 ff 同步主 checkout；控制仓 main）。
- [x] 3.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md`：簇 81 共 4 项——三态可区分（今日额度满 / 等云端 / 断连），且不再出现「进度卡说今天先到这里、在场感说顺路去作者主页」的同屏矛盾。 <!-- 2026-07-14 -->

## 备注：未纳入本 change 的相邻缺口（审计发现，另议）

- 云端因当日浏览额度用尽进入休眠时，把后续浏览命令在统一出口静默丢弃，不通知执行端也不下发结束——客户端只能靠 5 分钟新鲜度窗口自己翻脸。根治要落在云端（让「额度等待」走待机通知），与 `standby-covers-idle-waits` 相邻，本 change 不动。
- 打开作者主页的三条失败分支与一条降级分支在拟人 UI 上完全无痕（不进活动流、不刷新在场感、不计数）。
- 打开作者主页的日志不区分「拜访某位作者」与「采集本人昵称」，事后无法从日志判断走的哪条路。
