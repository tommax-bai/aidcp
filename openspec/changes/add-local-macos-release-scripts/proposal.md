## Why

本地 arm64 OL 出包目前依赖临时粘贴的长命令，签名版与公证版容易在 Rust 工具链、内置运行时 staging、环境注入和最终产物验证上发生漂移。需要把两条可复用、失败即停的入口固化到 Edge 仓库，让后续本机出包使用同一套受版本控制的发布门禁。

## What Changes

- 在 Edge 仓库提供“Developer ID 签名但不公证”的本地 arm64 OL 打包入口。
- 在 Edge 仓库提供“Developer ID 签名、Apple 公证并 staple”的本地 arm64 OL 打包入口。
- 两个入口共用构建和验证实现，自动使用项目声明的 Rust 版本，并构建/校验 TypeScript dist、AdsPower CLI、GOST 与 Native Page Engine。
- 凭据只通过环境变量、macOS Keychain 或交互式密码读取，不把证书密码、API 私钥内容写入仓库或日志。
- 最终验证 DMG 内应用的 OL/IP 配置、arm64 架构、嵌套运行时签名和整包签名；公证入口额外验证 App 与 DMG 的 staple 票据及 Gatekeeper 结果。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-desktop-packaging`: 增加可复用的本地 arm64 OL 签名/公证入口及其失败关闭的产物验证要求。

## Impact

- Affected repository: `aidcp-edge`
- Affected areas: `scripts/`, desktop release documentation, packaging contract tests
- No runtime protocol, product behavior, database, Cloud, Console, or deployed OL service changes
- No installer is built or published as part of implementing this change
