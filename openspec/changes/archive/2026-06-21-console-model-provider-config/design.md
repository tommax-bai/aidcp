# Design — console-model-provider-config

## 现状坐实（文件:行）

- 文本模型：`aidcp-cloud/src/llm/qwen.ts:57` `this.model = options.model ?? 'qwen-turbo'`（构造期定死，`private readonly`）；密钥 `:56` `?? process.env.DASHSCOPE_API_KEY`；base `:44` DashScope 兼容端点。`server.ts:106` `new QwenClient()`（无参，吃默认）。
- 图片模型：`aidcp-cloud/src/publish-agent/wanxiang-client.ts:74` `this.model ?? 'wan2.7-image-pro'`；密钥 `:73` `WANXIANG_API_KEY ?? DASHSCOPE_API_KEY`。`server.ts:188` 构造时传 key。
- 面板 API：`aidcp-cloud/src/panel/panel-server.ts` 极小 switch 路由 + JWT；`deps: PanelDeps` 注入云内部（`types.ts`）。读路由公开仅 health/version/login，其余 JWT。
- PG 建表惯例：各 store `CREATE TABLE IF NOT EXISTS` + `migrations/000N_*.sql` 同源（如 `alert-store.ts:21` / `migrations/0006_alerts.sql`）。
- console「设置」页 `aidcp-console/src/pages/SettingsPage.tsx` 当前仅 `<Empty>` 占位。

## 业界方案取舍

isales 的做法（`~/isales-web/src/views/Config/ModelProviderConfig.vue`）：凭据 Fernet 加密落 `provider_credential` 表，UI 掩码、永不回显、改 key 整段重输，**改 key 后重启 engine 生效（v1.0 不支持 live reload）**。本 change 取等价最小版：

- **加密**：Node 内置 `crypto` 的 **AES-256-GCM**（认证加密，自带完整性校验），等价 Fernet 角色，不引第三方（与 qwen.ts「不引 SDK」一致）。落库存 `iv‖authTag‖ciphertext`（base64）。主密钥 32 字节来自 env `AIDCP_CRED_KEY`。
- **掩码**：写时算 `头4****尾4` 存为非敏感提示列，读不需解密即可展示「已配置 + 掩码」。
- **生效时机**：模型名**热加载**（无密钥、改即生效，体验好）；密钥**重启生效**（客户端启动捕获，避免热换密钥的活态一致性问题，匹配 isales）。诚实文案区分两者。
- **provider 维度**：表带 `provider` 列（默认 `dashscope`），为将来多厂商留缝；本期 UI 只出百炼一家（Qwen 文本 + 万相图片共用同一 DashScope key）。**YAGNI**：不做厂商切换 UI、不做密钥热换、不做凭据历史。

## 数据模型（migrations/0007_model_config.sql，幂等）

- `model_config`（单行，主键固定 `id=1`）：`text_model text`、`image_model text`、`updated_at timestamptz`、`updated_by text`。缺行 = 回退代码默认。
- `provider_credentials`（按 `provider, field` 唯一）：`provider text`、`field text`（如 `dashscope_api_key`）、`ciphertext text`、`masked_hint text`、`updated_at timestamptz`、`updated_by text`。

## 运行时解析

- `ModelConfigStore`：启动 `ensureSchema()` + 载入内存镜像；`getCached()` 同步返回 `{textModel,imageModel}`（供客户端每调用解析）；`set(patch,by)` 写 PG + 刷新镜像（热加载）。
- `CredentialStore`：`ensureSchema()`；`canEdit()`（主密钥在否）；`getMasked(provider,field)`（读掩码 + source: db|env|none）；`setSecret(provider,field,value,by)`（加密落库，主密钥缺失抛诚实错）；`getSecretForRuntime(provider,field)`（解密；启动期用，注入客户端）。
- `QwenClient`/`WanxiangClient`：新增可选 `getModel?: () => string`；`chat()`/`generate()` 用 `this.getModel?.() ?? this.model`（保留默认与测试桩）。`server.ts` 构造时传 `getModel` 指向 `modelConfigStore.getCached()`，`apiKey` 传启动期解密凭据（无则回退 env）。

## 面板接口（JWT 守护，非乐观，诚实）

- `GET /api/config/model` → `{ provider:'dashscope', baseUrl, textModel, imageModel, credential:{ field, configured, maskedHint, source }, canEditCredential }`。**永不含明文密钥**。
- `PUT /api/config/model` `{ textModel?, imageModel? }` → 校验非空字符串 → `set` → 回新模型配置（热加载即时真态）。
- `PUT /api/config/credential` `{ field:'dashscope_api_key', value }` → `canEdit` 否则 503 `{error:'cred_key_missing'}`；否则加密落库 → 回 `{ field, configured:true, maskedHint }`（**绝不回明文**）。空 value 视作"保持不变"（与 isales「空 = 不变」一致）。

## 红线

- 明文密钥：绝不回前端、绝不进日志、绝不入仓 / tasks.md（只记 env 变量名与路径）。
- 主密钥缺失：凭据写被拒 + 诚实 `cred_key_missing`，模型名仍可配；**绝不静默假成功**。
- 改 LLM 客户端不破坏既有 `complete/chat/generate` 行为与注入 `fetchImpl` 的测试桩。
- 面板新路由全程 JWT；写非乐观（前端 round-trip 后渲染真态）。
