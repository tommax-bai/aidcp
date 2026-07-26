## Why

视频号回复的 `reply_polisher` 目前以“入站客服”自居，示例也集中在商品、订单和物流，模型因此容易输出商家客服口吻；同时 `{{support_channel}}` 运行时没有读取账号已经配置的联系方式。需要把 AI 收敛为通用博主的简短亲切回复，并让私聊引导与联系方式继续由模板确定性控制。

## What Changes

- 将 `reply_polisher` 改为独立的通用内容博主角色：回复简短、自然、亲切，不默认扮演商家或客服，不自行增加营销承诺、私聊引导或联系方式。
- 当且仅当已发布模板显式使用 `{{support_channel}}` 时，读取并优先注入账号现有 `contact_info`；账号未配置时沿用 profile 的已发布安全 fallback，不自动追加任何联系方式。
- 把模板中包含联系方式的导流行视为受保护文本；AI 若删除或改写该行，候选结果回退为确定性模板渲染结果。
- 同步管理端角色提示词预览示例与 Cloud 自动化测试；保留“任何 AI 润色均需人工审核”、私信 AI 默认关闭及既有安全闸。

## Capabilities

### New Capabilities

- `wechat-creator-reply-composition`: 规定视频号 AI 短回复的通用博主口吻，以及模板、账号联系方式和 AI 润色之间的确定性组合边界。

### Modified Capabilities

无。

## Impact

- 影响 `aidcp-cloud` 的互动回复 AI 提示词、回复工作流依赖注入、静态角色预览与相关测试。
- 复用现有 `accounts.contact_info` 与 `{{support_channel}}`，不新增数据库字段、协议命令、Edge/Console 接口或第三方依赖。
- Cloud 运行时行为变化需部署到 `dev`；不触发 Edge 安装包发布，也不涉及 `ol`。
