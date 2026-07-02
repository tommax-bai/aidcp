## 1. aidcp-cloud — 协议与节奏中心值

- [ ] 1.1 `src/comm/protocol.ts`：给 `PageScrollPayload` 增加可选 `dwellMs?: number`；与 edge 侧逐字一致（字段 parity 人工核对，`MessageType` 不新增）
- [ ] 1.2 `src/comm/command-bridge.ts`：修 `scroll` 分支——当前只透传 `reason`、丢弃 `command.params`，改为把 `dwellMs` 透传进 `page.scroll`（对照 `back` 分支已 spread params 的写法）
- [ ] 1.3 `src/risk/pacing.ts`：新增常量 `FEED_FLOOR = { perCardMs: 450, capMs: 7000 }`（可调）与 `computeFeedFloorMs({ newCount, status, progress })`，复用 `tempoForStatus` + `fatigueMultiplier`；`newCount <= 0 → 0`，否则 `round(clamp(perCardMs * newCount * tempo * fatigue, 0, capMs))`

## 2. aidcp-cloud — 新卡差分与下发接线

- [ ] 2.1 会话上下文：新增"上一批 feed 卡 `noteId` 集合"字段（简版：每次 feed 上报覆盖，不跨轮保留）
- [ ] 2.2 `src/orchestrator/role-dispatcher.ts` 的 `page.cards.arrived` 处理：**仅 `sourcePageType === 'feed'`** 时——用本批 `noteId` 差分"上一批"集合算 `newCount`（缺 `noteId` 计为非新卡）→ 用本批刷新集合 → 调 `computeFeedFloorMs` 并**覆盖写** `pendingFeedFloorMs`（含写 0）
- [ ] 2.3 `role-dispatcher.ts` 的 `feed.scrolled → sendCommand('scroll')`：消费 `pendingFeedFloorMs`——`floor > 0` 才挂 `params: { dwellMs: floor }`（镜像既有 `dwellMs === undefined ? {} : { dwellMs }`），随后把 `pendingFeedFloorMs` 归零
- [ ] 2.4 确认 search 结果页与 recovery/idle nudge 翻页**不**消费 feed 兜底（不带 `dwellMs`），保持恢复类翻页快速

## 3. aidcp-edge — 协议与停留执行

- [ ] 3.1 `src/comm/protocol.ts`：给 `PageScrollPayload` 增加可选 `dwellMs?: number`（与 cloud 逐字一致；这是 load-bearing 改动，`ensureFeedDwell` 依赖它）
- [ ] 3.2 `src/browse/browse-session.ts`：新增锚点 `feedCardsArrivedAt`，在 `reportVisibleCards` 末尾每次上报时刷新为当前时刻
- [ ] 3.3 `browse-session.ts`：新增 `ensureFeedDwell(dwellMs)`，照抄 `ensureDetailDwell` 的"抖动中心值、只睡 `目标 − (now − feedCardsArrivedAt)`、遇空 / ≤0 早返回"
- [ ] 3.4 `browse-session.ts` 的 `page.scroll` 处理：在 `scrollNext()` **之前**调用 `ensureFeedDwell(payload.dwellMs)`

## 4. docs

- [ ] 4.1 `aidcp/docs/protocol.md`：`page.scroll` 字段列表补一个可选 `dwellMs`（消息计数不变）；一句话说明 feed 按新卡数兜底

## 5. 测试与回归

- [ ] 5.1 cloud 单测：`computeFeedFloorMs` 曲线（0 新卡→0；3–4 张→~1.3–1.8s；10+→封顶；warned/疲劳放大）
- [ ] 5.2 cloud 单测：`newCount` 差分（全新 / 部分重叠 / 全重复→0 / 含无 `noteId` 卡）+ feed-only 门控（search 上报不写 / 不消费 feed 集合）+ `pendingFeedFloorMs` open→return 覆盖写不残留
- [ ] 5.3 edge 单测：`ensureFeedDwell` 只补差额（已过时长≥目标→立即返回；无 / ≤0 `dwellMs`→立即返回；与 `ensureDetailDwell` 互不叠加）
- [ ] 5.4 回归：edge + cloud 各跑 `npm run test:acceptance`（含 `AC-PROTO-*` 两份 `protocol.ts` 不漂移）→ 全量 `npm test` → `npm run typecheck`

## 6. 收尾

- [ ] 6.1 `openspec validate feed-scroll-card-floor --strict` 通过
- [ ] 6.2 各 task 用 HTML 注释标 `[x]` 并附 `<!-- <repo> <commit-sha> 备注 -->`；commit + push（cloud/edge `master`）
- [ ] 6.3 按需部署 cloud（走 §5 安全序列：备份→rsync→restart→healthcheck→失败回滚；绝不碰同机 isales）；部署后 tasks 追加 `<!-- <date> deployed -->`
