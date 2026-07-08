# Tasks — rewrite-image-count-parity

> cloud-only 改动；已实装 + 测试全绿 + 集成 master + 部署 dev。
> <!-- aidcp-cloud b1fbcec landed→master; deployed dev(0be613f) 2026-07-08 -->

## 1. aidcp-cloud — 选题角色张数逻辑

- [x] 1.1 `image-set-planner.ts`：`DEFAULT_MAX_IMAGES` 3 → 9 <!-- aidcp-cloud b1fbcec -->
- [x] 1.2 `image-generator.ts`：`DEFAULT_MAX_IMAGES` 3 → 9 <!-- aidcp-cloud b1fbcec -->
- [x] 1.3 `ImageSetPlanner.execute` 增 `context`；经 `referenceImagesForGeneration` 取有效源图数 <!-- aidcp-cloud b1fbcec -->
- [x] 1.4 目标张数：有效源图 ≥1 → `clamp(len,1,maxImages)`；否则 undefined（非洗稿内容驱动）<!-- aidcp-cloud b1fbcec -->
- [x] 1.5 `buildImageSetPlanPrompt` 增 `exactCount?`（洗稿钉死张数 + 等量主题）<!-- aidcp-cloud b1fbcec -->
- [x] 1.6 `buildPlan` 增 `targetCount?`（按目标夹取 + 补齐；图 0 封面位）<!-- aidcp-cloud b1fbcec -->
- [x] 1.7 降级/默认输出维持 1 张（LLM 失败诚实不凑数）<!-- aidcp-cloud b1fbcec -->

## 2. aidcp-cloud — 测试

- [x] 2.1 image-set-planner 洗稿对齐单测（源5→5、源12→夹9、有效口径3、无源图回落、LLM失败降级1）<!-- aidcp-cloud b1fbcec -->
- [x] 2.2 prompt 固定张数措辞单测 <!-- aidcp-cloud b1fbcec -->
- [x] 2.3 非洗稿零回归（默认上限现 9）；全量绿 <!-- aidcp-cloud b1fbcec -->
- [x] 2.4 typecheck + test:acceptance(45) + 全量（本地 1597 / landed 1616）全绿 <!-- aidcp-cloud b1fbcec -->

## 3. 验证与部署

- [x] 3.1 `openspec validate rewrite-image-count-parity --strict` 通过
- [x] 3.2 cloud 走 §5 安全序列部署 dev（备份→rsync快照→restart→healthcheck 全绿）<!-- 2026-07-08 deployed dev(0be613f) -->
- [ ] 3.3 真机项已登记 backlog：源 N 张图洗稿验证产出 N 张(≤9)、图0文字卡/钩子 <!-- backlog registered; 真机待核 -->
- [x] 3.4 archive change（delta 合并进 `openspec/specs/publish-multi-image`）
