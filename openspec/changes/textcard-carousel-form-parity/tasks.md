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
- [ ] 2.4 部署 dev（安全序列：`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck），开 `AIDCP_POST_FORM_PROFILE` 影子；登记真机验收项到 `docs/real-machine-acceptance-backlog.md`：纯卡源稿实际频率、内页（非封面）图判定准确率。

## 3. GATE — 影子数据评审（阶段 1 前置闸）

- [ ] 3.1 复核影子数据：纯文字卡源稿是否足够常见、内页判定准确率是否达标。达标 → 进阶段 1；不达标 → 本 change 作为「诚实形态信号」收尾归档，不建阶段 1。
- [ ] 3.2 确认 `category-adaptive-images-and-judgment` 已归档（阶段 1 单写者串行的前置）；否则等待其归档再动热点文件。

## 4. aidcp-cloud — 阶段 1：多卡文案 + 整帖渲卡（category-adaptive 归档后，单写者串行）

- [ ] 4.1 `src/publish-agent/prompts.ts`：新增 `buildCardSetPrompt`（一次多卡）——只喂洗稿产物 `createdContent{title,content,tags}` + 图集选题 `themes[i]{subject,intent}`，产 N 张卡（[0] 封面钩子、[1..N-1] 正文段落），卡面短句适配版式；**绝不喂 referenceNote 原文/原图**。
- [ ] 4.2 `src/publish-agent/roles/cover-card-writer.ts`：`all_text_card` 档 + 渲染旗标开 + 渲染器/OSS **整帖预检**通过时，一次多卡调用 → N 张卡；每张过同一 `findViolation`（≥12 逐字重叠/原作者名/引流促销/违禁词）+ 一次收紧重试；**任一张仍违规 → 整帖回落生成式**、落 `carousel_copy_failed`；产出写 `cardSet`。
- [ ] 4.3 `src/publish-agent/roles/image-generator.ts`：把 `i===0` 渲染判据换成「该槽有 `cardSet[i]` 非空即渲染」；`renderCoverCard` 泛化为 `(card, {accountId, runToken, seq}, postKey=${sourceId}#${seq})` 写 `${seq}.png`；渲染器/OSS 可用性做**整帖预检**（不可用整帖降级、不半途裂帧）；某槽渲染中途失败只降级该槽走生成式（享完整每图槽预算）；OSS 键无碰撞（`${seq}.png` 与 `${seq}` 基名不并存）。
- [ ] 4.4 `src/server.ts`：接旗标 `AIDCP_PUBLISH_TEXTCARD_CAROUSEL`（默认关，门控整帖渲卡）；审计扩每槽 `renderStatus`（rendered / render_failed_generative / render_failed_none）。
- [ ] 4.5 确认**不改** `src/render/text-card.ts`（单卡 `render(copy,seed)` 复用）与 `src/cache/curated-content-store.ts`（逐项 CAS 回写复用）。

## 5. aidcp-cloud — 阶段 1：测试与部署

- [ ] 5.1 acceptance AC-PUB：`buildCardSetPrompt` 输入源无关断言（不含 referenceNote 任何文本）；N 折 `findViolation`；任一张违规整帖回落生成式（不只替换违规张）。
- [ ] 5.2 单测 `image-generator`：轮播档每槽渲染键 `${seq}.png` 无碰撞、按序收齐；某槽中途渲染失败只降级该槽、其余槽不受影响；渲染器/OSS 预检不可用整帖降级（无裂帧半成品）；帧内同尺寸。
- [ ] 5.3 回归纪律：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿（AC-PUB/AC-PROTO/AC-RISK 必过）。
- [ ] 5.4 部署 dev（安全序列），behind `AIDCP_PUBLISH_TEXTCARD_CAROUSEL`；真机验收项登记 backlog：轮播视觉连贯性（同风格族/同尺寸）、纯卡源稿产物形态一致、混合源稿仍 `card_cover` 不裂。

## 6. 控制仓 — 收尾

- [ ] 6.1 回写本 tasks.md 进度（按 sub-repo 分节、HTML 注释标 `[x]` 带 commit-sha，格式 `<!-- <repo> <sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`）。
- [ ] 6.2 `openspec validate textcard-carousel-form-parity --strict` 通过。
- [ ] 6.3 全部 task 完成 + dev 验证通过 → archive（排在 `category-adaptive-images-and-judgment` 归档之后，避免 `publish-multi-image` spec 交织合并冲突）。
