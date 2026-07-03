# 节奏兜底后台可调 + 最小间隔语义 — 设计

> 一句话：把边缘「每类操作后无条件附加的固定等待」做两件事——① 数值从硬编码常量抽成后台可编辑配置；② 语义从「无脑加一段」改成「最小间隔」（记住上次操作完成时刻，下一个操作到达时够久就立即执行、不够只补差额，云端往返时间被自然吸收、绝不与兜底累加）。作用域=全局一套（保留风控档 tempo / fatigue 联动，留账号覆盖扩展缝）；粒度=每类操作独立数值。
>
> 本稿已吸收三份对抗评审（YAGNI / 约束违背 / 失败模式）的裁定，逐条在正文标注「裁定 + 理由」。

---

## 0. 关键裁定速览（三评审分歧处的终审）

| # | 议题 | 三评审立场 | 终审裁定 | 理由 |
|---|---|---|---|---|
| A | **下发通道** | 三份调研默认搭 `session.budget.pacing`；草案改走 `welcome` 握手 | **走 `welcome`** | `session.budget` 是死通道（边缘从不请求、不在主动命令白名单、会落「暂忽略」被丢）；`welcome` 是 `hello` 的请求/响应，按 pending-id 命中返回，**永不经过主动命令白名单**（`edge-client.ts:331-337` 先于 `:346` 返回），零白名单遗漏风险。 |
| B | **op 粒度** | R1 砍 6→4 | **v1 = `{action, scroll, card_gap, detail_dwell}` 四行** | 现役拟人节奏只有 3 个 gate 相关预设（`action`/`scroll`/`cardGap`），`action` 一档已覆盖 open/like/collect/follow/comment。拆成 open/interact/back 是发明现役不存在、也无证据需要的区分。命令→op 映射留边缘代码，日后拆分零 schema 成本。这不违背「每类操作独立数值」——只是把「类」定义成与现役模型对齐的真实 3 类 + dwell floor。 |
| C | **`sigma_pct` 配置列 / 协议字段** | R1 砍（投机 schema）；R3 保留并当防指纹旋钮 | **砍配置列与协议字段；防指纹改在边缘采样实现（reflect + 内置 σ 略放宽）** | σ 现役每预设硬编码，运营调 σ 属 YAGNI。R3 关切的「硬左壁指纹」真正的更优解是**边缘反射采样**（越界值反弹回分布、消掉竖直壁），比暴露 σ 更彻底且零配置面。协议 payload 是最贵的热点改动，瘦成 `{minMs,maxMs}`。 |
| D | **通知巡视 gating** | R1 砍出 v1 | **v1 只收口浏览闭环；通知巡视 fast-follow** | 非核心诉求，且是 `back` op 歧义来源，砍掉同时消歧、缩小改造面。 |
| E | **`{min,max}` vs 单个「中位」值** | R1 建议只暴露中位数 | **保留 `{min,max}` 区间** | 现役 `makeDwellFloorTiming`（`browse-session.ts:151`）已从 `{min,max}` 派生分布、被本设计当 detail_dwell 模板直接复用——不是新造映射；`{min,max}` 对「最小间隔」语义更直观（运营看「这类动作等 X~Y 秒」），移动整段区间即移动中心，未丢中心控制。 |
| F | **tempo** | R1 降级+断言 1.0≡无；R2 要求如实写「握手冻结」；R3 要求重连重注入 | **保留 tempo 标量随快照下发；重连时重注入（correctness）；中途非重连升级不收紧 floor、如实文档化；断言 1.0≡无 tempo；不建任何推流刷新** | 用户既定决策要求保留风控档联动。重连重注入是修 R3 最严重缺口（见 §7），非「刷新机制」。 |
| G | **看门狗 lockstep** | R2 要具体 CAP+接线；R3 要跨 store 代码级约束 | **CAP=15_000ms 小常量，结构上 < `IDLE_NUDGE_MIN_MS`(200_000)；在 resume-limits 不变量测试加常量关系断言 tripwire** | CAP 是代码常量而非配置，floor 恒 ≤15s ≪ 200s，R3 的「两 store 各调击穿」场景被小 CAP 结构性消除；再加编译期/测试期断言防未来有人下调 idle 下限。 |

---

## 1. 背景与现状（带 文件:行）

### 1.1 边缘现状：兜底延迟散落、硬编码、且语义是「无条件累加」

- **拟人节奏预设**（`aidcp-edge/src/humanize/timing.ts:37-46`）：全套 gate 相关只有 3 个 lognormal 预设——`action{mu:ln(2500),σ:0.3}`（覆盖 like/collect/follow/comment/open）、`scroll{ln(800),σ:0.3}`、`cardGap{ln(5000),σ:0.4}`；第 4 个 `reading` 是 dwell/内容预设。**σ 每预设硬编码**。
- **采样硬裁边界**：`sampleDelay`（`timing.ts:67`）对越界样本做 `Math.min(hi, Math.max(lo, raw))` **硬裁到 `[min,max]`**——这是后文防指纹「硬左壁」的根因。
- **动作前犹豫**：`thinkBefore`（`browse-session.ts:237-241`）**无条件附加** `jitterAround(thinkMs)`，thinkMs 由云端下发。
- **互动/卡间/滚动前 humanPause**（`browse-session.ts:1097/1166/1289/1418`，分发层 `:575/754`）：**无条件附加** `sampleDelay×fatigue`——「操作后兜底累加」的实体。
- **已达标的最小间隔模板**：`ensureDetailDwell`（`browse-session.ts:249-260`，锚 `noteOpenedAt`→补差额）与 `ensureFeedDwell`（`:269-279`，锚 `feedCardsArrivedAt`、消费云端 `dwellMs`）**已经是「记锚点、只补差额」语义**——本设计的参考样板。
- **裸 pad**：关注点击后 `sleep(1500)`（`:1426`）、评论码前 `sleep(300)`（`:1284`）。
- **时钟**：`this.now` 默认 `Date.now`（**墙钟**，`browse-session.ts:229`，注释自称单调实为墙钟）。
- **sleep 不可打断**：`this.sleep` 是裸 `setTimeout`（`browse-session.ts:143`）——停止/结束命令在等待期只入队（`:430`），要等 sleep 自然醒。
- **死参数 `dwellFloorMs`**：`main.ts` 组装 `browseOpts` 时今天只塞 `exploreUrl`，`options.dwellFloorMs` 从不触发——本设计正好接活它。
- **握手**：`edge-client.ts:160-170` `request('hello')`（15s 超时）；`main.ts:382/386` 只构造一次 `BrowseSession`；身份翻转重连 `reestablishIdentity`（`main.ts:366/371`）`close()`→`connect()` 重新握手后 `browse?.start()` **复用同一对象、不重注入**；握手失败被 `main.ts:562` 当致命错误非零退出。

