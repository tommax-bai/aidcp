## Why

后台角色配置页的只读 prompt 查看器（change `role-prompt-visibility`，Option A 忠实渲染）落地时**只做了浏览侧**：15 个浏览文本角色能看到真实 prompt，而 7 个发布文本角色一律返回 `available:false` + 一句「发布侧待后续」的诚实占位（`aidcp-cloud/src/config/role-prompt-preview.ts` 发布分支）。这与该能力 spec「现役 LLM 角色的 prompt 在后台只读可见」的意图有缺口——运营想核对发布选题/文案/标题/配图/评分/审批各角色到底被喂了什么话时，仍只能翻源码。本 change 把发布侧补齐。

## What Changes

- **发布 7 个文本角色 prompt 只读可见**：预览提供方的发布分支从「统一返回不可用」改为**按 roleId 忠实渲染**——复用发布管线既有的 `build*Prompt` 构建函数、传入最小合法示例输入（占位串沿用浏览侧 `<示例…>` 约定），返回 `available:true` + 真实 prompt 文本。覆盖：发布选题侦察 / 技术帖文案创作 / 技术帖标题创作 / 配图选题 / 配图指令 / 内容质量评分 / 发布审批裁决。
- **发布预览示例输入注册表**：新增一个 roleId → 渲染闭包的小注册表（每个闭包用示例入参调对应 `build*Prompt`），与浏览侧角色实例的 `previewPrompt()` 并列，接入预览提供方。
- **发布侧人设口径诚实标注（V1 不做按账号切）**：发布正文人设当前是构建函数内置默认（写死），**不随账号切换**。故发布预览按系统默认忠实渲染、不做「按账号人设高亮/回落」；给定 `accountId` 时诚实标注「发布侧人设为内置默认、不随账号切换」，绝不伪造账号维度。
- **配图生成执行（图像角色）展示有效图片指令**：它没有大模型文本 prompt，但发给文生图模型的图片指令 = 「配图指令」角色按正文产出的主体（示例占位）+ 系统统一追加的固定风格基底 `IMAGE_STYLE_BASE`（每张图被强制施加的风格/负向约束，此前在查看器各处均不可见）。改为 `available:true` 显示该有效图片指令，并诚实标注「文生图图片指令、非大模型文本 prompt、用全局图片模型生成」；不附人设来源段、不随账号切。

不做（OUT OF SCOPE）：可编辑 prompt（Option B 模板抽存库，仍 YAGNI）；发布侧按账号人设高亮/回落（留后续）；改动任何 `build*Prompt` 的现有逻辑（线上 prompt 行为零变化）。

## Capabilities

### New Capabilities
<!-- 无新增 capability -->

### Modified Capabilities
- `role-llm-config`：修订「角色 prompt 在后台只读可见，忠实渲染且优雅降级」这条要求——把「忠实渲染」明确覆盖到**发布侧文本角色**（经其真实 `build*Prompt` + 示例输入渲染），并补齐发布侧人设口径约束（内置默认、V1 不随账号切、诚实标注）与「渲染失败降级」在发布侧同样成立；图像/纯规则角色仍返回不可预览。

## Impact

- **cloud（aidcp-cloud）**：`src/config/role-prompt-preview.ts` 发布分支改为忠实渲染 + 新增发布预览示例输入注册表（可置于同文件或邻近的 `publish-agent/` 下，仅调既有 `build*Prompt`、不改其逻辑）；`test/role-prompt-preview.test.ts` 补发布侧断言（7 角色 `available:true` 且 prompt 非空；渲染抛错降级；配图生成仍不可预览；带 `accountId` 时发布侧诚实标注不伪造账号人设）。
- **console（aidcp-console）**：无需改——`RolesPage` 已能渲染 `available:true` 的扁平 prompt；发布侧不附来源段，走既有扁平分支。
- **协议 / DB / 迁移**：无（纯只读、不碰协议、不碰库）。
- **红线**：纯只读无写路径；单角色渲染失败 → `available:false` + 诚实原因，绝不抛、绝不崩、绝不连累浏览/发布闭环；不改任何 `build*Prompt` 现有逻辑（线上 prompt 零变化）。
