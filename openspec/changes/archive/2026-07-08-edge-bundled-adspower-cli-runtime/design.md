## Context

edge 支持两种浏览器来源：`self`（自起本机 Chrome）与 `adspower`（经 AdsPower Local API 托管指纹浏览器，默认已是它）。现役 adspower 形态下，运营机上线要人工装 AdsPower 桌面客户端、GUI 登录、首开分身等内核下载。核心接入链已 provider-agnostic：`AdsPowerProvider` 只按可配 base（`AIDCP_ADS_API_BASE`，默认 `http://local.adspower.net:50325`）打 Local API 拿 `debug_port` 再走 CDP，对客户端是 GUI 还是 CLI 无假设。

AdsPower 官方另有 npm CLI `adspower-browser`，独立于桌面客户端、自带同一套 Local API 引擎与按版本内核下载。本 change 用它把「装浏览器」压成随包分发 + 首启下内核。

**2026-07-08 本机实测依据**（删除桌面客户端后的 mac、arm64）：
- `npm i -g adspower-browser`(v2.1.0) 装成，`ads`/`adspower`/`adspower-browser` 三别名指向 `cli/index.js`；可直接 `node cli/index.js` 跑，无需全局安装。
- `ads start -k <KEY>` 起 Local API 于 `http://local.adspower.net:50325`；根级 `/status` 免鉴权返 `{code:0}`；`/api/v1/user/list` 带 Bearer key 鉴权通、真列出账号 profile。
- `get-kernel-list` 含内核 148（我们指纹 pin 值，`aidcp-edge/src/electron/ads-fingerprint.cjs:17`）；`download-kernel {"kernel_type":"Chrome","kernel_version":"148"}` 走完 `pending→downloading 0→100%→installing→completed`，落 `~/.adspowerCli/chrome_148`，**单架构 749MB**（整个 `~/.adspowerCli` 855MB）。
- `GET /api/v1/browser/start?user_id=…&open_tabs=1&ip_tab=0&headless=0` 返 `code:0` + `debug_port`；`127.0.0.1:<port>/json/version` = `Chrome/148.0.7778.97`（headful，用刚下的 148）；`browser/stop`→`browser/active`=Inactive 回收正常。
- 包体 58MB：引擎 `cwd/lib/main.min.js`(11MB) 纯 JS + playwright-core；**唯一 native 模块是 sqlite**，预编译 5 架构（mac/arm64/x64/linux/ia32）**且为 N-API**（`node_sqlite3.node` 含 298 个 napi 符号）。
- edge 用 Electron `^31.7.7`（自带 Node 20，满足 CLI `engines.node>=18`），现成就用 `ELECTRON_RUN_AS_NODE=1` + `process.execPath` spawn 核心子进程（`src/electron/main.cjs:644`）。

## Goals / Non-Goals

**Goals:**
- 新机器无需单独安装 AdsPower 桌面客户端、无需 npm / 单独 Node / 全局安装即可跑 adspower 形态。
- 首次开机自动、可见（带进度）地下载一次浏览器内核，之后即开即用。
- edge 核心侧尽量零改动（继续按可配 base 打 Local API）。

**Non-Goals:**
- 不做全 CLI 化 / 无 GUI / headless / 服务器化——运营机仍是有屏幕的普通机器、浏览器仍 headful。
- 不下线 `self`（本机 Chrome 备用腿保留）。
- 不解决登录态跨机自动同步——接受新机器重新扫码登录。
- 不修订 `pluggable-browser-provider` / `chrome-instance-isolation` / `adspower-desktop-env-picker` / `adspower-environment-provisioning`（后续 change）。
- 内核不打进主安装包。

## Decisions

**D1. 用 Electron 自带 Node 跑内嵌运行时，不单独打包 Node。**
sqlite 是 N-API（ABI 跨 Node 版本稳定、Electron 支持），故 `adspower-browser` 的预编译 `.node` 能在 Electron 自带 Node 下加载。复用现有 `ELECTRON_RUN_AS_NODE=1`+`process.execPath` spawn 模式起 `cli/index.js start -k <key>`。
- 备选：随包再打一个独立 Node 二进制（每平台 +~40-50MB）。否决：N-API 已保证兼容，白增体积。

**D2. 运行时随包置于 asar 之外（extraResources / asarUnpack）。**
引擎要 dlopen native `.node` 且会 spawn 子进程（SunBrowser/chromedriver）、读写工作目录——asar 内做不到。
- 备选：打进 asar。否决：native 模块与子进程 spawn 均不可行。

