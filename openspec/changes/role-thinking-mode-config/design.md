## Context

云端唯一文本模型出口在 `aidcp-cloud/src/llm/qwen.ts` 的 `chat()`：请求体只发 `{model, messages, temperature}`，**非流式**，从不传任何 thinking 参数，返回**只读 `choices[0].message.content`**（全仓 0 处读 `reasoning_content`）。因此"是否思考"当前不可由运营控制，只随模型名 + 厂商默认。

模型 / 温度 / 厂商已经是"按角色（`role_config`）/ 按分类（`category_config`）/ 全局（`model_config`）"三层可配 + 热加载，解析器在 `server.ts` 注入 QwenClient 的 `getModel` / `getTemperature` / `getProvider`。本 change 沿用同一套机制，加一维 thinking。

2026-07-02 线上探测（`llm_token_usage` 表 `calls` vs `ok_calls`）证实：qwen3.7-plus/max 在"非流式 + 不传参数"路径成功率≈100%，即**默认（不传参数）零回归且安全**——这是必须守住的基线。

## Goals / Non-Goals

**Goals:**
- 让运营在后台**按角色 / 按分类**设置思考模式三态：`default` / `off` / `on`，热加载生效。
- 模型出口按解析出的 provider 把三态翻译成对应厂商参数；`default` 态请求体与现在逐字一致（零回归）。
- `on` 在"非流式即可思考"的厂商（DeepSeek / 豆包）上真正兑现；对"非流式无法思考"的 DashScope Qwen，**绝不发出会 400 的请求**。
- 缺省 / 非法一律回落 default，绝不 brick。

**Non-Goals:**
- **不做流式改造**：整条出口保持非流式 + 只读 `content`。因此 DashScope Qwen 的 `on` 本期不兑现（需后续单独 change 引入流式 + 读 `reasoning_content`）。
- 不引入全局 thinking 默认列（全局隐含 = `default`；只做 role / category 两层覆盖）。
- 不广撒 `<think>` 清洗逻辑（非流式路径 `content` 本就干净，污染非真实风险）。
- 不改动边缘、风控单写、发布链、`onCall` 记账。

## Decisions

### D1. 存储：role/category 各加一个可空列，NULL = default
`role_config` / `category_config` 各自愈加列 `thinking_mode TEXT`（`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`，与现有 provider 列的自愈加列同模式）。取值 `'off'` / `'on'`；`NULL` / 空 / 非法 = `default`（发起时不发任何 thinking 参数）。
- **为何不加全局列**：全局隐含 default 即"跟模型走"，正是今天的行为，加全局列只增表面、无收益（YAGNI）。
- **为何三态而非布尔**：`default`（不干预）与 `off`（显式关）语义不同——前者请求体零回归、后者主动发关闭参数。运营需要"不干预"作为安全缺省。

### D2. 解析：新增 `getThinking(role?)`，两层回落
解析器新增 `getThinking(role?) → 'off' | 'on' | undefined`：role 层有值取 role，否则取 category 层，否则 `undefined`（= default）。与 `getModel` 同源、同一内存镜像、热加载。QwenClient 构造期可选注入 `getThinking`；**不注入时（单测 / 旧路径）行为与改造前逐字一致**。

### D3. 出口翻译：集中一个纯函数 `buildThinkingParams(provider, model, mode)`
在 `chat()` 里，用解析出的 `provider` + `model` + thinking 三态算出**要合并进请求体的附加字段**，`default`（undefined）返回空对象：
- `off`：
  - dashscope + Qwen 系 → `{ enable_thinking: false }`（安全，且非流式下本就近乎如此）。
  - dashscope + DeepSeek 系 → DeepSeek 的关思考参数。
  - volcengine 豆包 → `{ thinking: { type: 'disabled' } }`。
- `on`：
  - dashscope + DeepSeek 系 → 开思考参数（非流式可用，推理落 `reasoning_content`、我们仍只读 `content`、最终答案质量受益）。
  - volcengine 豆包 → `{ thinking: { type: 'enabled' } }`。
  - **dashscope + Qwen 系 → 守卫：不发任何参数（等价 default）+ 告警一次**。因为 Qwen 开思考必须流式，非流式发 `enable_thinking:true` 会 400。
