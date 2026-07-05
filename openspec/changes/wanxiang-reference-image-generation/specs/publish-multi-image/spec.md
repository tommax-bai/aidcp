# publish-multi-image Specification Delta

## MODIFIED Requirements

### Requirement: 参考图使用状态必须如实持久化

当参照洗稿触发输入携带原文参考图时，配图生成链路 SHALL 将图片 provider 对参考图的真实使用状态汇总为发布审计字段并持久化。审计字段 MUST 至少包含请求参考图数量、可用参考图数量、生成图数量、状态枚举（`used` / `unsupported` / `unavailable` / `skipped` / `none`）以及 provider 是否声称实际使用参考图。provider 不支持参考图时 MUST 记录 `unsupported`，MUST NOT 把“传了 URL 给文生图 prompt”标记为已使用参考图。普通发布或未携带参考图时 SHALL 记录 `none` 或不展示，MUST NOT 编造参考图审计。

DashScope/Wanxiang provider 在使用支持图像输入的 Wan 2.7 image 模型且收到可用参考图 URL 时，SHALL 将参考图作为图片输入提交给 Wan 2.7，而不是只把 URL 写进文本 prompt。只有 provider 请求确实包含图片输入且返回真实新图 URL 时，系统 MAY 标记参考图状态为 `used`。若参考图请求因密钥缺失、provider 拒绝、任务失败、超时或缺少结果 URL 而未产出真实新图，系统 SHALL 标记为 `unavailable` 或保留失败状态，MUST NOT 标记为 `used`。

#### Scenario: provider 不支持参考图时记录 unsupported
- **WHEN** 参照洗稿携带 2 张可用参考图，图片 provider 返回 `referenceStatus='unsupported'`
- **THEN** 发布记录的参考图审计显示 requestedCount=2、usableCount=2、status=`unsupported`、providerClaimedUsed=false，MUST NOT 显示为 `used`

#### Scenario: provider 实际使用参考图时记录 used
- **WHEN** 参照洗稿携带参考图，图片 provider 返回 `referenceStatus='used'`
- **THEN** 发布记录的参考图审计显示 status=`used` 且 providerClaimedUsed=true

#### Scenario: 无参考图不伪造审计
- **WHEN** 普通发布或参照洗稿选择仅文本参照
- **THEN** 发布记录不显示“已使用参考图”，审计状态为 `none` 或空值

#### Scenario: Wanxiang 使用图片输入生成参考图
- **WHEN** 当前图片厂商为 `dashscope`、图片模型为 Wan 2.7 image 模型、且 `ImageGenerator` 向 provider 传入可用 `referenceImages`
- **THEN** Wanxiang provider 的提交请求包含这些参考图 URL 作为 `image` content，并包含生成指令作为 `text` content
- **AND** 成功返回真实新图 URL 时 provider 返回 `referenceStatus='used'`、`referenceUsed=true`

#### Scenario: Wanxiang 参考图请求失败不伪装 used
- **WHEN** Wanxiang 参考图请求因缺密钥、HTTP 错误、任务失败、轮询超时或响应缺少图片 URL 而未生成真实新图
- **THEN** provider 返回 `referenceStatus='unavailable'`、`referenceUsed=false`，该张图按既有失败语义不进入 `imageUrls`
