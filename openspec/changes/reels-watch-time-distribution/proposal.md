# Proposal: reels-watch-time-distribution

## Why

Facebook Reels 每条的实际观看时长目前近似常数:云端对 reels 面翻页统一挂 Facebook 的 11s 扫屏地板(`aidcp-automation/src/platform/registry.ts:286` 的 `feedScrollDwellFloorMs`,经 `role-dispatcher.ts` 的 `scrollDwellParams` 不分面取 max),边缘只叠 σ=0.2 的 lognormal 抖动,实测分布约 95% 落在 7.5–16.5s、峰值 9–13s。真人刷短视频是重尾行为(多数快划、少数看完、极少数深看),恒定 11s 是可识别的机械指纹。

## What Changes

- 云端为 `surface='reels'` 的翻页命令单独采样每条 Reel 的观看时长中心值:三段加权混合(约 55% 快划 10–20s / 35% 正常观看 20–45s / 10% 深看 45–90s),乘现有 tempo(风控/配额档)与 fatigue(会话进度)系数后 clamp 到 [10s, 90s],作为 `dwellMs` 随命令下发。
- feed / search 面的翻页停留计算完全不变(仍走 11s 扫屏地板 + 卡片数地板)。
- 边缘抖动层不动(照旧 ±20% lognormal + 停留达标 + 吸收云端评估耗时);不新增协议字段、不碰两份 `protocol.ts`。
- 90s 上限在既有系统预算内:idle 看门狗轻推阈值 240s,其注释明写「须 > 详情页停留上限(pacing capMs=90s)」;阅读模型 `READ.capMs` 本就是 90_000。

## Capabilities

### New Capabilities

- `facebook-reels-watch-pacing`: Facebook Reels 每条观看时长的云端采样分布——重尾混合分布、tempo/fatigue 联动、[10s, 90s] 边界、只作用于 reels 面、边缘抖动层与 feed/search 面不变。

### Modified Capabilities

(无——`command-pacing` 的既有要求[云端出中心值、边缘只叠抖动、缺字段回落非零兜底]全部保持;本 change 是在该框架内为 reels 面新增一个中心值来源,不改任何既有 requirement。)

## Impact

- 代码:仅 `aidcp-automation`——`src/risk/pacing.ts` 新增采样函数(常量内置,不新增 PacingOp、不动配置面),`src/orchestrator/role-dispatcher.ts` 的 scroll 出口按面分流。
- 部署:纯云端改动,部署 dev 即生效,不需要客户端发版。
- 吞吐(已获用户知情确认):平均每条 Reel 从 ~12s 变 ~25–30s,单位时间浏览条数下降一半以上;60 动作预算的会话时长拉长约 2–3 倍或先撞会话时长上限。
- 边缘长尾:云端 clamp 90s 后,边缘 ±20% 抖动的长尾偶尔可达 ~110–130s,仍远低于 240s 看门狗;10–90s 指中心值采样区间,非实际停留的硬上界。
