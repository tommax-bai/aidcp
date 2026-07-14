# image-postcheck-vision-model

## Why

配图管线现在按内容品类选风格档，默认走 faceless / no-text / no-watermark（已实装，见归档 change `category-adaptive-images-and-judgment`）。但这些约束是**写在 prompt 里的意图**，文生图模型并不保证遵守：它仍可能画出「像可识别真人 / 名人」的正脸，或在封面留白处渲染出**乱码中文**。当前系统**无任何产后核验**——prompt 写了 `faceless` 就当作生效，这正是「无声假成功」红线要防的：以为合规、实际没有。

这一条产后校验必须**看生成图**才能判（乱码 / 像不像真人），需要**新接一个视觉 / 多模态模型**（现有图像模型只文生图、文本客户端只纯文本）。这是一个**新能力 + 成本 / 延迟 / 选型决策**，不是纯代码活。为不让整条发布 spec 归档链卡在这个待决策项上，本 change 从 `category-adaptive-images-and-judgment` 拆出，独立承接产后校验 + 视觉模型选型。

## What Changes

- 新增一道**产后视觉校验**：对**含真人或含封面文字**的生成图，用视觉 / 多模态模型判「是否像可识别真实 / 名人」「文字是否乱码」，命中即丢弃该张、重生成（有界重试）；无真人无文字的图走既有 no-text + faceless 默认兜底、不必调视觉模型（控成本）。
- **视觉模型选型 / 成本 / 延迟为本 change 的核心待决策项**（见 Open Questions），首版可覆盖子集（先只查「含真人」或「含封面文字」的图，逐步扩）。
- MUST NOT 建假占位校验（永远返回 pass）——那等于违反本 change 要治的同一条红线。宁可先不接、显式声明未实装，也不做假校验。

## Impact

- Affected specs: `publish-multi-image`（ADDED：产后校验条文 + 高风险图重生成 scenario，即从 category-adaptive 拆出的那条）。
- Affected code（实装时）：`aidcp-cloud` 发布配图管线（`ImageGenerator` 产图后新增校验步 + 视觉模型客户端）。
- 依赖：视觉 / 多模态模型接入（选型见 design / Open Questions）；在此之前本 change 保持 proposal 态、不实装。

## Open Questions

- 视觉模型选型：走哪家多模态（成本 / 延迟 / 中文 OCR 乱码识别能力 / 名人相似度判定）？与现有文本模型选型口径（见 memory `china-llm-model-selection-by-role`）一致，由厂商账单反算成本、禁硬编码价目表。
- 触发范围：仅「prompt 声明含真人 / 含封面叠字」的图查，还是全量抽查？首版覆盖子集即可。
- 重生成上限：命中后重试几次、几次仍不过则如何诚实降级（丢该张 / 换风格档 / 缺图诚实发）？
