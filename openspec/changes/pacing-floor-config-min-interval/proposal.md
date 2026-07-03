## Why

边缘「各类操作后的兜底延迟」当前是**无条件附加**：一个操作做完，边缘再固定等一段兜底时间才做下一步。但等云端思考 + 网络往返本身也花了时间，于是变成「云端已经慢了、边缘还要再固定等一次」——双重等待，既拖慢又机械（大量操作间隔堆在同一固定值上，本身是可被行为分析识别的机器特征）。同时这些兜底数值全是源码里的硬编码常量，运营无法在后台调整。

本 change 把兜底延迟做两件事：语义从「无条件累加」改成「最小间隔」（等云端返回消耗的时间算进兜底、绝不二次叠加），数值从硬编码抽成后台可编辑。完整设计见 `docs/design/pacing-floor-configurable-min-interval.md`（经三轮对抗评审裁定）。

## What Changes

- **最小间隔 gating（核心语义）**：边缘记住上次操作完成时刻（单锚点、单调时钟），下一个操作到达时算「距上次已过多久」——已 ≥ 兜底则立即执行、不累加；不足则只补差额。云端往返时间被 `elapsed` 自然吸收，等待与兜底**绝不累加**。复用详情页停留已在用的「记锚点、只补差额」模板，推广到动作间隔。
- **兜底 floor 后台可配置**：数值从硬编码常量抽成 console 可编辑、存 PostgreSQL、下次握手热加载。作用域=全局一套（保留风控档 `tempo` / `fatigue` 联动，留账号覆盖扩展缝、v1 不建 scope 列）；粒度=每类操作独立数值，v1 四个 op：`action` / `scroll` / `card_gap` / `detail_dwell`。
- **绝不零延迟的三道夹逼**：facade 校验（含 `max_ms ≥ min_ms × 1.5` 最小展宽）+ 云端读出口 `clamp(防呆下限, CAP=15000ms)` + 边缘 `Math.max` 二次夹。不变量：配置只能抬高延迟、**永远抬不穿非零下限**——「配置绕过零延迟红线」设计上不可能。
- **防指纹**：floor 每次现采样，边缘用**反射采样**消掉「补差额到固定值」造成的硬左壁尖峰，间隔散布成自然分布而非堆一根针。
- **下发走 welcome 握手响应**（非死通道 `session.budget.pacing`）：零主动命令白名单遗漏风险；**重连必重注入**配置快照（设计判为最严重缺口）。
- **看门狗不冲突**：`CAP=15s` 结构上 ≪ `IDLE_NUDGE_MIN_MS(200000)`，加 `resume-limits` 不变量 tripwire。
- **协议漂移双盲区补强**：两仓 `protocol.ts` 加 `WelcomePayload` / `PacingSnapshotPayload` 结构化契约断言 + 端到端「非默认 floor 真到边缘 gate」红线测试（typecheck 与 AC-PROTO 均抓不到 payload 字段漂移）。

向后兼容，不含 BREAKING：旧边缘忽略新 `pacing` 字段、走内置非零默认；旧云端不发、新边缘收 `undefined` 回落默认。新旧任意组合不 brick。

## Capabilities

### New Capabilities
<!-- 无新增 capability：复用现有 command-pacing / console-* spec。 -->

### Modified Capabilities
- `command-pacing`: 新增「操作间隔最小间隔 gating（不累加）」、「兜底 floor 后台可配置（全局、每类操作、welcome 下发、热加载、重连重注入）」、「绝不零延迟三道夹逼 + 防指纹反射采样」三类 requirement；修订「缺时间指令时的安全降级」以纳入配置来源与逐字段回落。
- `console-panel-api`: 新增只读端点 `GET /api/pacing`（返回每类操作生效值 + `overridden` + 审计字段；deps 未注入 → `503 pacing_unavailable`）。
- `console-write-operations`: 新增 `PUT /api/pacing` 写操作——经拥有该写的进程内 facade 单写、诚实非乐观（写后 invalidate 重取真态）、服务端二次校验并夹逼（`unknown_operation`→404、`invalid_value`/最小展宽不足→400）、审计 `updatedBy`。

## Impact

- **aidcp-cloud**：新建 `src/config/pacing-config-store.ts`（含内联 `SCHEMA_SQL` + 读出口 clamp）、`src/config/pacing-config-facade.ts`；改 `src/risk/pacing.ts`（`buildPacingSnapshot` total 函数 + `CAP_MS`/`opMinFloor`/`BUILTIN_FLOOR`）、`src/comm/handler.ts`（welcome 附 pacing）、`src/comm/protocol.ts`（**热点、串行**）、`src/panel/panel-server.ts` + `src/panel/types.ts`、`src/server.ts`、`src/config/resume-limits.ts`（不变量 tripwire）；新建 `migrations/0031_pacing_floor_config.sql`（台账不执行）。
- **aidcp-edge**：改 `src/comm/protocol.ts`（与 cloud 逐字一致、串行）、`src/client/edge-client.ts`、`src/main.ts`（重连 `applyPacingSnapshot`）、`src/browse/browse-session.ts`（`monoNow`/`gateBeforeAction`/`ensureMinInterval`/`sleepInterruptible`/`markActionEnd`）、`src/humanize/timing.ts`（`sampleReflect`）。
- **aidcp-console**：改 `src/api/queries.ts`、`src/types/api.ts`、`src/pages/QuotasPage.tsx`（并入 Card + 三条运营预期 Alert）。
- **docs**：`docs/protocol.md`（welcome payload，不动 MessageType 计数）。
- **协议四处同步**：两份 `protocol.ts` 逐字一致（改）+ `command-bridge.ts`（不改，welcome 非动作）+ `docs/protocol.md`（改）+ 边缘主动命令路由白名单（不改，welcome 走 `request('hello')` 响应、永不经白名单）。
- **并发竞争区（集成串行、rebase 后再 build、绝不 force）**：`panel-server.ts`/`QuotasPage.tsx`（撞 `console-cloud-panel-hardening`）、`browse-session.ts` 命令入口（撞 `comment-search-command`、`fix-interaction-and-comment-capture`）、`edge-client.ts`/`main.ts`（撞 `edge-companion-ui`）、`pacing.ts`（可能撞 `category-adaptive-images-and-judgment`）。
