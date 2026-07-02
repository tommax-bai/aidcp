## 1. aidcp-cloud — 协议与节奏中心值

- [x] 1.1 `src/comm/protocol.ts`：给 `PageScrollPayload` 增加可选 `dwellMs?: number`；与 edge 侧逐字一致（字段 parity 人工核对，`MessageType` 不新增） <!-- aidcp-cloud 1fc31d5 -->
- [x] 1.2 `src/comm/command-bridge.ts`：修 `scroll` 分支——当前只透传 `reason`、丢弃 `command.params`，改为把 `dwellMs` 透传进 `page.scroll`（对照 `back` 分支已 spread params 的写法） <!-- aidcp-cloud 1fc31d5 -->
- [x] 1.3 `src/risk/pacing.ts`：新增常量 `FEED_FLOOR = { perCardMs: 450, capMs: 7000 }`（可调）与 `computeFeedFloorMs({ newCount, status, progress })`，复用 `tempoForStatus` + `fatigueMultiplier`；`newCount <= 0 → 0`，否则 `round(clamp(perCardMs * newCount * tempo * fatigue, 0, capMs))` <!-- aidcp-cloud 1fc31d5 -->

## 2. aidcp-cloud — 新卡差分与下发接线

- [x] 2.1 会话上下文：新增"上一批 feed 卡 `noteId` 集合"字段（简版：每次 feed 上报覆盖，不跨轮保留） <!-- aidcp-cloud 1fc31d5 SessionContext._lastFeedNoteIds + feedBatchNewCount()；不在 reset 清（跨重连保持，避免整屏误判为新卡） -->
- [x] 2.2 `src/orchestrator/role-dispatcher.ts` 的 `page.cards.arrived` 处理：**仅 `sourcePageType === 'feed'`** 时——用本批 `noteId` 差分"上一批"集合算 `newCount`（缺 `noteId` 计为非新卡）→ 用本批刷新集合 → 调 `computeFeedFloorMs` 并**覆盖写** `pendingFeedFloorMs`（含写 0） <!-- aidcp-cloud 1fc31d5 -->
- [x] 2.3 `role-dispatcher.ts` 的 `feed.scrolled → sendCommand('scroll')`：消费 `pendingFeedFloorMs`——`floor > 0` 才挂 `params: { dwellMs: floor }`（镜像既有 `dwellMs === undefined ? {} : { dwellMs }`），随后把 `pendingFeedFloorMs` 归零 <!-- aidcp-cloud 1fc31d5 -->
- [x] 2.4 确认 search 结果页与 recovery/idle nudge 翻页**不**消费 feed 兜底（不带 `dwellMs`），保持恢复类翻页快速 <!-- aidcp-cloud 1fc31d5 by construction：search.scrolled / idle_nudge / recover 分支不读 pendingFeedFloorMs；page.cards.arrived 仅 feed 来源写 floor -->

## 3. aidcp-edge — 协议与停留执行

- [x] 3.1 `src/comm/protocol.ts`：给 `PageScrollPayload` 增加可选 `dwellMs?: number`（与 cloud 逐字一致；这是 load-bearing 改动，`ensureFeedDwell` 依赖它） <!-- aidcp-edge 98f41fe -->
- [x] 3.2 `src/browse/browse-session.ts`：新增锚点 `feedCardsArrivedAt`，在 `reportVisibleCards` 末尾每次上报时刷新为当前时刻 <!-- aidcp-edge 98f41fe -->
- [x] 3.3 `browse-session.ts`：新增 `ensureFeedDwell(dwellMs)`，照抄 `ensureDetailDwell` 的"抖动中心值、只睡 `目标 − (now − feedCardsArrivedAt)`、遇空 / ≤0 早返回" <!-- aidcp-edge 98f41fe -->
- [x] 3.4 `browse-session.ts` 的 `page.scroll` 处理：在 `scrollNext()` **之前**调用 `ensureFeedDwell(payload.dwellMs)` <!-- aidcp-edge 98f41fe -->

## 4. docs

- [x] 4.1 `aidcp/docs/protocol.md`：`page.scroll` 字段列表补一个可选 `dwellMs`（消息计数不变）；一句话说明 feed 按新卡数兜底 <!-- aidcp (本仓) 随 tasks 提交 -->

## 5. 测试与回归

- [x] 5.1 cloud 单测：`computeFeedFloorMs` 曲线（0 新卡→0；3–4 张→~1.3–1.8s；10+→封顶；warned/疲劳放大） <!-- aidcp-cloud 1fc31d5 test/risk-pacing.test.ts +5 -->
- [x] 5.2 cloud 单测：`newCount` 差分（全新 / 部分重叠 / 全重复→0 / 含无 `noteId` 卡）+ feed-only 门控（search 上报不写 / 不消费 feed 集合）+ `pendingFeedFloorMs` open→return 覆盖写不残留 <!-- aidcp-cloud 1fc31d5 test/session-context-feed-floor.test.ts(7) + test/integration/feed-scroll-card-floor.test.ts(2, 出新卡带dwellMs / 返回同批不带) -->
- [x] 5.3 edge 单测：`ensureFeedDwell` 只补差额（已过时长≥目标→立即返回；无 / ≤0 `dwellMs`→立即返回；与 `ensureDetailDwell` 互不叠加） <!-- aidcp-edge 98f41fe test/browse/browse-session.test.ts +3 -->
- [x] 5.4 回归：edge + cloud 各跑 `npm run test:acceptance`（含 `AC-PROTO-*` 两份 `protocol.ts` 不漂移）→ 全量 `npm test` → `npm run typecheck` <!-- edge acceptance 11/0 + full 449/0 + typecheck 干净；cloud acceptance 27/0 + full 1103/0 + typecheck 仅 1 个既有无关报错 test/feishu-ws-receiver.test.ts(354) 'res' 未用（属 change edit-note-draft-before-publish@8eb0664，非本 change 引入、未碰该文件）；AC-PROTO 两端消息类型均 56 一致 -->

## 6. 收尾

- [x] 6.1 `openspec validate feed-scroll-card-floor --strict` 通过 <!-- aidcp 随 tasks 提交，validate 见下 -->
- [x] 6.2 各 task 用 HTML 注释标 `[x]` 并附 `<!-- <repo> <commit-sha> 备注 -->`；commit + push（cloud/edge `master`） <!-- edge 98f41fe pushed 6bb9358..98f41fe / cloud 1fc31d5 pushed f9f270c..1fc31d5 -->
- [ ] 6.3 按需部署 cloud（走 §5 安全序列：备份→rsync→restart→healthcheck→失败回滚；绝不碰同机 isales）；部署后 tasks 追加 `<!-- <date> deployed -->` <!-- 待用户确认：cloud 部署可让云端开始下发 dwellMs；但完整生效还需 edge 更新（旧 edge 向后兼容忽略 dwellMs，无害但不加停留）。edge 本地跑/自更新，非 ECS 部署 -->
