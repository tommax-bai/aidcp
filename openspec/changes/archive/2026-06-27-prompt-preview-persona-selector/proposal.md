## Why

角色 prompt 只读预览当前只能看到**默认账号**的人设效果：渲染走一个写死 `accountId='default'` 的专用预览 dispatcher（`aidcp-cloud/src/server.ts:847`），人设解析恒为默认账号（回落打包 `soul.yaml`）。多账号已上线后，每个账号有各自人设，但运营无法在后台查看「同一个角色，换成某个具体账号的人设后，prompt 长什么样」——也就无法核对某账号人设是否被正确带入各角色指令。

## What Changes

- **cloud（只读预览按选定账号渲染）**：`GET /api/roles/:roleId/prompt` 增加**可选** `?accountId=` 查询参数；给定时，预览层在**同步**渲染前把预览 dispatcher 的当前账号临时切到该账号、渲染、再还原（角色人设按 dispatcher 可变当前账号动态解析，无需改动任何角色的 `buildPrompt`/`previewPrompt`）。
- **诚实回落标注**：选定账号**没有**人设行时（解析器回落打包默认 `soul.yaml`），返回体 MUST 诚实标注「该账号未配人设，预览用默认人设」，绝不把默认人设冒充为该账号人设。
- **人设来源段语义对齐**：既有「人设来源段标注」用于派生人设段的「同一份人设」明确为**选定账号**的人设（不传 accountId 时即系统默认）。
- **console（加选择框）**：`/roles` 的「角色模型配置」卡片增加一个账号/人设选择框，驱动现有「查看 Prompt」弹窗按选定账号人设刷新；账号列表复用现有 `GET /api/accounts`。
- **向后兼容**：不传 `accountId` 时行为与现状**逐字一致**（仍渲染系统默认人设）；返回体保留既有字段，新增字段为可选；旧查看器不升级也能正常显示。

## Capabilities

### New Capabilities
<!-- 无新增 capability：本变更是对既有 prompt 预览能力的需求扩展。 -->

### Modified Capabilities
- `role-llm-config`: 「角色 prompt 在后台只读可见」需求扩展——预览 MAY 接受可选 `accountId`，按该账号人设忠实渲染；账号无人设行时诚实回落默认并明示标注。「prompt 预览可标注账号人设来源段」需求中用于派生人设段的「同一份人设」明确为选定账号人设。

## Impact

- **cloud（纯只读，不动协议 / 风控 / 迁移 / 浏览发布闭环）**：
  - `src/config/role-prompt-preview.ts` — provider `get()` 增加可选账号入参 + 渲染前后切账号的安全包裹；附「所用账号 / 是否回落默认」诚实标注。
  - `src/server.ts` — 预览 provider 接线传入预览 dispatcher 的账号 set/还原口与「是否有人设行」判定（复用 `personaStore.getForAccount`）。
  - `src/panel/panel-server.ts` — 预览路由解析 `?accountId=`，透传给 provider。
  - `src/panel/types.ts` — `RolePromptView` 增加可选字段（所用 accountId / personaFallback 标志），向后兼容。
- **console**：
  - `src/pages/RolesPage.tsx` — 「角色模型配置」卡片加账号/人设选择框；「查看 Prompt」拉取带 `?accountId=`；展示回落标注。
  - `src/api/queries.ts` / `src/types/api.ts` — 复用/补账号列表查询与 `RolePromptView` 类型字段。
- **不影响**：边-云协议、风控状态单写、数据库迁移、浏览/发布闭环、其它 `/api/*` 接口。
