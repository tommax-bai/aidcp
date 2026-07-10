# Change: publish-image-postgen-safety-validation

## Why

`category-adaptive-images-and-judgment` 已经把品类风格档、无脸 / no-text 提示词、竖版尺寸、评审 / 门禁口径等能力上线，但它原先还包含一项更重的承诺：对生成后的高风险配图做“是否像可识别真人 / 名人、文字是否乱码”的视觉校验。这个校验必须实际读取生成图，需要新增视觉 / 多模态模型能力、成本与延迟策略，不能用 prompt 约束或占位规则冒充完成。

本 change 承接这项未决能力，避免老 change 归档后 baseline spec 误声明一个还没有真实实现的产后视觉闸。

## What Changes

- 为发布配图链路新增高风险图产后安全校验：只对可能含真人 / 人脸 / 封面文字的生成图触发。
- 接入视觉 / 多模态判定能力，输出结构化结论：`pass` / `reject` / `unavailable`，并区分真人可识别风险、名人风险、文字乱码风险。
- 命中 `reject` 时丢弃该张图并按既有部分成功语义重生成或少图继续；全失败仍诚实失败。
- 当视觉校验不可用、超时或返回非法结果时，必须如实降级并记录，不能标记为“已通过视觉校验”。

## Impact

- `aidcp-cloud`：配图生成 / 审计链路需要新增视觉校验客户端、重试 / 超时 / 日志与测试。
- OpenSpec baseline：在 `publish-multi-image` 中新增产后视觉校验 requirement。
- 不改变现有 prompt-level 风格档；不改变发布协议；不要求模型在画面内绘制水印。
