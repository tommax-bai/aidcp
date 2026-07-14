## ADDED Requirements

### Requirement: 高风险配图产后视觉校验

对**含真人或含封面文字**的生成图，系统 SHALL 做一道**产后视觉校验**（用视觉 / 多模态模型判：是否像可识别的真实 / 名人、文字是否乱码），命中即丢弃该张、重生成（有界重试），MUST NOT 因 prompt 写了 `faceless`/`no text` 就**假定生效**（守「无声假成功」红线）。无真人无文字的图 SHALL 走既有 no-text + faceless 默认兜底、不必调视觉模型（控成本）。视觉模型不可用时，系统 MUST 显式声明未校验并诚实降级，MUST NOT 让校验永远返回 pass（假占位校验＝违反本红线）。合规 AI 标识仍走既有发布声明 / 元数据链路，MUST NOT 由模型在画面内绘制水印。

#### Scenario: 高风险图未过产后校验即重生成
- **WHEN** 一张含真人或封面文字的图产后校验判为「像可识别真人 / 名人」或「文字乱码」
- **THEN** 该张 MUST 丢弃并重生成，MUST NOT 因 prompt 含 faceless/no-text 约束就当作已合规照用

#### Scenario: 无真人无文字图不调视觉模型
- **WHEN** 一张无真人、无封面叠字的图产出
- **THEN** 系统靠既有 no-text + faceless 默认兜底、不调视觉模型（成本护栏），不因此判其未校验

#### Scenario: 视觉模型不可用时诚实降级
- **WHEN** 产后校验所需的视觉模型不可用（未接入 / 超时 / 报错）
- **THEN** 系统 MUST 显式声明该张未经产后校验并走诚实降级，MUST NOT 让校验静默返回 pass 当作已合规
