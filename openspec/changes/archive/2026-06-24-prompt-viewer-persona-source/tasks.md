> **前置 / 排序**：本 change（查看器人设来源标注）排在 stream F `account-persona-config` 之后落更有意义（届时人设按账号解析，标注的就是当前账号人设）；但对「当前解析出的人设」即可工作（今天全局 soul / F 后按账号），**不硬阻塞 F**。
> **红线延续**：**绝不改任何角色 `buildPrompt` 的现有逻辑**——只新增只读 `personaSegments()`（线上 prompt 行为零变化）；只读、无写；定位不唯一 / 拼接不等 → 回落不标记（**绝不瞎标 = 软性静默假成功**）。
> **协调（5 流并发）**：APPEND-only 在共享 chokepoint 文件（cloud `src/panel/types.ts`、console `src/types/api.ts`），按 **C→D→F→B** 顺序追加、不改他流条目；**不碰协议**（stream B 独占 protocol.ts / command-bridge.ts / docs/protocol.md）与 **C 的 resolver 块**；无新路由、无迁移。

## 1. aidcp-cloud — 角色人设片段来源（只读，不改 buildPrompt）

- [x] 1.1 给 11 个浏览 LLM 角色各加只读 `personaSegments(): string[]`：用 `this.soul` 以与既有 `buildPrompt` **相同的拼接逻辑**产出人设片段（连续人设角色返回单片段；把人设拆开的 `search-evaluator`/`concept-extractor` 返回多片段，身份句 + 兴趣句）。**不改 buildPrompt**。逐角色核对真实拼接形态。<!-- cloud cdc988b 11 角色：content-evaluator/content-curator/interaction-appraiser 连续单段；author/follow/comment-reviewer/comment-appraiser/comment-like/comment-composer 单行段；search-evaluator/concept-extractor 双段。diff 为 additions-only（buildPrompt/previewPrompt 未动）-->
- [x] 1.2 角色无人设可标（纯规则 / 非文本 / 无 soul 注入）→ `personaSegments()` 不实现，预览层据此对该角色不出 `segments`。<!-- cloud cdc988b 仅 11 个文本浏览角色实现；其余（导航/通知/规则类）不实现 → hasPersonaSegments 守卫跳过 -->

## 2. aidcp-cloud — 预览层分段 + 两道诚实闸

- [x] 2.1 `src/config/role-prompt-preview.ts`：在 `safePreview` 渲染 prompt 后，对实现了 `personaSegments()` 的角色尝试分段——逐片段在渲染 prompt 里定位（导出纯函数 `segmentPromptByPersona`）。<!-- cloud cdc988b -->
- [x] 2.2 **唯一性闸**：片段必须恰好出现一次（`indexOf===lastIndexOf`）；0 或 >1 → 丢弃 `segments` 回落扁平。<!-- cloud cdc988b 另加片段重叠 → 丢弃 -->
- [x] 2.3 **拼接等值闸**：切出各段 `text` 拼回必须**逐字等于**扁平 prompt；不等 → 丢弃 `segments` 回落扁平。<!-- cloud cdc988b -->
- [x] 2.4 成功 → 返回交替 `segments`（空首/尾 `role` 段省略；仅当确有 persona 段才附）；失败 / 无片段 → 省略 `segments`、`available:true` + note。绝不伪造跨度、绝不抛、单角色失败不连累其它。<!-- cloud cdc988b note 同步改：人设为当前账号真实人设（修原「示例占位」误导）-->

## 3. aidcp-cloud — 面板返回体（APPEND，无新路由）

- [x] 3.1 `src/panel/types.ts`：`RolePromptView` **APPEND** 可选 `segments?: RolePromptSegment[]`（新增 `RolePromptSegment{source,text}`；不改既有 `prompt`/`available`/`note`）。<!-- cloud cdc988b -->
- [x] 3.2 `src/panel/panel-server.ts`：路由不变（同 `GET /api/roles/:roleId/prompt`），返回体经预览层自带 `segments`；无新路由、无写路径。<!-- cloud cdc988b panel-server 未改（view 直接带 segments）-->

## 4. aidcp-console — 弹窗渲染（背景色 + 顶部图例）

- [x] 4.1 `src/types/api.ts`：**APPEND** `RolePromptView.segments?` + `RolePromptSegment`（镜像 cloud）。<!-- console 47119c6 -->
- [x] 4.2 `src/pages/RolesPage.tsx`：查看 Prompt 弹窗——有 `segments` 时按段渲染，`persona` 段加**灰底（代码块样式）** + 顶部图例「灰底=来自当前账号的真实人设；其余为该角色独有指令」；无 `segments` 回落扁平。图例为文字 + 色块（不只靠颜色）；单 `<pre>` 可整段复制。<!-- console 47119c6 -->

## 5. 验证

- [x] 5.1 cloud 单测：连续人设角色单段、拼接等值；拆段角色多段各自唯一定位、拼接等值（纯函数 + 真实 ContentEvaluator 集成）。<!-- cloud cdc988b test/role-prompt-persona-segments.test.ts -->
- [x] 5.2 cloud 单测：唯一性闸——片段 0 次 / 2 次 → null 回落。<!-- cloud cdc988b -->
- [x] 5.3 cloud 单测：拼接等值闸——拼接 ≠ prompt（重叠 / 空片段）→ null 回落。<!-- cloud cdc988b -->
- [x] 5.4 cloud 单测：绝不瞎标——撞字 / 未命中由唯一性闸拦截；集成测真实 prompt 定位正确、拼接逐字等值。<!-- cloud cdc988b -->
- [x] 5.5 cloud `npm run typecheck` 绿；`npm run test:acceptance`（AC-PROTO 不漂移）→ 全量 `npm test`；buildPrompt 体零改动（additions-only diff 核验）。<!-- cloud cdc988b typecheck 绿；acceptance 26/26；全量 **640/640**；agents diff additions-only（buildPrompt/previewPrompt 未动）-->
- [x] 5.6 console `npm run typecheck` + `npm run build` 绿；查看 Prompt 弹窗渲染分段 / 回落。<!-- console 47119c6 typecheck+build 绿（页面真机渲染待 6.4）-->

## 6. 收尾与部署

- [x] 6.1 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <commit-sha> 备注 -->`）。<!-- cloud cdc988b / console 47119c6，均推 origin -->
- [x] 6.2 `openspec validate prompt-viewer-persona-source --strict` 通过 <!-- 本次归档前跑 -->
- [ ] 6.3 cloud + console 按 §5 安全序列部署 ECS（备份 → rsync → restart → healthcheck；console → 8088）；**部署后复查关键文件内容 + 新启动日志**（确认 `personaSegments` / 分段逻辑 / `segments` 字段在；buildPrompt 未变）。
- [ ] 6.4 上线后核对：逐角色查看 Prompt——连续人设角色见人设段标注；拆段角色（`search-evaluator`）见多段标注或诚实回落；人设值撞字角色诚实回落不误标。
- [x] 6.5 `/opsx:archive` 归档（delta 合并进 `openspec/specs/role-llm-config`）<!-- 按用户顺序：先归档、后部署（6.3/6.4 在归档后执行）-->
