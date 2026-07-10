## Why

在小红书 explore feed 上，当前浏览闭环找不到可开的笔记时会**无止境地向下滚动**——既没有「已浏览卡片数」计数器，也没有 feed 深度上限，只靠会话时长 / 动作数上限收口。这种深度盲滚既不像真人、也把账号暴露在异常行为特征下。真人到一定深度会点右下角「刷新」按钮，从第一条重新开始。

本 change 让系统在会话内累计浏览到一定数量的 feed 卡片后，**不再继续向下滚，而是主动点击 feed 右下角的「刷新」按钮**，让 feed 回到顶部、换出全新一批，然后计数归零、周期性重复。

## What Changes

- 新增 cloud→edge 主动控制命令 `feed.refresh`（**独立消息类型**，非复用 `page.scroll`）：指示执行端点击 explore feed 右下角悬浮的「刷新」按钮。
- 云端 per-session 新增「已浏览 feed 卡片数」计数器（`SessionContext`），在结构化上报 feed 卡片时按「本批新卡数」累加（只在 feed 页计数，搜索结果页不计）。
- 云端 feed 滚动决策处新增「到阈值改刷新」分支：滚动决策点先判是否已达阈值，达到则改发 `feed.refresh`、计数与连续滚动数归零，否则维持原有「滚 / 转搜索」逻辑。阈值默认约 60 张（env `AIDCP_FEED_REFRESH_AFTER` 可调回 200），功能默认开启、env `AIDCP_FEED_REFRESH=false` 为总开关兜底。
- 执行端新增 `feed.refresh` 处理：复用现有「点击 + 后置校验」模板（页面上下文闸 → 定位刷新按钮 → 验证码复检 → 拟人点击 → 轮询确认「滚动归零 + 首卡 noteId 换新」），**诚实回执**成功 / 失败原因，绝不静默假成功；成功才上报新一批卡片。
- 协议四处同步 + 执行端主动命令白名单 + 执行端 switch 分支 + 内部事件（详见 design / tasks）。
- 修正 `docs/protocol.md` 头部**过期的消息类型计数**（现写 61，实际代码 70），随本命令 +1 到 71。
- 落定标定探针 `aidcp-edge/scripts/feed-refresh-button-probe.ts`（真机确认按钮结构与刷新行为）。

## Capabilities

### New Capabilities
- `feed-depth-refresh`: 会话内浏览 feed 卡片累计到阈值后，改为点击右下角「刷新」回到顶部换新批的行为契约——计数与复位语义、阈值 / 开关、诚实回执（按钮不存在 / 非 feed 页 / 点击未生效均如实失败）、失败后浏览闭环续跑不死锁。

### Modified Capabilities
- `browse-loop-resilience`: feed 滚动闭环新增一条「深度到阈值 → 刷新回顶」的续跑路径；刷新成功以新一批 `page.cards` 单次驱动、失败走既有失败兜底滚动，保证闭环不因刷新分支死锁。

## Impact

- **aidcp-cloud**：`src/comm/protocol.ts`（新消息类型 + payload）、`src/comm/command-bridge.ts`（`refresh`→`feed.refresh` 映射）、`src/orchestrator/role-dispatcher.ts`（`EdgeCommand.action` 并集 + `feed.refresh.needed` 翻译 + `page.cards.arrived` 计数 + 失败兜底）、`src/agents/session-context.ts`（计数器）、`src/agents/feed-scroller.ts`（阈值分支 + env 开关）、`src/event-bus/types.ts`（内部事件）、`test/acceptance/protocol-contract.test.ts`（`AC-PROTO` 计数 71）。
- **aidcp-edge**：`src/comm/protocol.ts`（与云端逐字一致）、`src/client/edge-client.ts`（onMessage 主动命令白名单——typecheck 抓不到，漏则静默丢弃）、`src/browse/browse-session.ts`（switch 分支 + `refreshFeed` 处理器）、`test/acceptance/protocol-contract.test.ts`、`scripts/feed-refresh-button-probe.ts`。
- **aidcp（本仓）**：`docs/protocol.md`（计数修正 + §2.3 表新增行）。
- **协议**：`PROTOCOL_VERSION` 不变（仍为 2）；新增一个 cloud→edge 命令消息，消息类型总数 70→71。
- **风控 / 配额**：刷新是导航类动作，计入会话动作数、**不**消耗互动风控配额；经统一命令出口下发，软暂停期间自动抑制。
- **部署**：随 dev 默认部署上线、默认开启，env kill-switch 可秒级关闭回滚。真机验收项（真机点刷新是否真换新批）登记到 `docs/real-machine-acceptance-backlog.md`。
