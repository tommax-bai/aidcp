# Design — image-provider-volcengine-seedream

## 现状（坐实，文件:行）
- `src/publish-agent/image-provider.ts`：`ImageProvider` 接口 = `generate(prompt, style?) => Promise<ImageResult>`；`ImageResult = { url: string|null, taskId?, error? }`。干净 DI。
- `src/publish-agent/wanxiang-client.ts`：`WanxiangClient implements ImageProvider`，写死 DashScope 异步端点（提交 + 轮询，`X-DashScope-Async`），失败返 `{url:null,error}` 不抛。
- `src/publish-agent/roles/image-generator.ts`：`ImageGeneratorRole` 依赖注入 `imageProvider: ImageProvider`，并行出图 + 每图独立超时 + 部分成功诚实（红线已在角色层，本 change 不碰）。
- `src/server.ts:491`：构造 `wanxiangClient`，`getModel: () => modelConfigStore.getCached().imageModel`；`:1168` 注入 `imageProvider: wanxiangClient`；`:1381` panel 快照 `imageProvider: 'dashscope'` 钉死。
- `src/server.ts:228-241`：启动期把每文本厂商 key 一次性载入 `providerRuntime[id] = {baseUrl, apiKey}`——**火山 key 已在 `providerRuntime['volcengine']`**（base = `https://ark.cn-beijing.volces.com/api/v3`）。
- `src/config/model-config-store.ts`：`model_config` 单行表有 `text_model` / `text_provider` / `image_model`，**无 image_provider**；有自愈 `ALTER ... ADD COLUMN IF NOT EXISTS text_provider`。
- `providers.ts`：文本厂商字面注册表（dashscope/volcengine）+ `normProvider` 归一。图片不在此。

## 决策
1. **不动 `ImageProvider` 接口 / ImageGenerator 角色**——只加第二实现 + 一个路由实现，保住配图诚实红线原封不动。
2. **Seedream 走 Ark 同步 OpenAI 形状**：`POST {arkBase}/images/generations`，body `{ model, prompt, size, response_format:'url', watermark:false }`，解析 `data[0].url`；非 200 / 无 URL / 异常 → `{url:null,error}`（诚实、不抛）。用 `AbortController` 单次超时（默认 60s，Seedream 实测 ~15s）。**无轮询**——比万相简单。
   - `style` 与万相一致并入提示词文本（Ark 基础文生图无独立 style 字段）。
   - key/base 复用 `providerRuntime['volcengine']`（与文本火山同源）；缺则回退 env `ARK_API_KEY` / `VOLCENGINE_API_KEY`。
3. **图片厂商注册表 + 路由**：新 `image-providers.ts` 字面枚举 `ImageProviderId = 'dashscope' | 'volcengine'`、`normImageProvider`（未知/脏串→dashscope）、`RoutingImageProvider`：每次 `generate` 读 `getImageProvider()` → 归一 → 从 `{dashscope: wanxiang, volcengine: seedream}` 取对应客户端分发。
   - **红线**：路由只在 provider **未知**时归一到 dashscope；**已选定厂商生图失败/缺密钥不跨厂商顶替**——由被选中客户端自己诚实返回 error（镜像文本侧「绝不跨厂商兜底」）。
4. **配置**：`model_config` 加 `image_provider TEXT NOT NULL DEFAULT 'dashscope'`（自愈 ALTER + 迁移 `0025`，与 text_provider 同法）；`ModelConfigValue.imageProvider`；reload/set 带上；`getCached().imageProvider` 供路由热加载。
5. **面板**：`GET /api/config/model` 回显 `imageProvider` 当前值与可选项（图片厂商注册表派生）；`PUT` 接受 `imageProvider`，按已知图片厂商白名单校验（未知诚实拒/归一——与 text_provider 一致，选归一以不 brick）。console 前端下拉本 change 不做（缺省 dashscope 零回归）。

## 为什么不复用文本 `TextProviderId` 注册表
图片厂商的语义与文本不同（dashscope→万相异步、volcengine→即梦同步），baseUrl 用途也不同（文本 chat vs 图片 images）。共用一张表会把两套不同的端点/客户端耦进一个 `normProvider`。**YAGNI + 清晰**：单开一份仅含 id/显示名的极薄图片厂商枚举，key/base 仍复用 `providerRuntime`（同厂商同密钥），不重复造凭据存储。

## 零回归 / 失败模式
- 缺省 `image_provider='dashscope'` + `image_model='wan2.7-image-pro'`：未配置即与改造前逐字一致。
- 配 `volcengine` 但无火山 key：SeedreamClient 首次 `generate` 诚实返回 `{url:null, error:'seedream key 缺失…'}` → ImageGenerator 那张记失败（M 少一张）→ 若 M=0 下游 executor 诚实 `failed`（不静默假成功）。**不**回落万相。
- 配 `volcengine` 但 `image_model` 仍填成万相 ID：请求发往 Ark、Ark 报模型无效 → 诚实 error。面板保存时前端应成对设 provider+model（后端不强绑，避免 brick）。
