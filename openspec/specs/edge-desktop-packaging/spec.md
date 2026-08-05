# edge-desktop-packaging Specification

## Purpose
TBD - created by archiving change edge-desktop-packaging. Update Purpose after archive.
## Requirements
### Requirement: 打包产物自带可运行的编译产物

打包后的桌面应用 MUST 在**不依赖目标机有任何开发工具链**（Node / npm / npx / tsx / TypeScript）的前提下启动并运行 edge 业务逻辑。应用 MUST 运行**构建期预编译出的 JavaScript**，并用 Electron 自带的 Node 运行时执行（而非在运行时解释 TypeScript 源码）。构建脚本 MUST 在打包前完成编译；编译失败 MUST 使整体构建失败，MUST NOT 带着过期或缺失的编译产物出包。

#### Scenario: 装到无 Node/tsx 的机器上能启动

- **WHEN** 应用被装到一台未安装 Node / npx / tsx 的 macOS 或 Windows 机器并启动
- **THEN** edge 子进程正常拉起并进入运行（不出现「找不到 tsx / node / npx」类启动失败）

#### Scenario: 编译失败即构建失败

- **WHEN** 打包构建期 TypeScript 编译报错
- **THEN** 构建整体失败、不产出安装包，MUST NOT 用上一次的旧编译产物或原始 `.ts` 源码替代

### Requirement: 双平台打包目标

构建 MUST 能产出 macOS 与 Windows 两个平台的可分发产物。macOS MUST 同时覆盖 `x64` 与 `arm64` 架构，并产出可拖装的 `dmg`（`zip` 供后续自动更新留口）。Windows MUST 产出 `nsis` 安装包。打包脚本 MUST NOT 把目标写死为单一平台。

#### Scenario: macOS 双架构产物

- **WHEN** 在 macOS 主机执行 macOS 打包
- **THEN** 产出覆盖 `x64` 与 `arm64` 的 macOS 安装产物（`dmg`+`zip`）

#### Scenario: Windows 产物

- **WHEN** 执行 Windows 打包
- **THEN** 产出 `nsis` 安装包

### Requirement: 运行时路径跨平台

edge 运行时 MUST NOT 依赖 POSIX-only 的硬编码路径。发布审批信号文件目录的默认值 MUST 为当前系统的临时目录（`os.tmpdir()`），并 MUST 可经 `AIDCP_PUBLISH_APPROVAL_SIGNAL_DIR` 环境变量覆盖。当 edge 与写入方在同机协作（本地 mock/e2e）时，两端 MUST 能经该环境变量对齐到同一目录。

#### Scenario: Windows 上本地 mock/e2e 不因 /tmp 缺失而失败

- **WHEN** 在 Windows 上跑本地 mock/e2e 走 edge 文件审批闸
- **THEN** 信号文件落在 `os.tmpdir()` 下、可被正常写入与读取，不因 `/tmp` 不存在而失败

#### Scenario: 环境变量覆盖两端对齐

- **WHEN** 设置 `AIDCP_PUBLISH_APPROVAL_SIGNAL_DIR` 为某目录并在同机运行写入方与 edge
- **THEN** 两端解析出的信号文件路径一致

### Requirement: 启动与运行失败对运维可见

当 edge 子进程异常退出、Chrome 缺失、或连接云端失败时，桌面应用 MUST 主动把失败暴露给运维（弹出主窗口 + 发系统通知），MUST NOT 停在「starting/运行中」的外观而实际未在运行（守「不静默假成功」红线）。edge 在连云失败时 MUST 诚实硬失败（清晰报错 + 非零退出），MUST NOT 加退避重试去制造「看着在重连其实没跑」的假象。

#### Scenario: 连云失败时崩溃可见

- **WHEN** edge 无法连接云端
- **THEN** edge 以清晰错误诚实退出（非零退出码），且桌面应用弹出窗口 + 发系统通知告知失败，不停留在「运行中」外观

#### Scenario: Chrome 缺失时明确提示

- **WHEN** 目标机未安装 Google Chrome
- **THEN** 应用显示「请安装 Chrome」类明确提示并发系统通知，MUST NOT 静默装作已在运行

#### Scenario: 不以退避重试掩盖失败

- **WHEN** 实现连云失败处理
- **THEN** 采用「快速失败 + 可见」，MUST NOT 引入无限/退避重试来掩盖未连通状态

#### Scenario: 同机第二个实例诚实拒绝（不静默接管）

- **WHEN** 在同一台机器上已有一个实例运行时再启动第二个实例（多开隔离尚未实现）
- **THEN** 第二个实例 MUST 诚实拒绝（明确提示「已在运行」并退出），MUST NOT 静默接管第一个实例/账号的浏览器；该单实例保护 MUST NOT 影响「同一应用退出后重启、重连其自身浏览器」

