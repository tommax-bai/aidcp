## Why

`multi-account-node-support` 打通了同机多账号的**进程 / 路由 / 账号隔离**，但明确把「同机不同账号**防关联**」列为 Non-Goal——edge 仍是**一机一套真实指纹、共用本机出口 IP**。规模化生产多账号时，同机的多个小红书账号会在**设备指纹 + 出口 IP**两个维度被平台判定为同一设备而关联、风控连坐。本 change 把这条「防关联」补上：以**可选的浏览器 provider** 形式接入 AdsPower 指纹浏览器（每 profile 独立指纹 + 独立代理 + 独立账号），并修订上述 Non-Goal 的范围边界。默认仍是 self 真实指纹，AdsPower 为显式 opt-in。

## What Changes

- **edge — 新增可插拔浏览器 provider 抽象**：把「浏览器启动 / 生命周期」从 `launchChrome` 抽成 `BrowserProvider` 接口（返回现有 `ChromeInstance` 形状：`pid` / `reused` / `kill` / `killAndConfirmDead`）。两实现：`AdsPowerProvider`（**默认**，调 AdsPower 本地 API `browser/start|stop|active` 拿标准 `debug_port`、须配 `AIDCP_ADS_USER_ID`）、`SelfChromeProvider`（包现有 `launchChrome`、行为零变化）。由 `AIDCP_BROWSER_PROVIDER`（`self` | `adspower`，**默认 `adspower`**）选择。
- **edge — 连接层零改动**：AdsPower 返回的 `debug_port` 直接喂给现成 `attachToPage`；CDP attach 及以下（targets / session / 定位 / 拟人 / `readSelfIdentity`）**一行不改**（接缝已真机验证，见 Impact）。
- **edge — 反检测层加 env 开关**：新增 `AIDCP_STEALTH`（`on` | `off`）。AdsPower 模式**默认关**自研 stealth、由 AdsPower 的 `cdp_mask` 独占指纹层（避免两层注入互相覆盖制造不自洽）；self 模式**默认开**（保持现状）。
- **edge — AdsPower 模式经 `launch_args` 固定桌面视口**（`--window-size=1440,980`），否则落进小红书窄屏布局变体致定位 / 滚动选择器失效。
- **edge — 诚实失败红线延续**：AdsPower API 不可达 / profile 未登录小红书 / 取不到 `debug_port` → **诚实报错停手**，MUST NOT 静默回落 self 或假成功。
- **运维契约 — 防关联绑定**：1 个 AdsPower profile = 1 套指纹 = 1 个独立 IP = 1 个小红书账号，长期稳定绑定；**指纹绑账号、不绑任务 / 进程**（同账号配多套指纹 = 换设备登录告警，适得其反）。
- **修订 Non-Goal（跨 change 协调）**：把 `multi-account-node-support` 中「MUST NOT 引入第三方指纹浏览器」从**绝对禁止**软化为**范围说明**——「该 change 本次不引入；同机防关联经本 change 以可插拔 provider 接入」。
- **BREAKING — 默认翻为 adspower（用户 2026-06-27 拍板）**：`AIDCP_BROWSER_PROVIDER` 缺省由 `self` 改为 `adspower`，让主用路径默认走 AdsPower。裸 `npm start` 须配 `AIDCP_ADS_USER_ID`，否则诚实报错；不用 adspower 的部署须显式 `AIDCP_BROWSER_PROVIDER=self`。命令行多节点启动器（`launch-multinode`）在代码内钉回 self、不受影响。
- **edge — 桌面外壳应用内选择 provider（2026-07-01 追加，反转桌面钉回 self）**：Electron 桌面外壳不再钉回 self，改为**应用内浏览器选择**（默认 `adspower`、可一键切 `self`），把选择与 AdsPower 配置（分身 id 必填、API key / API base 可选）持久化到本机、按选择注入核心进程的 `AIDCP_BROWSER_PROVIDER` 等 env（外部 env 仍可覆盖）；面板全量中文化并提供 AdsPower 下载入口。缺分身 id / 写盘失败等诚实暴露、不假成功。见 tasks §9。

## Capabilities

### New Capabilities
- `pluggable-browser-provider`：edge 的浏览器启动 / 生命周期层**可插拔**。**默认 `adspower`**（外部指纹浏览器，做同机多账号防关联，须配 `AIDCP_ADS_USER_ID`）；`self`（自起真实指纹 Chrome，等价现状）经显式 `AIDCP_BROWSER_PROVIDER=self` 选用。provider 边界 = **仅启动 / 生命周期**，CDP attach 及以下不变；诚实失败不静默回落；AdsPower 模式由其 `cdp_mask` 独占指纹层、并要求 profile = 指纹 = IP = 账号 1:1:1:1 稳定绑定。命令行多节点启动器钉回 self；Electron 桌面外壳提供应用内 provider 选择、默认 adspower（tasks §9）。

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
- **BREAKING 迁移（默认翻 adspower）**：裸 `npm start` / 任何未配 AdsPower 的节点默认走 adspower，缺 `AIDCP_ADS_USER_ID` 即诚实报错（绝不静默回落 self）；要保持 self 的部署显式设 `AIDCP_BROWSER_PROVIDER=self`。`launch-multinode`（`scripts/launch-multinode.ts` 冻结 env）在代码内钉回 self、不需改动。Electron 桌面外壳（`src/electron/main.cjs`）**2026-07-01 起改为应用内 provider 选择、默认 adspower**（不再钉 self；选择持久化到 userData/settings.json 并注入 spawn env，外部 env 仍可覆盖），见 tasks §9。整体回滚 = 把 `selectBrowserProvider` 缺省改回 self（桌面外壳另有其应用内选择、独立于此缺省）。
- **cloud / console / 边-云协议**：**完全不动**。账号归并 / 风控 / 多租户编排仍按 `multi-account-node-support`；AdsPower 只替换 edge 的浏览器启动层，accountId 仍由 `readSelfIdentity` 从登录态读出。
- **文档**：`aidcp-edge/docs/anti-detection.md` Phase 3「指纹浏览器 + 住宅代理池 + profile×指纹×IP 三元绑定」由路线图转为本 change 落地依据（回写实现指针）。
- **非目标**：替换默认 self 路径；为 self 模式补指纹伪造；自建指纹引擎 / 代理池管理（交给 AdsPower + 运营）；任何 cloud / console / 协议改动。
