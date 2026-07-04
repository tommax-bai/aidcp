## Context

> 权威、逐 `文件:行` 的完整设计在 `docs/design/pacing-floor-configurable-min-interval.md`（362 行，经三轮对抗评审裁定）。本文件是提炼版，记录关键技术决策与理由；落地细节以权威文档为准。

现状（`文件:行` 见权威文档 §1）：

- 边缘各类操作前/后的兜底延迟散落、硬编码、且语义是**无条件累加**——`browse-session.ts` 的 `thinkBefore` 与各命令入口的 `humanPause` 无条件附加 `sampleDelay`，与云端往返时间叠加成双重延迟。
- 节奏预设（`humanize/timing.ts`）与云端下限常量（`risk/pacing.ts` 的 `DWELL_FLOOR_MS`/`tempo`/`fatigue`）全是源码 `const`，运营无法调整。
- 已有两处**已达标**的最小间隔模板：`ensureDetailDwell` / `ensureFeedDwell`（记锚点、只补差额）——本设计的参考样板。
- `session.budget.pacing` 是**死通道**：边缘从不请求、不在主动命令白名单，携带的 pacing 默认块实际被丢弃。
- 协议契约测试 `AC-PROTO` 只数 `MessageType` 总数、typecheck 的 `Record<MessageType,true>` 只穷举消息类型——**payload 字段漂移落在两者双盲区**。

约束：边轻云重、状态单写、绝不静默假成功、绝不零延迟、协议四处同步、console 只读面板 API 不直连边缘、PG schema 启动自建无迁移器、YAGNI。

## Goals / Non-Goals

**Goals:**
1. 兜底延迟从硬编码 → 后台(console)可编辑、存 PostgreSQL、下次握手热加载。
2. 语义「无条件附加」→「最小间隔 gating」：单锚点记上次操作完成时刻，`remaining = max(0, floor − elapsed)`，云端往返被 `elapsed` 吸收、**绝不累加**。
3. 全局一套配置，保留风控档 `tempo`（标量下发、边缘乘算）+ `fatigue`（边缘真值）联动。
4. 每类操作独立数值：`action` / `scroll` / `card_gap` / `detail_dwell`。
5. 守死红线：配置只能抬高延迟、**永远抬不穿非零下限**；功能性 settle / 有界轮询排除在 gating 外（绝不静默假成功）。

**Non-Goals（v1 明确不做，留扩展缝）:**
- 不做配置版本号（welcome 现读、无缓存漂移窗口）。
- 不建账号 scope 列 / 不穿 `accountId`（仅文档+迁移注记扩展缝）。
- 不建 `sigma_pct` 配置列/协议字段（防指纹改边缘采样实现）。
- 不配置化内容模型族（`READ.*`/glance/familiar/`FEED_FLOOR`/think base）。
- 不接通知巡视 / 搜索子流程 gating（fast-follow，先收口 browse-session）。
- 不动发布链 `PACING_MS`（与 CommandSequencer 超时耦合、独立通道）。
- 不接「真实平台封号/限流信号驱动状态迁移」（现役 tempo 几乎恒 1.0，非本设计范围）。

## Decisions

- **下发走 `welcome` 握手响应，不复活 `session.budget.pacing`**。`welcome` 是 `request('hello')` 的响应，按 pending-id 命中返回、**永不经过主动命令路由白名单**——零白名单遗漏风险（`session.budget` 是死通道，改它要额外接线且仍有丢命令风险）。
- **op 粒度 = 四类 `{action, scroll, card_gap, detail_dwell}`**。对齐现役仅有的 3 个 gate 相关 lognormal 预设（`action` 一档已覆盖 open/like/collect/follow/comment）+ dwell floor。命令→op 映射留边缘代码，日后细分零 schema 成本。
- **不建 `sigma_pct` 配置**，防指纹改**边缘反射采样** `sampleReflect`：越界样本反弹回分布内、消掉「补差额到固定值」造成的竖直左壁尖峰，比暴露 σ 更彻底且零配置面。协议 payload 瘦成 `{minMs, maxMs}`。
- **floor 区间用 `{min, max}` 而非单个中位值**：复用 `makeDwellFloorTiming` 现成映射，对「这类动作等 X~Y 秒」的运营语义更直观。
- **tempo 保留标量随快照下发，重连时经 `applyPacingSnapshot` 重注入**；中途非重连的风控升级不收紧 floor（如实文档化：现役 tempo 恒 1.0，减速由云端随命令保鲜的 dwell/think 承载），断言 `tempo=1.0` 与「无 tempo」逐位等价。
- **绝不零延迟 = 三道夹**：facade 校验（含 `max ≥ min×1.5` 最小展宽）+ 云端读出口 `clamp(防呆下限, CAP=15000ms)`（权威、防 psql 直插绕面板）+ 边缘 `Math.max` 二次夹。
- **看门狗 lockstep**：`CAP_MS=15_000` 小常量，结构上 ≪ `IDLE_NUDGE_MIN_MS(200_000)`；在 `resume-limits` 不变量测试加常量关系断言 tripwire，防未来有人下调 idle 下限。
- **单调时钟 `monoNow`**（`performance.now` 优先）：单一实现、单一注入口、只自身作差、绝不持久化/跨基准/跨进程比较；防 NTP/改表/休眠致 `elapsed` 变负或暴增。既有 `noteOpenedAt`/`feedCardsArrivedAt` 短时长历史稳定，v1 不迁移。
- **记账 `markActionEnd` 放 uplink 之后**：让边缘 `elapsed` 起点与云端 idle 起点对齐同一 uplink 事件，两把时钟量同一段 gap。
- **协议漂移双盲区补强**：两仓 `protocol.ts` 各加 `WelcomePayload`+`PacingSnapshotPayload` 结构化契约断言（同一份填满全字段的样例常量、逐字人工同步）+ 端到端「非默认 floor 真到边缘 gate」红线测试。

