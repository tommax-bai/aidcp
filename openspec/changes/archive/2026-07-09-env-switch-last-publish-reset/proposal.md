## Why

客户端切换浏览器环境（= 换账号）后，「上次发布」卡片仍显示上一个账号的发布内容。根因已查实（2026-07-09 多 agent 追踪 + 对抗性验证）：壳层把 `lastPublish` 存在主进程单例 + `userData/ui-state.json` 全局文件，**不带账号/环境归属**（`main.cjs:247-269`）；切环境重启核心时有意不清（`main.cjs:671-682` 注释「等云端快照覆盖」）；而云端快照对**无发布记录**的新账号按「宁缺毋假」不带 lastPublish 字段甚至整包不发（`aidcp-cloud/src/comm/ui-snapshot.ts:86-87,108`）。整条链路没有「清空」语义 → 切到没发过帖的账号，旧账号内容永久滞留。这是把 A 账号的发布历史展示在 B 账号名下，属跨账号内容串显，必须修。

## What Changes

- `ui-state.json` 持久化增加**环境归属键**（`envKey`）：`provider='self'` 记 `self`，adspower 记 `ads:<adsProfileId>`（与核心 edgeId 派生规则同源）。
- 应用启动加载 `ui-state.json` 时**校验归属**：`envKey` 与当前设置推导的键不一致、或缺失（旧版文件）→ 不采纳 `lastPublish`，发布卡回落既有「还没有发布过内容」空态占位（宁缺毋假：归属不明就不显示）。
- 核心（重）启动时**校验归属**：内存中 `lastPublish` 的归属键 ≠ 本次启动的环境键 → 随重启补丁清空（`lastPublish: null`），UI 即刻回落空态；同环境重启行为不变（历史态保留）。
- 云端快照回填 / 本地发布成功写入 `lastPublish` 时，**以核心 spawn 时刻的环境键**记归属并落盘（避免「保存了新设置但未重启」窗口内把旧核心的事件记到新环境名下）。
- 云端带回新账号真实记录时照常覆盖（现有行为不变）；无记录则停留空态占位——这正是用户指定的期望行为。
- **不动协议、不动云端**：纯 edge 壳层（Electron main.cjs + 新增小型纯逻辑模块）改动。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `edge-companion-ui`: 发布卡「上次发布」历史态从「全局唯一、跨账号共享」改为「按环境归属」；切换到不同环境时不得展示上一环境的发布内容，无归属或归属不符时回落空态占位，云端快照仍是权威覆盖源。

## Impact

- `aidcp-edge/src/electron/main.cjs`：`loadUiState` / `saveUiState` / `startEdge` 重启补丁 / `handleEdgeLogLine` 两处 `lastPublish` 写入点。
- `aidcp-edge/src/electron/ui-state.cjs`（新增）：环境键推导 + 存量采纳判定的纯函数，按仓内惯例（ads-runtime / ui-events 模式）从 main.cjs 拆出可单测模块。
- `aidcp-edge/test/electron/ui-state.test.ts`（新增）：少数关键用例（同键采纳 / 异键丢弃 / 缺键丢弃-升级路径 / 序列化含键）。
- 升级兼容：旧版 `ui-state.json` 无 `envKey`，首次升级后发布卡一次性回空态，核心启动、云端快照带回真实记录后自愈；此为有意选择（旧文件无法判归属，宁缺毋假）。
- 与活跃 change `edge-multi-environment-fleet`（未实装）在 `main.cjs` 有潜在交叠：本改动的 `envKey` 与其 `edgeId=ads-<id>` 方案同构，多环境实装时可直接复用按环境分键的 ui-state。
