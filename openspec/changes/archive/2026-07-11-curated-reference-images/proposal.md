## Why

精选内容池已经成为发帖创作的正向素材来源，并且后台支持对单条精选笔记触发“参照洗稿”。但当前参照只包含标题、正文、话题和作者，不包含原笔记图片。小红书图文内容的表达往往强依赖首图钩子、图集顺序、构图和视觉语气；只参考文字会让洗稿草稿的配图链路仍按新正文自由生成，容易和原笔记的视觉叙事脱节。

同时，直接复用原笔记图片不可接受：它会把“参照创作”变成搬运，带来版权、平台重复、人物/水印/品牌泄露和账号风控风险。本 change 的目标是让系统能采集并保存原笔记图片引用，在洗稿时把它们作为“视觉参考”生成新图，而不是上传原图。

## What Changes

- **边端采集**：`note.detail` 增加可选 `images` 数组。边端在笔记详情作用域内提取图文轮播图片 URL、顺序和基础元数据，去重、限量、诚实置空；不抓不到就编造。
- **云端精选存储**：`curated_content` 为笔记行新增 `reference_images` JSONB 快照，保存图片顺序、原始 URL、OSS URL、捕获状态和时间。精选准入和自有收藏自动纳入都合并图片快照。
- **OSS 稳定化**：云端 best-effort 下载原始图片并转存 OSS，成功时写稳定 `ossUrl`；失败时保留 `sourceUrl` 与 `captureStatus`，不得伪造稳定图。
- **后台展示与触发**：精选页展示缩略图/详情图集。洗稿触发时默认带可用参考图，也允许运营明确选择“仅文本参照”以避开敏感图。
- **发布链视觉参考**：`referenceNote` 扩展 `images`。图片选题/提示词/生成链路可读取视觉参考，生成新图时只借构图、色彩、图集节奏和信息层级，禁止复刻原图、水印、人物脸、品牌标识和原图文字。
- **图片 provider 契约**：`ImageProvider.generate` 扩展可选 `referenceImages` 参数。支持参考图的 provider 走参考生成；不支持或参考图不可用时必须显式降级/告警，并在审计中可见，不能静默假装用了参考图。

## Capabilities

### Modified Capabilities

- `note-extraction-fidelity`: 笔记详情抽取增加图片引用上报，协议双份同步。
- `curated-inspiration-corpus`: 精选笔记可保存有界图片快照，仍按账号隔离、保留上限和 PII 姿态约束。
- `panel-curated-content`: 精选页展示图片并在行级洗稿动作中控制是否带图参照。
- `publish-pipeline`: 洗稿参照从纯文本扩展为可选视觉参考，仍禁止照抄和直接搬运。
- `publish-multi-image`: 配图生成支持可选参考图，失败/不支持时诚实降级，不伪造图。

## Impact

- **aidcp-edge**
  - `src/comm/protocol.ts`: `NoteDetailPayload.images?`。
  - `src/browse/note-extractor.ts`: 抽取详情页图片引用。
  - `src/browse/browse-session.ts`: 上报 `note.detail.images`。
  - 对应 browse/note extraction 单测与协议漂移测试。

- **aidcp-cloud**
  - `src/comm/protocol.ts`、`src/event-bus/types.ts`、`src/comm/handler.ts`: 接收并传递图片引用。
  - `src/cache/curated-content-store.ts`: `reference_images` DDL、DTO、upsert、select/list/getOne。
  - `src/server.ts`、`src/agents/curated-note-evaluator.ts`: 精选准入和自有收藏路径写入图片快照。
  - `src/storage/object-store.ts` 或新 helper: 原图 best-effort 转存 OSS。
  - `src/publish-agent/types.ts`、`publish-scheduler.ts`、`roles/image-set-planner.ts`、`roles/image-prompt-composer.ts`、`roles/image-generator.ts`、`image-provider.ts`、`wanxiang-client.ts`、`seedream-client.ts`: 参考图贯穿发布配图链路。

- **aidcp-console**
  - `src/types/api.ts`: DTO 镜像新增 `referenceImages`。
  - `src/pages/CuratedContentPage.tsx`: 列表缩略图、详情图集、洗稿触发“带图参考/仅文本参考”。
  - 对应页面测试。

## Non-goals

- 不直接上传原笔记图片作为发布图。
- 不把所有精选素材的图片自动用于普通发帖，只在人工指定参照洗稿时使用。
- 不做“相似度越高越好”的目标。目标是视觉叙事借鉴，而不是复刻。
- 不把评论类型内容强行补图片；评论行仍不支持洗稿参照。

## Risks

- **图片 URL 可用性**：小红书 CDN 链接可能过期、需防盗链或带鉴权。缓解：云端尽快转存 OSS；转存失败保持 `url_only/failed` 状态，使用时可见。
- **版权/搬运风险**：原图不可直接发布。缓解：生成新图、prompt 加反复刻护栏、审批卡提示图片参考来源。
- **PII/人脸/水印**：原图可能含人物、品牌和水印。缓解：默认只参考构图/色彩/信息层级，生成提示禁止可识别脸、水印、logo、原图文字；必要时允许运营仅文本参照。
- **协议漂移**：`note.detail` 是 edge/cloud 双份协议。缓解：同步两份 `protocol.ts`、`command-bridge` 若相关、`docs/protocol.md` 与协议漂移守护。
- **成本与存储增长**：图片转存与参考生成成本更高。缓解：仅精选行、仅前 N 张、每账号保留上限沿用精选表；默认洗稿最多取 3 张参考图。