### 1.2 云端现状：节奏常量集中、tempo/fatigue 骨架、welcome 只用一个字段

- 常量全在 `aidcp-cloud/src/risk/pacing.ts`：`DWELL_FLOOR_MS={2500,5000}`（`:41`）、`tempoForStatus`（`:52-64`，normal 1.0/warned 1.3/restricted 1.6）、`fatigueMultiplier`（`:70-75`）、`computeDwellMs`（`:97`）/`computeThinkMs`（`:111`）**每条命令用 fresh status 重算**、`FEED_FLOOR`（`:123`，内容模型）。
- `WelcomePayload` 现仅 `{sessionId, serverVersion}`（`protocol.ts:115-119`），边缘只取 `sessionId`、其余丢弃。
- `onHello`（`handler.ts:320-345`）组装 welcome；`controllerFor`（`:151-153`）纯解析已存在 controller、不构造不写；`getState`（`risk-controller.ts:101`）纯读，写只在 `record()`/`transition()`/quota（`:87/117/129`）。**读 status 不触发任何风控写**。`session.accountId` 在 `handler.ts:325` 已可得。
- 看门狗：`DEFAULT_IDLE_NUDGE_MS=240_000`（`resume-limits.ts:25`）可后台热调、下限 `IDLE_NUDGE_MIN_MS=200_000`（`:34`）；MUST 不变量（`:21-25`）要求 idleNudge > max(180s 模型天花板, 90s 详情停留封顶)。
- **契约测试盲区**：`test/acceptance/protocol-contract.test.ts:56` 的 AC-PROTO 只断言 `MessageType` 总数=56、版本=2、信封可构造、JSON 往返——**不比较 `WelcomePayload` 字段**。加可选 `pacing?` 不新增 MessageType，计数断言不动，两仓各自 `typecheck` 各自过 → **payload 字段漂移静默**。
- 配置范式：`quota-config-store.ts`（`:83` validInt、`:107/112` init/reload、`:153/158/166` UPSERT+审计）；schema 启动自建、无迁移器。

### 1.3 现有并发活跃 change 与本设计的文件竞争（R2 #2，落地前必须协调）

- `panel-server.ts` / `panel/types.ts` / console `queries.ts`·`types/api.ts`·**`QuotasPage.tsx`** — 撞 `console-cloud-panel-hardening`。
- `browse-session.ts` 命令入口区 — 撞 `comment-search-command`、`fix-interaction-and-comment-capture`。
- `edge-client.ts` / `main.ts` — 撞 `edge-companion-ui`。
- `pacing.ts` — 可能撞 `category-adaptive-images-and-judgment`。

**裁定**：按 §7 并行纪律「开发并行、集成串行」——落地前 `fetch`+rebase 到最新 master，把上述文件当竞争区、rebase 后再 build，**绝不 force**；在 change 里显式登记集成顺序。

---

## 2. 目标与非目标

### 目标
1. 各类操作后的兜底延迟从硬编码常量 → 后台（console）可编辑、存 PostgreSQL、热加载。
2. 语义从「无条件附加固定等待」→「最小间隔 gating」：单锚点记上次操作完成时刻，下个操作到达时 `remaining = max(0, floor − elapsed)`，够久立即执行、不够只补差额，**云端往返被 `elapsed` 吸收、绝不累加**。
3. 全局一套配置，保留风控档 tempo（标量下发、边缘乘算）+ fatigue（边缘侧真值）联动。
4. 每类操作（`action`/`scroll`/`card_gap`/`detail_dwell`）独立数值。
5. 守死红线：配置只能抬高延迟、**永远抬不穿非零下限**（绝不零延迟）；**绝不静默假成功**（功能性 settle / 轮询排除在 gating 外）。

### 非目标（v1 明确不做，YAGNI 延后）
- **不做配置版本号**（welcome 现读、无缓存无漂移窗口，没有它要解的问题）。
- **不建账号 scope 列 / 不穿 accountId**（仅留文档+迁移注记扩展缝，见 §8）。
- **不建 `sigma_pct` 配置列 / 协议字段**（防指纹改边缘采样实现，见 §7）。
- **不配置化内容模型族**（`READ.*`/glance/familiar/`FEED_FLOOR`/think base）——留单行表扩展缝、v1 不建。
- **不接通知巡视 gating**（fast-follow）。
- **不动发布链 `PACING_MS`**（与 CommandSequencer ~30s 单步超时耦合，独立通道）。
- **不接「真实平台封号/限流信号驱动状态迁移」**（现役 tempo 几乎恒 1.0，非本设计范围）。
- **不建任何 tempo/配置的会话内推流刷新机制**（生效边界=连接级，见 §7）。