### Requirement: 不捆绑 Chrome、缺失时诚实报错

桌面应用 MUST NOT 捆绑分发 Google Chrome，运行 MUST 依赖目标机系统已安装的 Chrome。当 Chrome 不存在时，应用 MUST 诚实报错并提示安装，MUST NOT 静默继续或伪装成功。运维文档 MUST 写明「前置须安装 Google Chrome」。

#### Scenario: 无 Chrome 诚实失败

- **WHEN** 启动时系统找不到 Chrome 可执行文件
- **THEN** 应用以明确的「Chrome 未找到、请安装」提示停手，不进入伪运行状态

### Requirement: 安装包捆绑可运行的 AdsPower CLI 运行时、但不捆绑浏览器内核

打包后的桌面应用 MUST 随包分发一份可直接运行的 AdsPower CLI 运行时（`adspower-browser`），使目标机在**不单独安装 AdsPower 桌面客户端、且无 npm / 独立 Node / 全局安装**的前提下即可经该运行时的 Local API 托管指纹浏览器。运行该运行时 MUST 复用 Electron 自带的 Node 运行时（`ELECTRON_RUN_AS_NODE`），MUST NOT 随包再打独立 Node 二进制。运行时中的 native 模块（sqlite）MUST 置于 asar 归档之外并随应用的 hardened runtime 一同签名，以便加载与 spawn 子进程。桌面应用 MUST NOT 把浏览器内核（约每架构数百 MB）捆绑进主安装包——内核由运行时在首次需要时按需下载。

#### Scenario: 无桌面客户端与工具链也能起运行时

- **WHEN** 目标机只装了本桌面应用、未装 AdsPower 桌面客户端、也无 npm/独立 Node
- **THEN** 应用用自带 Node 拉起随包的 AdsPower CLI 运行时并对外提供 Local API，无需任何额外安装

#### Scenario: 主安装包不含浏览器内核

- **WHEN** 构建产出主安装包
- **THEN** 安装包内 MUST NOT 含浏览器内核二进制；内核在运行期按需下载到用户可写目录

#### Scenario: native 模块随应用签名且可加载

- **WHEN** 在已签名/公证的 macOS 应用中加载运行时的 sqlite native 模块
- **THEN** 该 native 模块位于 asar 之外、随 hardened runtime 一同签名，能被 Electron 自带 Node 正常加载

### Requirement: 发版不再需要改 console 源码的版本号

Publishing a new desktop installer SHALL consist of building the artifact and placing it in the target host's downloads directory. The release procedure MUST NOT require editing a version constant in console source, nor rebuilding and redeploying the console, in order for the download page to offer the new installer.

This removes the class of release bug where the page and the directory disagree: a forgotten source edit used to leave the page advertising an old version or linking to a file that was never uploaded, and the page had no way to detect that it was lying.

#### Scenario: 上架新包即生效

- **WHEN** a new signed installer is placed in a host's downloads directory
- **THEN** that host's download page offers it without any console source change, rebuild, or redeploy

#### Scenario: 版本号不再是需要跨分支对账的东西

- **WHEN** a release branch is cut from trunk
- **THEN** no installer version constant needs to be reconciled between the release branch and trunk, because the version is not carried in source

### Requirement: 桌面监督者提供可见且可恢复的托盘入口

桌面监督者 SHALL 使用随应用分发、Electron 在目标平台明确支持的图像文件创建托盘图标，MUST NOT 使用解码为空的图像或不受支持的内联格式创建透明托盘入口。开发态与打包态 SHALL 分别从确定性资源路径加载同一品牌图标；打包配置 MUST 将该资源实际放入安装包。图标文件缺失或解码为空时，监督者 SHALL 诚实暴露错误并保持主窗口可见，MUST NOT 允许窗口隐藏后只留下不可发现但仍持有单实例锁的后台进程。

#### Scenario: Windows 开发态显示托盘图标

- **WHEN** 运维在 Windows 以开发态启动监督者且随仓 PNG 资源有效
- **THEN** 通知区显示可辨识的 AIDCP Edge 图标，点击该入口可切换主窗口显示状态

#### Scenario: 打包态从随包资源加载图标

- **WHEN** 运维启动安装后的桌面应用
- **THEN** 监督者从安装包资源目录加载受支持的托盘图像，通知区图标可见且不依赖开发仓库或当前工作目录

#### Scenario: 托盘资源失效时保持窗口可恢复

- **WHEN** 托盘图像文件缺失、无法读取或解码结果为空
- **THEN** 监督者不创建透明托盘入口，明确暴露加载失败并保持主窗口可见，关闭动作不得把应用变成不可发现但仍占单实例锁的后台进程

