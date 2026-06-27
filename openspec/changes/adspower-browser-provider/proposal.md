## Why

`multi-account-node-support` 打通了同机多账号的**进程 / 路由 / 账号隔离**，但明确把「同机不同账号**防关联**」列为 Non-Goal——edge 仍是**一机一套真实指纹、共用本机出口 IP**。规模化生产多账号时，同机的多个小红书账号会在**设备指纹 + 出口 IP**两个维度被平台判定为同一设备而关联、风控连坐。本 change 把这条「防关联」补上：以**可选的浏览器 provider** 形式接入 AdsPower 指纹浏览器（每 profile 独立指纹 + 独立代理 + 独立账号），并修订上述 Non-Goal 的范围边界。默认仍是 self 真实指纹，AdsPower 为显式 opt-in。

## What Changes

- **edge — 新增可插拔浏览器 provider 抽象**：把「浏览器启动 / 生命周期」从 `launchChrome` 抽成 `BrowserProvider` 接口（返回现有 `ChromeInstance` 形状：`pid` / `reused` / `kill` / `killAndConfirmDead`）。两实现：`SelfChromeProvider`（**默认**，包现有 `launchChrome`、行为零变化）、`AdsPowerProvider`（调 AdsPower 本地 API `browser/start|stop|active` 拿标准 `debug_port`）。由 `AIDCP_BROWSER_PROVIDER`（`self` | `adspower`，**默认 `self`**）选择。
- **edge — 连接层零改动**：AdsPower 返回的 `debug_port` 直接喂给现成 `attachToPage`；CDP attach 及以下（targets / session / 定位 / 拟人 / `readSelfIdentity`）**一行不改**（接缝已真机验证，见 Impact）。
- **edge — 反检测层加 env 开关**：新增 `AIDCP_STEALTH`（`on` | `off`）。AdsPower 模式**默认关**自研 stealth、由 AdsPower 的 `cdp_mask` 独占指纹层（避免两层注入互相覆盖制造不自洽）；self 模式**默认开**（保持现状）。
- **edge — AdsPower 模式经 `launch_args` 固定桌面视口**（`--window-size=1440,980`），否则落进小红书窄屏布局变体致定位 / 滚动选择器失效。
- **edge — 诚实失败红线延续**：AdsPower API 不可达 / profile 未登录小红书 / 取不到 `debug_port` → **诚实报错停手**，MUST NOT 静默回落 self 或假成功。
- **运维契约 — 防关联绑定**：1 个 AdsPower profile = 1 套指纹 = 1 个独立 IP = 1 个小红书账号，长期稳定绑定；**指纹绑账号、不绑任务 / 进程**（同账号配多套指纹 = 换设备登录告警，适得其反）。
- **修订 Non-Goal（跨 change 协调）**：把 `multi-account-node-support` 中「MUST NOT 引入第三方指纹浏览器」从**绝对禁止**软化为**范围说明**——「该 change 本次不引入；同机防关联经本 change 以显式 opt-in provider 接入」。默认仍 self 真实指纹，**非 BREAKING**。

## Capabilities

### New Capabilities
- `pluggable-browser-provider`：edge 的浏览器启动 / 生命周期层**可插拔**。默认 `self`（自起真实指纹 Chrome，等价现状）；可显式 opt-in 切到 `adspower`（外部指纹浏览器）做同机多账号防关联。provider 边界 = **仅启动 / 生命周期**，CDP attach 及以下不变；opt-in、诚实失败不静默回落；AdsPower 模式由其 `cdp_mask` 独占指纹层、并要求 profile = 指纹 = IP = 账号 1:1:1:1 稳定绑定。

### Modified Capabilities
<!-- 无 baseline 能力的 REQUIREMENTS 变更。「MUST NOT 引入第三方指纹浏览器」目前只存在于**尚未归档**的
     multi-account-node-support change 的 chrome-instance-isolation delta、未并入 baseline openspec/specs/，
     故不作为 baseline MODIFIED delta（否则 validate --strict 失败）；改以跨 change 协调软化其 Non-Goal 措辞，
     见 Impact 与 design.md。 -->

## Impact

- **aidcp-edge（主体）**：
  - 新增 `src/cdp/browser-provider.ts`：`BrowserProvider` 接口 + `SelfChromeProvider`（包 `launchChrome`）+ `AdsPowerProvider`（调本地 API，默认 `http://local.adspower.net:50325`，限速 1 req/s，开安全校验时 `Authorization: Bearer <key>`）。
  - `src/main.ts:88` 改为按 `AIDCP_BROWSER_PROVIDER` 选 provider 再 `attachToPage`（attach 及以下不动）。
  - `src/cdp/session.ts:32/53` 的 `stealth` 由 `main.ts` 读 `AIDCP_STEALTH` 注入（self 默认 on、adspower 默认 off）；现仅代码层 `AttachOptions.stealth`，本 change 补 env 接线。
  - `chrome-launcher.ts` 的 self 路径保持原样（`launchChrome` 被 `SelfChromeProvider` 包装、不改其逻辑）。
- **接缝已真机验证（2026-06-27）**：`aidcp-edge/scripts/adspower-poc.ts`（独立脚本、不碰主代码）实测 **C1 attach ✅**（现成 `attachToPage` 零改动连上 AdsPower `debug_port`）、**C3 ✅**（cdp_mask 开 + edge stealth 关 → `navigator.webdriver` 藏住、自洽）。本 change = 把该 PoC 固化为正式 provider。
- **协调 `multi-account-node-support`**：软化其 `proposal.md` Non-Goal 与 `specs/chrome-instance-isolation/spec.md` 的指纹浏览器禁止措辞为范围说明（指向本 change）。两 change 错峰、加性协调。
- **cloud / console / 边-云协议**：**完全不动**。账号归并 / 风控 / 多租户编排仍按 `multi-account-node-support`；AdsPower 只替换 edge 的浏览器启动层，accountId 仍由 `readSelfIdentity` 从登录态读出。
- **文档**：`aidcp-edge/docs/anti-detection.md` Phase 3「指纹浏览器 + 住宅代理池 + profile×指纹×IP 三元绑定」由路线图转为本 change 落地依据（回写实现指针）。
- **非目标**：替换默认 self 路径；为 self 模式补指纹伪造；自建指纹引擎 / 代理池管理（交给 AdsPower + 运营）；任何 cloud / console / 协议改动。
