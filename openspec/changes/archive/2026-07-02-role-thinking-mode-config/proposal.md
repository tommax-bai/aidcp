## Why

当前"某角色是否以思考模式（thinking）调用大模型"完全由绑定的模型名 + 厂商默认决定，运营无法控制：云端唯一模型出口只发 `{model, messages, temperature}`、非流式、从不传任何 thinking 参数、且只读 `content`。同一模型在判定/裁决/创作等不同场景对 thinking 的需求相反（判定/口语撰写要关、发布审批要开），却无法按角色区分。本 change 把 thinking 提升为与"模型 / 温度 / 厂商"同级的、按角色 / 按分类可配的一维旋钮，交给运营在后台控制。

## What Changes

- 新增**按角色 / 按分类**可配的三态思考模式：`default`（不干预、跟模型走，= 当前行为）/ `off`（强制关思考）/ `on`（强制开思考）。落 PostgreSQL，复用现有 `role_config` / `category_config` 三层配置 + 热加载机制，新增一个可空维度（NULL = default）。
- 模型出口按**解析出的 provider** 把三态翻译成对应厂商参数：DashScope Qwen → `enable_thinking`；DashScope DeepSeek → thinking 开关参数；火山方舟豆包 → `thinking:{type}`。**`default` 态一个 thinking 参数都不发**，请求与改造前逐字一致（零回归红线）。
- **`on` 仅在"非流式即可思考"的厂商上兑现**（DeepSeek / 豆包，正好覆盖唯一真需要 thinking 的发布审批）。DashScope Qwen 的 `on` 需要流式，本 change **不做流式改造**：对当前绑定为 DashScope Qwen 模型的角色，后台"开启"不可用（UI 禁用 + 说明），后端对 Qwen+on 诚实回落 default 并告警，**绝不发出会 400 的请求**。
- 面板 API 读写扩展该维度（含读写校验、缺省回落），后台角色配置页 + 分类默认页新增三态控件。

## Capabilities

### New Capabilities
<!-- 无新增 capability：本 change 在既有 role-llm-config 能力上加一维配置。 -->

### Modified Capabilities
- `role-llm-config`: 在既有"按角色 / 按分类可配模型与温度、缺省回落绝不 brick、LLM 客户端按角色覆盖向后兼容"的能力上，**新增 thinking 模式作为第三类可配维度**——包含：三态语义与三层回落（NULL=default）、模型出口按 provider 的 thinking 参数构造、`default` 态零回归不变量、DashScope Qwen `on` 的诚实回落守卫（绝不 400）、面板读写校验。

## Impact

- **aidcp-cloud**：`role_config` / `category_config` 自愈加列（thinking 维度）；解析器（`server.ts` 注入的 per-role 解析）新增 `getThinking`；`llm/qwen.ts` 的 `chat()` 按 provider + 三态构造请求体（default 不发参数）；面板 `role-config-store` / `category-config-store` / `role-config-facade` / `category-config-facade` / `panel-server` / `panel/types.ts` 扩展读写与校验。
- **aidcp-console**：`pages/RolesPage.tsx`（角色行三态控件 + Qwen+on 禁用态与说明）、分类默认页、`api/queries.ts`、`types/api.ts`。
- **不影响**：`content`-only 解析、180s 单次 / 600s 发布闸超时不变量、`onCall` token 记账、边缘、风控单写路径、发布链。
- **零回归**：不写该维度或写 `default` 时，请求体与当前逐字一致。
