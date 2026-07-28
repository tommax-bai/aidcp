## ADDED Requirements

### Requirement: 本地 arm64 OL 打包入口可复用且失败关闭

Edge 仓库 SHALL 提供两个受版本控制的 macOS arm64 OL 本地打包入口：一个生成 Developer ID 签名但未公证的 DMG，另一个生成 Developer ID 签名、Apple 公证并 staple 的 DMG。两个入口 MUST 共用同一套构建和最终产物验证逻辑，MUST 基于无已跟踪改动且无构建相关未跟踪源码的 checkout、锁定的 npm 依赖和 Native Page Engine 声明的 Rust 版本重新构建 TypeScript dist、AdsPower CLI 运行时、GOST 与 Native Page Engine。任一构建、架构、环境注入或签名门禁失败 MUST 使脚本非零退出，MUST NOT 报告安装包成功。

#### Scenario: 仅签名入口生成 arm64 OL 包

- **WHEN** 操作者在 macOS 上以有效 Developer ID 凭据运行仅签名入口
- **THEN** 脚本生成只包含本次 arm64 构建的 OL DMG，验证 DMG 内应用、GOST、Native Page Engine 与 AdsPower sqlite 的 arm64 架构及有效代码签名，并明确标记产物未公证

#### Scenario: 仅签名入口不要求公证凭据

- **WHEN** 操作者运行仅签名入口且未提供 App Store Connect API 凭据
- **THEN** 脚本跳过公证凭据检查并继续构建，MUST NOT 在 Developer ID 身份检查后静默退出

#### Scenario: 公证入口串行完成 App 与 DMG 公证

- **WHEN** 操作者以有效 Developer ID 与 App Store Connect API 凭据运行公证入口
- **THEN** 脚本先签名并公证/staple App，再由该 App 生成 DMG，随后公证/staple DMG，并仅在 Gatekeeper、staple 与包内运行时验证全部通过后报告成功

#### Scenario: 自动使用项目要求的 Rust 工具链

- **WHEN** 当前默认 Rust 版本低于 Native Page Engine `Cargo.toml` 声明的 `rust-version`
- **THEN** 脚本解析并使用声明版本的 Cargo/Rustc，必要时安装该工具链，而不是继续使用不兼容的默认版本

#### Scenario: 最终 DMG 环境注入不匹配

- **WHEN** 挂载后的 DMG 内 `app.asar` 未包含预期 `ol` 环境或指定的客户登录 URL
- **THEN** 脚本非零退出并且不报告成功

#### Scenario: 凭据不进入仓库和日志

- **WHEN** 脚本需要 p12 密码或 Apple API 私钥
- **THEN** 密码仅从环境变量或 `/dev/tty` 隐式读取，私钥仅以文件路径引用，脚本 MUST NOT 把秘密值写入源码或日志

#### Scenario: 旧产物不进入本次验证或公证

- **WHEN** 构建前输出目录已有其他架构或版本的安装包
- **THEN** 脚本先隔离旧输出，并仅按本次版本和 arm64 文件名选择待验证或公证的 DMG

#### Scenario: 无关未跟踪文件不阻塞构建

- **WHEN** checkout 没有已跟踪改动，且未跟踪文件仅为根目录临时探针或历史 `dist-electron.backup-*` 等不属于源码构建图的文件
- **THEN** 脚本保留这些文件并继续构建，MUST NOT 因无关未跟踪文件拒绝出包

#### Scenario: 构建相关未跟踪源码仍被拒绝

- **WHEN** checkout 在 `src/`、`native/` 或 `scripts/` 下存在未跟踪源码，或存在任何已跟踪文件改动
- **THEN** 脚本列出相关路径并非零退出，避免不可审计内容进入最终安装包
