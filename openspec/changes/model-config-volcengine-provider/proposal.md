## Why

当前"模型配置"在文本侧**结构性地只认一个厂商（阿里百炼 DashScope）**：唯一的文本 LLM 出口在进程启动时把 baseUrl + API key **固定**注入（`server.ts:216` 构造 `QwenClient`，baseUrl 硬编 DashScope 兼容端点），只有**模型名**按调用做四层解析（角色 → 分类 → 全局 → 代码默认）。运营要在后台把某些角色（或全局默认）切到火山引擎方舟（Ark / Doubao）时，**无处可配 provider、无处可存第二把 key**：模型名换成 Doubao 也只会被发到 DashScope 端点 → 鉴权/找不到模型失败。

火山方舟 Ark 是 **OpenAI 兼容**接口（`/chat/completions`、`Authorization: Bearer`、响应带 `usage`），与现有出口的 HTTP 形状逐字相同 —— 唯一的 per-provider 差异就是 **baseUrl + key + 模型名**。凭据存储也早已 `PK(provider, field)` 的多厂商形状（当前只用了 `dashscope`）。所以这是一次"把单厂商假设泛化为多厂商、provider 跟模型一起逐层选"的改造，而非新建一套客户端。

## What Changes

- **新增文本厂商：火山引擎方舟 Ark / Doubao**。文本模型配置从"单厂商"升级为"**provider 跟模型一起逐层选**"——全局默认、按角色覆盖、按分类默认三层各自带 provider，**provider 永远跟"胜出那一层"的模型同行，绝不把一层的 provider 配另一层的 model**。
- **每次调用按胜出 provider 取地址与密钥**（关键正确性）：文本出口从"构造期固定 baseUrl+key"泛化为"按本次解析出的 provider 在启动期预载的 `provider → {baseUrl, key}` 映射里取"。选中厂商的 key 缺失时 **诚实抛错（发请求前）**，**MUST NOT 退回另一厂商的 key/baseUrl**（那会把 Doubao 模型名发到 DashScope、或反之 = 静默走错厂商）。
- **凭据按厂商分别配**：写凭据接口从写死 `dashscope` 泛化为 `(provider, field)`，白名单由 provider 注册表派生（`dashscope:dashscope_api_key`、`volcengine:volcengine_api_key`）；模型配置视图按厂商分别回报 key 是否已配、掩码、来源。AES-256-GCM 加密、明文绝不外泄、主密钥缺失诚实 503 等红线**逐字不变**。
- **保存前探活按 provider 探**：角色/分类/全局保存模型时，探活用**该 provider 的 baseUrl+key**（否则合法的 Doubao 模型名被 DashScope 端点判无效、永远存不进去）。选中 provider 的 key 缺失时探活返回**可区分的原因**（`provider_key_missing`，区别于 `model_invalid`），让运营知道是"去配 key"还是"改模型名"。
- **存储自愈 + 迁移**：`model_config` 加 `text_provider`、`role_config` 与 `category_config` 各加 `provider`；老行回填 `dashscope`。除独立迁移外，各 store 的 `init()` **额外跑 `ALTER ... ADD COLUMN IF NOT EXISTS`**（自愈），因为 ECS 上表已存在、`CREATE TABLE IF NOT EXISTS` 不会补列，rsync 先于迁移时不至于让新 SELECT 报错回落静默失效。
- **后台两页加 provider 选择**：设置页加"全局文本厂商"下拉 + 各厂商 key 分开输入；角色/分类页在模型名旁加 provider 下拉，provider 变更也触发重新探活。
- **图片侧零改动**：provider 解析**只管文本**；通义万相图片客户端保持自己独立的 DashScope key、永不经文本 provider 路由；即便全局文本厂商切到火山，图片仍走 DashScope（万相 key 启动期照常加载）。
- **零回归不变量**：**不配火山时，DashScope 路径逐字不变**——`getModel` 签名不动、provider 注册表里 dashscope 项 == 现有 key + 现有 baseUrl，请求 URL / Authorization / 模型名 / 记账与改造前完全一致；以验收测试坐实。
- **协议与边缘零改动**：纯云端 + console；不碰边-云协议（两份 `protocol.ts` 不漂移）。

## Capabilities

### Modified Capabilities
- `model-provider-config`: 文本模型配置从单厂商泛化为多厂商——新增 provider 注册表与"全局文本厂商"选择、凭据按厂商分别加密落库与回报、每次调用按胜出 provider 取地址与密钥（缺失诚实失败、绝不跨厂商兜底）、后台设置页 provider 下拉 + 各厂商 key。
- `role-llm-config`: 按角色/分类的模型覆盖**带上 provider**——provider 跟同层模型一起解析、null/未知 provider 回落 `dashscope` 绝不跨层混搭、温度仍独立；保存前探活按 provider 探（key 缺失可区分）；按角色可观测日志补 `provider` 维度。

## Impact

- **代码（仅 aidcp-cloud）**：新增 `src/llm/providers.ts`（provider 注册表常量 + 凭据白名单派生）；`src/llm/qwen.ts` 文本出口泛化（per-call provider → baseUrl+key、缺失诚实抛错、`getModel` 不变、新增可选 `getProvider`/`providerRuntime`、`onCall` 补 `provider`）；`server.ts` 启动期把 dashscope/volcengine 两把 key 解密成 `providerRuntime` 静态映射、`resolveSelection` 一次解析出 `{provider, model}`、`buildModelConfigView`/`setCredential`/`probeModel` 改 per-provider；三个 config store 加列 + `init()` 自愈 ALTER + 写时 (model, provider) 原子；`src/panel/*` 模型与角色/分类接口形状改造；新增迁移 `migrations/0018`。
- **代码（aidcp-console）**：`types/api.ts` 的 `ModelConfig` 与角色/分类类型加 provider；`api/queries.ts`；`SettingsPage.tsx`（provider 下拉 + 各厂商 key）；`RolesPage.tsx` 与分类页（provider 下拉 + provider 变更重探活）。
- **协议 / 边缘**：零改动。
- **环境变量**：新增 `ARK_API_KEY`（或 `VOLCENGINE_API_KEY`，火山方舟密钥的 env 回退，与 db 内凭据二选一、db 优先）、`ARK_BASE_URL`（可选，区域/自定义端点覆盖，默认 `https://ark.cn-beijing.volces.com/api/v3`）。`AIDCP_CRED_KEY` 仍是凭据可编辑的前提。
- **已知限制（记账）**：token 用量表保持按模型名聚合、本期不加 provider 维度；同名模型跨厂商会并行归并到同一行（Qwen 与 Doubao 命名实际不重叠，且 `onCall` 与 `[llm]` 日志已带 provider 可回溯）。列为债务、留作扩展缝。
- **运维**：新增 provider 的 **key 改动需重启 cloud 才生效**（与现有 DashScope key 行为一致——模型名热加载、密钥重启生效），UI 文案诚实告知。