---

## 3. 核心语义：最小间隔 gating（不累加等待与兜底）

### 3.1 边缘侧行为骨架

```
// 单调时钟：单一实现、单一注入口；进程启动时二选一固定，运行期不切换；只自身前后作差、绝不跨基准、绝不持久化
monoNow(): number                       // 优先 performance.now()，备选 hrtime.bigint()/1e6

lastActionEndAt: number | null = null   // 单锚点=上次操作完成时刻（会话内内存、单进程；重启/重连即 null，首操作跳过间隔）
opFloorCfg: Partial<Record<PacingOp,{minMs,maxMs}>> // welcome 快照注入；重连时 applyPacingSnapshot 刷新
tempo = 1.0                             // welcome 快照标量；重连刷新

// 每类操作的有效 floor：配置区间「反射采样」× tempo × edgeFatigue，夹在 [opMinFloor[op], CAP]
effectiveFloor(op): number {
  const cfg   = opFloorCfg[op] ?? BUILTIN_FLOOR[op]              // 逐 op 回落非零内置
  const scale = tempo * rhythm.getSpeedFactor(progress())        // tempo 来自快照、fatigue 边缘真值
  const raw   = sampleReflect(cfg.minMs, cfg.maxMs, BUILTIN_SIGMA[op])  // 反射采样：消硬左壁（见 §7 防指纹）
  return clampEdge(raw * scale, opMinFloor[op], CAP_MS)          // 边缘二次夹（第三道）
}

// 动作前统一闸：折 thinkBefore + 最小间隔，同一跨度只比一次、用 max 不用 +
async gateBeforeAction(op, thinkMs?) {
  const think = thinkMs && thinkMs > 0 ? jitterAround(thinkMs, 0.25, random) : 0
  let remaining = 0
  if (lastActionEndAt != null) {
    const floor   = effectiveFloor(op)                  // 现采样一次，勿在循环里重采
    const elapsed = monoNow() - lastActionEndAt         // 含云端 RTT / 决策 / LLM 时间
    remaining     = Math.max(0, floor - elapsed)        // 只补差额；elapsed≥floor 则补 0
  }
  const wait = Math.max(remaining, think)               // ← max，绝不 +
  if (wait > 0) await sleepInterruptible(wait)          // 单次 sleep；可被 stopRequested / 命令到达唤醒
}

// 每条命令执行完（原子动作 + 其功能性 settle + uplink 之后）记账
markActionEnd() { lastActionEndAt = monoNow() }
```

### 3.2 六条精确不变量

1. **基准 = 上次操作完成时刻**（单锚点 `lastActionEndAt`），非命令下发时刻、非 per-kind Map。对齐诉求「记住上次操作完成时刻」。
2. **单调时钟**（`monoNow`），防 NTP/改表/休眠致 `elapsed` 变负（卡死）或暴增（失效）；绝不持久化、绝不跨进程/跨基准比较；重启/重连丢弃重置。
3. **只补差额、吸收 RTT**：`remaining = max(0, floor − elapsed)`，云端往返计入 `elapsed`，**天然不累加**。
4. **floor 自带随机（防指纹）**：每次现采样，被补齐的间隔散布成分布而非堆一根针；采样用**反射**而非硬裁（见 §7）。
5. **绝不零延迟 = 有效间隔恒 > 0，不是每次都额外 sleep**：有效间隔 = `max(elapsed, floor)`，floor 夹 `opMinFloor[op] > 0` → 恒 ≥ 非零下限；`remaining==0`（RTT 已够）时由 `think>0`（有云端指令）兜底；首操作无锚点跳过间隔，由会话起点初始扫描延迟（`browse-session.ts:314-319`）兜住。
6. **两层同轴取 max、每 span 一次；dwell 层独立不串联**：think（动作前犹豫）+ 最小间隔测同一「now→执行本动作」跨度 → 一处 max；detail-dwell / feed-dwell 测另一跨度（离页前总停留），保留各自锚点，**不与动作间隔叠闸**（防双计）。

### 3.3 逐操作裁定（纳入 / 原样 / 排除）

| 操作 | 现状 | 裁定 | 理由 |
|---|---|---|---|
| note.open / profile.open 前 `thinkBefore` | 无条件附加 | **纳入** → `gateBeforeAction('action', thinkMs)` | 主改造点 |
| interaction.like/collect/follow/comment/like_comment 前 | 无条件附加 | **纳入** → `gateBeforeAction('action', thinkMs)` | 与现役 `action` 预设覆盖面一致 |
| note.browse_images 前 | 无条件附加 | **纳入** → `gateBeforeAction('card_gap', thinkMs)` | — |
| note.scroll_comments 前 | 无条件附加 | **纳入** → `gateBeforeAction('scroll', thinkMs)` | — |
| 处理器内**引导性**轻停顿 `humanPause`（`:1097/1166/1289/1418`） | 无条件附加 | **删除**（被入口 gate 覆盖） | 累加根因；仅删「引导性」那一个 |
| 命令内**子步骤间**微停顿（如开评论框↔输入↔提交之间） | — | **保留** | 属独立人类微动作、非「操作后兜底」；删了会让多步命令机械化秒过 |
| 详情页离页停留 `ensureDetailDwell` | 已是最小间隔 | **保留机制，仅 floor 源改配置**（`detail_dwell` 行替 `DEFAULT_DWELL_FLOOR_MS`，复活死参数 `dwellFloorMs`） | 已达标、是本设计模板 |
| feed 翻页看新卡 `ensureFeedDwell` | 已是最小间隔（消费云端 `dwellMs`） | **原样保留** | floor 来自云端内容×卡数模型，属内容族 v1 不动 |
| page.scroll / navigation.back / note.close 的间隔 | 已走 dwell 层 | **原样**，不再叠动作间隔闸 | 防与 dwell 层双计 |
| 功能性 settle（等页面加载/编辑器出现/重渲染窗） | 固定 sleep | **排除（红线）** | 折进会打断真实前置条件 → 静默假成功 |
| 有界轮询/复检（`pollDomUntil`/`waitFor*`） | 命中即返回 | **排除** | 非附加睡眠 |
| 关注后 `sleep(1500)` / 评论码前 `sleep(300)` | 裸 pad | **v1 保留、标清理缝**（见 §9） | 边际 |
| 通知巡视（notification.open/back_home/browse_*） | 无条件附加 | **v1 排除、fast-follow** | 非核心诉求、消 `back` op 歧义 |
| 搜索子流程 humanPause（search-handler） | 无条件附加 | **fast-follow**（复用同 helper） | v1 先收口 browse-session |
| 发布链 `PACING_MS` | 独立通道 | **排除** | 与 CommandSequencer 超时耦合 |