**D3. 引擎工作目录/缓存指到用户可写位置。**
mac app bundle 只读且已签名，引擎自更新（`cwd/lib/version/*` 版本包 + `update-patch`）与缓存不能写进 bundle。内核缓存本就落 `~/.adspowerCli`；包自带的 `cwd/` 若需写，首次运行复制到用户可写目录再从那儿跑。
- 备选：直接从只读 bundle 跑。否决：自更新/缓存写失败或破坏签名。

**D4. 启动时条件式内核预检，门控 edge 核心启动。**
插在 `startAdsPowerFlow`（`src/electron/main.cjs:767`）里、`startEdge()`（`main.cjs:622`）之前：`get-kernel-list` 查 `is_downloaded` → 在则秒过；缺则 spawn `download-kernel`、解析其 `Kernel progress: N% [state]` 流经 `updateStatus`/`status:update`（`main.cjs:478`，新增 kernel 进度字段）推渲染层画确定型进度条，**completed 才 `startEdge()`**。
- 备选：不预检、让引擎在 `browser/start` 撞「内核未就绪」时惰性下载。**否决（红线）**：749MB 要下数分钟，会撑爆 edge 的 CDP 就绪 15s / `browser/start` 30-60s 超时 → 伪失败 + 无进度可见 + 反复重试看着像坏了。

**D5. 内核按需下载、不打进主安装包。**
- 体积：749MB×（mac arm64+x64、win x64）≈ 2GB+，与 `edge-installer-oss-distribution`（安装包瘦身走 OSS）方向冲突。
- 引擎自管内核（版本清单 + `is_downloaded` + 完整性），out-of-band 预塞易被判未下载/校验失败。
- 版本会漂（内核升级要重发安装包）、再分发 SunBrowser 二进制授权含糊。
- 备选（未来/out-of-scope）：真要离线/弱网首启，走自建 OSS 镜像或独立可选「内核预置包」，不塞主安装包。

**D6. Local API 端口以 `ads status` 实际值为准喂 `AIDCP_ADS_API_BASE`，不硬编码 50325。**
默认 50325，但被占时引擎会在端口段内回退；伴侣端读实际端口再起核心，避免漂。

## Risks / Trade-offs

- **N-API 在目标 Electron 版本仍需真机验** → 打包后在干净 mac(arm64/x64)+win 各起一次运行时，确认 `.node` 加载、`ads start` 起服、端点直连通。
- **mac 签名/公证**：内嵌 `.node` 须随 hardened runtime 一起签（build 已配 `hardenedRuntime`+`notarize`）；内核/chromedriver 运行时下到 `~/.adspowerCli`、不在 bundle 内、走 AdsPower 自签，**干净机首启 Gatekeeper 行为需验**（可能对下载的二进制弹阻）。→ 真机验收项。
- **运行时进程无人看护**（现状 critic 已指出）→ 伴侣端须看护该运行时：起不来/中途死则诚实呈现 + 重起，不静默把核心带进注定失败的启动。
- **首启下载耗时/中断** → 进度文案标「约 750MB、仅首次」；断网失败诚实停「准备失败+重试」不起 edge；`download-kernel` 重跑续传/重来行为需实测确认。
- **付费门槛 + api-key**：Local API 仅付费套餐；首次 api-key 目前仍需一次桌面客户端 GUI 生成，之后账号级复用到各机（key 为敏感值，只记读取方式、不落文档/提交/tasks.md）。
- **GUI/headless 互斥不成问题**：只装内嵌 CLI 运行时、不装桌面客户端，运营机无同机互斥、50325 归其独占。

## Migration Plan

1. 先在干净机器（mac arm64/x64、win）打包并起运行时，坐实 N-API 加载 + 端点直连 + 内核下载 + `browser/start`+CDP + Gatekeeper 首启行为。
2. 伴侣端接入：内嵌运行时启动看护 → 内核预检+进度 → 端口对接 → 起核心。edge 核心零改动验证。
3. 灰度：单账号完整 cloud 闭环（对应真机 backlog `adspower-browser 8.2`，本 change 前置）。
4. 回滚：保留 self 备用腿与外部 `AIDCP_ADS_API_BASE` 逃生阀；内嵌运行时不可用时可回退到「外部已装 AdsPower 客户端 + 手填 base」旧路径。

## Open Questions

- `download-kernel` 中断后是续传还是重来？失败重试是否幂等？
- 预检下哪些内核：固定 148 vs 读该机 profile 实际内核版本集合（先保 148，多版本后扩）。
- `cwd/` 是否必须复制到可写目录，还是仅缓存/版本目录需可写（首次打包后实测引擎写路径）。
- win 下 native `.node` 与运行时的签名/SmartScreen 行为（对齐 mac 公证的等价验证）。
