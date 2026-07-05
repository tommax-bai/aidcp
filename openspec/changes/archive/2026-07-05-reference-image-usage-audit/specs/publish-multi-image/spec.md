## ADDED Requirements

### Requirement: 参考图使用状态必须如实持久化

当参照洗稿触发输入携带原文参考图时，配图生成链路 SHALL 将图片 provider 对参考图的真实使用状态汇总为发布审计字段并持久化。审计字段 MUST 至少包含请求参考图数量、可用参考图数量、生成图数量、状态枚举（`used` / `unsupported` / `unavailable` / `skipped` / `none`）以及 provider 是否声称实际使用参考图。provider 不支持参考图时 MUST 记录 `unsupported`，MUST NOT 把“传了 URL 给文生图 prompt”标记为已使用参考图。普通发布或未携带参考图时 SHALL 记录 `none` 或不展示，MUST NOT 编造参考图审计。

#### Scenario: provider 不支持参考图时记录 unsupported
- **WHEN** 参照洗稿携带 2 张可用参考图，图片 provider 返回 `referenceStatus='unsupported'`
- **THEN** 发布记录的参考图审计显示 requestedCount=2、usableCount=2、status=`unsupported`、providerClaimedUsed=false，MUST NOT 显示为 `used`

#### Scenario: provider 实际使用参考图时记录 used
- **WHEN** 参照洗稿携带参考图，图片 provider 返回 `referenceStatus='used'`
- **THEN** 发布记录的参考图审计显示 status=`used` 且 providerClaimedUsed=true

#### Scenario: 无参考图不伪造审计
- **WHEN** 普通发布或参照洗稿选择仅文本参照
- **THEN** 发布记录不显示“已使用参考图”，审计状态为 `none` 或空值

