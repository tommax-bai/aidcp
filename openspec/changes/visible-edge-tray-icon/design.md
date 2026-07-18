## Context

监督者当前用内联 SVG data URL 构造 Electron `NativeImage`。Electron 跨平台稳定支持 PNG/JPEG，Windows 还支持从文件加载 ICO；SVG 不在受支持格式内。Windows 因而保留了一个名为 AIDCP Edge 的通知区按钮，但图像为空，用户无法发现后台实例。

桌面包由 electron-builder 生成，开发态应用根目录与打包态资源目录不同。修复既要保证资源进入安装包，也要避免路径解析依赖当前工作目录或 `app.asar` 内部路径。

## Goals / Non-Goals

**Goals:**

- 在 Windows 开发态和打包态显示清晰、稳定的 AIDCP 托盘图标。
- 使用 Electron 明确支持的随包图像格式与确定性路径。
- 图标缺失或解码失败时不创建透明托盘入口，并把主窗口保持为可恢复入口。
- 用源码级契约测试防止资源、打包声明或空图检查回归。

**Non-Goals:**

- 不改变单实例锁、环境托管、登录门或云端协议。
- 不重绘产品标识；PNG 从现有 Windows 应用图标导出。
- 不在本 change 中构建或发布安装包。

## Decisions

### 1. 运行时托盘统一使用 PNG

复用仓库已有的 `build/icon.png`，它与现有 `build/icon.ico` / `build/icon.icns` 属于同一品牌资产。PNG 是 Electron 在所有平台明确支持的透明无损格式，比运行时解析 SVG 更稳定；不复用 ICO 作为跨平台托盘输入，因为 ICO 只在 Windows 文件路径上额外受支持。

### 2. 作为 extraResource 放到 asar 外

electron-builder 将 `build/icon.png` 复制为 `process.resourcesPath/tray-icon.png`。开发态从仓库 `build/icon.png` 读取，打包态从 `process.resourcesPath` 读取。资源不依赖当前工作目录，也不要求操作系统直接读取 `app.asar` 内部虚拟路径。

### 3. 创建托盘前校验解码结果

主进程先检查文件存在，再调用 `nativeImage.createFromPath`，随后检查 `isEmpty()`。任一步失败都不调用 `new Tray(...)`，而是通过既有故障暴露通道显示主窗口并记录可操作错误。主窗口关闭逻辑只有在托盘真实存在时才允许隐藏；托盘不可用时保持窗口可见，避免形成新的不可恢复后台实例。

### 4. 契约测试覆盖资源链路

测试读取主进程源码和 `package.json`，断言不再使用 SVG data URL、存在 PNG 路径与空图检查、打包 `extraResources` 包含该 PNG，并验证仓库中的 PNG 文件签名与非零尺寸。该测试不替代安装包真机冒烟；发布时仍按桌面发版清单验证产物。

## Risks / Trade-offs

- [PNG 是单一 1024×1024 表示，托盘需要由 Electron 缩小] → 保留高分辨率 RGBA 源图让系统按当前 DPI 缩放；后续如需模板图或多倍率资源可另行增加，不阻塞可见性修复。
- [extraResources 路径配置漂移导致打包态缺图] → 契约测试同时检查文件和打包声明；创建时再做存在性与空图校验。
- [托盘创建失败后窗口无法隐藏，与既有关闭习惯不同] → 这是有意的诚实降级，优先保证用户仍能退出或排障，而不是留下不可见监督者。

## Migration Plan

1. 将 PNG 资源、主进程路径解析和打包声明一同合入 edge `master`。
2. 运行 Electron 生命周期/托盘契约测试、完整 typecheck；发布安装包时按 `docs/release-desktop.md` 做打包态资源与真机托盘冒烟。
3. 回滚时可恢复旧主进程逻辑并移除 extraResource；不涉及数据或协议迁移。

## Open Questions

无。
