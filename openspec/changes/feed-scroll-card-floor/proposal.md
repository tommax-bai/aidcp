## Why

Feed 翻页目前**没有停留兜底**：两次翻页之间只有约 0.7s 的 `thinkMs`，没有任何按内容计的驻留。今天对 ECS 自动化日志的分析显示，实际观察到的 op-to-op 间隔（中位 17–25s）主要是被云端大模型评估卡片的延迟"撑"出来的**副产品**，而非设计保证。详情页停留按内容长度计算、是安全的；**暴露点在 feed 翻页这一层**——一旦把评估角色换成更快的模型，feed 翻页会掉到一两秒、呈现机器般的规律快节奏。本 change 把 feed 的"像人"从"碰巧靠模型慢"变成一条**设计保证**。

## What Changes

- 新增一条 feed 翻页节奏兜底：**按本次翻页冒出的"新卡片数"**计算一个停留时长，随翻页命令下发。
- **返回未刷新（同一批卡）→ 不加任何延迟**；**刷新/下拉冒出新卡 → 按新卡数计兜底**。新旧卡的区分复用每张卡片已自带的 `noteId`（差分于"上一批 feed 卡"的集合），**不新增任何协议消息或"刷新"标志**。
- 节奏中心值云端算、边缘只保证达标：云端 `pacing.ts` 新增 `computeFeedFloorMs(newCount)`（复用现有 tempo/fatigue 系数）；边缘新增 `ensureFeedDwell`，照详情页停留那套"只补差额、遇空值早返回"执行——**云端评估卡片的耗时被吸收进停留**（与详情页一致），只有模型比目标快时才真正补睡。
- 协议：`page.scroll` 载荷新增可选 `dwellMs?`（两份 `protocol.ts` 逐字同步）。**不新增 `MessageType`**，`page.scroll` 已在主动命令路由白名单内，白名单无需改动。
- 顺带修一处 bug：动作↔消息映射的 `scroll` 分支当前丢弃了命令参数（只透传 `reason`），改为透传 `dwellMs`（对照 `back` 分支已 spread 参数）。
- 门控与隔离：卡片到达对 feed 与 search 都会触发，本兜底的差分/标记/消费**一律限定来源为 feed**，避免搜索结果的 `noteId` 污染 feed 集合；`ensureFeedDwell` 与详情页停留锚点、触发命令均不同，**不双算**。

不是 BREAKING：新字段可选、缺省即旧行为；返回未刷新时不带 `dwellMs`，行为与现状完全一致。

## Capabilities

### New Capabilities
<!-- 无新增能力：这是既有节奏能力的扩展 -->

### Modified Capabilities
- `command-pacing`: 在现有"节奏系数收口云端 + `thinkMs`/`dwellMs` 下发 + 边缘只叠抖动并保证达标"之上，**新增 feed 翻页的按新卡数停留兜底**——返回未刷新零延迟、出新卡按数计时，中心值云端算、边缘只补差额。

## Impact

- **aidcp-cloud**：`src/risk/pacing.ts`（新增 `computeFeedFloorMs` + `FEED_FLOOR` 常量）、`src/orchestrator/role-dispatcher.ts`（卡片到达处做 `noteId` 差分算 `newCount`、暂存 `pendingFeedFloorMs`；feed 翻页下发时消费并挂 `params.dwellMs`）、`src/comm/protocol.ts`（`PageScrollPayload` 加可选 `dwellMs?`）、`src/comm/command-bridge.ts`（`scroll` 分支透传 `dwellMs`）；"上一批 feed 卡"的 `noteId` 集合存于会话上下文，仅 feed 来源写入。
- **aidcp-edge**：`src/comm/protocol.ts`（`PageScrollPayload` 加可选 `dwellMs?`，与云端逐字一致）、`src/browse/browse-session.ts`（新增 `ensureFeedDwell`、`feedCardsArrivedAt` 锚点在卡片上报处刷新、`page.scroll` 处理开头 scrollNext 之前调用）。
- **docs**：`docs/protocol.md` 的 `page.scroll` 字段列表补一个可选 `dwellMs`（消息计数不变）。
- **关系（避免撞车）**：扩展 `command-pacing`；与活跃 change `recency-aware-revisit-pacing`（用 `_recentEvaluatedIds` 做 familiarity/`thinkMs` 折扣）**不冲突**——本 change 刻意用**独立的"上一批 feed 卡"集合**做 feed 停留兜底，不复用也不改动 `_recentEvaluatedIds` 及其折扣逻辑。
- **回归红线**：`AC-PROTO-*`（两份 `protocol.ts` 不漂移）必须全过。
