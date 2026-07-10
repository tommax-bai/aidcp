# Design: publish-image-postgen-safety-validation

## Scope

本 change 只做“生成后看图”的安全闸，不重新设计品类风格档。触发范围应保持窄：

- 画图 prompt / 风格档明示可能出现人物、人脸、手部、身体局部、背影、POV、封面文字或任何文字。
- 图源返回的 metadata 或后续实现能标出疑似文字 / 人脸时。
- 运营显式配置某账号 / 品类为高风险图校验。

低风险内页（明确 no people / no text 且非高风险品类）首版可不跑，以控制延迟和费用。

## Decision

新增一个视觉校验步骤，位于 `ImageGenerator` 得到真实新图 URL 之后、`imageDirective.imageUrls` 写出之前。校验只消费本次生成的新图 URL，不能读取或复用原参考图充数。输出至少包含：

- `status`: `pass | reject | unavailable`
- `reasons`: `recognizable_person | celebrity_like | garbled_text | provider_error | timeout | invalid_response`
- `checkedAt`
- `provider`

`reject` 的图不进入 `imageUrls`，可按受控重试策略重生成同一张；重试仍失败则按既有部分成功语义继续。`unavailable` 不得写成 `pass`，审计必须暴露“未完成视觉校验”的事实。

## Risks

- 视觉模型误判：先以窄触发 + 保守 reject reason 审计降低误杀。
- 延迟 / 成本：只跑高风险图，设置短超时和最大重试次数。
- 安全语义漂移：禁止把 prompt 约束当作视觉校验通过；只有实际模型读取生成图后才能记录 `pass`。
