# Tasks — model-config-volcengine-provider

> 红线贯穿全程：诚实失败（缺 key 发请求前抛、不跨厂商兜底）、零回归（不配火山时 DashScope 路径逐字不变、`getModel` 签名不动、图片不动）、token 与 ok 解耦、明文密钥不外泄、绝不 brick、协议不漂移。
> 实装：cloud `f1e0883`、console `73ca4c5`。验证：cloud test 733/733、acceptance 26/26、my-file tsc 干净（仅并发 publish-multi-image WIP 报错，非本 change）；console tsc + vite build 绿。

## 0. 前置坐实

- [x] 0.1 apply 时重新 `ls aidcp-cloud/migrations` 确认迁移号（0018 实测未被占用） <!-- aidcp-cloud f1e0883 -->
- [x] 0.2 火山方舟密钥来源：db `provider_credentials('volcengine','volcengine_api_key')` 优先，env 回退 `ARK_API_KEY` / `VOLCENGINE_API_KEY`；区域端点 env `ARK_BASE_URL` <!-- aidcp-cloud f1e0883 src/llm/providers.ts -->

## 1. aidcp-cloud — provider 注册表 + 文本出口泛化

- [x] 1.1 `src/llm/providers.ts`：`TextProviderMeta` + `TEXT_PROVIDERS` 字面常量 + 白名单派生(`isAllowedCredential`) + `normProvider` + `resolveProviderBaseUrl`/`resolveProviderEnvKey` <!-- aidcp-cloud f1e0883 -->
- [x] 1.2 `src/llm/qwen.ts`：`LlmCallOpts.provider`；`QwenClientOptions.getProvider`/`providerRuntime`；`onCall` 加 `provider`；`ProviderKeyMissingError` <!-- aidcp-cloud f1e0883 -->
- [x] 1.3 `qwen.ts` `chat()`：按 provider 解析 baseUrl+key；缺 key 发 fetch 前抛、绝不跨厂商兜底；未注入走构造默认（零回归）；日志带 provider <!-- aidcp-cloud f1e0883 -->
- [x] 1.4 单测 `test/qwen-provider.test.ts`：缺 key 抛错且未发 fetch / provider 路由命中正确 host / 未注入零回归 / 注册表+白名单+baseUrl 覆盖 <!-- aidcp-cloud f1e0883 -->

## 2. aidcp-cloud — 数据模型（三列 + 自愈 init + 迁移）

- [x] 2.1 `migrations/0018_text_provider.sql`：三表 `ADD COLUMN IF NOT EXISTS` + 回填 model 非空行 dashscope（幂等） <!-- aidcp-cloud f1e0883 -->
- [x] 2.2 `model-config-store.ts`：`textProvider` + 自愈 ALTER + reload/get/set 带 textProvider <!-- aidcp-cloud f1e0883 -->
- [x] 2.3 `role-config-store.ts`：`provider` + 自愈 ALTER + `set()` (model,provider) 原子 + `getForRole` 返 provider <!-- aidcp-cloud f1e0883 -->
- [x] 2.4 `category-config-store.ts`：同 2.3（`set(categoryId, model, provider, by)`） <!-- aidcp-cloud f1e0883 -->
- [x] 2.5 单测：model/role store 加列读写 + 原子写 + 老行(provider NULL)读出（`model-config-store.test.ts` / `role-config-store.test.ts`） <!-- aidcp-cloud f1e0883 -->

## 3. aidcp-cloud — server 接线（解析器 + runtime 映射 + 探活）

- [x] 3.1 启动期构建 `providerRuntime` 静态映射（`getSecretForRuntime ?? env`；dashscope 项 == 现有 key+baseUrl 零回归） <!-- aidcp-cloud f1e0883 -->
- [x] 3.2 `resolveSelection(role)→{provider,model}` 四层同行解析 + `normProvider` 归一；`getModel`/`getProvider` 同源薄视图；温度独立 <!-- aidcp-cloud f1e0883 -->
- [x] 3.3 `new QwenClient` 注入 `getProvider`+`providerRuntime`；日志/记账带 provider <!-- aidcp-cloud f1e0883 -->
- [x] 3.4 `probeModel(provider, model)`：路由到该厂商；key 缺失映射 `provider_key_missing`、模型不可用映射 `model_invalid` <!-- aidcp-cloud f1e0883 -->
- [x] 3.5 图片：`WanxiangClient` 仍独立 dashscope key、不经 providerRuntime；`textProvider=volcengine` 时图片零回归 <!-- aidcp-cloud f1e0883 dashscopeApiKey 仍载入 -->
- [x] 3.6 facade 单测覆盖按 provider 探活 + provider_key_missing + 未知 provider 归一 + effectiveProvider（`role/category-config-facade.test.ts`） <!-- aidcp-cloud f1e0883 -->

