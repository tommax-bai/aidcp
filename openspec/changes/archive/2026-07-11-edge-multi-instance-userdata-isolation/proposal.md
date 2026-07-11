## Why

运营 / 开发时需要在**同一台机器**上并行运行两个 edge 监督者（GUI）实例——一个连 dev 云、一个连 ol 云，各自操作不同的 AdsPower 分身。当前第二个 GUI 会被单实例锁硬拦（`aidcp-edge/src/electron/main.cjs` 的 `requestSingleInstanceLock`）：锁按 Electron 用户数据目录（userData）划分，而 userData 走默认路径、代码里无覆盖口子，两实例共用同一 userData → 同一把锁 → 第二个弹「已在运行」并 `app.quit()`。同源地，设置 / 名册、界面状态、日志、内置运行时落地目录都从 userData 派生，即便绕过锁也会互相覆盖。

## What Changes

- 新增一个**实例级 userData 隔离开关**：监督者启动时读环境变量 `AIDCP_USER_DATA_DIR`，非空则在取任何 userData 派生路径与请求单实例锁**之前**把 Electron 用户数据目录指到该路径。
- 一处改动即让**单实例锁、设置 / 名册（settings.json）、界面状态（ui-state.json）、日志（logs/edge.log）、内置浏览器运行时落地目录（ads-runtime）**全部按实例分开。
- **不设该变量时行为完全不变**（默认目录），对现有单实例 dev GUI 零回归。
- 云端仍由既有的 `AIDCP_CLOUD_URL` 机制各自选择，不新增云端选择逻辑。
- 明确**不做**：跨实例的分身占用租约、单实例锁逻辑改写、同分身双驱动——见 design 的 Non-Goals。

## Capabilities

### New Capabilities
- `edge-multi-instance-isolation`: 监督者实例的本机状态（userData 及其派生的锁 / 设置 / 名册 / 界面状态 / 日志 / 运行时落地）可按实例隔离，从而允许同机多个监督者并存；并规定并存的运营前置约束（分身不重叠、错峰启动、保持 AdsPower 模式）。

### Modified Capabilities
<!-- 无：现有 spec 均未覆盖监督者实例隔离 / 多实例并存；单实例锁行为此前无 spec 明文，本 change 以新能力首次成文。 -->

## Impact

- **代码**：仅 `aidcp-edge/src/electron/main.cjs` 顶部新增一段 userData 覆盖（require 之后、`requestSingleInstanceLock()` 与任何 `getPath('userData')` 之前）。edge-only。
- **协议 / 云端 / 单实例锁逻辑 / 风控**：均不改。
- **配置**：新增可选环境变量 `AIDCP_USER_DATA_DIR`（未设 = 旧行为）。
- **运营**：并存要求两实例使用不重叠的 AdsPower 分身、先后启动（避免抢占机器全局 50325 守护进程）、保持默认 AdsPower 模式。
- **测试**：edge 单元测试断言覆盖生效 / 未设时默认；`npm run typecheck`。真机验收登记 backlog。
