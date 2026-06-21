# Tasks — console-model-provider-config

## 1. aidcp-cloud — 加密凭据 + 模型配置存储

- [x] 1.1 `migrations/0007_model_config.sql`：幂等建 `model_config`（单行 id=1：text_model/image_model/updated_at/updated_by）与 `provider_credentials`（provider+field 唯一：ciphertext/masked_hint/updated_at/updated_by）<!-- aidcp-cloud fee7e88 -->
- [x] 1.2 `src/config/credential-store.ts`：AES-256-GCM 加解密（Node 内置 crypto，主密钥读 `AIDCP_CRED_KEY`）+ PG 落库 + 掩码；`canEdit()` / `getStored()` / `setSecret()` / `getSecretForRuntime()`；主密钥缺失 `setSecret` 抛 CredentialKeyMissingError、明文绝不落库/日志<!-- aidcp-cloud fee7e88 -->
- [x] 1.3 `src/config/model-config-store.ts`：PG 单行模型配置 + 内存镜像；`init()` / `getCached()`（同步）/ `get()` / `set(patch,by)`（写库+刷新镜像，热加载）；缺行回退代码默认（qwen-turbo / wan2.7-image-pro）<!-- aidcp-cloud fee7e88 -->
- [x] 1.4 单测：crypto 往返 + iv 随机 + authTag 防篡改、掩码格式、主密钥缺失拒绝；model-config 默认回退 + set 后 getCached 即时变更<!-- aidcp-cloud fee7e88 test/credential-store.test.ts + test/model-config-store.test.ts，13 pass -->

## 2. aidcp-cloud — LLM 客户端可配置化（不破坏既有行为/桩）

- [x] 2.1 `src/llm/qwen.ts`：加可选 `getModel?: () => string`，`chat()` 用 `this.getModel?.() ?? this.model`；默认与 `fetchImpl` 注入签名不变；导出 DEFAULT_BASE_URL<!-- aidcp-cloud fee7e88 -->
- [x] 2.2 `src/publish-agent/wanxiang-client.ts`：同上，图片模型名运行时解析<!-- aidcp-cloud fee7e88 -->
- [x] 2.3 既有 llm/wanxiang 单测仍绿（行为不变护栏）<!-- aidcp-cloud fee7e88 wanxiang-client.test 13 pass；full suite 295/295 -->

## 3. aidcp-cloud — 装配 + 面板接口

- [x] 3.1 `src/server.ts`：装配 modelConfigStore + credentialStore（init）；QwenClient/WanxiangClient 传 `getModel` 解析器 + 启动期解密凭据注入 apiKey（无则回退 env）；面板 deps 注入 modelConfig 外观（buildModelConfigView 共用）<!-- aidcp-cloud fee7e88 -->
- [x] 3.2 `src/panel/types.ts`：PanelDeps 加可选 `modelConfig`（getView / setModel / setCredential）+ ModelConfigView / SetCredentialResult 类型<!-- aidcp-cloud fee7e88 -->
- [x] 3.3 `src/panel/panel-server.ts`：`GET/PUT /api/config/model`、`PUT /api/config/credential`（JWT 守护、非乐观、明文绝不回、主密钥缺失 503 cred_key_missing、未注入 503 model_config_unavailable）<!-- aidcp-cloud fee7e88 -->
- [x] 3.4 面板路由单测：GET 形状（无明文）、PUT model 回真态 + 全空 400、PUT credential 主密钥缺失 503 / 有则回掩码 / 未知 field 400、未鉴权 401<!-- aidcp-cloud fee7e88 test/panel-config.test.ts -->
- [x] 3.5 回归：`npm run typecheck` + 全量 `npm test`（295/295）+ `npm run test:acceptance`（AC-PROTO/AC-PUB/AC-RISK 红线 18/18 全过）<!-- aidcp-cloud fee7e88 -->

## 4. aidcp-console — 模型配置页

- [x] 4.1 `src/types/api.ts`：`ModelConfig` + `ModelConfigCredential` 类型<!-- aidcp-console 30af0b2 -->
- [x] 4.2 `src/api/queries.ts`：`useModelConfig()` GET；`src/api/client.ts` 加 `apiPut`<!-- aidcp-console 30af0b2 -->
- [x] 4.3 `src/pages/SettingsPage.tsx`：真表单——模型配置区（文本/图片模型名 + 保存，非乐观）+ 凭据区（password、掩码状态、永不回显、改 key 整段重输、保存）+ provider/baseUrl 只读 + 诚实横幅；canEditCredential=false 时禁用密钥编辑并说明<!-- aidcp-console 30af0b2 -->
- [x] 4.4 `npm run typecheck` + `npm test` + `npm run build` 绿<!-- aidcp-console 30af0b2 -->

## 5. docs / 部署文档

- [x] 5.1 cloud 部署文档追记 `AIDCP_CRED_KEY`（用途 + `openssl rand -base64 32` 生成法；**绝不记值**）与「改密钥重启生效 / 改模型名热加载」语义<!-- aidcp-cloud fee7e88 docs/deployment-ecs.md（无 .env.example，沿用部署文档惯例） -->
- [x] 5.2 `openspec validate console-model-provider-config --strict` 通过

## 6. 部署（显式动作，单独执行 —— 待用户确认时机）

- [ ] 6.1 ECS `.env` 写入 `AIDCP_CRED_KEY`（`openssl rand -base64 32` 生成；不记值，仅记已配置）
- [ ] 6.2 cloud 安全序列部署（备份→rsync→restart→healthcheck→失败回滚，绝不碰 isales）+ console rebuild & rsync dist
- [ ] 6.3 线上验证：配置页可读、改模型名即时生效、改密钥重启后生效；明文不外泄
