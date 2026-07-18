## Why

Windows 当前为监督者创建了可点击的托盘槽位，但外壳把不受 Electron `nativeImage` 支持的 SVG data URL 当作图标，结果槽位透明、用户无法发现仍在后台运行的监督者，重复启动时只会看到单实例拒绝提示。需要让开发态与打包态都使用随包携带、平台支持的真实图像资源，并在资源失效时诚实失败。

## What Changes

- 将监督者托盘图标改为从随应用分发的 PNG/ICO 文件加载，不再运行时解析 SVG data URL。
- 为开发态与打包态分别解析稳定的资源路径，并保证 Windows 安装包确实携带托盘资源。
- 在托盘图像缺失或解码为空时记录并显式暴露错误，避免继续创建不可见托盘入口。
- 增加源码级契约测试，覆盖受支持格式、打包资源声明、路径解析与空图防护。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `edge-desktop-packaging`: 桌面监督者的托盘入口必须使用随包携带、平台支持且可见的图标资源，开发态与打包态行为一致。

## Impact

- `aidcp-edge/src/electron/main.cjs`：托盘资源解析与创建失败处理。
- `aidcp-edge/package.json` 与图像资源目录：打包文件清单和随包资源。
- `aidcp-edge/test/electron/`：托盘资源与打包契约回归测试。
- 不改变协议、云端行为、环境生命周期或单实例锁语义；不要求立即构建/发布安装包。
