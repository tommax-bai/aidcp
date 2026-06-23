> **协调注记（与已部署的 C role-model-category-config 同域）**
> - **只读、无 DB、无迁移、不碰协议**。无迁移号占用。
> - 与 C 共享文件只 **append**，不动 C 的块：`src/server.ts`（C 拥有 resolver 块，本 change 只 append 预览外观装配）、`src/panel/panel-server.ts`（C 之后追加只读路由）、`src/panel/types.ts`、console `src/types/api.ts` / `src/api/queries.ts`。
> - **绝不改任何角色 `buildPrompt` 的现有逻辑**——只新增 `previewPrompt()`（线上 prompt 行为零变化）。
> - 不进 `role-dispatcher.ts` 运行时分发逻辑（仅借已注册的角色实例读预览）。

## 1. aidcp-cloud — 浏览侧角色预览入口（仅新增，不改 buildPrompt）

- [x] 1.1 给 ~11 个浏览 LLM 角色各加 public `previewPrompt(): string`：用本角色最小合法示例数据 + `this.soul` 调既有私有 `buildPrompt`，占位串用 `<…>` 明示。**不改 buildPrompt 逻辑**。<!-- aidcp-cloud bd037eb 11 角色经脚本插入(content-evaluator/content-curator-role/search-evaluator/interaction-appraiser-role/follow-agent/author-evaluator/comment-appraiser/comment-composer/comment-reviewer/concept-extractor-role + comment-like-appraiser)；comment-de-ai-flavor 无 buildPrompt，previewPrompt 复刻其 inline rewrite 模板 -->
- [x] 1.2 comment-like-appraiser（catalog 内）同样加 `previewPrompt()`；纯规则角色不加。<!-- aidcp-cloud bd037eb -->

## 2. aidcp-cloud — 发布侧 + 汇集模块 + 安全降级

- [x] 2.1 新建 `src/config/role-prompt-preview.ts`：按 `roleId` 汇集预览；浏览侧经角色实例 `previewPrompt()`。<!-- aidcp-cloud bd037eb 偏离：发布侧本期 available:false + 诚实 note(prompt 集中在 publish-agent/prompts.ts 可直接读源码，V1 browse-only)，不伪造；发布侧示例输入渲染留后续 -->
- [x] 2.2 `role-prompt-preview.ts`：每个预览 `safePreview()` try 包裹 → `{available, prompt, note}`；单角色失败降级「预览不可用」**绝不抛**；未知/非 LLM 角色 `available:false` + 说明。<!-- aidcp-cloud bd037eb -->
- [x] 2.3 `src/server.ts`：**append** 预览外观装配（借 `roleDispatcher.getRoles()` + 注入面板依赖）；**未动 C 的 resolver 块**。<!-- aidcp-cloud bd037eb + RoleDispatcher.getRoles() 只读 getter -->

## 3. aidcp-cloud — 面板 API（只读，reserved-order append 在 C 之后）

- [x] 3.1 `src/panel/types.ts`：append `RolePromptView` + `PanelDeps.rolePromptPreview?`（未注入则 503）。<!-- aidcp-cloud bd037eb -->
- [x] 3.2 `src/panel/panel-server.ts`：append **只读** `GET /api/roles/:roleId/prompt`（JWT、未知 roleId 404 via isKnownRole、非文本 available:false）。**无任何写路由**。<!-- aidcp-cloud bd037eb -->

## 4. aidcp-console — 只读查看弹窗

- [x] 4.1 `src/types/api.ts`：append `RolePromptView` 类型（镜像 cloud）。<!-- aidcp-console 3b67a08 -->
- [x] 4.2 按需取 prompt（点开时拉 `GET /api/roles/:id/prompt`）。<!-- aidcp-console 3b67a08 偏离：未加 queries.ts 常驻 hook，改为 RolesPage 内点开时直接 apiGet(惰性、不常驻轮询)，更贴只读弹窗语义 -->
- [x] 4.3 `src/pages/RolesPage.tsx`：每个文本角色加「查看 Prompt」按钮 → 只读弹窗（等宽可滚展示 prompt；顶部 Alert 说明「实时数据/人设为示例占位」；不可预览角色显 warning note）；**无编辑控件**（footer 仅「关闭」）。<!-- aidcp-console 3b67a08 -->

## 5. 验证

- [x] 5.1 cloud 单测：`role-prompt-preview` —— 已知文本角色 `available:true` 且 prompt 非空；构造抛错降级不抛；非 LLM / 未知 / 发布侧 available:false。<!-- aidcp-cloud bd037eb test/role-prompt-preview.test.ts 6/6 -->
- [x] 5.2 cloud 单测：面板 `GET /api/roles/:id/prompt` —— 401 / 200 含 prompt / 未知 404 / 未注入 503 / **PUT 该路径不被接受(404)**。<!-- aidcp-cloud bd037eb test/role-prompt-panel.test.ts 2/2 -->
- [x] 5.3 cloud `npm run typecheck` 绿（不碰协议，AC-PROTO 零变化）→ `test:acceptance` → `test`。<!-- aidcp-cloud bd037eb typecheck 干净 / acceptance 全过 / test 325/325 -->
- [~] 5.4 console `npm run typecheck` + build 绿；/roles「查看 Prompt」弹窗手测。<!-- aidcp-console 3b67a08 typecheck+build 绿；浏览器内弹窗手测留部署后做 -->
- [x] 5.5 确认浏览/发布闭环 prompt 行为零变化（buildPrompt 未改逻辑；全量回归绿）。<!-- aidcp-cloud bd037eb 仅新增 previewPrompt，未改任何 buildPrompt 体；全量 325/325 含浏览/发布角色 -->

## 6. 收尾与部署

- [x] 6.1 按 sub-repo 分节回写本 tasks.md 进度。<!-- cloud bd037eb / console 3b67a08 -->
- [x] 6.2 `openspec validate role-prompt-visibility --strict` 通过。<!-- 2026-06-23 valid -->
- [ ] 6.3 cloud + console 按 §5 安全序列部署 ECS（备份 → rsync → restart → healthcheck；console → 8088）；**部署后复查关键文件内容 + 新启动日志**。<!-- 待部署（且当前本机→GitHub/网络间歇性掐断，commit 已本地：cloud bd037eb / console 3b67a08，待网络恢复 push 后部署） -->
- [ ] 6.4 上线后核对：后台逐个角色「查看 Prompt」能看到真实 prompt（逐 roleId GET /api/roles/:id/prompt available:true）；渲染失败角色优雅降级。<!-- 真实 previewPrompt 渲染本地未逐个构造验证(构造依赖各异)，留部署 E2E 逐角色确认 -->
- [ ] 6.5 `/opsx:archive` 归档（delta 合并进 `openspec/specs/role-llm-config`）。
