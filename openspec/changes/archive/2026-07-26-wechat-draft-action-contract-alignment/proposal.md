## Why

视频号客户工作区已经能读取互动详情，但保存草稿调用文档约定的 `PUT /environments/:envKey/replies/:jobId/draft` 时，Cloud 路由只接受未公开的 `/replies/:jobId` 形态，因此返回 `404`。同时，Cloud 把评论回复/私信发送能力门禁提前应用到生成、编辑和批准草稿，导致平台尚未确认真实发送能力时，这些纯 Cloud 操作返回 `403`，并被客户端误写成“当前登录没有权限”。

发送能力保守关闭本身是正确的；问题在于路由实现和门禁边界偏离了既有客户 API 与交互工作区契约。

## What Changes

- Cloud 接受并只使用已约定的 `PUT /environments/:envKey/replies/:jobId/draft` 草稿保存路由。
- 对属于当前客户环境的互动，生成、编辑和批准草稿只要求有效的客户环境作用域、活动中的渠道授权与身份、有效配置及版本条件，不再要求平台回复/发送能力已生效。
- 真实发送、自动入队和派发继续要求平台写能力及所有既有熔断、暂停、风险与幂等门禁；不放宽视频号写探针。
- Edge 将平台能力拒绝描述为渠道能力问题，不再误导为客户登录没有查看或操作权限。
- 增加 Cloud 和 Edge 回归测试，固定公开路由、草稿操作边界和实际发送门禁。

## Capabilities

### New Capabilities

- `wechat-draft-action-contract`: 统一视频号客户草稿 API 路由和 Cloud-only 草稿操作的鉴权边界，同时保持真实发送 fail-closed。

### Modified Capabilities

<!-- None. -->

## Impact

- Cloud 客户互动 API 路由与回复工作流鉴权。
- Edge 客户互动工作区错误文案与契约测试。
- 不修改 Edge/Cloud 协议枚举、数据库结构、风险控制、运行时写能力探针或真实发送门禁。
- 不构建或发布 Edge 安装包；Cloud 修复部署到 dev。
