## Why

Facebook 点赞成功后，客户端活动流目前只显示“点了个赞”，用户无法判断刚才点赞的是哪篇内容。点赞执行器已经从实际被作用的帖子读取了作者与正文开头，因此可以在不改协议、不猜测目标的前提下，像“读”记录一样展示可辨识的稿件摘要。

## What Changes

- Facebook 真正点赞成功后，客户端活动流展示该稿件的正文/标题开头与作者。
- 摘要只使用点赞执行器从实际被作用帖子读取的见证数据，避免复用上一条阅读记录造成串稿。
- 作者或正文缺失时按现有“读”记录原则诚实降级；不展示 permalink、原始 note ID，也不为失败、shadow、已点赞或未找到目标的路径生成成功记录。
- 保持现有点赞计数、云端归账、风险控制与协议字段不变。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-companion-ui`: 扩展 Facebook 已确认点赞的结构化活动流要求，增加基于实际被作用帖子见证数据的作者与正文/标题摘要，以及缺失字段时的诚实降级。

## Impact

- 代码：`aidcp-edge/src/facebook/facebook-session.ts`
- 测试：`aidcp-edge/test/facebook/facebook-session.test.ts`
- 契约：`edge-companion-ui`
- 不影响 cloud、协议、风险控制、点赞定位/执行逻辑或桌面打包流程。
