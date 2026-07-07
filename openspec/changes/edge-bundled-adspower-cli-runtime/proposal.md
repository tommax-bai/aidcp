## Why

新机器上线目前要人工下载安装 AdsPower 桌面客户端、GUI 登录、首开分身时等内核下载——步骤多、依赖 GUI、易出错。AdsPower 官方 npm CLI（`adspower-browser`）独立于桌面客户端、自带 Local API 引擎与按版本内核下载，且其唯一 native 模块（sqlite）为 N-API、能在 Electron 自带 Node 下加载。据此可把「装浏览器」这步压成「装一个 Electron 应用 + 首次开机下一次内核」，全程无需 npm / 单独装 Node / 全局安装。已于 2026-07-08 在删除桌面客户端的机器上端到端实测通过（见 design.md）。

## What Changes

- **内嵌 AdsPower CLI 运行时进安装包**：把 `adspower-browser` 包随 edge 桌面应用一起分发；Electron 伴侣端用自带 Node 拉起并看护该运行时，edge 核心连它的 Local API。新机器**不再需要单独安装 AdsPower 桌面客户端**，也不需要 npm / Node / 全局安装。
- **启动时条件式内核预检 + 进度**：伴侣端在起 edge 核心前检查所需浏览器内核是否就绪；缺则先下载并以确定型进度呈现，**下完才放行**核心启动；已就绪则秒过。下载失败诚实停手可重试，**绝不**让 edge 核心在浏览器启动调用里惰性下载（大内核会撑爆启动超时、伪失败）。
- **内核按需下载、不打进安装包**：单架构约 750MB 的浏览器内核 MUST NOT 捆绑进主安装包（体积、引擎自管内核完整性、版本漂移、再分发授权）；首次运行下载一次、缓存到用户可写目录。
- 不改动：`self`（本机 Chrome 备用腿）保留；浏览器仍 headful；登录态跨机不自动同步——运营接受新机器重新扫码登录（均不在本 change 范围）。

## Capabilities

### New Capabilities
- `adspower-cli-embedded-runtime`: 伴侣端拉起并看护随包分发的 AdsPower CLI 运行时、edge 核心连其 Local API（形态与桌面客户端无关）；启动时对所需浏览器内核做条件式预检——缺则带进度下载并门控核心启动、失败诚实可重试、绝不惰性下载；内核按需下载并落用户可写目录、不进安装包。

### Modified Capabilities
- `edge-desktop-packaging`: 新增一条打包契约——安装包 MUST 随应用捆绑可运行的 AdsPower CLI 运行时（native 模块随 hardened runtime 签名、置于 asar 之外），并 MUST NOT 捆绑浏览器内核；运行该运行时 MUST 复用 Electron 自带 Node、不依赖目标机的 Node/npm/全局安装。

## Impact

- **代码（aidcp-edge）**：`src/electron/main.cjs`（启动链 `startFlow`→`startAdsPowerFlow`→`startEdge`、状态推送 `updateStatus`/`status:update`、新增运行时启动看护与内核预检、`AIDCP_ADS_API_BASE` 指向本地运行时端口）、`src/electron/renderer/`（准备态 + 进度条）、`src/electron/preload.cjs`（新 IPC 通道）；`package.json` electron-builder `extraResources`/`asarUnpack` + 签名。edge 核心侧 `AdsPowerProvider` 预期零改动（已按可配 base 打 Local API）。
- **依赖**：新增随包依赖 `adspower-browser`（约 58MB，含预编译 sqlite N-API + playwright-core 引擎）。运行时依赖 AdsPower 付费套餐的 Local API 权限与一把账号级 api-key（敏感值，只记读取方式）。
- **安装包体积**：+~58MB（运行时）；内核不进包。
- **归档顺序提醒**：`edge-desktop-packaging` 亦被活跃 change `edge-installer-oss-distribution` 触及，delta 为纯新增；归档时若两者交织需按序合并。
- **文档**：`docs/anti-detection.md`、OPERATOR 新机装机路径（后续随实装补）。
