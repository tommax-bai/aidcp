# edge-bundled-ads-runtime Specification

## ADDED Requirements

### Requirement: Windows local development uses the patched bundled runtime

On a Windows development checkout, `npm run build:ads-runtime` SHALL stage `adspower-browser` without directly spawning `npm.cmd`, and `electron:dev` SHALL resolve the patched staged runtime before any raw npm package. This build-time use of the local Node/npm toolchain MUST NOT change the production runtime host: the AdsPower CLI SHALL still execute with Electron's bundled Node via `process.execPath` and `ELECTRON_RUN_AS_NODE=1`.

#### Scenario: Node 24 stages the runtime on Windows
- **WHEN** a developer runs `npm run build:ads-runtime` on Windows with Node 24
- **THEN** the staging script invokes `npm-cli.js` through the current build-time Node executable, completes without `spawnSync npm.cmd EINVAL`, and produces `build/ads-runtime/adspower-browser/cli/index.js`

#### Scenario: Electron development resolves compatibility patches
- **WHEN** both a patched `build/ads-runtime` tree and a raw `node_modules/adspower-browser` package are present
- **THEN** the desktop runtime resolves the staged CLI first and executes it with Electron's bundled Node

### Requirement: 随包内置指纹浏览器运行时，不依赖外部 AdsPower 客户端

edge 桌面客户端 SHALL 在安装包内随包分发 AdsPower CLI 运行时（`adspower-browser`）作为只读模板，并在需要时自行拉起该运行时提供本机 LocalAPI，**MUST NOT** 依赖运营机另行安装或运行 AdsPower 桌面客户端。原生模块（`node_sqlite3.node`）SHALL 置于 `app.asar` 之外（经 `extraResources` 落到 `Contents/Resources/adspower-browser`），因为原生 `.node` 无法从 asar 内 `dlopen`。指纹内核（SunBrowser）**MUST NOT** 打进安装包，SHALL 由运行时在首次启动浏览器时按需下载一次到用户可写目录。

#### Scenario: 冷机零输入启动
- **WHEN** 一台从未装过 AdsPower 客户端 / CLI 的运营机安装本客户端并首次触发需要浏览器的操作
- **THEN** 客户端先把随包模板暂存到用户可写目录，用内置密钥拉起 CLI 运行时（`ads start`），采用运行时实际上报的端口作为权威 base；首次启动浏览器时带确定性进度下载指纹内核，随后打开真实指纹浏览器——全程无需运营输入密钥、无需外部 AdsPower 客户端

#### Scenario: 运行时缺失时诚实硬停
- **WHEN** 解析随包 CLI 入口失败（包损坏 / 未随包）
- **THEN** 客户端诚实报「未随包指纹浏览器运行时」并停手、弹窗提示，**MUST NOT** 回落去连 50325，**MUST NOT** 拉起注定失败的核心子进程

### Requirement: 硬切换——始终使用随包运行时，单一 base 权威

运行时确保逻辑 SHALL 始终驱动**本客户端随包的** CLI（`ads status` 已在跑则复用、否则 `ads start -k <密钥>`），**MUST NOT** 探测 50325 并接管任意应答方（移除 external 模式与 none「继续尝试」分支）。运行时实际绑定的端口 SHALL 作为主进程所有 LocalAPI 读写（新建 / 状态 / 代理 / 删除 / 巡视）与全部核心子进程的**单一 base 权威**；主进程取参 SHALL 优先采用该 base 而非硬编码 50325。

#### Scenario: 50325 被外部占用时不串台
- **WHEN** 机器上有一个外部 AdsPower 桌面客户端占着 50325，本客户端拉起自己的运行时
- **THEN** 本运行时取一个回落端口（如 50326），本客户端把该端口作为 base 用于新建 / 启动等所有调用，**绝不**驱动那个外部服务，也不会出现「主进程发去 50325、核心发去回落端口」的串台

#### Scenario: 复用已在跑的运行时不重复起
- **WHEN** 本客户端的运行时（或机器上兼容的全局 CLI）已在某端口运行
- **THEN** `ads status` 命中即复用其上报端口，不重复起第二个 daemon；因 LocalAPI 不逐请求校验密钥，即使被复用的 daemon 是用不同密钥启动的，请求仍正常

### Requirement: 新建环境只确保服务、不触发内核下载

LocalAPI 的**元数据类**操作（新建环境 / 代理编辑 / 删除环境）SHALL 在调用前 `await` 服务确保（`ensureAdsServiceOnce`），但 **MUST NOT** 触发约 735MB 的指纹内核下载；只有**首次启动浏览器**才 `await` 内核确保。服务确保与内核确保 SHALL 各为独立单飞（single-flight），使并发的多环境启动最多触发一次内核下载。