---

## 4. 分层设计

### 4.1 云端：配置存储（PG schema）+ 读取门面 + pacing 计算改造

#### PG 表（照搬 quota_config「每 key 一行」，权威 SQL 内联 store）

```sql
-- migrations/0031_pacing_floor_config.sql（台账，不被迁移器执行；权威副本内联 store 的 SCHEMA_SQL，init() 跑）
CREATE TABLE IF NOT EXISTS pacing_floor_config (
  operation   TEXT PRIMARY KEY,        -- op 白名单：action | scroll | card_gap | detail_dwell
  min_ms      INTEGER NOT NULL,
  max_ms      INTEGER NOT NULL,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_by  TEXT
);
-- 无 sigma_pct 列（裁定 C：防指纹改边缘采样，运营调 σ 属 YAGNI）
-- 账号覆盖扩展缝（v1 不建，见 §8）：ALTER ADD COLUMN scope，主键改 (scope, operation)
```

- **表空 = 逐项回落内置默认**（= 现役预设/`DWELL_FLOOR_MS` 量级），零回归。
- **范围约束放读出口 clamp（权威），不靠 DB CHECK**（有人可 psql 直插绕面板——与「schema 启动自建、有人直写」现实吻合）。

#### 读取门面（照搬 `quota-config-store.ts`）

**新建 `src/config/pacing-config-store.ts`**（`implements PacingFloorProvider`）：
- 内联 `PACING_FLOOR_SCHEMA_SQL` 幂等建表，`init()` 跑 SCHEMA → `reload()`。
- **`reload()` 用「构建新 Map → 原子替换引用 `this.cache = next`」**，非原地 `clear()`+`fill`（R3 5a：防握手正好读到半填 Map → 该 op 缺失回落默认、不可复现）。`floorFor` 只读引用快照。
- `validInt()` 数字校验；脏行/未知 op 忽略。
- `floorFor(op): {minMs,maxMs}`——运行时每次现读、零 IO、逐项回落非零内置默认，**并在此 clamp 到 `[opMinFloor[op], CAP_MS]`**（权威夹点：即便有人 psql 直插 0/负数/超界，离开云端进程前已夹成非零合法）。
- `getAll()`/`getRow()`（面板读）；`set()` = UPSERT `ON CONFLICT DO UPDATE` + 先写库后刷镜像 + 审计。

**新建 `src/config/pacing-config-facade.ts`** `createPacingConfigPanel({store})`：
- `buildCatalog()`：生效值 + `overridden`（库内有行否）+ 审计字段。
- 校验：`operation` 在白名单（否则 `unknown_operation`）；`min_ms/max_ms` 非负整数、`min ≤ max`、`≤ CAP`（否则 `invalid_value`）；**最小展宽 `max_ms ≥ min_ms × 1.5`**（R2 gap A：防 `min==max` 零展宽退化、复活直方图尖峰）；整块拒不部分落库。

#### pacing 计算改造（`src/risk/pacing.ts`）
- 新增 `buildPacingSnapshot(status, provider): PacingSnapshotPayload | undefined`，**total 函数**——整体 try/catch，取 status 失败/store 抛错一律**返回 undefined（省略 pacing 字段）**（R3 1a：绝不让它进入 welcome 失败路径 brick 握手）。`tempo = tempoForStatus(status)`；`opFloorsMs` = 逐 op `clamp(provider.floorFor(op))`。
- 骨架不变：仍以「配置基础 × tempo × fatigue」，`status`/`progress` 输入链不动。`DWELL_FLOOR_MS`/tempo 表保留。

### 4.2 下发协议：`PacingDefaultsPayload` 扩展 + 协议四处同步影响面 + 向后兼容

> 本节标题的 `PacingDefaultsPayload` 即实装类型 `PacingSnapshotPayload`（承载 tempo + 每类操作 floor 默认区间）。

#### payload 扩展（两份 `protocol.ts` 逐字一致）

```ts
export type PacingOp = 'action' | 'scroll' | 'card_gap' | 'detail_dwell';

export interface PacingFloorPayload {
  minMs: number;
  maxMs: number;           // 无 sigmaPct（裁定 C）
}

export interface PacingSnapshotPayload {
  tempo: number;                                        // 风控档标量，边缘乘算
  opFloorsMs: Partial<Record<PacingOp, PacingFloorPayload>>;  // 已含 clamp 护栏、非零
}

export interface WelcomePayload {
  sessionId: string;
  serverVersion: string;
  pacing?: PacingSnapshotPayload;                       // 新增、可选（旧端忽略）
}
```

