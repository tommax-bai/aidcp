# publish-multi-image Specification (delta)

## ADDED Requirements

### Requirement: 配图生成支持可选参考图且失败诚实

发布配图链路 SHALL 支持可选参考图输入。参考图输入 MUST 从 `referenceNote.images` 派生，经过账号隔离、数量上限和可用 URL 过滤后进入图片计划/生成链路。图片选题与提示词角色 MAY 使用参考图元数据或引用来调整图集节奏和视觉约束，但 MUST NOT 调用图源；只有 `ImageGenerator` 可把参考图传给 `ImageProvider` 执行生成。

`ImageProvider.generate` SHALL 扩展可选参考图参数，并对 provider 支持情况诚实回报。支持参考图的 provider MAY 走图像参考/编辑端点生成新图；不支持参考图的 provider MUST 返回明确状态或触发显式 prompt-only 降级。无论哪种路径，最终 `imageDirective.imageUrls` 仍只包含真实生成成功的新图 URL，失败那张不进数组，不补空、不复用原图、不伪造。

#### Scenario: 参考图进入生成执行层

- **WHEN** `ImagePlan` 含可用 `referenceImages`
- **THEN** `ImageGenerator` 调用 `ImageProvider.generate(prompt, { referenceImages })` 或等价契约，由 provider 决定具体 API 形态

#### Scenario: 决策角色不调图源

- **WHEN** `ImageSetPlanner` 或 `ImagePromptComposer` 读取视觉参考信息
- **THEN** 它们只能产出主题、提示词或计划元数据，MUST NOT 下载图片、上传图片或调用图片 provider

#### Scenario: provider 不支持参考图时诚实降级

- **WHEN** 当前选中图片 provider 不支持参考图输入
- **THEN** 系统 MUST 标记参考图未使用或 prompt-only 降级，MUST NOT 在审计中声称已参考图片

#### Scenario: 单张参考生成失败只丢该生成图

- **WHEN** 某张图片生成因参考图不可用、provider 失败或超时而失败
- **THEN** 该生成图不进入 `imageUrls`，其它成功生成图保留，部分成功和全失败语义沿用既有多图能力

#### Scenario: 红线反例 - 原图充当生成成功图

- **WHEN** provider 参考生成失败，有实现把原笔记参考图 URL 塞进 `imageDirective.imageUrls` 充数
- **THEN** MUST 视为违规，不予合入；`imageUrls` 只能包含本次真实生成的新图 URL
