# 设计：模型配置增加火山引擎方舟（多文本厂商）

> 经多 agent 工作流（侦察 → 综合 → 三透镜对抗评审）打磨；本文已吸收对抗评审的 7 个 BLOCKER + 多个 MAJOR 修复。

## Context（坐实现状，带 文件:行）

- 文本 LLM **唯一出口** `QwenClient`（`aidcp-cloud/src/llm/qwen.ts`）：OpenAI 兼容 `chat/completions`。**构造一次**于 `server.ts:216`，`apiKey`/`baseUrl` 固定 DashScope（`DEFAULT_BASE_URL` = `https://dashscope.aliyuncs.com/compatible-mode/v1`，`qwen.ts:101`）；仅 `model`/`temperature` 按调用解析（`getModel(role)`/`getTemperature(role)`）。`!this.apiKey` 守卫在 `chat()` 顶部一次（`qwen.ts:144-147`），`Authorization: Bearer ${this.apiKey}`（`qwen.ts:160-165`）。`usage` 从响应体捡回交 `onCall` 记账（token 与 ok 解耦红线）。
- 模型解析四层回落（`server.ts:183-190` `resolveModelForRole`）：per-role 覆盖 → 分类默认 → 全局 `textModel` → 代码默认（store 缺省）。**各层只存模型名、无 provider**。温度两层独立（`server.ts:192` role 覆盖 → 代码默认）。
- `ModelConfigStore`（`config/model-config-store.ts`，迁移 0007）：单行 `model_config`，`text_model`+`image_model`，**无 provider 列**；`getCached()` 供热加载。
- `RoleConfigStore`（`config/role-config-store.ts`，迁移 0008）：`role_config(role_id PK, model, temperature)`；`set()` 把 model/temperature **各自独立** merge（`role-config-store.ts:124-128`）。`CategoryConfigStore`（迁移 0009）：`category_config(category_id, account_id, model)`，读恒 `account_id IS NULL`。
- `CredentialStore`（`config/credential-store.ts`）：`provider_credentials` 表 **`PK(provider, field)`**，AES-256-GCM，主密钥 env `AIDCP_CRED_KEY`（base64 32B）。**已 provider-keyed**，当前仅 `('dashscope','dashscope_api_key')`。`getSecretForRuntime(provider, field)` 启动期取明文、篡改/缺失返回 null 不 brick。`canEdit()` = 主密钥就位。
- 启动期 `dashscopeApiKey = getSecretForRuntime('dashscope','dashscope_api_key') ?? env DASHSCOPE_API_KEY`（`server.ts:175-177`）。
- 探活 `probeModel(model)`（`server.ts:917-919`）：用**唯一** `llm.chat` 显式 model 覆盖（8s 超时、`role='system:model_probe'`、探活也记 token）。被 `roleConfigPanel`/`categoryConfigPanel`（`server.ts:921-933`）与全局 `setModel` 保存路径共用。
- 面板：`buildModelConfigView`（`server.ts:895-913`）**硬编** `provider:'dashscope'`、`baseUrl=QWEN_BASE_URL`；`setCredential` 写死 `setSecret('dashscope', ...)`（`server.ts:999-1003`）；`PUT /api/config/credential` 白名单写死 `['dashscope_api_key']`（`panel-server.ts:405`）。`ModelConfigView` 形状在 `panel/types.ts:115`。
- 图片：`WanxiangClient`（DashScope 异步任务 API，**非** OpenAI 兼容），key 回退 `dashscopeApiKey`（`server.ts:354-361`）—— **本次不动**。
- 火山方舟 Ark：OpenAI 兼容 `/chat/completions`，baseUrl `https://ark.cn-beijing.volces.com/api/v3`，`Authorization: Bearer <ARK_API_KEY>`，`model` 接 Doubao 模型名或接入点 id（`ep-xxx`），响应带 OpenAI 形状 `usage`（现有出口逐字可解析）。

## 关键决策

