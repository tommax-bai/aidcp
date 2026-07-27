## Context

Edge 已有 CI 导向的 `scripts/build-desktop-macos.sh`，但本机 arm64 OL 出包仍依赖临时命令。签名版与公证版重复了依赖安装、Rust 工具链选择、AdsPower/GOST/Native staging 和最终 DMG 验证，已经出现默认 Rust 工具链版本错误、交互式 zsh 注释解析失败以及旧产物可能混入验证范围的问题。

## Goals / Non-Goals

**Goals:**

- 提供两个稳定的可执行入口：本地 arm64 OL 仅签名，以及本地 arm64 OL 签名并公证。
- 让两个入口复用同一套构建、凭据解析和最终 DMG 验证逻辑。
- 自动读取 Native Page Engine 的 `rust-version`，避免使用错误的默认工具链。
- 仅验证本次明确生成的 arm64 产物，失败时不报告成功。
- 不在仓库、参数回显或构建日志中记录密码与私钥内容。

**Non-Goals:**

- 不自动上传、部署或发布安装包。
- 不改变客户端运行逻辑、默认产品配置或现有 CI 工作流。
- 不增加 x64/Windows 本地发布入口。
- 不把 Developer ID 签名等同于 Apple 公证。

## Decisions

1. 两个公开脚本调用一个私有公共实现。公共实现以 `signed-only` 或 `notarized` 模式运行，使依赖构建、环境注入和验证门禁只有一个维护点。
2. 脚本使用 Bash 文件执行，而不是要求用户粘贴交互式 shell 片段。这样注释、heredoc 和密码读取不受 zsh `interactivecomments` 设置影响。
3. 默认目标固定为 arm64 OL，并允许通过 `AIDCP_CLIENT_AUTH_URL` 覆盖登录地址。默认地址保持当前明确要求的 OL IP URL。
4. Rust 版本从 `native/page-engine/Cargo.toml` 读取；缺少工具链时用 `rustup` 安装，并显式设置 Cargo/Rustc 路径。
5. 签名凭据支持两种方式：Keychain 中的 `CSC_NAME`，或 `CSC_LINK` 加 `CSC_KEY_PASSWORD`。若使用 p12 且密码未注入，脚本从 `/dev/tty` 隐式读取。
6. 公证模式要求 `APPLE_API_KEY`、`APPLE_API_KEY_ID`、`APPLE_API_ISSUER`，并严格按“签名 App → 公证/staple App → 从该 App 生成 DMG → 公证/staple DMG”串行执行。
7. 最终门禁挂载本次 DMG，验证包内 OL/IP 元数据、GOST、Native Page Engine、AdsPower arm64 sqlite、嵌套签名、整包签名；公证模式额外执行 staple 与 Gatekeeper 验证。
8. 已有 `dist-electron` 目录先移动到时间戳备份，不用通配符选择待公证 DMG，避免旧产物被误处理。

## Risks / Trade-offs

- [本机构建依赖网络下载 npm 包、GOST、Rust 工具链及 Apple 公证服务] → 任一依赖失败即退出，并保留已完成产物和公证日志供重试。
- [默认 OL IP 以后可能变化] → 支持 `AIDCP_CLIENT_AUTH_URL` 显式覆盖，并在最终 ASAR 中验证实际注入值。
- [签名证书轮换但 Team ID 不变] → 支持 `CSC_NAME` 或 `CSC_LINK` 切换证书，不把证书密码写入仓库；若 Team ID 改变，必须显式更新发布信任契约和嵌套产物验证，不能只用环境变量绕过。
- [仅签名包在其他 Mac 上仍可能被 Gatekeeper 拦截] → 输出明确标记为 signed-only，且不运行或宣称公证门禁。
