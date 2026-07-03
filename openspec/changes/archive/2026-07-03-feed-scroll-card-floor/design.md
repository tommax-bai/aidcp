## Context

现役节奏系统（`command-pacing` spec）已实现：内容 / 状态相关时长系数在云端一处算出中心值（`aidcp-cloud/src/risk/pacing.ts` 的 `computeThinkMs` / `computeDwellMs`，复用 `tempoForStatus` / `fatigueMultiplier`），随决策指令下发 `thinkMs`（动作前犹豫）/ `dwellMs`（离页前总停留）；边缘只叠 lognormal 抖动 + 保证达标（`aidcp-edge/src/browse/browse-session.ts` 的 `ensureDetailDwell`：从 `noteOpenedAt` 起算、只补 `目标 − 已过时长`、缺失早返回）。

**缺口**：feed 翻页这一层**没有停留兜底**——`page.scroll` 只带约 0.7s 的 `thinkMs`，没有按内容计的驻留。今天 ECS 日志分析显示，观察到的 op-to-op 间隔（中位 17–25s）主要由云端评估卡片的 LLM 延迟"撑"出，是副产品而非设计保证；详情页停留按内容长度算、安全，暴露点集中在 feed 翻页。若评估角色换更快模型，feed 翻页会压到一两秒、呈机器般规律快节奏。

**已确认的现状约束（代码坐实）**：
- 每张 feed 卡片上报（`page.cards` / `PageCardsPayload`）已自带可选 `noteId`（边缘从卡片 `/explore/<id>` 链接解析，`aidcp-edge/src/browse/feed-scroller.ts`）。无新协议消息即可判"新旧卡"。
- 边缘每次翻页、每次返回 feed 都**重新全量上报**当前可见卡片；`history.back` 保留滚动位置，返回未刷新时上报的是**同一批 `noteId`**。
- 云端 `page.cards.arrived` 处理（`role-dispatcher.ts`）只保留最新一批 `visibleCards`（覆盖写、无历史），故需自备"上一批"集合做差分。
- feed 翻页 100% 命令驱动（边缘无自主翻页循环），故"云端算 + 挂在命令上"不会有边缘先滑的竞态。

## Goals / Non-Goals

**Goals:**
- feed 翻页的"像人"变成**设计保证**而非模型慢的副产品：按本次翻页**新卡片数**计一个停留兜底。
- **返回未刷新 → 零额外延迟**；**出新卡 → 按数计时**。语义从既有信号（`noteId` 差分）自然得出，不新增协议消息 / 不加"刷新"标志。
- 严守架构铁律：节奏中心值收口云端、边缘只叠抖动 + 保证达标；红线绝不假成功 / 绝不 fake-fast。

**Non-Goals:**
- 不改动详情页停留（`ensureDetailDwell`）与其内容驱动模型。
- 不改动 `recency-aware-revisit-pacing` 的 `_recentEvaluatedIds` familiarity / `thinkMs` 折扣逻辑（本 change 用**独立**集合）。
- 不给搜索结果翻页加兜底（同路径可后续一行扩展，本 change 只做 feed）。
- 不接"状态迁移接真实封号/限流信号"（既有缺口，正交）。

## Decisions

### D1. 新旧卡识别：`noteId` 差分（不新增协议）
用每张卡已有的 `noteId` 做集合差分算 `newCount`。**替代方案**：新增 `page.cards` 的 `newCount` 字段或 `page.scroll` 的 `refresh` 标志——被否，因为徒增协议面 + 两份 `protocol.ts` 维护成本，而现有 `noteId` 已足够。缺 `noteId` 的卡（广告 / 懒加载）计为"非新卡"：方向安全（只少加停留），且保证"返回未刷新"永远算作 0 新卡。

### D2. 差分基准：只存"上一批 feed 卡"集合（简版），不用全时段无界集合
对抗评审确认：详情页发 `note.detail` 不发 `page.cards`，故"打开笔记→返回"期间"上一批"不被覆盖，返回后仍等于上一批 → 新卡数 0 → 零延迟，**需求满足**。**替代方案**：跨轮保留的全时段 seen 集合——被否（YAGNI）：只在"翻很多屏后再往回滚回早先卡"这种极端场景才有别，且那也只是安全方向的多加停留。简版好处：O(1) 存储、自清、无跨重连 / 重置的推理负担。若未来明确要求"长距离往回也严格 0 延迟"，再升级。