### D1 — Provider 注册表 = 冻结字面常量（不是机制）
新文件 `aidcp-cloud/src/llm/providers.ts`：

```ts
export interface TextProviderMeta {
  id: string;            // 'dashscope' | 'volcengine'
  displayName: string;   // '阿里百炼 DashScope' / '火山引擎方舟 Ark'
  baseUrlDefault: string;
  baseUrlEnv?: string;   // 可选 env 覆盖（火山区域/自定义端点）：ARK_BASE_URL
  credentialField: string; // 'dashscope_api_key' / 'volcengine_api_key'
  envKeys: string[];       // db 缺失时的 key env 回退（火山：['ARK_API_KEY','VOLCENGINE_API_KEY']）
}
export const TEXT_PROVIDERS = { dashscope: {...}, volcengine: {...} } as const;
export type TextProviderId = keyof typeof TEXT_PROVIDERS;
```

扩展即"加一条字面项"；**不提供 register() / 动态发现**（YAGNI：只有两个 OpenAI 兼容厂商）。凭据白名单从此常量派生：`{ [meta.credentialField]: meta.id }`。

### D2 — 文本出口泛化：每次调用按胜出 provider 取 baseUrl+key，缺失诚实抛错、绝不跨厂商兜底
`QwenClient` 新增**两个可选注入**（不传即与现状逐字一致）：
- `getProvider?: (role?) => string` —— 与 `getModel` 平级。两者都是 `server.ts` 里**同一个** `resolveSelection(role)` 的薄视图（`getModel = r => resolveSelection(r).model`、`getProvider = r => resolveSelection(r).provider`），**同输入同胜出层 → provider 与 model 必然一致**，从根上消除"两个独立函数各自重算胜出层而漂移"的红线风险。`getModel` **签名不变（仍返回 string）** → 零回归。
- `providerRuntime?: Record<string, { baseUrl: string; apiKey: string }>` —— 启动期预载的**静态**映射（非每调用函数；与现状"key 启动期一次性加载"一致，不引入不存在的 key 热加载）。

`chat()` 解析顺序：
```
provider = opts.provider ?? this.getProvider?.(opts.role)        // 不注入则 undefined
if (provider && this.providerRuntime) {                          // 多厂商路径
  rt = this.providerRuntime[provider]
  if (!rt || !rt.apiKey) throw Error(`${provider} apiKey 缺失（后台为该厂商配置密钥并重启 cloud）`)  // 发 fetch 前诚实失败
  baseUrl = rt.baseUrl; apiKey = rt.apiKey                       // 绝不退回别的 provider 的 key/baseUrl
} else {                                                          // 零回归路径（单测/未注入）
  baseUrl = this.baseUrl; apiKey = this.apiKey
  if (!apiKey) throw Error('Qwen apiKey 缺失（设置 DASHSCOPE_API_KEY 或传入 apiKey）')
}
```
key 守卫从**构造期**下移到**provider 解析之后**。生产里 `providerRuntime.dashscope = { baseUrl: DEFAULT_BASE_URL, apiKey: dashscopeApiKey }`，未被覆盖的角色 provider 恒 `'dashscope'` → 命中该项 → **请求逐字等同改造前**。`LlmCallOpts` 仅加 `provider?: string`（**不**加裸 baseUrl/apiKey，保住"唯一出口"不变量、密钥不外溢调用点）。`onCall` info 加 `provider`，`[llm]` 日志带 provider。

### D3 — 解析器：provider 取自胜出 model 的**同一行**；null/未知 → dashscope；温度独立
`server.ts` `resolveSelection(role) → { provider, model }`：
1. per-role 行 `{model, provider}`：`model` 非空 → 返回 `{ model, provider: normProv(provider) }`
2. 分类行 `{model, provider}`：`model` 非空 → 返回 `{ model, provider: normProv(provider) }`
3. 全局 `{textModel, textProvider}` → 返回 `{ model: textModel, provider: normProv(textProvider) }`

