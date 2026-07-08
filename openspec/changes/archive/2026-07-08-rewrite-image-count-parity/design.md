## Context

配图张数在 `ImageSetPlanner`（`image-set-planner.ts`）决定：它 watch `createdContent`、把洗稿正文喂给 LLM，LLM 回 `{imageCount, themes}`，`buildPlan` 把张数 `clamp(1, maxImages)`、主题裁/补到该数。`maxImages` 缺省读 `AIDCP_PUBLISH_MAX_IMAGES`，未设 → 代码默认 **3**（硬顶 9）。源参照笔记的图片（`trigger.generateInput.referenceNote.images`，含 `ossUrl/sourceUrl`）当前只作为**生图参考图**（`referenceImagesForGeneration` 过滤有效项、封顶 9），**从不参与张数决策**。文字卡封面（change textcard-cover-form）只作用于图 0，与本 change 正交。

## Goals / Non-Goals

**Goals:**
- 洗稿帖配图张数对齐源稿有效图数（≤9），让产出与原帖体量一致。
- 默认张数上限提到 9（不再需要为此单设 env）。
- 决策/执行解耦、只产选题不碰图源的红线不变。

**Non-Goals:**
- 不搬运源图当配图（仍是重新生成的新图；源图只作参考图）。
- 不让图 1..N 变文字卡（文字卡仍只封面）。
- 不改下发上传 / 部分成功（M<N）诚实收敛逻辑。
- 不为原创（非洗稿）帖强加张数（维持内容驱动）。

## Decisions

### 决策 1：洗稿目标张数 = 有效源图数（复用 referenceImagesForGeneration 口径）
「有效图」沿用生图侧同一口径 `referenceImagesForGeneration(images)`（`ossUrl ?? sourceUrl` 可用、`slice(0,9)`），取其 `length` 作洗稿目标张数 `targetCount = clamp(len, 1, maxImages)`。用同一口径保证「参考图张数」与「产图张数」语义一致，不引入第二套「有效」判定。

- **为何不用原始 `images.length`**：源笔记可能有无 URL 的占位/坏图；按有效图数对齐才是「真能参考的图」数，也与实际喂给生图的参考图张数一致。

### 决策 2：选题角色读上下文里的源笔记，而非新增 watchKey
`ImageSetPlanner.execute` 增加 `context` 形参（`BasePublishRole` 已支持，`CoverCardWriter` 同款），从 `context.snapshot().trigger?.generateInput?.referenceNote?.images` 读源图。**不**把 `trigger` 加进 `watchKeys`——`createdContent` 就绪时 `trigger` 必已在快照里（生成段起点），加 watchKey 反而多余。

### 决策 3：洗稿时把张数钉死并要求 LLM 产等量主题
`buildImageSetPlanPrompt` 增可选 `exactCount?`：洗稿传 `targetCount`，prompt 明确「本帖固定配 N 张、themes 必须给 N 项、各图叙事递进不重复」；非洗稿不传、维持「建议 3 张、范围 1~cap」。`buildPlan` 收 `targetCount?`：给了就按它夹取（而非 maxImages）+ 主题补齐到该数（图 0 封面位）。

### 决策 4：默认上限改代码默认 3→9，env 覆盖保留
`DEFAULT_MAX_IMAGES` 3→9（`image-set-planner.ts` + `image-generator.ts` 两处保持一致）。`AIDCP_PUBLISH_MAX_IMAGES` 仍可下调（如临时省成本）。硬顶 `IMAGE_COUNT_HARD_MAX=9` 不变。

## Risks / Trade-offs

- **短文洗稿被迫凑 9 张 → 主题稀释/补齐图偏泛**：源图多但正文短时，LLM 可能产不满 N 个有区分度的主题，触发「补充图 N」占位。→ 缓解：这是运营明确要的「体量对齐」，接受少量补齐图；补齐主题取标题派生（现有逻辑），图 0 仍是最抓眼钩子图。
- **出图变慢变贵（尤其 concurrency=1 串行）**：源 9 张 → 串行生 9 次。→ 缓解：可用 `AIDCP_PUBLISH_IMAGE_CONCURRENCY` 提并发、或按需 env 下调 `AIDCP_PUBLISH_MAX_IMAGES`；本 change 不动并发默认。
- **LLM 选题失败降级**：降级路径仍退到 1 张通用图（诚实、不凑数），不强行按源数产 N 张泛图。→ 罕见路径，接受与源数不一致。
- **部分成功 M<N**：某几张生图失败 → 按既有「诚实发 M 张」收敛（本 change 不改），最终附着数可能 < 目标数，如实记 `images_attached_count`。

## Migration Plan

- 无 DB 迁移、无新 env 强制项。
- 部署：cloud 纯代码 → `npm run typecheck` + `test:acceptance` + `npm test` 全绿 → §5 安全序列部署 dev。
- 回滚：纯代码回滚上一 commit 重部署；无数据形态变更。

## Open Questions

- 无阻塞项。（可选后续：短文+源图多时，是否引入「按正文密度下调目标数」的软策略——本期按运营诉求严格对齐，不做。）
