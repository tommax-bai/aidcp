## Why

云端为每个 edge 连接建独立的「私有事件通道 + 角色调度器 + 会话状态」，入站按会话号路由，是结构性隔离——一台 edge 的上报不可能串到另一台的调度器。但**出站定向下发不是结构性隔离，而是靠目标节点号（edgeId）过滤**：调度器把命令交给出口时带上本连接的 edgeId，出口在共享在线表里按 edgeId 挑连接。

问题在于握手层只强校验账号号、**从不校验节点号**：一旦某连接握手漏带 edgeId，出口的目标就是空值，而出口在目标为空时会**退化成向所有在线 edge 广播**。于是「A 的上报触发的命令」可能被投递到 B——直接违反系统核心红线「绝不静默假成功 / 绝不误伤」。这是一个潜在缺陷（非设计意图），且发布路径早已确立「无目标就诚实失败、绝不广播」的纪律，本次把该纪律补齐到握手层与浏览调度出口。

## What Changes

- **握手强校验节点号**：edge 握手缺 / 空 edgeId 与缺账号号同等，判为配置错误、拒绝握手、不建立连接运行时（复用既有配置错误出口）。无节点号 = 无可路由的出站身份。
- **出口禁止隐式广播**：定向下发接口在未提供目标 edgeId 时 **MUST NOT** 广播——命中 0 条、如实返回 0、记警告，绝不 fan-out。
- **广播须显式**：若将来确需「全网广播」，只能经一个新增的、语义明确的独立方法触发，禁止靠「省略目标参数」隐式广播。
- **补安全红线级回归断言**：握手无 edgeId 被拒；空目标下发命中 0 且不向任何连接发送；正常带目标仍只命中目标那一台。
- 次要风险（同 edgeId 重连瞬间双活连接导致定向命令瞬时扇给两个）**本次不修**，仅在设计中记录并留扩展缝（更彻底解是「定向按唯一会话号而非节点号」的单独收敛）。

## Capabilities

### New Capabilities
- `edge-command-targeting`: 定向边缘命令的目标寻址与投递保证——握手须携带可路由的节点身份，出站命令只投递到唯一的目标节点，绝不隐式广播或误投到非目标节点。

### Modified Capabilities
<!-- 无：本次不改动任何已合并 spec 的既有需求，只新增一个能力。 -->

## Impact

- **代码（全部落 aidcp-cloud）**：
  - 连接握手校验：`src/orchestrator/connection-runtime.ts`（`onHandshake` 增补 edgeId 校验，复用 `onConfigError`）。
  - 出口投递：`src/comm/ws-server.ts`（`pushToEdges` 空目标不再广播；如需广播另立显式方法），及同构的 `EdgePusher` 接口注释与调用点（`server.ts`、`command-sequencer.ts`、`like-command.ts`、`comment-agent/edge-steps.ts`、`handler.ts`）语义对齐。
- **测试（aidcp-cloud）**：`test/integration/connection-runtime.test.ts`、`test/ws-server.test.ts`、`test/comm/ws-server-pause.test.ts`；acceptance 侧可挂到协议 / 风控红线系（`protocol-contract` / `risk-guard`）。
- **不影响**：edge 端（一直携带 edgeId，无需改）；入站结构性隔离；同账号多连接的账号级共享态（风控 / 冷却 / 互动闸）。
- **无破坏性变更**：确认无任何调用点故意用空目标广播，收紧行为对现有路径零回归。
