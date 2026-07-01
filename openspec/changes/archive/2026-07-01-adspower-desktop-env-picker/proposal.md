## Why

承接 `adspower-browser-provider` §9（桌面外壳应用内 provider 选择）。当前桌面外壳对 AdsPower 是**盲配**：面板只让运维**手敲一个分身 id**（`src/electron/main.cjs:267` 仅校验非空），AdsPower 没装 / 没开 / 本地 API 没启 / 环境不对，统统要等核心进程起来、调 `browser/start` 失败才**延迟暴露**——反馈晚、错误笼统。手敲 id 易错，也无从核对每个环境的代理 / IP（防关联绑定 D6）。本 change 把「AdsPower 可用性前置探测 + 环境选择」补上，让失败提前、选择可视。

## What Changes

- **edge 桌面外壳 — AdsPower 可用性前置探测**：面板在打开设置 / 点「检测」时调本地 API `GET /status`。可达 = 客户端在运行且开了本地 API；不可达 = 没装 / 没开 / 没启 API → **诚实提示**「请启动 AdsPower 并开启本地 API」并给下载入口，不再只靠核心延迟失败。（「是否已安装」无独立接口，由不可达反推引导。）
- **edge 桌面外壳 — 浏览器环境列表拉取 + 下拉选择**：调 `GET /api/v1/user/list`（可带 group_id / 分页）列出所有浏览器环境（名称 / 分身 id / 分组 / 代理配置摘要），面板用**下拉选择**替代手敲分身 id；顺带显示每个环境的代理配置（proxy 类型 / host + 配置 `ip`，可能为空 / 占位，**非实测出口 IP**——实测以 AdsPower『检测代理』为准），供运维初步核对防关联绑定铁律（1 环境 = 1 指纹 = 1 独立 IP = 1 账号）。选中环境的 **`user_id`**（非 `serial_number` 序号）写入现有 `settings.adsProfileId`、注入 `AIDCP_ADS_USER_ID`，**下游零改动**。手敲 id 作兜底保留（拉取失败诚实降级仍可手填）。
- **edge 桌面外壳 —「打开 AdsPower 新建环境」入口**：AdsPower 客户端不公开跳到其内部「新建浏览器」tab 的深链 / URL scheme，故**不承诺一键直达那个 tab**。折中方案：按钮 best-effort 拉起 / 聚焦 AdsPower 客户端（起不来退回 `shell.openExternal` 到官网 / 控制台），提示「请在 AdsPower 中点『新建浏览器』完成配置后回来点刷新」，配合「刷新环境列表」闭环。**不**采用 `POST /api/v1/user/create`（要传指纹 + 代理一堆参数，等于在面板重做建环境表单，越界且过重）。
- **edge — Electron 主进程侧新增自包含只读模块**（`src/electron/ads-local-api.cjs`，含 `status` / `listProfiles`）：因主进程是 CJS、核心是 spawn 出的 ESM 子进程（两进程不通、`require` 也复用不了），**自持一条 ≥1s 串行节流**（本地 API 1 req/s 限速）+ 可选 Bearer，按端点显式拼 URL（根级 `/status` 免鉴权、`/api/v1/user/list` 开校验时带 api-key）；**不改、不复用**核心 `browser/start|stop|active` 与其 `api<T>()`。
- **诚实失败红线延续**：探测不通 / 拉取失败 → 如实提示，绝不假成功、绝不静默回落 / 空跑。
- **全量中文化**（承接 §9 面板已中文化风格）。

## Capabilities

### New Capabilities
- `adspower-desktop-env-picker`：桌面外壳内的 **AdsPower 环境探测与选择**——① 前置探测本地 API 可用性（`/status`），不可达诚实提示 + 下载入口；② 拉取并下拉选择浏览器环境（`user/list`），替代手敲分身 id、显示代理 / IP 供核对防关联绑定，选中写入既有 `adsProfileId`、下游零改动，手敲作兜底；③「打开 AdsPower 新建环境」best-effort 入口（拉起 / 聚焦客户端 + 提示 + 刷新闭环，不 `user/create`）。所有新增本地 API 调用**只读**、沿用 ≥1s 节流、MUST NOT 碰启动 / 生命周期层，探测 / 拉取失败**诚实降级**、不假成功。

### Modified Capabilities
<!-- 无 baseline 能力的 REQUIREMENTS 变更。桌面 provider 选择需求（「桌面外壳内可选浏览器 provider 且默认 adspower」，
     含「分身 id 必填」）目前只存在于**尚未归档**的 adspower-browser-provider change 的 pluggable-browser-provider
     delta、未并入 baseline openspec/specs/，故本 change 不作 MODIFIED delta（否则 validate --strict 找不到 baseline
     需求而失败）。改以**加性衔接**：环境下拉是既有「分身 id 必填」的获取方式增强，手敲 id 仍保留、不与其冲突，无需软化
     对方措辞。参 adspower-browser-provider D7。本 change 只 ADD 新能力 adspower-desktop-env-picker。 -->

## Impact

- **aidcp-edge（主体，仅 Electron 外壳 + 本地 API 只读查询）**：
  - **新增** `src/electron/ads-local-api.cjs`（Electron 主进程侧自包含只读模块）：`status()` / `listProfiles()`，自持 ≥1.1s 串行节流 + 可选 Bearer，按端点显式拼 URL；核心 `src/cdp/browser-provider.ts` 的 `api<T>()` 与 `browser/start|stop|active` **不改、不复用**（跨进程 + CJS/ESM 隔离，见 design D3/D3a）。
  - `src/electron/main.cjs`：新增 IPC handler（探测 / 拉列表 / 打开新建），在打开设置 / 保存前触发探测。
  - `src/electron/preload.cjs`：暴露 `ads:status` / `ads:listProfiles` / `ads:openCreate` 通道。
  - `src/electron/renderer/`（`index.html` / `renderer.js` / `styles.css`）：新增「检测状态徽标、环境下拉 + 刷新、打开新建环境」控件 + 中文化；手敲 id 输入框保留为兜底。
  - `settings` 结构：仍存 `adsProfileId`（选中即写入）；是否加可选 `adsGroupId`（按分组过滤列表）由 design 定。
- **不动**：cloud / console / 边-云协议 / 核心 provider 启动生命周期层（`browser-provider.ts` 的 `launch` / `kill` / `killAndConfirmDead`）/ CDP 接入及下游（定位 / 拟人 / 读身份）。
- **与 adspower-browser-provider 协调**：加性、无需软化对方措辞；两 change 归档顺序不强制（本 change 只 ADD 独立新能力）。
- **文档**：`aidcp-edge/OPERATOR.md` 补「可用性探测 + 环境选择 + 新建入口」用法。
- **非目标**：面板内建环境（指纹 / 代理配置仍属 AdsPower）；AdsPower 分组的服务器侧编排；任何 cloud / console / 协议改动；改核心 provider 启动 / 生命周期层。