`normProv(p) = (p?.trim() && TEXT_PROVIDERS[p.trim()]) ? p.trim() : 'dashscope'` —— 处理①老行 provider 为 NULL 的 model-bearing 行 → `dashscope`；②配置行里的脏/未知 provider 串 → `dashscope`（**绝不 brick、绝不跨层混搭**）。**一层只在其 model 非空时才贡献 provider**（纯温度覆盖行 model 为 null → 既不贡献 model 也不贡献 provider）。温度解析保持两层独立、与 provider 无关。

### D4 — 数据模型：三列 + 自愈 init + 迁移 0018 + 回填 dashscope
列：`model_config.text_provider TEXT NOT NULL DEFAULT 'dashscope'`、`role_config.provider TEXT`、`category_config.provider TEXT`。`provider_credentials` **不改 schema**（已 `PK(provider, field)`）。

迁移 `migrations/0018_*.sql`（**apply 时重新 grep `migrations/` 确认 0018 未被并发会话占用，被占则顺延；绝不复用 0012 缺号**）：对三表 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...` + 把现有 model 非空行回填 `provider='dashscope'`（幂等、可重跑）。

**自愈（修部署时序 MAJOR）**：每个 store 的 `init()` 在 `CREATE TABLE IF NOT EXISTS` 之后、`reload()` SELECT 之前**额外**跑 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS provider/text_provider`。原因：ECS 上表已存在，`CREATE TABLE IF NOT EXISTS` 是 no-op、不补列；若新 SELECT 含新列而迁移尚未跑（rsync 先于迁移），SELECT 抛错 → `init` 的 catch 静默回落代码默认 → provider 配置失效且无人知。自愈让运行中的 store **永不领先于自己的 schema**。

**写时原子（修部分 patch MAJOR）**：store `set()` 把 `(model, provider)` 当**一个单元**——写 model 必带 provider（UI 永远同发）；清空 model（置 null）同时清 provider；纯温度 patch 两者都不碰。

### D5 — 凭据：按厂商写/读，白名单由注册表派生
- `setCredential(provider, field, value)`：`(provider, field)` 须命中注册表派生的白名单，否则诚实拒（非静默）。`setSecret(provider, field, ...)`。主密钥缺失 → `cred_key_missing` → 503，明文绝不落库。
- 运行时 key：启动期把每个 provider 的明文解密进 `providerRuntime`：`getSecretForRuntime(provider, meta.credentialField) ?? env[meta.envKeys...]`；baseUrl = `env[meta.baseUrlEnv] ?? meta.baseUrlDefault`。
- **新 key 改动需重启 cloud 才生效**（与现有 DashScope key 一致：模型名热加载、key 重启生效）。UI 文案明示。

### D6 — 探活按 provider
`probeModel(provider, model)`：仍用**唯一** client，opts `{ provider, model, timeoutMs, role:'system:model_probe' }` → 经 D2 路由到该 provider 的 baseUrl+key。该 provider 的 key 未载 → 返回**可区分**原因 `provider_key_missing`（区别 `model_invalid`），让 console 区分"去配 key（并重启）"还是"改模型名"。`provider` 端到端穿过 `roleConfigPanel`/`categoryConfigPanel`/全局 `setModel` 保存路径。**provider 变更也触发重新探活**（dashscope 上合法的模型名在 volcengine 上未必合法）。**不对模型名做格式校验**（Ark 的 `ep-xxx` 必须放行）——探活是唯一判据。

