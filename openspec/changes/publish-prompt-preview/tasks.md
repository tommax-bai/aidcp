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
- [x] 4.3 按 §5 安全序列部署 cloud（备份 → rsync → restart → healthcheck）；**绝不碰同机 isales**。<!-- 2026-07-01 deployed：备份 cloud.bak.20260701-184746.tar.gz + .env.bak.20260701；scoped rsync 3 文件(prompts-preview.ts 新 / role-prompt-preview.ts / test)；prod 跑 npx tsx src/server.ts 无需 build；复查 ECS prompts.ts 签名与本地逐字一致；restart→active/8787 起(pid1608884)/飞书长连接已建立/PG select1=1；isales 未碰 -->
- [x] 4.4 上线后逐个发布 roleId `GET /api/roles/:id/prompt` 核 `available:true` 且 prompt 非空；配图生成执行仍 `available:false`；后台「查看 Prompt」发布角色能看到真实 prompt。<!-- 2026-07-01 API 层核：server 启动无 import 错(role-prompt-preview 依赖 prompts-preview 已随 server.ts 加载成功)；panel 8090 GET publish/browse prompt 未鉴权均 401(路由已接线+JWT 守护)；带 token 的 available:true 逐角色点测 + 后台「查看 Prompt」浏览器点测留用户 -->

## 6. aidcp-cloud — 图片类角色（配图生成执行）补预览

- [x] 6.1 `prompts-preview.ts` 新增图片指令预览：`IMAGE_PROMPT_PREVIEW_BUILDERS['publish:ImageGenerator'] = () => \`<示例主体>. ${IMAGE_STYLE_BASE}\``（示例主体用配图指令角色文档里的英文范例，固定风格基底逐字取自 `prompts.ts`）。<!-- aidcp-cloud 2c97fde -->
- [x] 6.2 `role-prompt-preview.ts` 图像分支：`llmKind==='image'` 时查表 → 命中则 `available:true` + 图片指令说明（try 降级），未命中回落旧「无文本 prompt」；`get()` 发布分支仅对**文本**角色加「人设不随账号切」标注，图像角色保留其图片指令说明（不被覆盖）。<!-- aidcp-cloud 2c97fde -->
- [x] 6.3 测试：图像角色 `available:true` 且 prompt 含固定风格基底特征串（no text/no watermark/no human faces）、无来源段；带 `accountId` 仍 `available:true`、保留图片指令说明、无 personaFallback。<!-- aidcp-cloud 2c97fde typecheck 干净 + role-prompt-preview 15/15 -->
- [x] 6.4 部署 ECS（scoped：prompts-preview.ts + role-prompt-preview.ts + test）。<!-- 2026-07-01 deployed：备份 cloud.bak.20260701-191922.tar.gz；ECS prompts.ts 仍含 IMAGE_STYLE_BASE(依赖满足)；restart→active/8787/飞书 onReady；GET publish:ImageGenerator/prompt 未鉴权 401；与并发 split-topic-roles 不同文件、零冲突；isales 未碰。带 token available:true 点测留用户 -->

## 7. 审计发现·本期不补（用户决定 2026-07-01，非任务，仅存档）

> 审计「还有哪些没做」时发现两个**真实但更大**的缺口（现役 LLM 调用但不在角色目录 → 查看器/模型配置均不可见）。均需改并发方（change `split-topic-roles`）正在动的文件（`prompts.ts` / `role-catalog.ts` / `content-creator.ts` / `types.ts` / `server.ts`）。**用户明确决定本期不补**（2026-07-01）——故以下**不是本 change 的任务**，仅留档，日后如需再单独立 change。

- **发布正文去 AI 味重写**（ContentCleaner 经注入的 PostProcessor 调 `llm.complete`，prompt 内联在 `server.ts`）不在角色目录。补齐需：抽 prompt 为共享 builder（server 与预览同源防漂移）+ 给该 `llm.complete` 接 roleId（否则配了模型是静默 no-op）+ catalog 加 `publish:ContentCleaner` + 预览 + 测试。
- **评论点赞择选**（`comment_like_appraiser`，`AIDCP_COMMENT_LIKE=true` 线上已开、现役）用 `BaseRole.decide` 且已有 `previewPrompt`/`personaSegments`，但不在角色目录 → 一行 catalog 即可让其可预览+可配模型（零运行时改动）。**已知缺口：线上在跑却看不见/配不了**。

## 5. 收尾

- [ ] 5.1 全部 task 标 `[x]` 并回写 commit-sha / 偏离说明；`openspec archive publish-prompt-preview`（delta 合并进 `openspec/specs/role-llm-config`）。<!-- 待用户浏览器点测确认发布/图片角色 prompt 正常显示后 archive -->
