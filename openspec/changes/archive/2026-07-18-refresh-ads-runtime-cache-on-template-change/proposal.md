## Why

Edge 当前只用应用版本与 Ads CLI 包版本判断用户目录中的运行时副本是否需要刷新；当兼容补丁改变但版本号未变时，旧副本会继续遮蔽新模板，客户端重启后仍运行旧逻辑。与此同时，真正退出 Edge 只停止环境核心进程、不会停止其 Ads CLI daemon，导致旧 daemon 跨客户端重启被继续接管并阻碍运行时更新。

## What Changes

- 为随包/开发态 Ads CLI 运行时模板建立内容身份，并把它纳入用户目录暂存判定。
- 开发态从当前 `build/ads-runtime` 模板暂存，不再让历史用户目录副本永久遮蔽当前代码。
- 模板内容变化时，先有界停止旧 Ads CLI daemon，再原子替换运行时副本；失败须诚实阻断，不能继续接管旧逻辑。
- Edge 真正退出时，在环境核心完成有界停机后停止由本应用管理的 Ads CLI daemon；关闭窗口到托盘不视为真正退出。
- 增加缓存失效、旧 daemon 清理与退出生命周期回归测试。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `adspower-cli-embedded-runtime`: 明确运行时模板刷新、开发态模板优先级以及 Edge 真正退出时的 Ads CLI daemon 生命周期。

## Impact

- `aidcp-edge/src/electron/main.cjs`：运行时暂存与退出清理。
- `aidcp-edge/src/electron/ads-runtime.cjs`：Ads CLI 有界停止编排。
- `aidcp-edge/scripts/stage-ads-runtime.mjs`：生成稳定的模板内容身份。
- Electron 单元/契约测试与运行时暂存测试。