### Requirement: Final packages exclude all migrated platform browser rules
The desktop build SHALL exclude migrated Facebook and WeChat browser-rule modules, production-reachable page probes, development probe scripts, standalone embedded-router sources, and source maps from distributable JavaScript and packaged resources. Verification MUST inspect both the production import graph and the final ASAR/resources rather than inferring absence from source imports.

#### Scenario: Migrated Facebook marker remains
- **WHEN** production-dist or final-package inspection finds a denied Facebook executor/probe path or representative cleartext page-rule marker
- **THEN** the desktop build fails and no distributable is accepted

#### Scenario: Development probe is accidentally packaged
- **WHEN** any `scripts/*probe*` input or equivalent calibration payload appears in ASAR or packaged resources
- **THEN** final-package verification fails

### Requirement: Expanded Native artifact is package-compatible
The packaged Native Page Engine manifest SHALL declare the protocol and adapter coverage required for Xiaohongshu, Facebook, and WeChat browser-session capture, and the executable SHALL match the target architecture and verified digest. Missing platform coverage or a mismatched artifact MUST fail packaging/startup.

#### Scenario: Facebook adapter is absent
- **WHEN** a customer package requires Facebook but its Native manifest does not declare the compatible Facebook adapter/protocol
- **THEN** package verification fails before a distributable is emitted

#### Scenario: Packaged smoke test opens each adapter
- **WHEN** the final packaged resource is smoke-tested
- **THEN** the executable starts outside ASAR and accepts bounded session/protocol validation for every declared platform adapter

### Requirement: 打包态运行时验证不得执行未签名的 macOS 中间应用

桌面打包流程 MUST 在产出安装包前验证最终 ASAR 中必需的生产依赖能够由目标 Electron Node 运行时加载。macOS 的该验证 MUST NOT 在 electron-builder 完成正式签名前启动刚生成的产品 App；同架构验证 SHALL 使用仓库锁定且代码签名有效的开发 Electron 读取最终 ASAR。验证运行时缺失、签名无效、架构不可执行或 smoke 失败时，构建 MUST 诚实失败并给出可诊断原因，MUST NOT 关闭 Gatekeeper、移除系统安全策略或把动态失败降级为成功。

#### Scenario: macOS 同架构构建不启动未签名产品 App

- **WHEN** arm64 macOS 主机为 arm64 目标执行 `afterPack`
- **THEN** 构建 SHALL 使用签名有效的开发 Electron 加载生成 App 内的最终 ASAR，且 MUST NOT 启动尚未正式签名的产品 App

#### Scenario: 打包依赖无法加载时仍然失败

- **WHEN** 最终 ASAR 中的 `jsdom`、`tough-cookie` 或 `ws` 缺失或不可加载
- **THEN** 动态 smoke SHALL 非零失败并阻止安装包生成，MUST NOT 因改用可信 runner 而跳过运行时验证

#### Scenario: 可信 runner 无效时诚实停手

- **WHEN** 开发 Electron 不存在或代码签名校验失败
- **THEN** 构建 SHALL 在执行 smoke 前失败并指出 runner 问题，MUST NOT 回退启动未签名产品 App

#### Scenario: 跨架构构建保持静态验证

- **WHEN** 构建目标架构不能由当前主机原生执行
- **THEN** 构建 SHALL 继续执行依赖闭包、native artifact 与泄漏静态检查，并跳过动态二进制执行

### Requirement: 本地 arm64 OL 打包入口可复用且失败关闭

Edge 仓库 SHALL 提供两个受版本控制的 macOS arm64 OL 本地打包入口：一个生成 Developer ID 签名但未公证的 DMG，另一个生成 Developer ID 签名、公证并 staple 的 DMG。两个入口 MUST 共用同一套构建和最终产物验证逻辑，MUST 基于无已跟踪改动且无构建相关未跟踪源码的 checkout、锁定依赖和 Native Page Engine 声明工具链重新构建全部运行时。OL 包 MAY 注入非秘密 `aidcpCloudDefaultEnv=ol` 作为登录页预选，但 MUST NOT 注入或验证 `aidcpClientAuthUrl` 等绝对 Cloud URL。任一构建、架构、目标目录、默认目标或签名门禁失败 MUST 使脚本非零退出。

#### Scenario: 仅签名入口生成 arm64 OL 包

- **WHEN** 操作者在 macOS 上以有效 Developer ID 凭据运行仅签名入口
- **THEN** 脚本生成本次 arm64 OL DMG，验证应用、GOST、Native Page Engine 与 AdsPower sqlite 架构及有效签名，并明确标记未公证

#### Scenario: 仅签名入口不要求公证凭据

- **WHEN** 操作者运行仅签名入口且未提供 App Store Connect API 凭据
- **THEN** 脚本跳过公证检查并继续构建，MUST NOT 静默退出

#### Scenario: 公证入口串行完成 App 与 DMG 公证

