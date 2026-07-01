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

## 7. 审计发现·补齐（用户 2026-07-01 决定补上；在隔离 worktree 做，避让并发 split-topic-roles WIP）

> 审计「还有哪些没做」发现两个现役 LLM 调用但不在角色目录（查看器/模型配置均不可见）。因并发方在主工作区有未提交改动动到同批文件（`prompts.ts` / `role-catalog.ts` / `server.ts`），改在基于干净 `origin/master` 的 **git worktree** 做，提交推送后主工作区他的 WIP 零扰动。

- [x] 7.1 **发布正文去 AI 味重写（ContentCleaner）**：抽内联 prompt 为共享 builder `buildDeAiRewritePrompt`（`server.ts` rewrite 与只读预览同源、防漂移，**逐字保留原文含「口吾」笔误 → 线上零变化**）；`server.ts` rewrite 调用带 `role='publish:ContentCleaner'`（模型/温度后台可配、非静默 no-op）；catalog 加 `publish:ContentCleaner`（publish_create，可调温度）；prompts-preview 加预览。<!-- aidcp-cloud 9a7f1ed -->
- [x] 7.2 **评论点赞择选（comment_like_appraiser）**：catalog 加 `browse:comment_like_appraiser`（browse_judge，不调温度）；已具 `previewPrompt`/`personaSegments` + `BaseRole.decide`，零运行时改动即可预览+可配模型。开关关闭未注册时预览诚实回落「暂不支持预览」。<!-- aidcp-cloud 9a7f1ed -->
- [x] 7.3 测试：ContentCleaner `available:true` 且 prompt 含「去除AI味」；comment_like_appraiser 注册时 `available:true`、未注册时诚实 `available:false`。<!-- aidcp-cloud 9a7f1ed 干净 worktree 全量 1022/1022 绿 -->
- [x] 7.4 部署 ECS（scoped：role-catalog/prompts/server/prompts-preview + test，从 worktree rsync）。<!-- 2026-07-01 deployed：先 md5 核 ECS 4 文件 == 基线 2c97fde（无并发方 WIP 落 ECS、无漂移）→ 备份 cloud.bak.20260701-194719 → rsync → md5 核 ECS == 目标 9a7f1ed → restart→active/8787/飞书 onReady；两新角色 prompt 路由未鉴权 401（接线+守护）；isales 未碰 -->

> 主工作区（并发 split-topic-roles WIP）零扰动；其提交后 pull 到 9a7f1ed 时，我的增量落在 role-catalog/prompts/server 的低冲突区（多为追加），一般可自动三方合并。

## 5. 收尾

- [ ] 5.1 全部 task 标 `[x]` 并回写 commit-sha / 偏离说明；`openspec archive publish-prompt-preview`（delta 合并进 `openspec/specs/role-llm-config`）。<!-- 待用户浏览器点测确认发布/图片角色 prompt 正常显示后 archive -->
