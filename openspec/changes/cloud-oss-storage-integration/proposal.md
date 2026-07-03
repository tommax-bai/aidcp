## Why

aidcp 需要一个可复用的对象存储后端:系统在运行时要上传图片/文件时,往阿里云 OSS 存、拿回一个稳定链接。第一个、也是最迫切的用处是**发帖生成的配图**——当前 `publish_log.image_url` / `images` 存的是文生图厂商(通义万相 / 即梦 Seedream)返回的**临时 URL(约 24h 过期)**,字节本身无任何持久化。当发帖走人工审批、审批延迟超过 provider TTL 时,边缘去下载已是死链 → 笔记以更少/无图发出(该失败已被边缘防御性写成诚实的 `image_fetch_failed`,证明痛是真的)。用户已开通阿里云 OSS(桶 `aidcp`,华北2·北京 `oss-cn-beijing`),希望系统把 OSS 集成进来,把生成的配图转存到 OSS、以稳定公读链接持久化,根治过期掉图,并为后续「系统上传图片/文件」提供统一出口。

## What Changes

- **新增** 云端可复用的 OSS 对象上传能力(基于 Node SDK `ali-oss`):给一段字节 + 对象键,上传到桶 `aidcp` 并返回稳定公网 URL。定义为可注入接口(`ObjectStore`),供未来任意「上传图片/文件」场景复用,首个消费者是配图。
- **新增** 配图转存:在**图片生成角色**内、图生成成功之后,把每张 provider 临时 URL 的字节抓下来 PUT 到 OSS(公读),把 `publish_log` 里持久化的 URL 换成 OSS 稳定 URL。下游(选封面 / 组装 / 落库 / 下发边缘)全程只传 URL 字符串,**零改动**;边缘 `upload_image{imageUrl}` 契约不变,**边缘侧零感知**。
- **新增** OSS 凭据加载:AccessKey/Secret + region + bucket 从现有加密凭据库读取(`provider='oss'`),回退环境变量,**照抄现有 DASHSCOPE 密钥的加载范式**;凭据库表是通用 `(provider, field)` 结构,**不改 schema**。明文仅启动期用于构造客户端,**绝不日志化、绝不回前端**。
- **红线** OSS 转存失败诚实降级:某张 PUT 失败即该张诚实落空(复用现有「失败那张不进数组、真实张数 M=K」语义),**绝不伪造 OSS URL、绝不假成功**。
- **决策** 配图设**公读、永久链接**(用户确认配图本就要公开发到小红书):不用签名 URL、不到期换新,最省事也照样根治过期。
- **不在本次范围**:安装包分发上 OSS(单独 change `edge-installer-oss-distribution`,走人手动上传 + 前端下载链接,不经云端);私有/签名 URL(配图选公读);存量旧行的回迁(仅新行走 OSS);console 配 OSS 密钥的网页入口(可选增量,day-1 用 env/SQL)。

## Capabilities

### New Capabilities
- `cloud-oss-storage`: 云端**对象存储集成**能力——可复用的 OSS 上传出口(字节→稳定公网 URL)、凭据从加密库读取 + env 回退、可注入测试接缝;以「发帖生成配图转存到 OSS 并以稳定链接持久化 + 失败诚实降级」为首个落地消费者;保持边缘图片下发契约不变。

### Modified Capabilities
<!-- 无:配图转存是实现层接线,不改任何现有 spec 的 requirement 语义(publish_log 写入形状、边缘契约、M=K 诚实语义均沿用)。 -->

## Impact

- **aidcp-cloud**:
  - 依赖:新增 `ali-oss`(^6.x)。
  - 新增 `ObjectStore` 接口 + OSS 实现(注入 `fetchImpl`,照 `wanxiang-client`/`seedream-client` 范式)。
  - `src/config` / `src/server.ts`:启动期读 OSS 凭据(`getSecretForRuntime('oss', …) ?? env`,对齐 `server.ts:247-250` 的 DASHSCOPE 写法)。
  - `src/publish-agent/roles/image-generator.ts`:给 `ImageGeneratorDeps` 加可选 `ossUploader`,在 `generateOne`(:106-123)返回前逐张转存;构造点 `server.ts:1277-1283`。
  - 测试:OSS 客户端用注入 `fetchImpl` 脱网单测;acceptance 守「转存失败不假成功」。
- **aidcp-console(可选)**:若要网页配 OSS 密钥,需放宽 `isAllowedCredential`(`src/llm/providers.ts:66-68`)加 OSS 允许字段;否则不动。
- **基础设施 / 部署**:桶 `aidcp`(`oss-cn-beijing`,配图对象公读);在 ECS 设 OSS 凭据(env 或直接写 `provider_credentials`);若 ECS 同在 `cn-beijing`,上传可用内网 endpoint(免流量费、更快),但存/发的 URL 用公网 endpoint。**绝不碰同机 isales**。
- **安全**:按用户决定,安全等级不高——用主账号 AK、存加密库(非明文)、不折腾子账号;但仍守「明文不进仓/日志/commit」。