- **WHEN** 操作者提供有效 Developer ID 与 App Store Connect API 凭据
- **THEN** 脚本依次完成 App 和 DMG 的签名、公证、staple、Gatekeeper 与包内运行时验证后方可报告成功

#### Scenario: 自动使用项目要求的 Rust 工具链

- **WHEN** 当前默认 Rust 版本低于 Native Page Engine 声明版本
- **THEN** 脚本解析并使用声明版本而不是继续使用不兼容默认版本

#### Scenario: Final package contains a valid target catalog and no baked auth URL

- **WHEN** 挂载最终 DMG 并读取 `app.asar`
- **THEN** 包内包含完整 DEV/OL 目标目录及预期默认目标，且不存在活动 `aidcpClientAuthUrl` 绝对地址元数据或独立登录 URL 路由

#### Scenario: 凭据不进入仓库和日志

- **WHEN** 脚本需要 p12 密码或 Apple API 私钥
- **THEN** 密码仅从环境变量或 `/dev/tty` 隐式读取，私钥仅以文件路径引用且秘密值不进入源码或日志

#### Scenario: 旧产物不进入本次验证或公证

- **WHEN** 输出目录已有其他架构或版本的安装包
- **THEN** 脚本隔离旧输出并仅选择本次版本与 arm64 产物

#### Scenario: 无关未跟踪文件不阻塞构建

- **WHEN** checkout 无已跟踪改动且未跟踪文件不属于源码构建图
- **THEN** 脚本保留这些文件并继续构建

#### Scenario: 构建相关未跟踪源码仍被拒绝

- **WHEN** `src/`, `native/`, `scripts/` 存在未跟踪源码或任一已跟踪文件有改动
- **THEN** 脚本列出相关路径并非零退出

### Requirement: Official desktop packages MUST include a compatible Native Page Engine

Every official package that advertises Xiaohongshu page automation SHALL include exactly one architecture-compatible Native Page Engine outside ASAR together with a manifest containing its platform, architecture, engine version, protocol version, capability digest, and SHA-256. Package construction and startup verification MUST fail honestly when the artifact or manifest is missing, mismatched, corrupted, or incompatible.

#### Scenario: macOS arm64 package is built
- **WHEN** CI builds the official macOS arm64 client
- **THEN** the package contains the arm64 Native executable and matching verified manifest under `extraResources`

#### Scenario: Artifact architecture is wrong
- **WHEN** a package stages an x64 artifact into an arm64 build or otherwise mismatches the target
- **THEN** package verification fails and no distributable is emitted

### Requirement: Nested Native artifacts MUST be signed and verified

On macOS, release construction SHALL sign the Native executable as a nested binary of the application bundle before the bundle itself is signed, notarized, and stapled. Release validation on macOS MUST verify the nested executable's own signature and its team identity against the outer bundle, the outer application and disk image's notarization, the manifest hash, the executable's architecture, and packaged startup behavior; a nested binary that resolves outside the signed resources directory MUST be rejected.

The Windows package flow SHALL stage the architecture-matched Native executable into the package, but it does not sign binaries and there is no nested-signature verification on that platform. Any artifact whose signature has not been verified — a Windows installer, or a local macOS build produced without Developer ID credentials — MUST be labelled by its actual signing state and MUST NOT be described or published as a signed distributable.

#### Scenario: Signed macOS package passes release gates
- **WHEN** the Native executable, app, and disk image have valid Developer ID signatures/notarization and the packaged smoke test starts the engine from resources outside ASAR
- **THEN** the macOS artifact may proceed to release review

#### Scenario: Inner signature is missing
- **WHEN** the outer app is signed but the nested Native executable fails signature verification
- **THEN** the release job fails and MUST NOT upload a distributable artifact

#### Scenario: Windows installer is produced
- **WHEN** the Windows package flow stages the x64 Native executable and emits an installer
- **THEN** the installer carries the architecture-matched executable
- **AND** it is recorded as unsigned and MUST NOT be presented as a signed distributable

### Requirement: Packaging MUST exclude migrated Xiaohongshu JavaScript core

The desktop build graph SHALL include only the selector-free Native facade for Xiaohongshu and MUST exclude migrated legacy browse/publish rule modules, source maps, and representative rule strings. This exclusion SHALL be verified against the final package, not inferred from TypeScript import reachability alone.

#### Scenario: ASAR contains a forbidden legacy module
- **WHEN** final-package inspection finds a migrated Xiaohongshu executor path or cleartext rule marker
- **THEN** the desktop build fails

#### Scenario: Ordinary non-Xiaohongshu code remains required
- **WHEN** a shared selector-free utility is still needed by another platform
- **THEN** it remains packaged only after dependency inspection proves it does not carry migrated Xiaohongshu page rules