- 云端 `onHello`（`handler.ts:341`）回 welcome 时加 `pacing: buildPacingSnapshot(controllerFor(session).getState().status, pacingConfigStore)`；握手早于风控态建立则回落 `normal`（tempo=1.0），安全。**纯读、不写风控态**（已核实 §1.2）。

#### 协议四处同步完整影响面

| 同步点 | 是否改 | 说明 |
|---|---|---|
| **edge + cloud 两份 `src/comm/protocol.ts`** | **改（逐字一致、单写者、串行）** | 加 `PacingOp`/`PacingFloorPayload`/`PacingSnapshotPayload` + `WelcomePayload.pacing?`。 |
| **`command-bridge.ts` 动作↔消息映射** | **不改** | welcome 非动作命令。 |
| **`docs/protocol.md`** | **改（人工）** | 更新 welcome payload；不动头部 MessageType 计数（无新增消息类型）。 |
| **`edge-client.ts` 主动命令路由白名单** | **不改** | welcome 是 `request('hello')` 响应，按 pending-id 在 `:331-337` 命中返回、**永不到 `:346` 主动命令分支、更不落 `:388` 暂忽略**。这是选 welcome 的关键红利：零白名单遗漏风险。 |

**关键补强（R2 #1 / R3 1b：漂移无人守）**：AC-PROTO 只数 `MessageType`（`protocol-contract.test.ts:56`）、typecheck 的 `Record<MessageType,true>` 也抓不到 payload 字段漂移——本设计的漂移风险**恰落在双盲区**。故：**两份 proto 契约测试各加一条 `WelcomePayload`+`PacingSnapshotPayload` 结构化断言**，用**同一份填满全字段的样例常量**（像 `ALL_MESSAGE_TYPES` 那样逐字人工同步），断言每字段 JSON 往返存活。别把 AC-PROTO 当 welcome payload 的安全网。

#### 向后兼容（新旧任意组合不 brick）
- 旧 edge 不认 `pacing` → 忽略、用内置默认 → 非零降级、无回归。
- 旧 cloud 不发 `pacing` → 新 edge 收 `undefined` → 内置默认 → 非零。
- **逐字段回落（非全有全无）**：`effectiveFloor(op) = validPositive(wire[op]) ?? BUILTIN_FLOOR[op]`；`scroll` 缺只 `scroll` 回落。**绝不回落 0**——`BUILTIN_FLOOR` 继承现役下限量级、天然非零，边缘再夹 `Math.max(opMinFloor[op], ·)`。

### 4.3 边缘：min-interval gating 落点 + 单调时钟 + 复用补差额 + 看门狗不冲突

#### 落点（`aidcp-edge/src/browse/browse-session.ts`）
- 新增状态：`lastActionEndAt`（单调）、`opFloorCfg`、`tempo`。
- 新增 `monoNow()`（单一实现、单一注入口，便于单测给可控递增；进程启动二选一固定，运行期不切换；只自身作差）。新锚点用 `monoNow`；既有 `noteOpenedAt`/`feedCardsArrivedAt` 沿用墙钟、短时长历史稳定，**v1 不迁移**（低优先扩展缝）。**绝不把 monoNow 值与 Date.now 值作差**（R3 2b）。
- 新增 `ensureMinInterval(op)`：把 `ensureDetailDwell`（`:249-260`）的「锚→elapsed→只补差额」抽成通用式。
- 新增 `gateBeforeAction(op, thinkMs?)`：§3.1 骨架，折 `thinkBefore` + max 合成。按 §3.3 映射改各命令入口；删引导性 `humanPause`、保留子步骤微停顿；`ensureDetailDwell` floor 源改 welcome 下发的 `detail_dwell` 行（复活 `options.dwellFloorMs`）。
- **新增可打断 sleep 原语 `sleepInterruptible`**（R3 6a：今天 `this.sleep` 是裸 `setTimeout` 不可打断）：等待可被 `stopRequested`/命令到达唤醒，醒来立即检查 `stopRequested`/`closing`；不改 `closing` 终态语义（迟到 nudge 不复活，`:376`）。gate 只用它。
- **记账 `markActionEnd`**：放在每条命令原子动作 + 功能性 settle + **uplink（`reportActionCompleted` `edge-client.ts:257`）之后**（R3 4b：让边缘 elapsed 起点与云端 idle 起点对齐同一 uplink 事件、两把时钟量同一段 gap）。
- `onCdpReconnected`（`:364-371`）已清 `noteOpenedAt`，同处加 `lastActionEndAt = null`（重连页面已变、间隔重置、首操作跳过）。

#### 构造期 + 重连注入（修死链 + 修最严重缺口）
- `edge-client.ts` `connect()`（`:168`）：读 `welcome.payload.pacing` 存字段 + 暴露 getter。
- `main.ts:382` `browseOpts`：把 `pacing.opFloorsMs['detail_dwell']` 塞 `dwellFloorMs`、整张 `opFloorsMs` + `tempo` 透传进 `BrowseSession`。
- **`BrowseSession` 新增 `applyPacingSnapshot(opFloorsMs, tempo)`；`reestablishIdentity`（`main.ts:366-371`）在 `connect()` 之后、`browse.start()` 之前调用它，把新 welcome 的 floors/tempo 灌进复用的 BrowseSession**（R3 2a，**最严重缺口**：BrowseSession 只构造一次，重连复用同一对象不重注入 → 连接级快照在唯一原地重连路径上退化成进程级快照、风控升级到不了边缘节奏层）。这条必做。

