# Tasks — image-postcheck-vision-model

> 从 `category-adaptive-images-and-judgment` 拆出（原 tasks 2.2 / 2.4）。核心待决策项 = 视觉模型选型（成本 / 延迟），在此决策前本 change 保持 proposal 态、不实装。**MUST NOT 建假占位校验**（永远返回 pass = 违反本 change 要治的红线）。

## 0. Blocker（待用户 / owner 决策）

- [ ] 0.1 视觉 / 多模态模型选型：定哪家、成本 / 延迟可接受、中文乱码 OCR + 名人相似度识别能力达标（口径同 memory `china-llm-model-selection-by-role`：厂商账单反算、禁硬编码价目表）。

## 1. aidcp-cloud — 产后视觉校验

- [ ] 1.1 视觉模型客户端：新增多模态调用封装（超时 / 降级 / 成本记账），接进发布配图管线。
- [ ] 1.2 产后校验步：`ImageGenerator` 产图后，对**含真人或含封面文字**的图调视觉模型判「像可识别真人 / 名人」「文字乱码」；无真人无文字的图跳过（控成本）。
- [ ] 1.3 命中即丢弃重生成（有界重试）；重试用尽后诚实降级（不静默照用未过校验的图）。

## 2. Verification

- [ ] 2.1 回归：一张含真人 / 封面文字的图产后校验判「像真人 / 乱码」→ MUST 丢弃重生成，MUST NOT 因 prompt 含 faceless/no-text 约束就当作已合规照用（对应 spec scenario「高风险图未过产后校验即重生成」）。
- [ ] 2.2 无真人无文字图不调视觉模型（成本护栏）。
- [ ] 2.3 假占位校验红线：实现中若视觉模型不可用，MUST 显式声明未校验 / 诚实降级，MUST NOT 让校验永远返回 pass。

## 3. Change Record

- [ ] 3.1 回写 commits / validation；`openspec validate image-postcheck-vision-model --strict` → archive。
