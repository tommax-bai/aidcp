## Why

客户端「暂停后点关闭」关不掉指纹浏览器：关闭按钮只在暂停态出现，是关浏览器的唯一入口，但关闭这条链路收尾不可靠。经 10-agent 交叉+对抗验证（锚点在 edge master `1d2620a` 仍在），根因是两层——(1) AdsPower 关闭完全托付软性「停止」本地 API，无任何独立实证与 OS 级强杀兜底；且暂停已先拆掉 CDP，疑使该驻留分身被判为脱离/非活跃，随后「停止」空操作、真窗口残留；(2) 收尾判断把「查不动/非活跃」一律当成「已关」，「停止」失败被静默吞掉，外壳只凭核心退出码就宣称「浏览器已关闭。」——踩中本仓最忌讳的「静默假成功」红线，且与 `pluggable-browser-provider` 现有需求「若无法确认已关则如实报告而非假装已回收」直接冲突。关键对抗验证洞见：只把收尾改诚实不够，只会把「假成功」变「诚实卡住」，浏览器仍不关；真关必须补一条不依赖 AdsPower 软状态的独立实证 + 实杀路径。

## What Changes

- AdsPower 关闭 SHALL 以**独立于 AdsPower 自报状态的肯定信号**确认浏览器真死（该分身的 CDP 调试端点不再应答），MUST NOT 把「无法查询/非活跃自报」当作「已关」。
- AdsPower 关闭 SHALL 在软性「停止」未达成实证死亡时**升级**：重发停止 +（可行时）对该分身内核进程做 OS 级强杀兜底，直至端点实证消失或在有界上限内如实判「未确认关闭」。
- 「停止」本地 API 的失败 MUST NOT 被静默吞掉，SHALL 如实纳入关闭结论。
- 关闭前若 CDP 已被暂停流程拆除，关闭路径 MUST NOT 因此静默空转（关闭时对目标分身重发权威停止并按端点实证判定，不依赖暂停前的连接）。
- 外壳（Electron 伴随窗）在用户发起关闭时，MUST NOT 仅凭核心进程退出即宣称「已关闭」；SHALL 反映核心诚实的「已确认关闭 / 未确认」结果。
- 外壳关闭路径在**核心子进程已不在**（驻留核心在暂停与关闭之间死亡）时，MUST NOT 零停止直接宣称「已关闭」；SHALL 对本进程自有分身补一次「停止 + 本机在跑分身实证」，或如实报告「无法确认已关」。
- 补齐当前只覆盖 happy-path 的测试：新增「停止未生效 / 无法查询 / 非活跃自报但窗口仍在 / no-child 关闭」等假成功分支的回归断言。

## Capabilities

### New Capabilities
<!-- 无新增能力：本变更强化两个既有能力的现有需求。 -->

### Modified Capabilities
- `pluggable-browser-provider`: 收紧「AdsPower 提供商经本地 API 托管浏览器生命周期」的**关闭并确认已关**需求——必须以独立于 AdsPower 自报的权威信号实证浏览器真死、无法确认绝不当已关、软停止未达成时升级到重试 + OS 级强杀兜底、且暂停期拆 CDP MUST NOT 使关闭静默空转。
- `edge-companion-ui`: 收紧外壳用户发起关闭的诚实语义——不得仅凭核心退出宣称已关、须反映诚实确认结果；无核心子进程时不得零停止假报已关。

## Impact

- 代码（edge，`../aidcp-edge`，edge-only，不动云端）：
  - `src/cdp/browser-provider.ts`（`AdsPowerProvider.killAndConfirmDead` / `stop` / `confirmClosed`，权威端点实证 + 升级实杀 + 不静默吞错）
  - `src/cdp/chrome-launcher.ts`（复用其调试端点探活 / 端口释放确认思路，供 adspower 路径共用权威实证）
  - `src/client/core-lifecycle.ts`（`finalize` 的关闭确认与暂停期 CDP 拆除交互，热点：与 self-contained-ads-runtime 逐字相同，须谨慎）
  - `src/electron/main.cjs`（`closeEdge` 的 no-child 分支 + 核心退出时的关闭结论投影；外壳自有 `browser/local-active`/`listActiveProfiles` 实证）
- 测试：`test/cdp/browser-provider.test.ts` 及相关核心生命周期/外壳测试补假成功分支断言；改动后跑 `npm run test:acceptance` → `npm test` → `npm run typecheck`。
- 无协议 v2 改动、无风控/发布链改动、无 ECS 部署（edge-only）。
- 真机验收：需在运营机确认「暂停→关闭」后浏览器真关、且失败态如实呈现（登记 backlog 真机项）。