#### Scenario: 冷机建环境不被内核下载拖住
- **WHEN** 运营在一台尚未下过内核的机器上新建环境
- **THEN** 客户端仅在数秒内确保 CLI 服务就绪即调用 `group/create`，**不**在建环境阶段下载 735MB 内核；建环境失败时返回可重试的诚实错误（不再是裸 `fetch failed`）

### Requirement: 浏览器生命周期统一使用 V2 并接管失联浏览器

核心 AdsPower provider 与 Electron 的手动检查、启动巡检 SHALL 统一使用随包 CLI 2.1.0 的 V2 profile 生命周期接口：`/api/v2/browser-profile/active`、`/api/v2/browser-profile/start`、`/api/v2/browser-profile/stop`。旧的 V1 `browser/start`、`browser/stop` 与全局 `browser/local-active` **MUST NOT** 再作为浏览器运行状态权威。Electron 巡检 SHALL 仅查询已知环境 roster 中的 profile id。

当 V2 因 daemon 重启而报告 `Inactive`、但对应 profile 的本地缓存仍记录一个活着的 SunBrowser 时，客户端 SHALL 在发起 V2 `start` 前尝试接管。接管 MUST 同时校验 `DevToolsActivePort` 中的端口和 browser websocket path 与 loopback `/json/version` 返回的 `webSocketDebuggerUrl` 完全一致；只看到端口、页面 target 或任意非 loopback 地址均不足以接管。没有通过校验的候选时 SHALL 回落到 V2 `start`，不得假成功。

#### Scenario: V2 正常报告 profile 活跃

- **WHEN** `/api/v2/browser-profile/active` 对目标 profile 返回 `Active` 和有效 `debug_port`
- **THEN** 客户端复用该端点，不发送重复的 `start`

#### Scenario: daemon 丢失 registry 但浏览器仍活着

- **WHEN** V2 对目标 profile 返回 `Inactive`，且 `~/.adspowerCli/source/cache/<profile_id>_*/DevToolsActivePort` 的端口与 browser path 都和 loopback `/json/version` 完全匹配
- **THEN** 客户端把该浏览器接管为正在运行，不启动第二个 SunBrowser，并记录失联接管日志

#### Scenario: 缓存候选过期或不匹配

- **WHEN** `DevToolsActivePort` 不存在、端口不可达、地址非 loopback，或 websocket browser path/端口与 `/json/version` 不一致
- **THEN** 客户端拒绝该候选并调用 V2 `start`，**MUST NOT** 仅凭一个可连接端口声明成功

#### Scenario: 停止后仍可连接

- **WHEN** 客户端调用 V2 `stop` 后 CDP 仍然可达
- **THEN** 客户端保持既有的 CDP-dark 确认与补救流程，并在最终无法确认关闭时诚实失败

### Requirement: 内置密钥可轮换且不硬编码，失败诚实

内置的共享 AdsPower API 密钥 SHALL 存放于随包**数据文件** `ads-runtime.json`，**MUST NOT** 硬编码进任何 `.cjs` 源码、**MUST NOT** 预置进 `settings.json`。密钥解析 SHALL 走单一解析器，优先级为 表单值 > 本机设置 > 环境变量 > 内置默认，并同时喂给主进程取参、核心子进程环境、运行时启动三处。密钥全缺失时 SHALL 诚实报「缺少 api-key」并停手，**MUST NOT** 静默假成功。

#### Scenario: 轮换密钥无需改源码
- **WHEN** 需要更换共享密钥
- **THEN** 全局轮换＝改 `ads-runtime.json` 的密钥并升 `version`、重打安装包；单机应急＝运营在高级设置填入密钥（在第二优先级生效覆盖内置默认）——两者都不需要改动源码

### Requirement: 运行时为机器级单例，退出不杀 daemon

CLI 运行时 SHALL 被视为机器级共享单例：应用退出时 `gracefulStopAllAndQuit` SHALL 仅优雅停止各核心子进程（各自诚实 `browser/stop`），**MUST NOT** 额外 `ads stop` 杀掉 CLI daemon（那会连带掐掉所有指纹浏览器、abrupt 掉锁、与其它 CLI 实例相争）。运行时若在会话中途崩溃，核心 SHALL 在连续 LocalAPI `fetch failed` 后诚实非零退出，由重启路径重跑服务确保并重新取得 base。

#### Scenario: 退出后下次启动秒复用
- **WHEN** 用户退出应用后再次打开
- **THEN** 上次留下的 daemon 仍在，`ads status` 直接复用、`reconcileRunningProfiles` 认领仍在跑的分身，不重复拉起、不重复下内核

<!-- 2026-07-25 用户决定砍掉：「席位/并发上限与内核下载失败诚实分类」需求整条删除，
     对应 tasks 7.1 / 7.2 一并作废。理由是该行为从未实装（主干搜不到席位相关实现，
     内核下载仍盲信 is_downloaded），与其把未实装的行为写进权威 spec，不如不立此条。
     若将来共享密钥席位成为真实痛点，另起 change 重新建模。 -->