## Risks / Trade-offs

- [`buildPacingSnapshot` 抛错 brick 握手] → total 函数 try/catch，失败返回 `undefined` 省略 pacing 字段；回归断言「必抛桩→握手仍成功回退默认」。
- [后台配 0/负数/超界绕过零延迟红线] → 三道夹，配置只能抬高、抬不穿非零下限，设计上不可能绕过。
- [`min==max` 零展宽退化打掉防指纹] → facade 强制 `max ≥ min×1.5`。
- [配大误触 idle 看门狗杀会话] → `CAP=15s ≪ 200s` 结构性消除 + tripwire。
- [补差额硬左壁指纹] → 边缘反射采样 + 内置 σ 略放宽；补差额集中在高频廉价动作（scroll/card_gap），这两类优先反射。**已知残留**：floor 全局一套 → 跨账号同一分布，完整解在账号覆盖扩展缝（v1 不做）。
- [协议 payload 字段静默漂移] → 结构化契约断言 + 端到端红线测试（别把 AC-PROTO 当 welcome payload 安全网）。
- [重连不重注入配置——最严重缺口] → `applyPacingSnapshot` + `reestablishIdentity` connect 后 start 前灌入（BrowseSession 只构造一次、重连复用同一对象）。
- [reload 半填 Map 竞态] → 构建新 Map 原子替换引用，`floorFor` 只读快照。
- [gate sleep 挡停止命令] → `sleepInterruptible`（可被 stopRequested/命令唤醒）+ 秒级小上界；`closing` 终态不复活。

## Migration Plan

- **无 DB 迁移器**：`pacing_floor_config` 表由 store `init()` 内联 `SCHEMA_SQL` 幂等自建；`migrations/0031_*.sql` 仅台账。表空 = 逐项回落内置默认 = 现役量级，零回归。
- **部署顺序无强约束**（向后兼容任意组合不 brick）：旧 edge 忽略新 `pacing` 字段走内置默认；旧 cloud 不发、新 edge 收 `undefined` 回落默认。建议 cloud 先、edge 后（先具备下发能力）。
- **生效边界 = 连接级**：PUT 后下次握手/重连的边缘取到新值；稳定 fleet 可能数小时才铺满，rollout 期行为异构——console Alert 必须写清。
- **回滚**：配置回滚 = 面板清空该 op 行（回落内置默认）或 psql 删行；代码回滚按各仓常规，向后兼容保证混版安全。

## Open Questions

以下 6 点权威文档 §9 均已给推荐默认，本 change 按推荐采纳、待用户复核：
1. `sampleReflect` 新建局部 helper（**推荐**，不动共享 `sampleDelay`）vs 改共享采样。
2. 内置 σ 是否随本次略放宽（action 0.3→0.35、card_gap 0.4→0.45）——倾向小幅放宽 + 反射双保险。
3. 两处裸 pad（关注后 `sleep(1500)`、评论码前 `sleep(300)`）v1 保留标清理缝 vs 本次删除——倾向保留。
4. search-handler / 通知巡视 gating 放 fast-follow vs 并入本 change——倾向 fast-follow。
5. `CAP=15000` 与各 op 默认区间/防呆下限具体数值（action 800 / scroll 300 / card_gap 1000 / detail_dwell 1000）是否符合运营预期。
6. tempo 去留：既定决策保留标量+重连刷新；若愿进一步瘦身热点协议可去掉 payload 的 `tempo` 字段（纯边缘 fatigue + 云端 per-command dwell/think 承载减速）——默认保留。
