## Why

配图执行当前**结构性钉死**在阿里百炼万相：唯一的图片客户端 `WanxiangClient` 写死 DashScope 异步端点、不经任何 provider 路由（`providers.ts` 只管文本厂商，注释明言"图片走 DashScope 独立客户端、不在此注册"）。但业界实测（本仓 2026-07 调研）显示，对小红书"大标题 + 短标签 + 强美感"的封面、尤其**多图笔记的组图一致性**，字节即梦 Seedream（经火山方舟 Ark）单价约为万相一半、且是 **OpenAI 兼容同步**接口（比万相的异步轮询还简单）。文本侧已支持多厂商（dashscope/volcengine），图片侧却单供应商——本 change 把图片也做成**可选厂商**，让运营能按封面风格在万相 / 即梦间切换，且不需改代码即热加载。

## What Changes

- **新增第二个图片厂商 Seedream（即梦，经火山方舟 Ark）**：新 `SeedreamClient implements ImageProvider`，走 Ark **OpenAI 兼容同步**端点 `POST {arkBase}/images/generations`（单次请求直接返图 URL，无异步轮询），复用启动期已载入的火山密钥（`providerRuntime['volcengine']`，与文本火山同 key 同 base）。失败恒返回 `{ url: null, error }`、绝不抛、绝不伪造 URL（延续配图诚实红线）。
- **图片厂商按配置路由**：新增全局 `image_provider`（`dashscope` 万相 / `volcengine` 即梦-Seedream，缺省 `dashscope` 零回归）落 `model_config` 单行表；新 `RoutingImageProvider implements ImageProvider` 每次生成按当前 `image_provider` 分发到对应客户端，热加载生效。`imageModel` 字符串按选中图片厂商解释（万相填 `wan2.7-image-pro`，即梦填 `doubao-seedream-4-5-251128` 等）。
- **图片厂商独立于文本厂商**：切图片厂商 MUST NOT 影响文本调用，反之亦然（两条解析链互不继承）。
- **缺密钥诚实失败、绝不跨厂商兜底**：配置为 `volcengine` 但火山密钥不可用时，`SeedreamClient` 诚实返回错误、`RoutingImageProvider` MUST NOT 静默改用万相顶替（镜像文本侧同名红线）。路由的 `fallback` 仅用于把**未知/脏串** provider 归一到 `dashscope`，绝不用于把"已选定但生图失败/缺密钥"的厂商偷换掉。
- **后台可配**：`model_config` 加 `image_provider` 列（幂等自愈 ALTER + 迁移 `0025`）；`GET /api/config/model` 回显当前图片厂商与可选项、`PUT /api/config/model` 接受 `imageProvider` 并按已知图片厂商白名单校验后写入。

## Capabilities

### Modified Capabilities
- `model-provider-config`：「图片模型名钉死 DashScope」升级为「图片厂商可配（dashscope 万相 / volcengine 即梦-Seedream）、独立于文本厂商、按配置热加载路由」；新增「图片厂商按胜出配置取地址与密钥、缺密钥诚实失败绝不跨厂商兜底」要求（镜像文本侧）。

## Impact

- **代码（仅 aidcp-cloud）**：新增 `src/publish-agent/seedream-client.ts`、`src/publish-agent/image-providers.ts`（图片厂商字面注册表 + `RoutingImageProvider` + `normImageProvider`）；改 `src/config/model-config-store.ts`（`imageProvider` 字段 + 自愈 ALTER + reload/set）；新迁移 `migrations/0025_image_provider.sql`；改 `src/server.ts`（装配 SeedreamClient + RoutingImageProvider、注入 ImageGenerator、panel 取消 imageProvider 钉死、PUT 收 imageProvider）；改 `src/panel/types.ts` + `src/panel/panel-server.ts`（config 读写带 imageProvider）。
- **协议 / 边缘 / console 前端**：协议零改动、边缘零改动。console 前端图片厂商下拉为**后续可选**前端工作（本 change 只做后端契约与路由，console 未接前不影响：缺省 dashscope 全链路零回归）。
- **测试**：新增 `seedream-client` 与 `routing-image-provider` 单测（成功 / 非 200 / 缺 URL / 缺密钥诚实失败 / 路由选择 / 不跨厂商兜底）；`model-config-store` imageProvider 往返；AC-PUB 配图诚实红线不回归（仅换 provider，M/K 语义不变）。
- **风控 / 配额**：零改动（图片厂商切换不改发布配额、不改张数上界、不改诚实语义）。
- **零回归基准**：`image_provider` 缺省 `dashscope`、`imageModel` 缺省 `wan2.7-image-pro`，未配置时行为与改造前逐字一致。