### D7 — 面板视图 + console：按厂商
`ModelConfigView` 新形状：
```ts
{
  textProvider: string;                 // 选中的全局文本厂商
  imageProvider: 'dashscope';           // 钉死、信息性（图片不动）
  textModel: string; imageModel: string;
  providers: { id: string; displayName: string; baseUrl: string }[]; // 可选文本厂商
  credentials: { provider: string; field: string; configured: boolean; maskedHint: string | null; source: 'db'|'env'|'none' }[]; // 按厂商凭据态
  canEditCredential: boolean;
}
```
端点：`GET/PUT /api/config/model`（PUT body `{textProvider?, textModel?, imageModel?}`：校验 `textProvider` 在注册表内，`textModel` 用 `textProvider` 探活后才写）；`PUT /api/config/credential`（body `{provider, field, value}`）；`GET /api/roles` 与 `PUT /api/roles/:id/config`、分类接口的视图加 `effectiveProvider`、patch 加 `provider`（与 model 同发）。role/category facade 的 `effectiveModel` 分支里**同址**算出 `effectiveProvider`（取自胜出同层）。

Console：`SettingsPage.tsx` 加"全局文本厂商"下拉 + 各厂商 key 分输入（掩码、永不回显、改 key 整段重输、保存后提示重启生效）；`RolesPage.tsx` 与分类页在模型名旁加 provider 下拉、provider 变更重探活。`types/api.ts` 的 `ModelConfig` 与角色/分类类型同步加 provider（与 cloud `panel/types.ts` lockstep，避免 typecheck 漂移 / 半渲染）。

### D8 — 图片侧零改动
provider 解析**只作用于文本**。`WanxiangClient` 保持自己独立的 DashScope key、**永不**经 `providerRuntime` 路由；即便 `textProvider=volcengine`，启动期 DashScope key 照常加载，图片路径仍走 DashScope。以零回归测试坐实。

### D9 — Token 归属
`onCall` info 与 `[llm]` 日志加 `provider`（诚实取证 + 扩展缝）。token 用量表保持按模型名聚合、**本期不加 provider 维度**（不引迁移）。**已知限制**：同名模型跨厂商会并行归并同一行（Qwen 与 Doubao 命名实际不重叠、且日志已带 provider 可回溯）——列为债务。

## 红线合规
- **诚实失败**：选中 provider key 缺失 → fetch 前抛错、不假成功、不跨厂商兜底；主密钥缺失 → 503 不明文落库。
- **零回归**：`getModel` 签名不动；dashscope 项 == 现有 key+baseUrl → 请求逐字一致；图片不动。AC 测试坐实。
- **token 与 ok 解耦**：保持（失败路径已有 usage 仍记）。
- **绝不 brick**：null/未知 provider → dashscope；store init 自愈；解析永不抛。
- **协议不漂移**：不碰边-云协议、两份 `protocol.ts` 不动。

## YAGNI 砍掉 / 扩展缝
- 不做图片多厂商（仅文本）。
- baseUrl 不进 UI（留 env `ARK_BASE_URL` 覆盖区域/端点）。
- provider 注册表 = 字面常量（扩展 = 加一条）。
- token 表不扩 provider 维度（仅进日志）。

## 测试计划（AC-*）
1. **零回归**：无 provider 配置时，某代表角色请求的 URL / Authorization / model / `onCall`（除新增 `provider` 字段外）与改造前逐字相同。
2. **图片零回归**：`textProvider=volcengine` 时图片路径仍走 DashScope、万相 key 仍加载。
3. **缺 key 诚实失败**：`provider=volcengine` 而 runtime 无火山 key → `chat()` 在 fetch 前抛 `volcengine apiKey 缺失`，**绝不**用 dashscope key/baseUrl（断言未发 fetch）。
4. **老行回落**：legacy role 覆盖（model 非空、provider NULL）即便全局切 volcengine 仍解析到 `dashscope`。
5. **探活按 provider**：探 volcengine 模型命中 Ark baseUrl + Ark key（注入假 fetch 断言 host）。
6. **主密钥缺失**：`setCredential('volcengine', ...)` 返回 `cred_key_missing`（503）、无明文。
7. **未知 provider**：配置行脏 provider 串 → 归一 `dashscope`、不 brick。
8. **部分 patch**：model-only patch 保持 (model, provider) 同步；temp-only patch 不贡献 provider。
9. 单元：`TEXT_PROVIDERS` 注册表、白名单派生、`normProv`。
10. Console：typecheck + build。
