> **前置 / 排序**：本 change（查看器人设来源标注）排在 stream F `account-persona-config` 之后落更有意义（届时人设按账号解析，标注的就是当前账号人设）；但对「当前解析出的人设」即可工作（今天全局 soul / F 后按账号），**不硬阻塞 F**。
> **红线延续**：**绝不改任何角色 `buildPrompt` 的现有逻辑**——只新增只读 `personaSegments()`（线上 prompt 行为零变化）；只读、无写；定位不唯一 / 拼接不等 → 回落不标记（**绝不瞎标 = 软性静默假成功**）。
> **协调（5 流并发）**：APPEND-only 在共享 chokepoint 文件（cloud `src/panel/types.ts`、console `src/types/api.ts`），按 **C→D→F→B** 顺序追加、不改他流条目；**不碰协议**（stream B 独占 protocol.ts / command-bridge.ts / docs/protocol.md）与 **C 的 resolver 块**；无新路由、无迁移。

## 1. aidcp-cloud — 角色人设片段来源（只读，不改 buildPrompt）

- [ ] 1.1 给 ~11 个浏览 LLM 角色各加只读 `personaSegments(): string[]`：用 `this.soul` 以与既有 `buildPrompt` **相同的拼接逻辑**产出人设片段（连续人设角色返回单片段；把人设拆开的角色如 `search-evaluator` 返回多片段，身份句 + 兴趣句）。**不改 buildPrompt**（与既有 `previewPrompt()` 并列的新增只读方法）。逐角色核对其真实拼接形态，不假设全部连续。
- [ ] 1.2 角色无人设可标（纯规则 / 非文本 / 无 soul 注入）→ `personaSegments()` 返回空数组或不实现，预览层据此对该角色不出 `segments`。

## 2. aidcp-cloud — 预览层分段 + 两道诚实闸

- [ ] 2.1 `src/config/role-prompt-preview.ts`：在 `safePreview` 渲染 prompt 后，对实现了 `personaSegments()` 的角色尝试分段——对每个人设片段在渲染 prompt 里定位。
- [ ] 2.2 **唯一性闸**：片段必须恰好出现一次（`indexOf === lastIndexOf`）；0 或 >1 → 该角色丢弃 `segments`、回落扁平不标记。
- [ ] 2.3 **拼接等值闸**：切出的各 `segments` 全部 `text` 拼回必须**逐字等于**扁平 prompt；不等 → 丢弃 `segments`、回落扁平。
- [ ] 2.4 成功 → 返回交替 `segments`（`source:'role'|'persona'`，空首/尾 `role` 段省略）；失败 / 无片段 → 省略 `segments`、`available:true` + note。**绝不伪造跨度、绝不抛、单角色失败不连累其它**。

## 3. aidcp-cloud — 面板返回体（APPEND，无新路由）

- [ ] 3.1 `src/panel/types.ts`：`RolePromptView` **APPEND** 可选 `segments?: Array<{ source:'role'|'persona'; text:string }>`（不改既有 `prompt`/`available`/`note` 形状；按 C→D→F→B 顺序追加）。
- [ ] 3.2 `src/panel/panel-server.ts`：同 `GET /api/roles/:roleId/prompt` 路由**不变**，返回体带上 `segments`（经预览层产出）；**无新路由、无写路径**。

## 4. aidcp-console — 弹窗渲染（背景色 + 顶部图例）

- [ ] 4.1 `src/types/api.ts`：**APPEND** `RolePromptView` 可选 `segments`（镜像 cloud；不改他流条目）。
- [ ] 4.2 `src/pages/RolesPage.tsx`：查看 Prompt 弹窗——有 `segments` 时按段渲染，`source:'persona'` 段加**浅背景色** + 弹窗**顶部一条图例**（「有底色 = 来自账号人设」）；无 `segments` 回落今天的扁平展示。**不做内联文字标记**；图例为文字说明（不只靠颜色）。

## 5. 验证

- [ ] 5.1 cloud 单测：连续人设角色 → 单 `persona` 段、拼接等值；`search-evaluator` 这类拆段角色 → 多 `persona` 段各自唯一定位、拼接等值。
- [ ] 5.2 cloud 单测：唯一性闸——人设片段在 prompt 里出现 0 次 / 2 次 → 回落扁平无 `segments`、`available:true`。
- [ ] 5.3 cloud 单测：拼接等值闸——人为构造 segments 拼接 ≠ prompt → 丢弃 `segments` 回落扁平。
- [ ] 5.4 cloud 单测：**绝不瞎标**——人设值与正文撞字时不误标（唯一性闸拦截）；单角色分段失败不连累其它角色。
- [ ] 5.5 cloud `npm run typecheck` 绿（~11 角色加 `personaSegments` 后编译过）；`npm run test:acceptance`（AC-PROTO 不漂移——本 change 未碰协议应保持）→ `npm test` 全量；确认 **buildPrompt 体零改动**（线上 prompt 行为零变化）。
- [ ] 5.6 console `npm run typecheck` + `npm run build` 绿；`/roles` 查看 Prompt 弹窗：有 `segments` 角色见背景色 + 图例、无 `segments` 角色见扁平（回落）。

## 6. 收尾与部署

- [ ] 6.1 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <commit-sha> 备注 -->`）。
- [ ] 6.2 `openspec validate prompt-viewer-persona-source --strict` 通过。
- [ ] 6.3 cloud + console 按 §5 安全序列部署 ECS（备份 → rsync → restart → healthcheck；console → 8088）；**部署后复查关键文件内容 + 新启动日志**（确认 `personaSegments` / 分段逻辑 / `segments` 字段在；buildPrompt 未变）。
- [ ] 6.4 上线后核对：逐角色查看 Prompt——连续人设角色见人设段标注；拆段角色（`search-evaluator`）见多段标注或诚实回落；人设值撞字角色诚实回落不误标。
- [ ] 6.5 `/opsx:archive` 归档（delta 合并进 `openspec/specs/role-llm-config`）——待 6.4 验证后归档。