- `default` → `{}`（零回归）。

**厂商 / 家族判定**集中在此函数：provider 来自解析层；"Qwen 系 vs DeepSeek 系"按模型名前缀判定（`qwen*` / `deepseek*`）。**失败安全**：无法识别的组合在 `on` 分支一律回落"不发参数 + 告警"，绝不发出可能 400 的参数。函数为纯函数、用注入的假 fetch 断言请求体形状做单测。
- **精确参数名后置校验**：`enable_thinking` / DeepSeek 关思考键 / 豆包 `thinking.type` 均晚于训练截止，实装时 MUST 先 `curl` compatible-mode 直探确认每个参数被目标模型接受（呼应模型选型记忆里的探活坑），再落码；翻译表集中一处便于校正。

### D4. Qwen+on 双层防护：UI 主防 + 后端兜底
- **UI 主防**：角色 / 分类当前绑定为 dashscope Qwen 模型时，前端"开启"选项**禁用 + 悬浮说明**"需流式支持，暂不可用"，从源头不让运营设成一个不生效的值（避免"设了没反应"的静默）。
- **后端兜底**：D3 的守卫在 egress 兜底——即便某行历史遗留 `on` + Qwen（例如先设 on、后把模型改回 Qwen），也回落 default + 告警一次，绝不 400。
- **写入不做硬拒**：`on` 值本身允许写库（存的是"意图"）——若该角色日后被重绑到 DeepSeek/豆包，`on` 自动生效。可行性在**发起时**按当时的模型判定，而非写入时锁死。

### D5. 面板 API：与现有 model/temperature 读写同形
`GET /api/roles`（目录）与角色 / 分类配置读接口回带 `thinkingMode`；`PUT` 接受可选 `thinkingMode ∈ {default, off, on}`，非法值拒绝、缺省视作 default。校验 / facade / store 复用现有 role-config / category-config 通路。写入 MUST 先持久化再刷内存镜像（与现有不变量一致）。

## Risks / Trade-offs

- **[后置参数名与训练截止后的模型行为漂移]** → D3 集中翻译表 + 实装期逐个 `curl` 探活确认 + 纯函数单测断言请求体；错了只需改一处。
- **[家族判定（Qwen vs DeepSeek）用模型名前缀，脆]** → 判定集中一处、覆盖单测；且 `on` 分支未识别即失败安全（不发参数），最坏是"该开没开"（可观测、可告警），绝不"发了 400"。
- **[`on` 被静默 no-op]** → UI 主防禁用不可行的组合 + 后端告警一次，双层可见，不静默。
- **[误伤零回归]** → `default` / 未注入 `getThinking` 路径必须走"空附加字段"分支；用"不传选项请求体逐字不变"的回归断言锁死（对齐 role-llm-config 既有向后兼容要求）。
- **[回滚]** → 自愈加列是 inert 列，旧码不读不发 thinking 参数；回滚只需部署旧码，列留库无害，无需降级迁移。

## Migration Plan

1. cloud：store 自愈加列（幂等 ALTER）→ 解析器加 `getThinking` → `chat()` 接 `buildThinkingParams` → 面板 API 扩字段。
2. console：类型 + 查询 + RolesPage 三态控件（含 Qwen+on 禁用态）+ 分类默认页。
3. 实装期先 `curl` 探活确认三厂商的 thinking 参数键名与非流式可用性，再定稿 D3 翻译表。
4. 测试：cloud `npm run test:acceptance` + 全量 + `typecheck`（新增：default 零回归断言、三厂商 off/on 请求体形状、Qwen+on 守卫回落）；console typecheck / build。
5. 部署走 §5 安全序列（备份 → rsync → restart → healthcheck → 失败回滚）。
6. 回滚：部署旧 cloud 码即可，列 inert。

## Open Questions

- DeepSeek 系在 DashScope compatible 模式下**关 / 开思考的精确参数键**（`enable_thinking` 是否通用，或需 `reasoning_effort` / `thinking`）——实装期探活确认。
- 是否需要"分类默认思考"页与"全局"解耦展示（本设计只做 role + category 两层；全局隐含 default）。若运营强烈需要全局一键，可后续加全局列，不影响本设计的回落链。
