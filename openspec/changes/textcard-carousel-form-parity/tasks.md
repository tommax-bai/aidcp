# Tasks — textcard-carousel-form-parity

> 分两阶段落地。阶段 0（形态档影子）基本增量、低风险，先走并攒 go/no-go 数据；阶段 1（整帖渲卡）触最热文件，**必须排在 `category-adaptive-images-and-judgment` 归档之后、单写者串行**。热点文件：`image-generator.ts` / `image-prompt-composer.ts` / `prompts.ts` / `cover-form-sensor.ts`。全程不碰 `render/text-card.ts` 与 `cache/curated-content-store.ts`（复用现状）。每批改后 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿（AC-PUB/AC-PROTO/AC-RISK 必过）。

## 1. aidcp-cloud — 阶段 0：帖级形态档判定（影子）

- [x] 1.1 `src/publish-agent/cover-form-sensor.ts`：抽出「判一张源图形态」纯 helper，当前单封面路径改为调用该 helper，**行为逐字节不变**（保留严格解析、无负缓存、绝不猜、绝不阻断、D13 无 OCR）；补回归断言锁死单封面路径等价。 <!-- aidcp-cloud 1b202d2 helper 命名为 senseImageAt、对外暴露 senseAt(ref,index)（interface 上 optional，旧 stub 不破）；导出 usableImageUrl 供形态档服务复用 -->
- [x] 1.2 新增 `src/publish-agent/post-image-form-profile.ts`（纯服务、依赖全注入、脱离网络/PG 可单测）：封面先行 → 封面非卡即 `generative` 零额外调用；封面卡则对其余有效源图 `mapWithConcurrency` 有界并发判形态（每张独立超时、上限 K 默认 9、超上限降级）；归三档（`generative`/`card_cover`/`all_text_card`），落 `gateReason` 穷举枚举；内页判定经注入的 `senseAt` 复用逐项按下标 `annotate`（不改回写通道）。 <!-- aidcp-cloud 1b202d2 -->
- [x] 1.3 `src/publish-agent/types.ts`：增量字段——`CoverCardPlan.formProfile`/`formProfileGate`/`perImageForms`、`PostFormProfile`+`PostFormGateReason`+`PerImageFormGuess`+`PostFormProfileResult` 枚举/型、`ImagePlan` 同名透传字段；预留 `CoverCardPlan.cardSet?`（阶段 1 用）；保留既有 `coverForm`/`coverCard` 标量使旗标关时逐字节一致。 <!-- aidcp-cloud 1b202d2 -->
- [x] 1.4 `src/publish-agent/roles/cover-card-writer.ts`：消费 `post-image-form-profile` 得形态档、经 `attach` 盖进 `CoverCardPlan`（旗标关→{}→attach 恒等→byte-identical）；形态档 ≠ `all_text_card` 时既有 0 号封面决策**完全不变**；恒写键、诚实 gateReason 不破坏。 <!-- aidcp-cloud 1b202d2 -->
- [x] 1.5 `src/publish-agent/roles/image-prompt-composer.ts`：`stampCover` 条件透传 `formProfile`/`formProfileGate`/`perImageForms`（旗标关不新增键→零回归）；每槽生成式 prompt 照常恒产出（降级兜底就位）。 <!-- aidcp-cloud 1b202d2 -->
- [x] 1.6 `src/server.ts`：接旗标 `AIDCP_POST_FORM_PROFILE`（默认关，只门控形态档计算+记录+审计）；装配 `createPostImageFormProfileService`（senseAt 取自 coverFormSensor、enabled=旗标）。 <!-- aidcp-cloud 1b202d2 -->
- [x] 1.7 审计扩字段：`CoverFormAudit` 携带帖级 `formProfile`/`formProfileGate`/`perImageForms`（image-generator 条件写入）。`publish-executor.ts` **无需改**（既有 `withCoverFormAudit` 整对象透传，新字段自动落库）；面板 `parseCoverFormAudit` 宽松解析、旧行/旗标关为 undefined 天然 null-safe，无需改。 <!-- aidcp-cloud 1b202d2 每槽 renderStatus 属阶段1（阶段0 renderStatus 恒现版值、无新增） -->
- [x] 1.8 阶段 0 零回归：CoverCardWriter 未装配/旗标关时计划不含 formProfile 键（byte-identical）；条件展开保 composer/image-generator 旗标关不新增键，补验收断言。 <!-- aidcp-cloud 1b202d2 -->
<!-- aidcp-cloud 1b202d2 阶段0 代码全部落地（origin/master 已含）；不改 render/text-card.ts 与 curated-content-store.ts -->
<!-- 集成：worktree 分支 rebase 到 origin/master(8160d0e) 后 ff 推 master(1b202d2) -->


## 2. aidcp-cloud — 阶段 0：测试与影子部署

- [x] 2.1 单测 `post-image-form-profile`：封面非卡零内页调用 / 纯卡轮播归 `all_text_card` / 混合源归 `card_cover` 不猜 / 出错·低置信·超上限各自降级枚举 / 并发有界 + senseAt 抛错兜底。 <!-- aidcp-cloud 1b202d2 test/publish-agent/post-image-form-profile.test.ts 8 例 -->
- [x] 2.2 acceptance/单测：CoverCardWriter 影子（旗标开盖章 formProfile、封面决策不变）+ 零回归（未装配/旗标关不含 formProfile 键）；绝不把缺失猜成 `all_text_card`（形态档服务单测锁死）。 <!-- aidcp-cloud 1b202d2 cover-card-writer.test.ts 新增 4 例 -->
- [x] 2.3 回归纪律：`npm run test:acceptance`(47) → `npm test`(1652) → `npm run typecheck` 全绿。 <!-- aidcp-cloud 1b202d2 rebase 后复跑 typecheck+acceptance(47) 全绿再 ff push -->
- [x] 2.4 部署 dev + 开 `AIDCP_POST_FORM_PROFILE` 影子；真机验收项登记 backlog 簇 23。 <!-- aidcp-cloud 1b202d2 代码经并发 fleet 部署已在 dev（md5 == 本地三文件）；本 session 仅 .env 加 AIDCP_POST_FORM_PROFILE=true（备份 .env.bak.2026-07-09-postform）+ 重启，healthcheck 全绿（active/8787/OSS/飞书/渲染出口就绪）。2026-07-09 deployed -->

