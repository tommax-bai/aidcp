# wechat-creator-reply-composition Specification

## Purpose
TBD - created by archiving change wechat-creator-reply-contact-guidance. Update Purpose after archive.
## Requirements
### Requirement: AI 润色必须保持通用博主式短回复

`reply_polisher` SHALL 以通用内容博主/创作者而非商家客服身份轻量润色确定性模板文本；默认输出 SHALL 简短、自然、亲切，MUST NOT 自行增加商品、订单、价格、优惠、售后承诺、私聊引导或联系方式。运行时提示词与管理端静态预览 MUST 使用同一 prompt builder，且示例不得把商品客服语境作为默认输入。

#### Scenario: 普通互动不产生商家客服口吻
- **WHEN** 一条普通视频号评论进入 AI 润色，确定性模板未包含商品服务或导流内容
- **THEN** polisher 被要求仅给出通用博主式的一到两句亲切回复，不主动补充商家身份、客服承诺、私聊 CTA 或联系方式

#### Scenario: 管理端预览与运行时同源
- **WHEN** 管理端读取 `reply_polisher` 的静态提示词预览
- **THEN** 预览使用与运行时相同的博主式 prompt builder 和非商家默认示例

### Requirement: 联系方式只能由显式模板变量注入

当且仅当生效的 published template 正文显式包含 `{{support_channel}}` 时，Cloud SHALL 读取该账号现有 `accounts.contact_info` 并将非空值作为该变量的首选渲染值；账号未配置时 SHALL 沿用 published profile 的非空安全 fallback。模板不包含该占位符时，系统 MUST NOT 读取、生成或自动追加联系方式与私聊引导。联系方式读取异常 MUST 使本次生成诚实失败，MUST NOT 静默伪装为未配置。

#### Scenario: 模板显式注入账号联系方式
- **WHEN** 生效模板包含 `{{support_channel}}` 且账号已配置非空 `contact_info`
- **THEN** 确定性渲染结果使用该账号联系方式，并且该值优先于 profile fallback

#### Scenario: 未配置联系方式时使用已发布 fallback
- **WHEN** 生效模板包含 `{{support_channel}}` 但账号没有 `contact_info`
- **THEN** renderer 使用 published profile 对 `support_channel` 的非空安全 fallback，不伪造账号联系方式

#### Scenario: 无占位符不追加联系方式
- **WHEN** 生效模板不包含 `{{support_channel}}`
- **THEN** 工作流不读取账号联系方式，也不在最终回复中自动追加联系方式或私聊引导

### Requirement: AI 不得改写模板导流行

模板正文中包含 `{{support_channel}}` 的每一行 SHALL 在确定性渲染后成为受保护行。AI 润色候选 MUST 逐字保留全部受保护行；若候选删除或改写任一受保护行，Cloud SHALL 丢弃该候选并回退为完整的确定性模板结果。该回退 MUST NOT 放宽既有 claim gate、人审、写入开关或私信 AI 默认关闭边界。

#### Scenario: AI 保留模板导流行
- **WHEN** AI 候选逐字包含所有已渲染的受保护导流行
- **THEN** 候选可继续经过既有安全校验与人工审核流程

#### Scenario: AI 删除或改写联系方式行
- **WHEN** AI 候选删除、改写或替换任一已渲染的受保护导流行
- **THEN** 工作流使用完整的原 rendered template，且该次 AI 调用仍不得获得自动发送资格

