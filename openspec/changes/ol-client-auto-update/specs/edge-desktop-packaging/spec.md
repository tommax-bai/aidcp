## MODIFIED Requirements

### Requirement: 双平台打包目标

构建 MUST 能产出 macOS 与 Windows 两个平台的可分发产物。macOS MUST 同时覆盖 `x64` 与 `arm64` 架构，并产出可拖装的 `dmg` 与用于自动更新的 `zip`；Windows MUST 产出 `nsis` 安装包。打包脚本 MUST NOT 把目标写死为单一平台。

对于构建时明确标记为 OL 的 macOS 分发包，构建 MUST 把固定的 OL generic HTTPS 更新通道配置写入打包应用，并 MUST 同时交付 `latest-mac.yml`、两个架构的签名 zip 及其 blockmap。该配置 MUST NOT 从运行时云端设置推导。Windows 在完成独立的签名和运行时发行条件前，MUST NOT 因本 requirement 被声明为自动更新客户端。

#### Scenario: macOS 双架构产物

- **WHEN** 在 macOS 主机执行 macOS 打包
- **THEN** 产出覆盖 `x64` 与 `arm64` 的 macOS 安装产物（`dmg`+`zip`）

#### Scenario: Windows 产物

- **WHEN** 执行 Windows 打包
- **THEN** 产出 `nsis` 安装包

#### Scenario: OL macOS 包携带完整更新工件

- **WHEN** 构建一个标记为 OL 的 macOS 分发版本
- **THEN** 构建输出包含固定 OL 更新配置、`latest-mac.yml`、x64 与 arm64 的签名 zip 及各自 blockmap，且 metadata 中的版本与包版本一致

#### Scenario: 非 OL 包不会继承 OL 更新配置

- **WHEN** 构建 dev、custom 或未标记的 macOS 包，或构建 Windows 安装包
- **THEN** 该产物 MUST NOT 因 OL 打包配置而被配置为检查 OL 自动更新
