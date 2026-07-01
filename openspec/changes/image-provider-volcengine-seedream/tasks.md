# Tasks — image-provider-volcengine-seedream

## 1. aidcp-cloud — Seedream 客户端与图片厂商路由
- [x] 1.1 新 `src/publish-agent/seedream-client.ts`：`SeedreamClient implements ImageProvider`，走 Ark 同步 `POST {baseUrl}/images/generations`（body `{model, prompt, size, response_format:'url', watermark:false}`），解析 `data[0].url`；非 200 / 无 URL / 异常 → `{url:null,error}` 不抛；`AbortController` 单次超时（默认 60s，env `AIDCP_SEEDREAM_TIMEOUT_MS`）；`getModel` 解析器；key 复用注入 apiKey，回退 env `ARK_API_KEY`/`VOLCENGINE_API_KEY`；style 并入提示词。<!-- aidcp-cloud 1c1f8da -->
- [x] 1.2 新 `src/publish-agent/image-providers.ts`：字面 `ImageProviderId = 'dashscope' | 'volcengine'` + 显示名注册表 + `normImageProvider`（未知→dashscope、不抛）+ `RoutingImageProvider implements ImageProvider`（每次 generate 读 `getProvider()` 归一后分发；已选定厂商失败不跨厂商顶替，仅未知归一到 dashscope）。<!-- aidcp-cloud 1c1f8da -->

## 2. aidcp-cloud — 配置存储与迁移
- [x] 2.1 `src/config/model-config-store.ts`：`ModelConfigValue.imageProvider`；`MODEL_CONFIG_DEFAULTS.imageProvider='dashscope'`；自愈 `MODEL_CONFIG_ALTER_SQL` 加 `ADD COLUMN IF NOT EXISTS image_provider TEXT NOT NULL DEFAULT 'dashscope'`；reload SELECT + set INSERT/UPDATE 带上 `image_provider`。<!-- aidcp-cloud 1c1f8da -->
- [x] 2.2 新 `migrations/0025_image_provider.sql`：幂等 `ALTER TABLE model_config ADD COLUMN IF NOT EXISTS image_provider TEXT NOT NULL DEFAULT 'dashscope';`。<!-- aidcp-cloud 1c1f8da -->

## 3. aidcp-cloud — 装配与面板
- [x] 3.1 `src/server.ts`：构造 `SeedreamClient`（apiKey/baseUrl 取 `providerRuntime['volcengine']`，getModel 取 `imageModel`）；构造 `RoutingImageProvider`（getProvider 取 `getCached().imageProvider`，providers `{dashscope: wanxiangClient, volcengine: seedreamClient}`，fallback dashscope）；ImageGenerator 注入改为路由 provider。<!-- aidcp-cloud 1c1f8da -->
- [x] 3.2 `src/server.ts` panel 快照：`imageProvider` 由钉死 `'dashscope'` 改为回显 `cfg.imageProvider` + 可选图片厂商列表；`PUT /api/config/model` 组装 patch 时收 `imageProvider`（按已知图片厂商归一/校验）后 `modelConfigStore.set`。<!-- aidcp-cloud 1c1f8da -->
- [x] 3.3 `src/panel/types.ts` + `src/panel/panel-server.ts`：config 读回形状加 `imageProvider` + 可选项；PUT 解析 `imageProvider`。<!-- aidcp-cloud 1c1f8da -->

## 4. aidcp-cloud — 测试与回归
- [x] 4.1 新 `seedream-client.test.ts`：成功返 URL / 非 200 诚实 error / body error / 缺 URL 诚实 error / 缺密钥诚实 error（发请求前）/ getModel 优先。<!-- aidcp-cloud 1c1f8da -->
- [x] 4.2 新 `routing-image-provider.test.ts`：按 getProvider 分发到对应客户端 / 未知归一 dashscope / 已选厂商失败不跨厂商顶替 / 未装配诚实 error。<!-- aidcp-cloud 1c1f8da -->
- [x] 4.3 `test/panel-config.test.ts` mock 补 `imageProvider` 状态 + `imageProviders` 视图 + setModel 收 imageProvider（专测 model-config-store 往返未新增，靠 reload/set 双写覆盖 + 全量回归）。<!-- aidcp-cloud 1c1f8da -->
- [x] 4.4 回归：`npm run typecheck` 通过；`npm run test:acceptance` 27/27（AC-PUB 配图诚实红线不回归）；`npm test` 1012/1012。<!-- aidcp-cloud 1c1f8da -->

## 5. 验证与收尾
- [x] 5.1 缺省零回归核对：`image_provider` 缺省 dashscope、`imageModel` 缺省 wan2.7-image-pro → 路由归一到万相，请求与改造前一致（RoutingImageProvider 未知/缺省归一测试 + 全量回归佐证）。
- [x] 5.2 `openspec validate image-provider-volcengine-seedream --strict` 通过。
- [ ] 5.3 （可选 / 后续）console 前端图片厂商下拉；ECS 配火山 Ark key 后真机探活一次 Seedream 出图。
