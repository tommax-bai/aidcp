## Why

系统当前用的模型（文本 Qwen / 图片万相，均走百炼 DashScope）写死在 cloud 代码里（默认文本 `qwen-turbo`、图片 `wan2.7-image-pro`），API 密钥只读 `.env`（`DASHSCOPE_API_KEY`）。运营要换模型或换密钥，只能改代码 / 改环境变量再重启，**管理后台一处都配不了**。isales 后台早有「模型与语音服务」配置页：模型名 + 各厂商密钥都能在后台填，密钥 Fernet 加密落库、掩码显示、永不回显、改 key 整段重输、重启生效。本 change 给 aidcp 后台补齐对齐 isales 的最小版「模型配置页」。

用户决策（范围基线）：**密钥也可在后台改、加密落库、重启生效**（对齐 isales，不走"密钥仍留 env"的更保守版）。

## What Changes

- **cloud / 加密凭据存储（新）**：新增进程内凭据存储，把 DashScope API 密钥经 **AES-256-GCM**（Node 内置 `crypto`，不引第三方）加密后落 PG（密文 + iv + authTag + 写时算好的掩码提示）。主加密密钥来自 env `AIDCP_CRED_KEY`，**绝不入库、绝不入仓、绝不进日志**。主密钥缺失时凭据写入被拒并诚实报因，**绝不静默假成功**；读出永不回明文，只回掩码 + 是否已配置。
- **cloud / 模型配置存储（新）**：文本/图片模型名落 PG 单行配置（缺省回退现有代码默认值）；内存镜像供 LLM 客户端**运行时按需解析模型名**（PUT 后热加载、无需重启）。
- **cloud / LLM 客户端可配置化**：Qwen 文本客户端与万相图片客户端的「模型名」改为运行时从共享配置解析（保留构造默认值与既有测试桩签名）；「API 密钥」启动时优先取解密后的库内凭据、回退 `.env`（密钥变更**重启生效**，匹配 isales v1.0，不做热换密钥）。
- **cloud / 面板配置接口（JWT 守护，非乐观）**：`GET /api/config/model`（模型名 + provider + baseUrl + 凭据 {configured, maskedHint, source} + canEditCredential）、`PUT /api/config/model`（改模型名，round-trip 回真态）、`PUT /api/config/credential`（加密存密钥，回掩码、**绝不回明文**；主密钥缺失返 503 + 诚实原因）。
- **console / 模型配置页**：「设置」页从占位空态改为真表单——模型配置区（文本/图片模型名 + 保存）+ 凭据区（API 密钥 password 输入、掩码占位显示当前、**永不回显明文、改 key 整段重输**、保存）+ provider/baseUrl 只读 + 诚实横幅（说明加密落库 + 重启生效）。写**非乐观**、文案诚实（已保存 / 已加密保存待重启 / 主密钥未配置无法保存）。
- **不做（YAGNI）**：多厂商切换（当前只接百炼一家，schema 留 provider 维度但 UI 只出 DashScope）；温度等采样参数下放 UI（规划要稳定，保持代码默认 0）；密钥热换（重启生效已够，避免热换密钥的活态一致性复杂度）；凭据轮转 / 多版本历史。

## Capabilities

### New Capabilities
- `model-provider-config`: 管理后台模型与凭据配置——模型名可配（热加载）、API 密钥加密落库可改（掩码、永不回显、重启生效）、面板接口 JWT 守护且写非乐观、主密钥缺失诚实拒绝绝不假成功。

## Impact

- **cloud（aidcp-cloud）**：新 `src/config/model-config-store.ts`（PG 单行模型配置 + 内存镜像）、新 `src/config/credential-store.ts`（AES-256-GCM 加解密 + PG 落库 + 掩码）、新 `migrations/0007_model_config.sql`（建表，幂等 `CREATE TABLE IF NOT EXISTS` 与 store 同源）；改 `src/llm/qwen.ts`、`src/publish-agent/wanxiang-client.ts`（模型名运行时解析、保留默认与桩签名）；改 `src/server.ts`（装配两个 store、解密凭据注入客户端、模型名解析器、面板 deps）；改 `src/panel/panel-server.ts`（3 个 `/api/config/*` 路由）、`src/panel/types.ts`（PanelDeps 加 modelConfig dep）。
- **console（aidcp-console）**：改 `src/pages/SettingsPage.tsx`（真配置页）、`src/api/queries.ts`（useModelConfig）、`src/types/api.ts`（ModelConfig 类型）；按需补 mutation。
- **docs / 部署**：cloud `.env` 新增 `AIDCP_CRED_KEY`（32 字节随机、base64；仅记变量名与用途，绝不记值）；`docs/handoff-*` 与 `aidcp-cloud/docs/deployment-ecs.md` 追记该 env 与重启生效语义。
- **风险面**：密钥安全红线——明文绝不回前端 / 不进日志 / 不入仓；主密钥缺失诚实降级（凭据只读、报因）。改 LLM 客户端不得破坏既有规划/选元素调用与测试桩；面板新路由仍受 JWT 守护、写非乐观。改密钥需**重启 cloud** 才生效（前端文案须诚实告知）。