## 4. aidcp-cloud — 面板接口（model / credential / roles / categories）

- [x] 4.1 `panel/types.ts`：`ModelConfigView` per-provider；`setModel` 入参加 `textProvider` + `SetModelResult`；`setCredential(provider,field,value)`；role/category 视图加 `effectiveProvider`、patch 加 `provider` <!-- aidcp-cloud f1e0883 -->
- [x] 4.2 `panel/panel-server.ts`：model PUT 接 `textProvider`；credential PUT 接 `{provider,field,value}` + 白名单 `isAllowedCredential`；roles/categories 接 provider patch <!-- aidcp-cloud f1e0883 -->
- [x] 4.3 `server.ts` facade：`buildModelConfigView` per-provider；`setModel` 带 textProvider 探活后写；`setCredential` per-provider；role/category facade `effectiveProvider` 同址 + 喂 probe <!-- aidcp-cloud f1e0883 -->
- [x] 4.4 面板单测：未知 (provider,field) 被拒 + 缺主密钥 503 + 视图 per-provider 形状（`panel-config.test.ts`） <!-- aidcp-cloud f1e0883 -->

## 5. aidcp-console — 前端

- [x] 5.1 `types/api.ts`：`ModelConfig` per-provider；角色/分类类型加 effectiveProvider <!-- aidcp-console 73ca4c5 -->
- [x] 5.2 `api/queries.ts`：`useModelConfig` 适配新形状（仅类型，无码改；RolesPage 复用其取 providers） <!-- aidcp-console 73ca4c5 -->
- [x] 5.3 `SettingsPage.tsx`：全局文本厂商下拉 + 各厂商 key 分输入（掩码/不回显/保存后提示重启）；imageModel 维持 DashScope <!-- aidcp-console 73ca4c5 -->
- [x] 5.4 `RolesPage.tsx` + 分类页：模型名旁加 provider 下拉；保存时 provider 与 model 同发；表内 provider 短标签 <!-- aidcp-console 73ca4c5 -->
- [x] 5.5 `npm run typecheck` + `npm run build` 绿 <!-- aidcp-console 73ca4c5 -->

## 6. 验证（中控触发，落 sub-repo 执行）

- [x] 6.1 cloud：`test:acceptance` 26/26 → `npm test` 733/733；my-file tsc 干净（并发 publish-multi-image WIP 报错非本 change，未触碰） <!-- aidcp-cloud f1e0883 -->
- [x] 6.2 console：`tsc --noEmit` 干净 + `npm run build` 绿 <!-- aidcp-console 73ca4c5 -->
- [x] 6.3 `openspec validate model-config-volcengine-provider --strict` 通过 <!-- aidcp 本仓 -->

## 7. 部署 + 真机

- [x] 7.1 已部署 ECS（06-26）：clean-master worktree(f1e0883, typecheck 0 err) 全量备份(cloud.bak.20260626-100621 + .env.bak) → `ARK_API_KEY` 加 `/opt/aidcp/cloud/.env`(server 侧, 未入仓) → rsync src+migrations → restart → healthcheck 全绿(active/8787/飞书长连接/PG select1/无错)。**连带上线另一会话已提交的 session-limits a015253**(用户放行)。console 73ca4c5 dist 部署 8088(HTTP200, isales 未碰) <!-- aidcp-cloud f1e0883 / console 73ca4c5 — 2026-06-26 deployed -->
- [x] 7.2 部署后 grep 实测：providers.ts/migration0018/session-config-facade 落地、qwen/server/panel 含 provider 码；自愈 ALTER 实测三表 provider 列已建(count 不报错)；model_config 空=系统仍 dashscope(零回归), 火山为休眠能力 <!-- 06-26 deployed -->
- [x] 7.3 真机：**已切全局文本厂商=火山 + 模型 `doubao-seed-character-260628`（06-26, LIVE）**，经部署系统 4/4 探活 ok=true（`[llm] provider=volcengine model=doubao-seed-character-260628 ms≈400-700 ok=true tokens=…`），token 记账正常、图片仍走万相。**火山 key 已只存加密 DB（env 明文已删）**，运行时解密加载实测通。**模型选型坑**：`doubao-1-5-pro-32k-250115` 从该 ECS 出去成功率仅 ~25%（间歇超时，TCP/TLS/ICMP 全正常、纯火山/跨云链路侧、非代码/密钥）；`doubao-seed-character-260628` 则 5/5 快（~0.2s），故选它。注意 seed-character 是角色/对话取向模型，分析类角色质量需观察、必要时按角色覆盖回 Qwen
