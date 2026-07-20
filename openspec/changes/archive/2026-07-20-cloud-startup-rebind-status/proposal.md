## Why

自动化引擎首次启动时尚未报告实际 Cloud，客户端会把空的实际值误判为“目标不一致”，短暂显示红色“待重绑”。这会把正常的首次连接过程说成需要人工处理的 Cloud 切换。

## What Changes

- 只有自动化引擎已经报告了一个实际 Cloud，且该值与已保存目标不一致时，才显示“待重绑”。
- 首次启动、实际 Cloud 尚未报告时，不显示红色“待重绑”，也不提供无必要的重绑操作提示。
- 保留真实目标不一致、显式重绑进行中和重绑失败的现有处理。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-cloud-env-selection`: 明确首次连接未知态不得被呈现为 Cloud 目标不一致或待重绑。

## Impact

- 代码：`aidcp-edge/src/electron/renderer/renderer.js` 的顶部 Cloud 状态派生。
- 测试：`aidcp-edge/test/electron/cloud-env-selector.test.ts`。
- 不改变 Cloud 地址、控制传输重绑流程、浏览器生命周期、任务调度或协议。
