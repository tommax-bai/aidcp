## ADDED Requirements

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