## 3. GATE — 影子数据评审（阶段 1 前置闸）

- [x] 3.1 复核影子数据：**用户明确要求「看到产物变化」→ 跳过影子灰度门直接进阶段 1**（同 07-08 文字卡封面做法）。内页判定准确率未经真机验证，登记 backlog 簇 23 真机核（误判则该篇退 card_cover、旗标秒回滚）。 <!-- 用户令 2026-07-09：跳过 shadow gate -->
- [x] 3.2 确认 `category-adaptive-images-and-judgment` **已归档**（origin/main 不含其活跃 change）→ 阶段 1 单写者串行前置解除。 <!-- 2026-07-09 -->

## 4. aidcp-cloud — 阶段 1：多卡文案 + 整帖渲卡（category-adaptive 归档后，单写者串行）

- [x] 4.1 `src/publish-agent/prompts.ts`：新增 `buildCardSetPrompt`（一次多卡，只喂洗稿产物、绝不喂 referenceNote 原文/原图；产 N 张卡 [0] 封面钩子 [1..N-1] 正文段落）。 <!-- aidcp-cloud 09eef52 CoverCardWriter 与 ImageSetPlanner 并行、无 themes，改按 count(=源稿有效图数) 让 LLM 切段，不依赖 themes -->
- [x] 4.2 `src/publish-agent/roles/cover-card-writer.ts`：`all_text_card` + 轮播旗标开 + 渲染器/OSS 门（gate5）过 + N≥2 → 一次多卡；每张过同一 `findViolation` + 一次收紧重试；任一违规整帖回落生成式（`formProfileGate=carousel_copy_failed`）；产出写 `cardSet`。N<2 落既有单封面卡。 <!-- aidcp-cloud 09eef52 -->
- [x] 4.3 `src/publish-agent/roles/image-generator.ts`：`i===0` 判据→「该槽有 `cardForSlot(i)` 即渲染」；`renderCoverCard`→`renderCardAt(card,{...,seq},postKey)` 写 `${seq}.png`；整帖预检（渲染器/OSS 不可用→整帖生成式，不半途裂帧、并发预渲染）；某槽中途失败只降级该槽；每槽 `cardRenderStatuses` 入审计。单封面卡种子保旧（零churn）。 <!-- aidcp-cloud 09eef52 生成式经 relocate 也落 ${seq}.png（同键，一槽一种产出无碰撞）；区分渲染/生成看 providerPrompts+cardRenderStatuses -->
- [x] 4.4 `src/server.ts`：接 `AIDCP_PUBLISH_TEXTCARD_CAROUSEL`；渲染出口加载 + `renderEnabled`(gate3) 任一渲染旗标(COVER‖CAROUSEL)开即放行。 <!-- aidcp-cloud 09eef52 -->
- [x] 4.5 确认**不改** `src/render/text-card.ts` 与 `src/cache/curated-content-store.ts`（复用现状）。 <!-- aidcp-cloud 09eef52 -->

## 5. aidcp-cloud — 阶段 1：测试与部署

- [x] 5.1 AC-PUB/单测：多卡违规整帖回落生成式（cover-card-writer.test.ts 3 例：合法多卡→cardSet；旗标关→单卡无 cardSet；任一逐字搬运→整帖生成式+carousel_copy_failed）；`buildCardSetPrompt` 输入结构上只喂洗稿产物（不接 referenceNote）。 <!-- aidcp-cloud 09eef52 -->
- [x] 5.2 单测 `image-generator`：轮播每槽渲 `${seq}.png` 按序收齐；某槽中途失败只降级该槽、其余不受影响；渲染器/OSS 不可用整帖生成式（无裂帧）（image-generator-textcard.test.ts 3 例）。 <!-- aidcp-cloud 09eef52 -->
- [x] 5.3 回归纪律：`npm run test:acceptance`(47) → `npm test`(1661) → `npm run typecheck` 全绿。 <!-- aidcp-cloud 09eef52 -->
- [x] 5.4 部署 dev + 开 `AIDCP_PUBLISH_TEXTCARD_CAROUSEL`；真机验收登记 backlog 簇 23（阶段1 项）。 <!-- aidcp-cloud 09eef52 git archive 快照 rsync（备份 cloud.bak.20260709-p1carousel + .env.bak.20260709-p1carousel）+ 开旗标 + 重启；healthcheck 全绿（active/8787/OSS/渲染出口/飞书）。四旗标均 true。2026-07-09 deployed -->

## 6. 控制仓 — 收尾

- [x] 6.1 回写本 tasks.md 进度（阶段0+1 全标注 sha）。 <!-- aidcp-cloud 09eef52 -->
- [ ] 6.2 `openspec validate textcard-carousel-form-parity --strict` 通过。
- [ ] 6.3 真机验收（backlog 簇 23）通过后 archive。 <!-- 代码全落地+部署 dev；真机核内页判定准确率 + 轮播视觉连贯性后再 archive -->