#### 与断连兜底 / 云端 idle 看门狗（~240s）不冲突论证
1. **量级安全**：所有 floor 经读出口 clamp 到 `CAP_MS=15_000 ≪ IDLE_NUDGE_MIN_MS(200_000)`，单次前台 sleep 恒 < nudge 与 end 阈值。idle 从上条 uplink 累积 < CAP ≪ 200s，永不误触。
2. **语义是减负非加负**：相对现役「无条件加固定等待」，最小间隔正常情况**缩短**边云静默（RTT 被吸收、云端慢时立即执行）。风险不来自语义、只来自可配上界失守 → 由三道夹 + 小 CAP 根除。
3. **可打断、不改终态**：gate 用 `sleepInterruptible`；因 floor 秒级，「前台 sleep 期间命令排队」最坏积压亦被小上界兜住；`onCdpUnrecoverable`（`:373-382`）置 `closing` 后迟到 nudge 不复活，与 min-interval 正交。

### 4.4 后台：面板 API + console 编辑 UI（照搬角色配置范式）

#### 云端装配（`server.ts`，照 quota 三处）
构造 `PacingConfigStore` → `init()` → `createPacingConfigPanel` → 注入 deps `pacingConfig` → 把 `pacingConfigStore` 交 handler 供 `buildPacingSnapshot` 现读（PUT 后下次握手即新值 = 热加载）。

#### 面板 API（`panel-server.ts`，照 quotas `:793/801`）
- `GET /api/pacing`：deps 未注入 → `503 pacing_unavailable`；返 catalog（生效值 + overridden + 审计）。
- `PUT /api/pacing`：`readJsonBody` 失败 → `400`；逐字段类型闸；`updatedBy = verified.payload.sub`；错误诚实映射（`unknown_operation`→404、`invalid_value`/`no_valid_fields`→400、成功→200 view）。
- `types.ts`：加 `PanelPacingConfig`（`getCatalog`/`set`）+ `PacingConfigView/Row`；`PanelServerDeps` 加可选 `pacingConfig?`。

#### console 前端（照搬 4 处，`aidcp-console`）
- `client.ts`（`apiGet:99`/`apiPut:115`）**不改**。
- `queries.ts` 加 `usePacingConfig()`（照 `useQuotaConfig:63`，`queryKey:['config','pacing']`）。
- `types/api.ts` 加 `PacingConfigRow/View`（含 `overridden`+审计）。
- **并入现有安全页 `QuotasPage.tsx` 作一块 Card**（复用整页装配、免加导航项、YAGNI 优于独立 `/pacing`）：`Card`+`Alert`(说明)+`Table`(生效值 + 已覆盖/系统默认 Tag)+`Modal`(表单 `InputNumber` min/max)；`useMutation`(`apiPut('/api/pacing')`→invalidate 重取真态，写非乐观)；本地 canSave + 服务端二次校验双闸。
- `App.tsx`/`AppShell.tsx` **免改**。
- **Alert 必须写清三条运营预期**（R3 1c/5c/6c）：① 新配置在各节点**下次重连后生效**（生效边界=连接级，稳定 fleet 可能数小时才铺满、rollout 期行为异构）；② `detail_dwell` **仅兜底下限**、内容驱动停留由云端计算；③ 若 fleet 混版，配置**仅对新版边缘生效**。

---

## 5. 配置项清单（每类操作：字段名、默认值、允许范围、防呆下限）

| operation | 覆盖命令 | min_ms 默认 | max_ms 默认 | 防呆下限（= 读出口 clamp 下界） | CAP 上限 | 内置 σ（边缘常量，不入库） | 来源 |
|---|---|---|---|---|---|---|---|
| `action` | note.open / profile.open / interaction.* | 1500 | 4000 | 800 | 15000 | 0.3（略放宽至 0.35 备选，见 §7） | `timing.ts` action 预设 ln(2500) |
| `scroll` | note.scroll_comments（及详情内滚动） | 500 | 1500 | 300 | 15000 | 0.3 | `timing.ts` scroll 预设 ln(800) |
| `card_gap` | note.browse_images（图片翻页） | 3000 | 7000 | 1000 | 15000 | 0.4 | `timing.ts` cardGap 预设 ln(5000) |
| `detail_dwell` | ensureDetailDwell 兜底 floor | 2500 | 5000 | 1000 | 15000 | 0.25 | `pacing.ts` `DWELL_FLOOR_MS` |

**规则**：
- **默认值 = 现役内置**（表空零回归）；实装时**从 `timing.ts` 预设 / `DWELL_FLOOR_MS` 逐字提取**为准，上表为量级示意。
- **允许范围**：`min_ms ∈ [防呆下限, CAP]`、`max_ms ∈ [min_ms×1.5, CAP]`（最小展宽 1.5×，防零展宽退化打掉防指纹）。
- **防呆下限**：每 op 一个 > 0 的下界，同时是读出口 clamp 的下界；即便 psql 直插更小值，离开云端进程前被夹回。**不变量：配置只能抬高延迟、永远抬不穿这个非零下限**——「配置绕过零延迟红线」设计上不可能。
- **CAP = 15000ms 全局小常量**，结构上 < `IDLE_NUDGE_MIN_MS(200_000)`；无 `sigma_pct` 列。

---

## 6. 分仓落地任务清单（edge / cloud / console / protocol 各改哪些文件）

