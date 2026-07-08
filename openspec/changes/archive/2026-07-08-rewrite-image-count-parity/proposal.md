## Why

洗稿帖的配图张数与源稿严重脱节：源笔记 9 张图、洗稿后只出 3 张。根因两条——① 配图张数由选题角色读**洗稿后的正文**让 LLM 自己定，**完全不看源稿图片数**；② 上限默认封在 3（`AIDCP_PUBLISH_MAX_IMAGES` 未设时的代码默认）。运营期望洗稿产出与源稿「图片体量对齐」，让洗稿帖看起来和原帖一样丰富。

## What Changes

- **默认张数上限 3 → 9**（`DEFAULT_MAX_IMAGES`，硬上限仍 9=小红书平台上界；`AIDCP_PUBLISH_MAX_IMAGES` env 覆盖照旧）。
- **洗稿帖张数对齐源稿**：触发含源参照笔记且其**有效图**（`ossUrl ?? sourceUrl` 可用）≥1 张时，配图张数 = `clamp(有效源图数, 1, 上限)`；选题角色让 LLM 产等量主题、不足由系统补齐至该数（图 0 恒封面/钩子位）。
- **非洗稿 / 无有效源图**：维持现状——LLM 读正文自定张数并 `clamp(1, 上限)`。
- 选题角色改为可读取管线上下文里的源参照笔记（现只 watch `createdContent`）；决策/执行解耦红线不变（只产选题、不调图源、不产万相 prompt）。

## Capabilities

### New Capabilities
<!-- 无新增 capability。 -->

### Modified Capabilities
- `publish-multi-image`: 「配图张数由正文决定并夹在安全范围」要求扩展——默认上限提到 9；**洗稿帖张数改为对齐源稿有效图数**（≤上限），非洗稿维持内容驱动。

## Impact

- **aidcp-cloud**：
  - `src/publish-agent/roles/image-set-planner.ts`：`DEFAULT_MAX_IMAGES` 3→9；`execute` 增读管线上下文的源参照笔记有效图数（经 `referenceImagesForGeneration`），洗稿时以其为目标张数；`buildPlan` 按目标数夹取/补齐主题。
  - `src/publish-agent/roles/image-generator.ts`：`DEFAULT_MAX_IMAGES` 3→9（仅用于角色总闸余量估算，保持与选题一致）。
  - `src/publish-agent/prompts.ts`：`buildImageSetPlanPrompt` 增可选「固定张数」入参（洗稿时把张数钉死、要求等量主题）。
- **不改**：协议 / 风控 / 发布下发上传链 / 封面形态（文字卡仍只作用于图 0）；无 DB 迁移；无 env 强制项（默认即 9，`AIDCP_PUBLISH_MAX_IMAGES` 仍可覆盖）。
- **代价**：洗稿帖图变多 → Seedream 出图更慢更贵（dev `AIDCP_PUBLISH_IMAGE_CONCURRENCY=1` 串行生，源 9 张要串行等 9 次）。
- **部署**：cloud 纯代码落 dev。
