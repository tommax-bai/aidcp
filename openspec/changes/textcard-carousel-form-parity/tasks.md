# Tasks — textcard-carousel-form-parity

> 分两阶段落地。阶段 0（形态档影子）基本增量、低风险，先走并攒 go/no-go 数据；阶段 1（整帖渲卡）触最热文件，**必须排在 `category-adaptive-images-and-judgment` 归档之后、单写者串行**。热点文件：`image-generator.ts` / `image-prompt-composer.ts` / `prompts.ts` / `cover-form-sensor.ts`。全程不碰 `render/text-card.ts` 与 `cache/curated-content-store.ts`（复用现状）。每批改后 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿（AC-PUB/AC-PROTO/AC-RISK 必过）。

## 1. aidcp-cloud — 阶段 0：帖级形态档判定（影子）

- [ ] 1.1 `src/publish-agent/cover-form-sensor.ts`：抽出「判一张源图形态」纯 helper（`senseOne`），当前单封面路径改为调用该 helper，**行为逐字节不变**（保留严格解析、无负缓存、绝不猜、绝不阻断、D13 无 OCR）；补回归断言锁死单封面路径等价。
- [ ] 1.2 新增 `src/publish-agent/post-image-form-profile.ts`（纯服务、依赖全注入、脱离网络/PG 可单测）：封面先行 → 封面非卡即 `generative` 零额外调用；封面卡则对其余有效源图 `mapWithConcurrency` 有界并发判形态（每张独立超时、上限 K 默认 = maxImages、超上限降级）；归三档（`generative`/`card_cover`/`all_text_card`），落 `gateReason` 穷举枚举；内页判定复用 `senseOne` + 逐项按下标 `annotate`（不改回写通道）。
- [ ] 1.3 `src/publish-agent/types.ts`：增量字段——`CoverCardPlan.formProfile`（三档枚举）、`PostFormGateReason` 穷举枚举、`ImagePlan.formProfile`；预留 `cardSet?: (CoverCardCopy|null)[]`（阶段 1 用）；保留既有 `coverForm`/`coverCard` 标量使旗标关时逐字节一致。
- [ ] 1.4 `src/publish-agent/roles/cover-card-writer.ts`：消费 `post-image-form-profile` 得形态档并盖进 `CoverCardPlan.formProfile`；形态档 ≠ `all_text_card` 时既有 0 号封面决策**完全不变**；恒写键、诚实 gateReason 不破坏。
- [ ] 1.5 `src/publish-agent/roles/image-prompt-composer.ts`：`stampCover` 透传 `formProfile`（增量字段）；每槽生成式 prompt 照常恒产出（降级兜底就位）。
- [ ] 1.6 `src/server.ts`：接旗标 `AIDCP_POST_FORM_PROFILE`（默认关，只门控形态档计算+记录+审计）；装配 `post-image-form-profile` 服务（注入 vision/annotate/getModel/getProvider/clock）。
- [ ] 1.7 审计扩字段：`CoverFormAudit` 携带帖级 `formProfile` + 每槽 `form` + 每槽 `renderStatus`（阶段 0 renderStatus 恒为现版值）；`publish-executor.ts` 并列落库；面板读取 null-safe（旧行无新字段解析为 null）。
- [ ] 1.8 阶段 0 零回归：两枚旗标全关时全管线 deep-equal 现版（含既有封面文字卡链路），补 deep-equal 验收断言。

## 2. aidcp-cloud — 阶段 0：测试与影子部署

- [ ] 2.1 单测 `post-image-form-profile`：封面非卡零内页调用 / 纯卡轮播归 `all_text_card` / 混合源归 `card_cover` 不猜 / unknown·低置信·出错·超上限各自降级枚举 / 并发有界。
- [ ] 2.2 acceptance：AC-PUB 诚实（旗标全关 deep-equal；影子模式只判不渲、封面/内页照现版；绝不把缺失猜成 `all_text_card`）。
- [ ] 2.3 回归纪律：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿。
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
