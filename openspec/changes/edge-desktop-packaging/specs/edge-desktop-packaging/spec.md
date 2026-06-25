## ADDED Requirements

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

### Requirement: 不捆绑 Chrome、缺失时诚实报错

桌面应用 MUST NOT 捆绑分发 Google Chrome，运行 MUST 依赖目标机系统已安装的 Chrome。当 Chrome 不存在时，应用 MUST 诚实报错并提示安装，MUST NOT 静默继续或伪装成功。运维文档 MUST 写明「前置须安装 Google Chrome」。

#### Scenario: 无 Chrome 诚实失败

- **WHEN** 启动时系统找不到 Chrome 可执行文件
- **THEN** 应用以明确的「Chrome 未找到、请安装」提示停手，不进入伪运行状态
