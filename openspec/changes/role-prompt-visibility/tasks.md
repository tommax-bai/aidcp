> **协调注记（与已部署的 C role-model-category-config 同域）**
> - **只读、无 DB、无迁移、不碰协议**。无迁移号占用。
> - 与 C 共享文件只 **append**，不动 C 的块：`src/server.ts`（C 拥有 resolver 块，本 change 只 append 预览外观装配）、`src/panel/panel-server.ts`（C 之后追加只读路由）、`src/panel/types.ts`、console `src/types/api.ts` / `src/api/queries.ts`。
> - **绝不改任何角色 `buildPrompt` 的现有逻辑**——只新增 `previewPrompt()`（线上 prompt 行为零变化）。
> - 不进 `role-dispatcher.ts` 运行时分发逻辑（仅借已注册的角色实例读预览）。

## 1. aidcp-cloud — 浏览侧角色预览入口（仅新增，不改 buildPrompt）

- [ ] 1.1 给 ~11 个浏览 LLM 角色（`src/agents/*.ts`：content-evaluator / content-curator-role / search-evaluator / interaction-appraiser-role / follow-agent / author-evaluator / comment-appraiser / comment-composer / comment-reviewer / comment-de-ai-flavor / concept-extractor-role）各加 public `previewPrompt(): string`：用本角色最小合法示例数据 + `this.soul` 调既有私有 `buildPrompt`，占位串用 `<…>` 明示。**不改 buildPrompt 逻辑**。
- [ ] 1.2 comment-like-appraiser（若现役、在 ROLE_CATALOG 内）同样加 `previewPrompt()`；非 catalog 内的纯规则角色不加。

## 2. aidcp-cloud — 发布侧 + 汇集模块 + 安全降级

- [ ] 2.1 新建 `src/config/role-prompt-preview.ts`：按 `roleId`（browse:/publish: 前缀）汇集预览函数；发布侧复用 `src/publish-agent/prompts.ts` 既有 builder（`buildScoutPrompt`/`buildCreatorPrompt`/`buildTitlePrompt`/`buildImagePrompt`/`buildAssemblerPrompt`/`buildGatekeeperPrompt`）+ 示例输入；浏览侧经传入的角色实例 `previewPrompt()`。
- [ ] 2.2 `role-prompt-preview.ts`：每个预览 `safePreview()` try 包裹 → `{available, prompt, note}`；单角色失败降级「预览不可用」**绝不抛**；未知/非 LLM(image/none) 角色 `available:false` + 说明。
- [ ] 2.3 `src/server.ts`：**append** 预览外观装配（把浏览角色实例 + 发布 builder 接进 preview 模块，注入面板依赖）；**不动 C 的 resolver 块**。

## 3. aidcp-cloud — 面板 API（只读，reserved-order append 在 C 之后）

- [ ] 3.1 `src/panel/types.ts`：append `RolePromptView { roleId; prompt: string | null; available: boolean; note: string }` + `PanelDeps.rolePromptPreview?`（未注入则 503）。
- [ ] 3.2 `src/panel/panel-server.ts`：append **只读** `GET /api/roles/:roleId/prompt`（JWT 守护、未知 roleId 404、非 LLM 角色 available:false）。**无任何写路由**。

## 4. aidcp-console — 只读查看弹窗

- [ ] 4.1 `src/types/api.ts`：append `RolePromptView` 类型（镜像 cloud）。
- [ ] 4.2 `src/api/queries.ts`：append 按需取 prompt 的 query（点开时拉 `GET /api/roles/:id/prompt`）。
- [ ] 4.3 `src/pages/RolesPage.tsx`：每个文本角色加「查看 Prompt」按钮 → 只读弹窗（等宽可滚展示 prompt；顶部说明「实时数据/人设为示例占位」）；**无编辑控件**。

## 5. 验证

- [ ] 5.1 cloud 单测：`role-prompt-preview` —— 已知文本角色返 `available:true` 且 prompt 非空含真实指令片段；构造抛错的角色降级 `available:false` 不抛；非 LLM 角色 available:false。
- [ ] 5.2 cloud 单测：面板 `GET /api/roles/:id/prompt` —— 401 未鉴权 / 200 含 prompt / 未知角色 404 / 未注入 503 / **无写路由**（PUT 该路径走 404 或不被接受）。
- [ ] 5.3 cloud `npm run typecheck` 绿（不碰协议，AC-PROTO 零变化）→ `test:acceptance` → `test`。
- [ ] 5.4 console `npm run typecheck` + build 绿；/roles「查看 Prompt」弹窗手测（看到真实指令文字 + 真实人设 + 示例占位数据）。
- [ ] 5.5 确认浏览/发布闭环 prompt 行为零变化（buildPrompt 未改逻辑；全量回归绿）。

## 6. 收尾与部署

- [ ] 6.1 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <commit-sha> 备注 -->`）。
- [ ] 6.2 `openspec validate role-prompt-visibility --strict` 通过。
- [ ] 6.3 cloud + console 按 §5 安全序列部署 ECS（备份 → rsync → restart → healthcheck；console → 8088）；**部署后复查关键文件内容 + 新启动日志**（多会话竞态教训）。
- [ ] 6.4 上线后核对：后台逐个角色「查看 Prompt」能看到真实 prompt；渲染失败角色优雅降级。
- [ ] 6.5 `/opsx:archive` 归档（delta 合并进 `openspec/specs/role-llm-config`）。
