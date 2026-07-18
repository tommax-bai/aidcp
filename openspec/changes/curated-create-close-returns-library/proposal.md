## Why

客户从精选详情进入“选择参考方式”页面后，右上角 `×` 当前会关闭整个内容工作区。此时用户预期结束本次参考创作并回到灵感池列表，而不是退出灵感工作区；同时左侧返回仍需要用于回到刚才的详情。

## What Changes

- “选择参考方式”页面右上角 `×` 改为直接返回灵感池列表，并跳过中间的正文详情页。
- 返回列表时保留进入详情前的分页、筛选与滚动位置。
- 该页面右上角 `×` 的可访问名称改为“返回灵感库”。
- 左侧返回按钮继续回到正文详情；精选详情的 `×` 以及其它页面的既有行为保持不变。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-companion-ui`: 扩展精选内容工作区的退出按钮导航契约，使参考创作页可直接返回灵感库。

## Impact

- `aidcp-edge/src/electron/renderer/content-workspace.js`: 增加从参考创作页跳过详情返回灵感库的栈处理，并按页面设置关闭按钮语义。
- `aidcp-edge/test/electron/content-workspace.test.ts`: 增加参考创作页 `×`、左侧返回及列表状态恢复回归。
- 不涉及 CSS、协议、云端、数据库或 API 变更。
