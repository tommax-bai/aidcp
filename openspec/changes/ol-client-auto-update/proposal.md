## Why

OL 桌面客户端目前没有更新能力；用户必须重新打开下载页、下载并安装新包，既容易错过修复，也无法确认正在使用的版本是否已过期。现有 macOS 发版已产出签名的双架构 zip、blockmap 与更新元数据，具备接入安全自动更新的基础，但还没有稳定的 OL 更新通道和受控的安装时机。

## What Changes

- 为**构建时标记为 OL**的 macOS 桌面客户端接入 `electron-updater` 的 generic HTTPS 更新通道；dev、custom 及未标记的开发包不检查、不下载 OL 更新。
- 在主窗口可用后检查更新，并以中文提示让用户选择下载、稍后提醒、或在下载完成后选择重启安装；不强制下载、不强制重启。
- 更新重启前复用 edge 的优雅停机能力：先停止全部受监管的 edge 子进程并等待有界收尾，再安装并重启；不得把正在运行的浏览器任务静默中断。
- 建立 OSS 上仅供 OL 使用的静态更新通道，发布签名 zip、blockmap、`latest-mac.yml` 与手动安装 dmg；全部版本文件先校验，最后才原子发布可变 manifest。
- 将 OL macOS 打包、CI 交付和发版脚本扩展为能交付并校验更新元数据；校验失败时不得提升 manifest。
- **不包含** Windows 自动更新、云端/边云协议变更、远程强制更新、自动重启或存量客户端的静默迁移。Windows 须待 Authenticode 签名、自包含运行时和真机升级验证完备后另立变更。

## Capabilities

### New Capabilities

- `ol-client-auto-update`: OL macOS 客户端的更新检查、用户提示、下载状态、受任务保护的安装重启与失败可见性。
- `ol-update-release-channel`: OL macOS 更新文件在 OSS 的寻址、完整性校验、缓存策略、原子 promotion 与发布失败闸。

### Modified Capabilities

- `edge-desktop-packaging`: OL macOS 分发包须携带固定更新通道配置，并交付自动更新所需的签名产物与元数据。

## Impact

- **aidcp-edge**：新增 `electron-updater` 运行时依赖和主进程更新服务；调整 macOS 打包配置、GitHub Actions、签名后交付脚本及 Electron 测试。
- **控制仓**：扩展桌面发版编排与文档，新增本变更的发布/验收契约；复用但不改写仍在进行的 `edge-installer-oss-distribution` 变更。
- **OSS / OL 分发**：新增 HTTPS 静态更新前缀及受控发布步骤。写入凭据仍仅在受控发版机使用，主账号 AK 不进入仓库、日志或 GitHub Actions。
- **不影响** aidcp-cloud、边云协议、账号风控和同机 isales 服务。