**aidcp-cloud**
- 新建 `src/config/pacing-config-store.ts`（`implements PacingFloorProvider` + 内联 `SCHEMA_SQL` + `reload` 原子替换 + `floorFor`(含 clamp) + `set/getAll`）。
- 新建 `src/config/pacing-config-facade.ts`（`createPacingConfigPanel`，含最小展宽 1.5× 校验）。
- 新建 `migrations/0031_pacing_floor_config.sql`（台账，不执行、无逻辑）。
- 改 `src/risk/pacing.ts`：加 **total 函数** `buildPacingSnapshot(status, provider)`（try/catch → 失败返 undefined）；定义 `CAP_MS=15_000`、`opMinFloor`、`BUILTIN_FLOOR`。
- 改 `src/comm/handler.ts:341` `onHello` → welcome 附 `pacing`（纯读 status）。
- 改 `src/comm/protocol.ts`（**热点、串行**）：加 payload 类型 + `WelcomePayload.pacing?`。
- 改 `src/panel/panel-server.ts` + `src/panel/types.ts`：`GET/PUT /api/pacing` + `PanelPacingConfig` + deps 字段。
- 改 `src/server.ts`：store 四步 + Provider 注入 handler。
- 改 `src/config/resume-limits.ts`：MUST 不变量注释追加 `PACING_OP_FLOOR_CAP_MS < IDLE_NUDGE_MIN_MS`；对应不变量测试加常量关系断言 tripwire（R2 gap B / R3 4a）。
- 测试：两份 proto 契约结构化断言（同一样例常量）；`buildPacingSnapshot` 注入必抛桩→握手仍成功回退默认（R3 1a）。

**aidcp-edge**（**热点 `protocol.ts` 与 cloud 逐字一致、串行**）
- 改 `src/comm/protocol.ts`：与 cloud 逐字一致。
- 改 `src/client/edge-client.ts:168`：读 `welcome.pacing` 存 + getter。
- 改 `src/main.ts:382/386` + `:366-371`：`browseOpts` threading `dwellFloorMs`+`opFloorsMs`+`tempo`；**`reestablishIdentity` 重连后调 `applyPacingSnapshot`**（R3 2a 必做）。
- 改 `src/browse/browse-session.ts`：加 `lastActionEndAt`/`monoNow`/`ensureMinInterval`/`gateBeforeAction`/`applyPacingSnapshot`/`sleepInterruptible`；按 §3.3 改命令入口；`markActionEnd`（uplink 之后）；`onCdpReconnected` 清锚点；`ensureDetailDwell` floor 源改配置。
- 改 `src/humanize/timing.ts`：加 `sampleReflect`（反射采样、消硬左壁；**新 helper，不改共享 `sampleDelay`**，见 §9）。
- 测试：端到端断言——云端下发**非默认** floor → 边缘 gate 实测间隔命中该值（而非内置），把「字段真被读到」变红线测试（R3 1b）；配 0/负数经三道夹后实测间隔仍 ≥ 防呆下限；云端慢回（elapsed≥floor）不额外 sleep 且不塌零、两层用 max 非 +。
- （fast-follow）`src/browse/search-handler.ts` 复用 helper；通知巡视 gating。

**aidcp-console**
- 改 `src/api/queries.ts`（`usePacingConfig`）、`src/types/api.ts`（`PacingConfigRow/View`）、`src/pages/QuotasPage.tsx`（加 Card + 三条运营预期 Alert）。`client.ts` 不改。

**docs**：`docs/protocol.md`（welcome payload；不动 MessageType 计数）。

**集成纪律**：上述 `QuotasPage.tsx`/`panel-server.ts`/`browse-session.ts` 命令入口区/`edge-client.ts`/`main.ts`/`pacing.ts` 为与 §1.3 四个活跃 change 的竞争区，集成串行、rebase 后再 build、绝不 force。

**回归红线**（改后先 `test:acceptance` 再全量 `test` 再 `typecheck`）：`AC-PROTO-*` + 新增 proto 结构化断言必过；两条最小间隔断言（三道夹非零、慢回不累加不塌零）；`buildPacingSnapshot` 抛错不 brick 握手。

---

## 7. 向后兼容与失败兜底（含绝不零延迟的夹逼、看门狗、防指纹）

| 失败模式 | 兜底 |
|---|---|
| PG 无值 / 脏行 | 逐项回落非零内置默认，读出口永不抛。**绝不回落 0**。 |
| **`buildPacingSnapshot` 抛错**（R3 1a） | **total 函数：try/catch → 省略 `pacing` 字段**，绝不进入 welcome 失败路径 brick 握手/致边缘非零退出。回归断言：必抛桩→握手仍成功回退默认。 |
| 后台配 0 / 负数 / 超界 | **三道夹**：① facade 拒（含最小展宽 1.5×）② 云端读出口 `clamp(v, 防呆下限, CAP)`（权威、防绕面板直插 PG）③ 边缘 `Math.max(防呆下限, ·)`。不变量：配置只能抬高延迟、抬不穿非零下限。 |
| **`min==max` 零展宽退化**（R2 gap A） | facade 强制 `max_ms ≥ min_ms × 1.5`，别让防呆下限和防指纹分布互相打架。 |
| 配大误触 idle 看门狗（R2 gap B / R3 4a） | `CAP_MS=15_000` 小常量、结构上 ≪ `IDLE_NUDGE_MIN_MS(200_000)`——R3「两 store 各调击穿」场景被小 CAP 结构性消除；再加 resume-limits 不变量测试的常量关系 tripwire。floor 恒 ≤15s、无法逼近 200s。 |
| **补差额硬左壁指纹**（R3 §3，防指纹只做一半） | **边缘采样从硬裁改反射**（`sampleReflect`：越界值反弹回分布内、消掉竖直左壁），内置 σ 略放宽（如 action 0.3→0.35）稀释左尾。补差额只在云端快回触发、集中在高频廉价动作（scroll/card_gap），故这两类优先反射。**已知残留指纹如实标注**：floor 全局一套 → 跨账号同一分布，非账号维度；完整解在 §8 账号覆盖缝（v1 不做）。 |
| welcome 未带 pacing（新旧混搭） | 逐字段回落、非零降级、无回归；后台 Alert 标「仅对新版边缘生效」。 |
| **协议 payload 字段漂移（静默）**（R2 #1 / R3 1b） | typecheck 与 AC-PROTO 均抓不到 → 两仓 proto 结构化断言（同一样例）+ 端到端「非默认 floor 真到边缘 gate」红线测试。 |
| 单调时钟跳变 / 跨基准作差（R3 2b） | `monoNow` 单一实现、单一注入、只自身作差、绝不持久化/跨基准/跨进程；备选时钟进程启动二选一固定。 |
| **重连不重注入配置**（R3 2a，最严重） | `applyPacingSnapshot` + `reestablishIdentity` connect 后 start 前灌入。 |
| gate sleep 挡停止（R3 6a） | `sleepInterruptible`（可被 stopRequested/命令唤醒）+ 小上界；`closing` 终态不复活。 |
| reload 半填 Map 竞态（R3 5a） | 构建新 Map → 原子替换引用；`floorFor` 只读快照。 |
| 无 uplink 动作累积 idle（R3 4b） | 每条命令路径（含失败分支）诚实 uplink；`markActionEnd` 放 uplink 之后对齐两把时钟。 |
| 首操作无锚点 | 跳过间隔（think 仍守零延迟）；会话起点初始扫描延迟兜住。 |
| **tempo 中途冻结**（R2 #5 / R3 5d，如实文档化） | welcome 是连接级快照，tempo 随快照冻结；**重连（身份翻转）重新握手时经 `applyPacingSnapshot` 刷新**，非重连的中途 normal→restricted 升级不收紧 floor——**减速由云端随命令保鲜的 dwell/think 承载**。**不再宣称「floor 保留 tempo 实时联动」**；加断言 `tempo=1.0` 与「无 tempo」逐位等价，钉死「现役恒 1.0 ≈ 尚未生效」这一事实、别误当已验证行为。fatigue 本就在边缘、是真值，照留。 |

