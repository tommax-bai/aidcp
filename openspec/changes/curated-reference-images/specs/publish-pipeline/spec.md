# publish-pipeline Specification (delta)

## ADDED Requirements

### Requirement: 参照洗稿可携带视觉参考但不得搬运原图

人工指定精选笔记进行参照洗稿时，发布输入 SHALL 支持在既有文本 `referenceNote` 基础上携带可选 `images` 视觉参考。视觉参考仅用于辅助发布配图链路理解原笔记的构图、色彩、图集节奏和信息层级；最终发布图片 MUST 仍由图片生成链路生成新图，MUST NOT 直接上传或复用原笔记图片。

参照笔记正文为空的拒绝规则保持不变。图片缺失、不可访问、运营选择仅文本、或图片 provider 不支持参考图时，系统 SHALL 诚实降级为文本参照或提示未使用图片参考，MUST NOT 静默宣称已参考图片。视觉参考的使用状态 SHOULD 进入发布审计或审批卡上下文，使运营能区分 `used`、`skipped`、`unsupported`、`unavailable`。

#### Scenario: 带图精选笔记触发参照洗稿

- **WHEN** 运营对一条正文非空且有可用参考图的精选笔记触发洗稿并选择带图参考
- **THEN** `TriggerInput.generateInput.referenceNote` 包含该笔记的文本信息与有界图片参考数组

#### Scenario: 仅文本参照仍可触发

- **WHEN** 运营选择仅文本参照，或该精选笔记没有可用图片
- **THEN** 洗稿按既有文本参照规则触发，不携带 `referenceNote.images`

#### Scenario: 图片参考不可用诚实可见

- **WHEN** 图片 URL 下载失败、OSS 未稳定化、或 provider 不支持参考图
- **THEN** 本次发布不得声称已使用图片参考；审计/回执 SHOULD 标出未使用原因

#### Scenario: 红线反例 - 直接发布原图

- **WHEN** 有实现把原笔记 `sourceUrl/ossUrl` 作为 `upload_image` 最终下发给 edge
- **THEN** MUST 视为违规，不予合入；参照图只能喂给生成链路或转成提示约束，不能成为最终发布图

#### Scenario: 红线反例 - 视觉参考导致文本照抄规则失效

- **WHEN** 参照图存在
- **THEN** 文本参照仍必须遵守借选题/结构/要点但禁止逐句照抄的既有规则，MUST NOT 因图片参考绕过非照抄护栏
