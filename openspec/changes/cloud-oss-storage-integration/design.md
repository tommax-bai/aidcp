## Context

发帖配图现状链路(已坐实 file:line):图片生成角色 `ImageGeneratorRole` 对每条图片指令调 provider 客户端(`wanxiang-client` / `seedream-client`),各返回 `{ url }`(provider 临时链);角色在 `generateOne`(`src/publish-agent/roles/image-generator.ts:106-123`)收集成 `imageUrls: string[]`,经 `CoverSelector` → `ContentAssembler` 纯透传,最终由 `publish-log-store.ts:165-189` 写入 `publish_log.image_url`(封面)/ `images TEXT[]`(正文图);派发时 `command-sequencer.ts:119-120` 逐张 emit `upload_image{imageUrl}`,边缘自己 fetch 字节上传小红书。存的确是 provider 临时 URL 字符串(非 base64、非本地路径),约 24h 过期——这是过期掉图的根因。

约束:① cloud 只跑在 ECS、本地不起 cloud,故 OSS 客户端必须能脱网单测(照 `wanxiang-client.ts:82-84` 的 `fetchImpl` 注入范式);② 加密凭据库 `credential-store.ts` 已有 `getSecretForRuntime(provider,field)`(:154)/`setSecret`(:133),表 `provider_credentials` 是通用 `(provider,field)` 结构(:24-34);③ 系统红线「绝不静默假成功」+ 现有「真实张数 M=K」诚实语义(`image-generator.ts:85-88`)必须沿用;④ 用户已明确安全等级不高(主账号 AK、不做子账号),但明文仍不进仓/日志。

## Goals / Non-Goals

**Goals:**
- 云端一个**可复用**的对象上传出口:字节 + 键 → 稳定公网 URL,供未来任意图片/文件上传复用。
- 首个消费者:配图在生成后转存 OSS,`publish_log` 存 OSS 稳定链接,根治过期掉图。
- 边缘契约、下游透传、M=K 诚实语义**全部不变**。
- 脱网可单测(注入假 fetch / 假 store)。

**Non-Goals:**
- 不做安装包分发(单独 change,不经云端)。
- 不做私有/签名 URL(配图选公读永久链接)。
- 不回迁存量旧行(仅新行走 OSS)。
- 不强制做 console 配 OSS 密钥的网页入口(day-1 用 env/SQL)。
- 不改图片**生成**逻辑(prompt/选题/风格),只在生成结果之后加转存。

## Decisions

**D1. Node SDK 用 `ali-oss@^6.x`,开 V4 签名。**
官方 Node 文档推荐 `ali-oss`(无官方 Node v2 SDK);客户端 `authorizationV4: true`。上传公读对象、返回稳定公网 URL,不需运行时签名。备选(自己拼 REST + 签名)被否——重复造轮子。

**D2. 转存插在图片生成角色的 `generateOne`,逐张转存,失败即该张诚实落空。**
最佳缝 = `src/publish-agent/roles/image-generator.ts:106-123` 的 `generateOne`,在 `return res.url ?? null`(:115)前把单张 provider URL 抓字节 PUT 到 OSS、换成 OSS URL;OSS 失败即返回 `null`,**天然复用现有「失败那张不进数组、M=K 诚实计数」语义**(:85-88),也落进现有 per-image 超时/并发预算内。备选(批量在 :83 之后转存)可行但失败粒度粗;备选(在 executor/落库层转存)离生成远、要多穿一层透传契约,被否。给 `ImageGeneratorDeps`(:28-39)加**可选** `ossUploader?`——未注入时行为与今天完全一致(零回归),注入后走转存。构造点 `server.ts:1277-1283`。

**D3. OSS 凭据照抄 DASHSCOPE「库内优先、回退 env」,不改 schema。**
启动期(`server.ts` 内,对齐 :247-250):
`accessKeyId = getSecretForRuntime('oss','access_key_id') ?? env.OSS_ACCESS_KEY_ID`;secret 同理;`region`/`bucket`/`endpoint` 为非敏感,可走 env(`OSS_REGION=oss-cn-beijing`、`OSS_BUCKET=aidcp`)或一并落库。表通用 `(provider,field)`,加 `provider='oss'` **不改 schema**。console 网页配密钥需放宽 `isAllowedCredential`(`providers.ts:66-68`)——列为**可选**增量,day-1 用 env 或直接 SQL 写 `provider_credentials` 最省事。明文仅启动期构造客户端用,绝不日志化、绝不回前端。

**D4. 配图设公读 + 永久链接,不签名。**
用户确认配图本就要公开发到小红书。上传对象 ACL 公读,`publish_log` 直接存 `https://aidcp.oss-cn-beijing.aliyuncs.com/<key>`。边缘 `upload_image{imageUrl}` 收到的仍是可 fetch 的 URL,**零改动**。因永久有效,彻底消除「审批超 TTL → 死链」,也不需派发时签名。备选(私有 + 派发时签名 URL)更安全但更复杂,鉴于用户明确不要高安全 + 图本就公开,不采用。

