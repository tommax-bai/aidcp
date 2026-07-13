## Why

Facebook 发帖图片使用管理后台素材池上传时，运营可能直接上传手机或微信原图。大图会拉长后续 Facebook 上传、转码和提交等待时间，表现为「发布中」长时间不消失。

## What Changes

- 在管理后台发帖图片上传入口增加客户端图片压缩预处理。
- 上传图片统一在浏览器端转换为 JPEG 并压缩后入队；不裁剪、不拉伸、不改变宽高比。
- 不能解码、不能转成 JPEG、或无法生成更小 JPEG 的文件不加入上传队列，运营需换图或另存后重传。
- 仍沿用既有 10MB 单图上限；该上限只约束源文件，实际上传为压缩后的 JPEG。
- 上传队列展示压缩前后大小，方便运营判断图片是否已被处理。

## Capabilities

### New Capabilities

- `console-image-upload-compression`: 管理后台发帖图片上传前的客户端压缩行为与运营可见反馈。

### Modified Capabilities

## Impact

- Affected repo: `aidcp-console`
- Affected UI: Facebook 账号「FB配置」→「发帖图片」素材上传
- No cloud API contract change; uploaded payload remains `{ filename, contentType, dataBase64 }`
- No publish protocol or edge behavior change