---

## 8. 干净扩展缝（日后账号维度覆盖如何加）

- **账号覆盖**（用户既定「留账号覆盖扩展缝」）：v1 仅文档+迁移注记、零代码零运行时分支。日后 `pacing_floor_config` 主键 `(operation)` → `ALTER TABLE ADD COLUMN IF NOT EXISTS scope TEXT NOT NULL DEFAULT 'global'`、主键改 `(scope, operation)`；`floorFor(op, accountId?)` 先查 `(accountId, op)` 缺则回落 `('global', op)`（镜像 session-limits「按账号→全局」反向路径）；`buildPacingSnapshot(status, provider, accountId)`——`onHello` 已有 `session.accountId`（`handler.ts:325`），**零协议改动**。这同时是「全局同一分布」残留指纹（§7）的完整解。
- **σ 调优**：若日后确需运营调形状，`ALTER ADD COLUMN sigma_pct`（自愈）+ payload 加字段即可；v1 反射采样 + 内置 σ 已消硬左壁，无需提前建列。
- **内容模型族配置化**：新建单行 `pacing_model_config`（session_config_global 范式、`ALTER ADD COLUMN` 自愈）承载 `READ.*`/glance/familiar/`FEED_FLOOR`/think base；`computeDwellMs`/`computeThinkMs`/`computeFeedFloorMs` 从该 store 现读。与本次 floor 表正交、可独立加。
- **tempo/fatigue 联动**：`effectiveFloor` 的 `× tempo × fatigue` 是干净乘法缝；未来接「真实平台封号/限流信号」驱动状态迁移时只换系数来源、不动 gating 本体。
- **会话内热更 / 「场」粒度生效**：v1 生效边界=连接级（云端自动续场在同一连接开新「场」、不重新握手，故同连接跨多场用同一快照）。日后要即时/更细，读全走 `PacingFloorProvider` 接口、drop-in；复活 `session.budget` 推流或加推流通道即可，现 YAGNI。
- **通知巡视 / 搜索子流程 gating**：复用同一 `gateBeforeAction`/`ensureMinInterval` helper + 命令→op 映射，加一处入口调用即可，无 schema 改动。

---

## 9. 开放问题（需用户拍板的少数点）

1. **反射采样的落点**：新增局部 `sampleReflect` helper 仅供最小间隔 floor 用（**推荐**，不动共享 `sampleDelay` 以免影响其它 caller），还是把反射改进共享 `sampleDelay`（一处改、但触及全部现役 dwell/pause）。倾向前者。
2. **内置 σ 是否随本次略放宽**（如 action 0.3→0.35、card_gap 0.4→0.45 稀释左尾），还是保持现值仅靠反射消壁。倾向小幅放宽 + 反射双保险。
3. **两处裸 pad 处理**：关注后 `sleep(1500)`（`:1426`）、评论码前 `sleep(300)`（`:1284`）——v1 保留标清理缝（本稿默认），还是本次一并删除交下个 `gateBeforeAction` 吸收。倾向保留。
4. **search-handler / 通知巡视 gating 时序**：确认放 v1 之后的 fast-follow（本稿默认）还是并入本 change。倾向 fast-follow、先收口 browse-session。
5. **CAP=15000 / 各 op 默认区间与防呆下限的具体数值**：§5 为量级示意，实装从 `timing.ts` 预设逐字提取；请确认 CAP 15s 与防呆下限（action 800 / scroll 300 / card_gap 1000 / detail_dwell 1000）是否符合运营预期。
6. **tempo 去留复核**：用户既定决策为「保留 tempo 联动」，本稿据此保留标量 + 重连刷新 + 冻结如实文档化；若为进一步瘦身热点协议、愿接受 v1 暂不下发 tempo（纯边缘 fatigue + 云端 per-command dwell/think 承载全部减速），可去掉 payload 的 `tempo` 字段。默认按既定决策保留。
