## Why

客户端左侧环境栏目前把暂停与离线环境合并为“暂停 · 离线”，用户无法快速区分主动暂停和已经离线的环境。将两种状态分开展示，可以让环境运行状态一眼可读，同时保持现有需处理浮顶逻辑不变。

## What Changes

- 将左侧环境栏的普通状态区拆分为“运行中”“暂停”“离线”三个独立分组。
- 暂停环境只进入“暂停”分组；停止、关闭或失联环境进入“离线”分组。
- 保留登录、验证码、风控和错误等“需处理”环境浮顶展示，不把它们混入普通状态分组。
- 增加渲染层回归测试，覆盖三个普通分组的标题、归属和顺序。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-fleet-console`: 修改左侧环境栏的状态分组要求，将暂停与离线拆为独立分组。

## Impact

- 代码：`aidcp-edge/src/electron/renderer/renderer.js` 的环境栏分组映射。
- 测试：`aidcp-edge/test/electron/fleet-console.test.ts` 的环境栏渲染回归。
- 不修改状态协议、生命周期控制、排序优先级或云端行为。
