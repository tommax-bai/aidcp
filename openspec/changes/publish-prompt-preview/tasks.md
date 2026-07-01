# Tasks — publish-prompt-preview

> 铁律：**绝不改任何 `build*Prompt` 的现有逻辑**（线上 prompt 行为零变化）——只新增调用它们的示例渲染。纯只读、无写路径、无 DB/协议改动。

## 1. aidcp-cloud — 发布预览示例输入注册表

- [x] 1.1 新增发布预览示例输入注册表（如 `src/publish-agent/prompts-preview.ts`）：`Record<publishRoleId, () => string>`，每个闭包用**最小合法示例输入**调对应导出的 `build*Prompt`；入参用 `src/publish-agent/types.ts` 的类型对齐、占位串沿用浏览侧 `<示例…>` 约定。覆盖 7 角色：`ContentScout`(`buildScoutPrompt`) / `ContentCreator`(`buildCreatorPrompt`) / `TitleCreator`(`buildTitlePrompt`) / `ImageSetPlanner`(`buildImageSetPlanPrompt`) / `ImagePromptComposer`(`buildImagePromptComposerPrompt`) / `QualityScorer`(`buildAssemblerPrompt`) / `ApprovalGatekeeper`(`buildGatekeeperPrompt`)。<!-- aidcp-cloud 4917c15 -->
- [x] 1.2 复核 7 个 `build*Prompt` 均为纯拼串函数（无 IO / 无状态写），示例渲染无副作用；注册表 key 与 `role-catalog.ts` 的 `publish:*` roleId 逐一对齐（含 `QualityScorer→buildAssemblerPrompt` 的映射）。<!-- aidcp-cloud 4917c15 复核：7 builder 均纯拼串、无 IO -->

## 2. aidcp-cloud — 预览提供方接线发布分支

- [x] 2.1 `src/config/role-prompt-preview.ts` 发布分支：由「统一返回 `available:false` + 占位 note」改为「查发布注册表 → 命中则 try 包裹忠实渲染（`available:true` + `PLACEHOLDER_NOTE`）→ 未命中则回落既有诚实 note」；渲染以 `safePreview` 或等价 try 包裹，单角色抛错 → `available:false` + 原因，绝不抛、绝不崩。<!-- aidcp-cloud 4917c15 偏离：发布用专属 PUBLISH_PLACEHOLDER_NOTE（原 PLACEHOLDER_NOTE 含「人设为当前账号真实人设」对发布不成立）；未用 safePreview（其绑定浏览 note），改等价 try/catch，无 segments -->
- [x] 2.2 发布侧 `accountId` 口径：给定 `accountId` 时发布角色仍按内置默认渲染，note 明示「发布侧人设为内置默认、不随账号切换」；**不**设 `personaFallback`、**不**附 `segments`（绝不伪造账号维度）。<!-- aidcp-cloud 4917c15 偏离：发布侧亦不回显 accountId（避免前端「人设来自账号」误导） -->
- [x] 2.3 保持配图生成执行（`publish:ImageGenerator`，`llmKind=image`）走 `llmKind !== 'text'` 分支、返回既有「图像角色无文本 prompt」——本分支不动。<!-- aidcp-cloud 4917c15 -->


## 3. aidcp-cloud — 测试

- [x] 3.1 `test/role-prompt-preview.test.ts` 补：7 个发布文本角色 `available:true` 且 `prompt` 非空（真实 `build*Prompt` + 示例输入渲染成功、零抛错）。<!-- aidcp-cloud 4917c15 -->
- [x] 3.2 补：某发布角色渲染抛错时降级 `available:false` + 原因、不抛（可注入一个会抛的示例闭包桩验证降级路径）。<!-- aidcp-cloud 4917c15 覆写导出的 PUBLISH_PREVIEW_BUILDERS 条目为抛错桩、finally 还原 -->
- [x] 3.3 补：发布角色带 `accountId` → 内置默认渲染、note 含「不随账号切换」、无 `personaFallback`、无 `segments`；配图生成执行仍 `available:false`「图像角色无文本 prompt」。<!-- aidcp-cloud 4917c15 -->
- [x] 3.4 回归断言 `build*Prompt` 本体未改（现有发布管线单测全绿，prompt 行为零变化）。<!-- aidcp-cloud 4917c15 全量 1019/1019 绿，含发布管线单测 -->

## 4. 验证与部署

- [x] 4.1 `cd ../aidcp-cloud && npm run typecheck && npm test`（含新增预览断言）全绿。<!-- aidcp-cloud 4917c15 typecheck 干净；test:acceptance 27/27；role-prompt-preview 15/15；全量 1019/1019 -->
- [x] 4.2 `openspec validate publish-prompt-preview --strict` 通过。<!-- aidcp 已过（proposal/design/specs/tasks 4/4） -->
- [ ] 4.3 按 §5 安全序列部署 cloud（备份 → rsync → restart → healthcheck）；**绝不碰同机 isales**。
- [ ] 4.4 上线后逐个发布 roleId `GET /api/roles/:id/prompt` 核 `available:true` 且 prompt 非空；配图生成执行仍 `available:false`；后台「查看 Prompt」发布角色能看到真实 prompt。

## 5. 收尾

- [ ] 5.1 全部 task 标 `[x]` 并回写 commit-sha / 偏离说明；`openspec archive publish-prompt-preview`（delta 合并进 `openspec/specs/role-llm-config`）。
