# standby-covers-idle-waits — 停工就让位：待机提示覆盖所有「接下来没活干」的等待

## Why

**目标是能力，不是止损**：让同一台机器往后能挂**更多**账号。

一个账号一天真正需要浏览器的时间只有约 6 小时（Facebook 按「每日在线 6h」上限；小红书按日浏览额 150 次折算 4–6h），**占空比约 25%**。理论上一个槽位能轮 4 个账号。但今天做不到，因为**槽位根本不轮转**。

根因是系统里有两套判断，各干各的、从不说话：

- **第一套决定「这账号还要不要接着干活」**（`role-dispatcher.ts` 的 `canAutoResume()`，约 1465-1482）：看周历排期、活跃时段窗口、每日续场场数 / 分钟上限、风控状态。它说「不干了」，账号就安静下来。
- **第二套决定「要不要关浏览器、让出槽位」**（`comm/browser-standby.ts` 的 `buildBrowserStandbyHint()`）：**只看一件事**——浏览动作有没有被**风控配额**挡住、要等多久。

于是：**因「配额用完」停下来的账号会关浏览器；因「排期到点了」「今天时长跑满了」「账号被冻结了」停下来的账号，浏览器一直开着——直到明天，或者永远。**

最讽刺的是**被冻结的账号**：它是所有情形里等待最长的（可能永远不再干活），但在待机判定里「冻结」不属于「配额」，于是被明确标成「等待 0 分钟、不用让位」（`browser-standby.ts:59` 的 `hard_blocker` 分支，对上 `risk-controller.ts:85` 的 `state:frozen`）。**越是不该占着浏览器的，占得越牢。**

而现行 spec **本身就写着这条错误的判据**：`browser-cold-standby` 的「云端发布确定性的浏览器冷待机提示」要求「MUST NOT publish an eligible hint for ... other hard blockers **without a deterministic wake time**」。冻结正好落在它下面——**代码是照 spec 写的，spec 判据本身错了**。

**正确的判据不是「有没有确定的恢复时刻」，而是「解除这个阻塞需不需要浏览器」**：验证码、登录、运维手动介入**需要**浏览器开着（人要在里面操作）；冻结、排期外、时长满**不需要**（解除发生在云端 / 后台）。前者绝不能关，后者应该关。

## 算账：天花板由什么决定

| 做到哪一步 | 一天的槽位供给 | 天花板 | 先撞到什么 |
| --- | --- | --- | --- |
| 今天（不轮转） | 6 槽位，全天被占 | **6 个账号** | 槽位被闲置账号攥死 |
| + 停工就让位（**本 change**） | 6 × 14h 活跃窗口 = 84 槽位·小时 | **约 14 个** | 窗口挤爆（大家都在 9–23 点） |
| + 按账号错峰排期（后续 change） | 6 × 24h = 144 | **约 24 个** | 唤醒开销 + 安全余量 |

本 change 是第一级：**把「占 24 小时」压成「占 6 小时」**，天花板从 6 抬到约 14。

（数字为估算；单账号日均真实需时须实测，见 change `browser-slot-scheduling` task 0.2——它是天花板公式里的分母，现在是拍脑袋填的。）

## What Changes

1. **待机门槛 20 分钟 → 5 分钟，两端同改。** 门槛在云端（`browser-standby.ts:4`）和客户端（`electron/browser-cold-standby.cjs:4`）各有一份默认值，而客户端算的是 `Math.max(自己的, 云端给的)`（`browser-cold-standby.cjs:62`）——**只改云端不生效**。

2. **待机提示覆盖所有「接下来没活干」的停工来源**，统一走同一条判据「预计等待时间 ≥ 门槛 → 让位」：
   - 周历排期关闭 / 活跃时段窗口外 → 恢复时刻 = 下一个可活跃时刻
   - 每日续场场数 / 分钟已满 → 恢复时刻 = 下一个本地日界
   - 风控 `frozen` / `restricted` → **无固定恢复时刻**，改由**事件驱动唤醒**
   - 原有的风控配额等待保持不变
   - 协议里 `UiBrowserStandbyPayload.source` 早已声明 `'session'` 这个来源、**全仓无人产出**——本 change 把它用起来。

3. **无固定恢复时刻的阻塞：让位 + 事件驱动唤醒。** 冻结账号必须关浏览器（它可能永远不再干活），但**必须同时接一条「状态变了就唤醒」的路**——它没有到点定时器，只按门槛关掉而不接唤醒，就是拿一个 700MB 的浪费换一个更糟的静默故障（解冻后账号永远醒不过来）。

4. **最短持有时长（抗抖动）。** 唤醒后 SHALL 至少保持浏览器开启 3 分钟，才允许再次进入待机。把「不要频繁开关」从推断变成保证。

5. **仍然绝不做**：需求驱动的「让位 / 槽位借调」（请一个休息中的账号提前腾位子）。理由见 `browser-slot-scheduling` task 5.8——它在**任何**密度下都是错的（会掐掉正在跑的会话、绕过验证码安全闸），而本 change 是纯供给侧的，密度越高越管用。

## Impact

- **Affected specs**: `browser-cold-standby`（MODIFIED 1 条 + ADDED 3 条）
- **Affected code**:
  - `aidcp-cloud`：`src/comm/browser-standby.ts`（判据与来源）、`src/orchestrator/role-dispatcher.ts`（把 `canAutoResume` 的裁决结构化暴露）、`src/risk/resume-limits.ts`（「下一个可活跃时刻」helper）、`src/comm/ui-snapshot.ts` / `src/server.ts`（接线 + 状态变化推送）
  - `aidcp-edge`：`src/electron/browser-cold-standby.cjs`（门槛默认值 + 最短持有时长）
- **零协议改动**：`UiBrowserStandbyPayload` 字段不变（`source: 'risk' | 'session'` 早已声明），不触发 CLAUDE.md §2 的协议四处同步。
- **不驱逐任何人**：只关「已经停工」的浏览器，绝不碰正在跑的会话。

## 与 browser-slot-scheduling 的职责划分（防归档时抢同一 capability）

两个 change 都动 `browser-cold-standby`，但**不碰同一条 requirement**：

- `browser-slot-scheduling` 拥有：MODIFIED「Edge 仅在安全状态下关闭并按预测时间恢复」+ ADDED「唤醒 SHALL 原地重建浏览器层」+ ADDED「按需唤醒 SHALL 由任务触发」——即**唤醒侧与安全闸**。
- 本 change 拥有：MODIFIED「云端发布确定性的浏览器冷待机提示」+ ADDED「最短持有时长」/「无固定恢复时刻的阻塞」/「门槛两端一致」——即**待机提示的产出侧与抗抖动**。

**归档序**：`browser-slot-scheduling` 先归档（它已 33/48、且本 change 依赖它已落的「唤醒原地重建、不重启核心」这一事实——否则 5 分钟门槛的收益算不过来）。
