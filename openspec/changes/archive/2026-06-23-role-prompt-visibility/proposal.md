## Why

后台「角色配置」页当前只能改模型 + 温度，**看不到也改不了每个角色的 prompt**。prompt 全部硬编码在代码里：浏览侧 ~11 个角色各有一个私有 `buildPrompt()`，发布侧集中在 `src/publish-agent/prompts.ts`；它们不是静态字符串，而是调用时由「写死的指令文字 + 注入的人设(soul) + 注入的实时数据(卡片/笔记/评论)」拼成。运营想知道「某个角色到底被喂了什么话」时，只能去翻代码。

本 change 做**只读查看（Option A）**：让后台能看到每个角色**真实**的 prompt（用最小示例数据 + 真实人设渲染出来），只看不改。明确**不做**可编辑（那是另一档 B：抽存库模板 + 校验/预览/回落，风险高，YAGNI 先不做）。

## What Changes

- **cloud**：给现役 LLM 角色加一个**只读 prompt 预览**能力——调用各角色**真实的** prompt 构建逻辑、传入最小示例数据 + 当前真实 soul，渲染出代表性 prompt 文本；用 `try` 包裹，单个角色渲染失败降级为「预览不可用」**绝不崩**、绝不影响运行闭环。
  - 浏览侧：各角色暴露一个 `previewPrompt()`（内部调用自己既有的 `buildPrompt(示例数据)`，**不改 buildPrompt 本身逻辑**）。
  - 发布侧：复用 `prompts.ts` 既有 builder 函数，传入示例输入渲染。
- **cloud 面板 API**：新增只读路由 `GET /api/roles/:roleId/prompt`（JWT 守护），返回 `{ roleId, prompt, available, note }`；**只读，无写路由**。
- **console**：角色配置页每个文本角色加「查看 Prompt」按钮 → 只读弹窗展示该角色 prompt（示例数据/人设以说明标注），不提供编辑。

**明确不做（OUT OF SCOPE）**：可编辑 prompt（Option B：模板抽取/存库/热加载/校验）；改动任何角色 `buildPrompt` 的现有逻辑；人设编辑（属 item 8 / change account-persona-config）。

## Capabilities

### New Capabilities
<!-- 无新增 capability -->

### Modified Capabilities
- `role-llm-config`：新增一条要求——现役 LLM 角色的 prompt 在后台**只读可见**（忠实渲染真实构建逻辑，渲染失败优雅降级，无写路径）。

## Impact

- **cloud（aidcp-cloud）**：浏览侧 ~11 个 `src/agents/*.ts` 各加一个 `previewPrompt()`（仅调既有 buildPrompt，不改其逻辑）；新增 `src/config/role-prompt-preview.ts`（按 roleId 汇集预览，try 包裹降级）；发布侧用 `src/publish-agent/prompts.ts` 既有 builder + 示例输入；`src/server.ts` append 预览外观装配（**不动 stream C 的 resolver 块**）；`src/panel/panel-server.ts` append `GET /api/roles/:roleId/prompt`（reserved-order，C 之后）；`src/panel/types.ts` append 预览形状类型。
- **console（aidcp-console）**：`src/pages/RolesPage.tsx` 加「查看 Prompt」只读弹窗；`src/api/queries.ts` append 预览读 query；`src/types/api.ts` append 预览类型。
- **协议 / 迁移**：无（只读、无 DB、不碰协议）。
- **红线**：只读、无写；预览渲染失败降级「不可用」绝不崩、绝不连累浏览/发布闭环；不改任何 buildPrompt 现有逻辑（线上 prompt 行为零变化）。
