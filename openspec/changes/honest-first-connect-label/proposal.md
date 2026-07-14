# 首次连接不得被讲成「断线重连」

## Why

关闭环境后再点启动，客户端先显示「启动中」，几秒后翻成 **「正在重新连接」**，直到云端连上才回「运行中」。用户的判断是对的：这一步是启动的正常过程，**显示「正在重新连接」是 bug**。

### 根因：状态投影里根本没有「这轮核心连上过云端没有」这个事实

「**重**新连接」这句话有一个语义前提——**曾经连上过，然后断了**。但两处判定用的都是 `cloud !== 'connected'`，而这个条件同时覆盖两种完全不同的处境：

| 真实处境 | `cloud !== 'connected'` | 诚实的说法 |
| --- | --- | --- |
| 这轮核心**从没连上过**（正在冷启动） | ✓ | 正在启动 |
| 曾经连上、**现在断了** | ✓ | 正在重新连接 |

代码把两者一律讲成后者。这与刚修的人设三态（`persona-bound-tristate`）是**同一族错误**：把「还没」读成「否」。

### 为什么整个浏览器冷启动窗口都会中招

三路状态在启动时是这样凑齐的：

1. `session: 'running'` —— `startEdge()` 在 **spawn 那一刻**就乐观写下（`main.cjs`）。
2. `edge: 'running'` —— 日志投影把「核心打印了任意一行 stdout」当作存活证据，**第一行 banner 就把 `starting` 翻成 `running`**。
3. `cloud: 'disconnected'` —— 核心 `main()` 里 `await client.connect()` 排在**浏览器冷启动之后**（准备浏览器 → `provider.launch()` 起 AdsPower 分身 → CDP attach → 身份/登录闸 → 才连云端）。

于是从「核心吐出第一行日志」到「已连接云端」之间的**整个浏览器冷启动窗口**（AdsPower 起分身秒级到数十秒，遇内核下载或扫码登录更长），UI 一直挂着「正在重新连接」。

### 代价不止是一句错话

环境栏那一处（`ui-logic.js` `fleetLevel`）把它判成 `attention` + **`needsAction: true`**：一次**正常冷启**会被染成琥珀色「需要你处理」并**浮到环境列表顶部**，与真正需要人工的登录 / 验证码 / 风控受限混在一起。多环境并行时，这会让「谁真的需要我」这个信号失真——而盯住这个信号正是环境栏存在的理由。

## What Changes

- **新增一个 per-core-run 的事实**：`cloudEverConnected`（这轮核心是否曾经连上过云端）。新核心 spawn = `false`，收到「已连接云端 / 已握手 / 云端已重连」= `true`，重启核心复位为 `false`。冷待机唤醒**不复位**（云端连接全程未断）。
- **两处判定按这个事实分流**，语义各归各位：
  - 从没连上过 → **「启动中」**（蓝色 launching，`needsAction: false`，不浮顶）
  - 连上过又断了 → **「正在重新连接」**（琥珀 attention，`needsAction: true`）——保持原样，这才是它该出现的时候。
- **不动 `edge` 字段的语义**。「核心进程活着」与「云端已连上」是两件事，前者由日志活性推断没有错；错的是把后者的缺席讲成断线。刻意不去改「第一行日志即 running」这条推断，避免波及 `settleLaunchReady` 等一串以 `edge` 为输入的既有逻辑（`browser-slot-scheduling` 正在同一区域施工）。

## Impact

- Affected specs: `edge-companion-ui`
- Affected code: `aidcp-edge/src/electron/main.cjs`（状态投影：默认值 / spawn / 重启 / 连上云端四处）、`aidcp-edge/src/electron/renderer/ui-logic.js`（`synthesizeHealth` / `fleetLevel` 两处判定）
- 纯呈现层修复：不改协议、不改云端、不改浏览行为。