### D3. 中心值云端算：`pacing.ts` 新增 `computeFeedFloorMs`
在 `computeDwellMs` / `computeThinkMs` 旁新增 `computeFeedFloorMs({ newCount, status, progress })`，**复用** `tempoForStatus` + `fatigueMultiplier`。常量 `FEED_FLOOR = { perCardMs ≈ 450, capMs ≈ 7000 }`（可调）。公式：`newCount <= 0 → 0`；否则 `round(clamp(perCardMs * newCount * tempo * fatigue, 0, capMs))`。依据：真人扫一眼一张新卡约 0.3–0.5s；3–4 张新卡 ≈ 1.3–1.8s；整屏 10+ 封顶 ≈ 7s；风控紧张 / 疲劳按系数放大。**替代方案**：按卡片数量的对数 / 分段——被否，线性 + 封顶已足够且直观可调。

### D4. 挂载与消费：卡片到达处算、翻页下发处消费
`page.cards.arrived` 处理里（仅 `sourcePageType === 'feed'`）：先对 `noteId` 差分算 `newCount` → 用本批刷新"上一批"集合 → 算出并**覆盖写** `pendingFeedFloorMs`（含写 0，避免 open→return 残留旧值）。`feed.scrolled → sendCommand('scroll')` 时消费：`floor > 0` 才挂 `params.dwellMs`（镜像现有 `dwellMs === undefined ? {} : { dwellMs }` 模式），并把 `pendingFeedFloorMs` 归零。顺序天然正确：`feed.scrolled` 只在 `page.cards.arrived → evaluate` 判无价值后发出，此时 `pendingFeedFloorMs` 已持有刚到批次的兜底。

### D5. 唯一协议改动 + 一处 bug 修复
`PageScrollPayload` 加可选 `dwellMs?: number`，两份 `protocol.ts` 逐字同步。**不新增 `MessageType`**，`page.scroll` 已在主动命令路由白名单，白名单无需动。修 `command-bridge.ts` 的 `scroll` 分支：当前只透传 `reason`、**丢弃了 `command.params`**（对照 `back` 分支已 spread params），改为透传 `dwellMs`——否则兜底到不了边缘。注意：两份 `PageScrollPayload` 的字段 parity 是**人工约定、非 typecheck 不变量**（`MessageType` 穷举才是），load-bearing 的是 edge 侧声明 `dwellMs`（否则 `ensureFeedDwell` 编译不过）。

### D6. 边缘只补差额：`ensureFeedDwell`
`browse-session.ts` 新增 `ensureFeedDwell(dwellMs)`，照抄 `ensureDetailDwell` 的"抖动中心值、只睡 `目标 − (now − anchor)`、遇空 / ≤0 早返回"。锚点 `feedCardsArrivedAt` 在 `reportVisibleCards` 末尾**每次上报刷新**；在 `page.scroll` 处理开头、`scrollNext` **之前**调用。效果：云端评估耗时被吸收进停留（与详情页一致），只有模型比目标快时才真正补睡。与 `ensureDetailDwell` 不双算：锚点（`feedCardsArrivedAt` vs `noteOpenedAt`）与触发命令均不同，且在 feed 时 `noteOpenedAt` 为空、`ensureDetailDwell` no-op。

## Risks / Trade-offs

- **[缺 `noteId` 的真新卡漏算兜底]** → 方向安全（只少加、绝不 fake-fast）。可选增强：某屏无 `noteId` 比例过高时回退按 `(title|author)` 去重计数兜底。本 change 先不做。
- **[返回 fallback 触发真刷新]** → `history.back` 落点异常时边缘会 `Page.navigate` 重载 explore（等于真刷新）→ 出新卡→有兜底。语义正确（确是新内容），接受；不为此加豁免复杂度。
- **[进程重启丢"上一批"集合]** → 首屏全算新卡 → 一次封顶 ≈ 7s 停留，自限、安全方向。仅 reconnect（会话 reset）不应清集合——但简版集合本就每次 feed 上报覆盖，reconnect 后首个 feed 上报即重建，无需特殊保留。
- **[search 页污染 feed 集合]** → 差分 / 刷新 / 消费一律 `sourcePageType === 'feed'` 门控。
- **[open→return 残留旧 floor]** → `pendingFeedFloorMs` 每次 `page.cards.arrived` 覆盖写（含 0），杜绝残留。
- **[两份 `protocol.ts` 字段漂移]** → typecheck 不抓 payload 字段 parity，需人工双改；回归靠 `AC-PROTO-*`（`MessageType` 穷举）+ 手动核对。
