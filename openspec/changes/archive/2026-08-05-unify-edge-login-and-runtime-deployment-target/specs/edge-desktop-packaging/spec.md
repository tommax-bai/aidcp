## MODIFIED Requirements

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
