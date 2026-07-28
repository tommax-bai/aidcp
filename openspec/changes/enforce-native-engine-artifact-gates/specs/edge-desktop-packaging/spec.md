## MODIFIED Requirements

### Requirement: 打包产物自带可运行的编译产物

打包后的桌面应用 MUST 在**不依赖目标机有任何开发工具链**（Node / npm / npx / tsx / TypeScript / Rust）的前提下启动并运行 edge 业务逻辑。应用 MUST 运行**构建期预编译出的 JavaScript**，并用 Electron 自带的 Node 运行时执行（而非在运行时解释 TypeScript 源码）。构建脚本 MUST 在打包前完成编译；编译失败 MUST 使整体构建失败，MUST NOT 带着过期或缺失的编译产物出包。

这条"不得带着过期产物出包"同样约束随包分发的 Native 页面引擎可执行文件。打包前 MUST 校验该产物**与当前引擎源码一致**，判据 MUST 由源码输入本身导出（引擎源码、页面规则分片及其清单、构建脚本、命令清单），MUST NOT 仅依赖产物自身写下的校验和、产物自身写下的清单、crate 版本号或不随实现改动变化的能力摘要——这些彼此自洽、对源码漂移无感。校验判定为过期时 MUST 重建或使构建失败，MUST NOT 打印通过。

#### Scenario: 装到无 Node/tsx 的机器上能启动

- **WHEN** 应用被装到一台未安装 Node / npx / tsx 的 macOS 或 Windows 机器并启动
- **THEN** edge 子进程正常拉起并进入运行（不出现「找不到 tsx / node / npx」类启动失败）

#### Scenario: 编译失败即构建失败

- **WHEN** 打包构建期 TypeScript 编译报错
- **THEN** 构建整体失败、不产出安装包，MUST NOT 用上一次的旧编译产物或原始 `.ts` 源码替代

#### Scenario: 引擎源码改了但产物没重编

- **WHEN** 引擎源码或页面规则分片已修改，而随包分发的 Native 引擎产物仍来自上一次构建
- **THEN** 打包前校验判定该产物过期并使构建失败或触发重建
- **AND** MUST NOT 报告校验通过、MUST NOT 把与当前源码不符的引擎打进安装包

### Requirement: 双平台打包目标

构建 MUST 能产出 macOS 与 Windows 两个平台的可分发产物。macOS MUST 同时覆盖 `x64` 与 `arm64` 架构，并产出可拖装的 `dmg`（`zip` 供后续自动更新留口）。Windows MUST 产出 `nsis` 安装包。打包脚本 MUST NOT 把目标写死为单一平台。

随包分发的平台相关资源（含 Native 页面引擎可执行文件）在打包时 MUST 按**目标平台与目标架构**解析其暂存目录，MUST NOT 取构建主机的平台。当目标与主机不同而资源解析或校验失败时，报错 MUST 同时写明目标平台/架构、主机平台/架构与实际解析到的目录，使失败原因可直接判读；MUST NOT 只给出"平台不匹配"而不指出解析取自何处。

#### Scenario: macOS 双架构产物

- **WHEN** 在 macOS 主机执行 macOS 打包
- **THEN** 产出覆盖 `x64` 与 `arm64` 的 macOS 安装产物（`dmg`+`zip`）

#### Scenario: Windows 产物

- **WHEN** 执行 Windows 打包
- **THEN** 产出 `nsis` 安装包

#### Scenario: 在 macOS 主机上打 Windows 包

- **WHEN** 在 macOS 主机执行 Windows 打包
- **THEN** 平台相关资源按目标平台 `win32` 解析暂存目录，而非按主机平台 `darwin`
- **AND** 若该目标平台的资源缺失，构建在拷贝阶段即失败，报错写明目标平台/架构、主机平台/架构与解析到的目录
