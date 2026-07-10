# Design — pacing-fallback-hardening

## 溯源结论（先坐实现状）

节奏兜底有两个物理载体，命运相反：

| 载体 | 内容 | 下发路径 | 边缘消费 | 现状 |
|---|---|---|---|---|
| A. welcome 快照 | `{ tempo, opFloorsMs }` | `welcome` 回 hello（`handler.ts:411`） | `edge-client.ts:257` 缓存 → `main.ts:640-647` 灌进 BrowseSession → `effectiveFloor()`（`browse-session.ts:484` `raw*this.tempo`）| **生效**（有洞） |
| B. session.budget 极薄默认块 | `{ tempo, dwellFloorMs }` | `session.budget` 回 request（`handler.ts:438`） | **无**：边缘不发 `session.budget.request`（reserved，`edge-client.ts:376`）、`onMessage` 白名单无 `session.budget`、`SessionBudgetPayload.pacing` 无 reader | **双死** |

tempo 联动现状：边缘唯一一处 `this.tempo` 乘法在 `effectiveFloor`（三个 gated op `action`/`card_gap`/`scroll` 的最小间隔）；`ensureDetailDwell`/`ensureFeedDwell`/`thinkBefore` 均不叠 tempo。tempo 握手期采一次、仅（重）连接边界经 `applyPacingSnapshot` 刷新。

## 三条真实缺口的最小修法

### 缺口 1 — 中途档位传播（`pacing.update`）

**取舍**：候选三种。
- (a) piggyback tempo 进每条命令 params——污染大量 payload 或走未类型化侧信道，与本仓「显式协议契约」价值观相悖。
- (b) 订阅风控状态机 transition 直推——须动 `risk-state-machine.ts`（§7 敏感单写热点），耦合过深。
- (c) **统一命令出口检测 tempo 变化去抖推送**（选定）——`role-dispatcher` 本就在每条命令读 `getRiskStatus()`；在统一出口 `sendCommand` 顶端比 `tempoForStatus(getRiskStatus())` 与 `lastPushedTempo`，变则先经 `rawSendCommand` 发一条 `pacing.update`。不碰风控状态机、不污染业务 payload、显式类型化。

**为何独立消息而非复用命令字段**：`tempo` 是会话级、变化稀疏的标量；独立 `pacing.update` 单一职责、复用边缘既有 `applyPacingSnapshot` 机理、显式进协议表可审计。代价是消息类型 +1、与并发 `feed-refresh-on-depth` 撞 `protocol.ts` 计数——机械 rebase 串行解决（§7「开发并行、集成串行」）。

**边缘应用**：新增 `applyTempoUpdate(tempo)`，只更 `this.tempo`（校验正数）、**不动 `lastActionEndAt`**（区别于 `applyPacingSnapshot` 的重连语义会清锚点）。中途刷新不得借机跳过一次最小间隔。

**去抖 + 基线**：`lastPushedTempo` 在 dispatcher 构造期初始化为 `tempoForStatus(getRiskStatus())`（= welcome 已下发值，try/catch 兜底 1.0），故会话初不冗余推一条；仅档位真变才推。

**旁路闸**：`pacing.update` 走 `rawSendCommand`（统一出口内的软暂停/配额/去重闸**之前**），控制消息不应被暂停抑制、不占配额。

### 缺口 2 — 边缘停留兜底叠档位

`ensureDetailDwell`：`center = dwellMs>0 ? dwellMs : sampleDelay(dwellFloorTiming)*this.tempo`。**只对采样兜底叠 tempo**，云端已下发的 `dwellMs` 不再叠（`computeDwellMs` 已烘 `tempoForStatus`，二次叠会 double-count）。feed 侧无停留兜底（无新卡即不停，见下「误报」），故不动。

### 缺口 3 — 移除 `session.budget.pacing`

删两端 `PacingDefaultsPayload` + `SessionBudgetPayload.pacing`、云端 `buildPacingDefaults`/`PacingDefaults`/`onSessionBudgetRequest` 的 `pacing:` 字段与 import、`risk/index.ts` 导出、`test/risk-pacing.test.ts` 相关用例。`session.budget` 其余字段（`SessionBudget.snapshot()` + `viewOnly`）不动。现役 spec 已把该通道判为废弃，本 change 只是让协议与现实一致。

## 两条误报 — 记录为设计意图（不改代码）

- **feed 翻页无停留兜底**：`command-pacing` spec「feed 翻页携带按新卡数计的可选停留时长」+「边缘保证 feed 翻页停留达标」明确「无 `dwellMs` → 立即翻页、不叠加任何额外延迟」。无新卡就是该快速划过；`page.scroll` 不叠最小间隔亦为 spec 场景「无停留字段立即翻页」所定。给它加停留/最小间隔会违反 spec 且落在并发 `feed-refresh-on-depth` 正在重写的 feed 回路里——不做。
- **`content_read`/`content_glance` 边缘不用**：spec「兜底 floor 全局后台可配置」明列可配四类为 `action`/`scroll`/`card_gap`/`detail_dwell`。`content_*` 是云端 `computeDwellMs` 的夹逼界，`feed_card_read` 是云端 feed 停留基数——都收口云端，边缘收到不 gating 属正常，非缺口。

## 不做（YAGNI）

- 不接「风控状态迁移接真实平台封号/限流信号」——那是独立未实装能力（CLAUDE.md §2 已知缺口）；本 change 只把**一旦升档就能实时到边缘**的管道补上，档位平时仍多停在 `normal`（缺口 1 当前 latent、无实际行为变化，属未来铺路）。
- 不给 `pacing.update` 加 env 开关——无变化不发（零回归），有变化才发一条极小控制消息，无需 kill-switch。
- 不重推 `opFloorsMs`（floor 由后台配置变、非会话中途变）——`pacing.update` 只带 `tempo`。

## 风险与回归红线

- **静默丢弃**：`pacing.update` 是独立主动命令，MUST 进边缘 `onMessage` 白名单（typecheck 抓不到，前车 notification-monitor 活锁）。回归断言路由放行。
- **协议不漂移**：两端 `protocol.ts` 逐字一致（`Record<MessageType,true>` 穷举）；`AC-PROTO` 计数同步 +1。
- **不重置锚点**：`applyTempoUpdate` 不碰 `lastActionEndAt`（回归断言）。
- **不 double-count tempo**：云端 `dwellMs` 路径边缘不叠 tempo（回归断言：给定 `dwellMs` 时兜底停留不随 `this.tempo` 变）。
