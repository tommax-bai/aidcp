## Why

客户端“添加环境”浮层中的视频号平台标签缺少专用配色规则，当前回落成小红书的红字与粉色背景，与左侧环境状态栏已经使用的绿色平台身份色冲突，容易让用户误判环境平台。

## What Changes

- 为“添加环境”列表里的 `wechat_channels` 平台标签补充视频号绿色文字和浅绿色背景。
- 复用客户端现有视频号平台身份色变量，使环境选择列表与左侧环境状态栏保持一致。
- 增加渲染层契约测试，锁定视频号标签不会再次回落到小红书默认配色。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `edge-fleet-console`: 明确视频号环境在环境状态栏和“添加环境”列表中的平台标识均使用一致的绿色系，同时保持平台色与运行状态、交互选择色正交。

## Impact

- `aidcp-edge/src/electron/renderer/styles.css`: 增加视频号环境平台标签的专用配色规则。
- `aidcp-edge/test/electron/`: 增加 CSS 契约回归覆盖。
- 不改 renderer 逻辑、协议、数据、Cloud、Console 或桌面安装包。