**D5. 对象键布局 `publish/<accountId>/<recordId>/<seq>.<ext>`。**
按账号 + 记录分层,便于排查与将来按记录清理;`<ext>` 从字节 magic-byte 或 provider content-type 判定(jpg/png/webp)。

**D6. 上传走内网 endpoint(若 ECS 同区),URL 用公网 endpoint。**
桶在 `oss-cn-beijing`;cloud 跑在 ECS,**若** ECS 同在 `cn-beijing`,上传用 `oss-cn-beijing-internal.aliyuncs.com`(免流量费 + 更快),但存库/发边缘的 URL 用公网 `oss-cn-beijing.aliyuncs.com`。ECS 实际 region 在部署前 SSH 核实;非同区则上传也用公网 endpoint 兜底。

**D7. 可注入接缝:`ObjectStore` 接口 + `fetchImpl`。**
定义 `ObjectStore { put(key, bytes, {contentType}): Promise<{ url }> }`,OSS 实现内部持 `ali-oss` client;抓 provider 字节用注入的 `fetchImpl?: typeof fetch`(默认 `globalThis.fetch`,照 `wanxiang-client.ts:82-84`)。本地单测注入内存假 store + 假 fetch,脱网可跑。这与现有 `ImageProvider`/`RoutingImageProvider` 注入范式同构。

**D8. 向后兼容:仅新行走 OSS,不回迁。**
存量 `publish_log` 行的 provider URL 短期仍可 fetch;不做批量回迁。派发路径无需区分(都是可 fetch 的 URL 字符串)。

## Risks / Trade-offs

- **[OSS PUT 失败 → 掉这一张图]** → 复用 M=K 诚实语义:该张 `null`、不进数组、真实张数如实,**绝不伪造 URL、绝不假成功**;记 warning。未注入 `ossUploader` 时行为同今天(零回归)。是否在 PUT 失败时回退保留 provider URL(保住图但会过期)= 开放取舍,默认按诚实落空处理(见 Open Questions)。
- **[转存新增下载 + PUT 延迟/失败面]** → 逐张转存落在现有 per-image 超时/并发预算内,超时即该张诚实落空;遵守单次模型/网络调用 time-box 纪律,不拖垮发布链。
- **[主账号 AK 泄漏面]** → 用户已知并接受(安全等级不高);仍存加密库(AES-GCM,非明文)+ env 回退,明文绝不进仓/日志/commit。
- **[公读桶枚举]** → 配图本就要公开,可接受;键含 accountId/recordId 但无敏感值。
- **[内网 endpoint 用错(ECS 非 cn-beijing)]** → 部署前 SSH 核 ECS region;非同区则上传也用公网 endpoint,功能不受影响、仅走公网流量。
- **[同机 isales]** → 本 change 仅动 cloud 代码 + 新建/读 OSS 资源,不碰 ECS 上 isales 的服务/目录/端口。

## Migration Plan

1. cloud 加 `ali-oss` 依赖;实现 `ObjectStore` + OSS 实现(注入 `fetchImpl`);启动期加载 OSS 凭据(库内 `??` env)。
2. `image-generator` 注入 `ossUploader`,`generateOne` 逐张转存 + 失败诚实落空;补单测(假 store/假 fetch)+ acceptance(转存失败不假成功)。
3. `npm run test:acceptance` → 全量 `npm test` → `npm run typecheck` 全绿(承回归纪律)。
4. 部署 ECS(承安全序列:先备份 → rsync → restart → healthcheck);在 ECS 设 OSS 凭据(env 或 SQL 写 `provider_credentials`);SSH 核 ECS region 定内/公网 endpoint。
5. 真机发一帖,验证配图落 OSS(`publish_log` 存的是 `aidcp.oss-cn-beijing` URL)、边缘从 OSS 下载并上传成功。
- **回滚**:不注入 `ossUploader`(或关开关)→ 立即回退到 provider URL 路径,零数据迁移。

## Open Questions

- OSS PUT 失败时:诚实落空该张(默认)还是回退保留 provider URL(保图但会过期)?倾向默认诚实落空 + warning,保持语义单一。
- 对象键是否用 accountId/recordId 明文,还是用不可枚举的随机键?鉴于安全等级不高,先用可读键。
- 旧配图对象的保留/清理策略(留存还是设 OSS 生命周期规则按时清)?
- 是否本次就放宽 `isAllowedCredential` 让 console 能配 OSS 密钥,还是先 env/SQL、后续再补网页入口?倾向先 env/SQL。
