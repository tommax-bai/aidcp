## Context

洗稿发布出图链上，「判形态」与「渲文字卡」两端都被写死成**封面独占**：

- 感知服务只挑参照图里**第一张有可用 URL** 的图判形态，判完立即 `break`，从不看第 2..N 张（`aidcp-cloud/src/publish-agent/cover-form-sensor.ts:156-166`）。
- 出图角色只在**封面槽（0 号）** 且判定 `text_card` 时走本地渲染分支，其余每一槽恒走生成式图源，且渲染写死 `.../0.png`（`aidcp-cloud/src/publish-agent/roles/image-generator.ts:152-244`）。
- 文案角色只产**一张**封面钩子卡 `{title, bullets≤5, tags≤3}`（`roles/cover-card-writer.ts`），渲染器输入契约也是这个单卡形状（`src/render/text-card.ts:44` `TextCardCopy`）。

已落地的前置：`rewrite-image-count-parity`（已归档）让配图**张数** = 源稿有效图数（`roles/image-set-planner.ts:65-113`）。`textcard-cover-form`（已归档）建立了封面形态感知 + 决策 + 渲染 + 影子模式 + 诚实降级链（能力 `publish-textcard-cover`）。`curated-reference-images`（已实装未归档）在 `reference_images` JSONB 上留了**逐项** `formGuess` 回写通道（`cover-form-sensor.ts` 的 `annotate(rowId, index, guess)`、`curated-content-store.ts`）。

因此当源稿是**纯文字卡轮播**时：张数对齐了，但只有 0 号槽渲成文字卡、其余走 AI 生图，帧内形态自相矛盾。缺口是判定与渲染的**封面独占**，不是张数。

现役硬约束（本设计必须守）：

- **诚实红线（贯穿 5 spec）**：MUST NOT 静默假成功——缺失/失败/低置信绝不猜 `text_card`，每次降级落诚实 `gateReason`，绝不阻断发布。
- **帧内一致（`category-adaptive` 持有的不变量）**：同一帖全部图同尺寸（1728×2304 == `AIDCP_SEEDREAM_IMAGE_SIZE`）、同风格族。
- **防搬运（D13 结构隔离）**：源卡文字**不 OCR、不采集、不进任何生成上下文**；卡面文案只由洗稿产物派生；产后校验做 ≥12 连续字符逐字重叠比对。
- **热点文件单写者**：`image-generator.ts`/`image-prompt-composer.ts`/`prompts.ts`/`cover-form-sensor.ts` 与活跃 change `category-adaptive-images-and-judgment` 同能力不同需求，须串行、按序归档。

## Goals / Non-Goals

**Goals:**

- 纯文字卡轮播源稿 → 产物**整帖每一槽都是文字卡**，形态一致。
- 「卡封面 + 照片内页」混合帖 → **保持现状**（`card_cover`），不回退、不抹平（守小红书原生合法版式，即归档 `textcard-cover-form` 的 Non-Goal）。
- 普通帖（封面非文字卡）→ **零额外判定调用**，行为不变。
- 全程守诚实红线、帧内一致、防搬运；影子先行、可随时旗标回滚。

**Non-Goals:**

- 不在照片槽上凭空捏文字卡；不把混合帖抹成全卡。
- 不复刻源卡文字（卡面永远是洗稿产物重排；本 change 能对齐**形态**、对齐不了**内容**，这是防搬运的必然）。
- 不改渲染器 `render/text-card.ts`（单卡 `render(copy, seed)` 已够用）与素材回写 `curated-content-store.ts`（逐项 CAS 已在）。
- 不引入封面索引、不改 `set_cover` 触发条件、不动张数对齐机制。
- 不做「照片类封面标题叠字」「非首图当封面」（归其他后续 change）。

## Decisions

### D1：帖级形态档（post-level form profile），三档而非每槽独立

一次判定得出**整帖**一个形态档，取代「每槽各判各渲」：

- `generative`：封面判出非 `text_card`（或无参照图）→ 全帖生成式，**零额外判定调用**。
- `card_cover`：封面 `text_card`，但内页未能一致高置信全是 `text_card` → **今天的行为**（卡封面 + 生图内页）。
- `all_text_card`：封面 `text_card` **且** 每张有效源图都被判 `text_card` 且置信 ≥ `AIDCP_COVER_FORM_MIN_CONFIDENCE` → 整帖渲卡。

**为什么不每槽独立**：① 洗稿是重新生成内容、源图不 1:1 保留，「按源槽形态渲该槽」语义对不上；② 每槽独立会产出「卡/照/卡/照」花帖，比现状更破帧内一致；③ 三档收敛到「全有或全无」渲染，天然守帧内一致。三套候选设计在「整帖统一渲染」上收敛一致。

**为什么不光看封面就判整帖**（否决的 B 方案）：封面 `text_card` 不蕴含内页也是——混合源稿（卡封面 + 照片内页）会被在照片位捏造文字卡，既失真又回退了原生版式，是诚实性违规。故 `all_text_card` **必须**有内页的正向证据（全体一致高置信），任何不确定一律降级。

### D2：封面先行（cover-gated）+ 内页有界并发判定

判定成本收在最需要处：封面非卡的绝大多数普通帖**一次额外调用都不发**。仅封面判卡时，才对其余有效源图**并发扇出**（`mapWithConcurrency`），每张独立超时（≤30s，复用 `AIDCP_COVER_FORM_TIMEOUT_MS`），并发上限受控。判定张数上限 `K`（默认 = `maxImages`）；有效源图数 > K → **降级而非猜**（`downgrade_over_cap`）。内页判定复用感知服务的严格解析（`form ∈ 枚举 + confidence ∈ [0,1]` 否则 error）、无负缓存、逐项 `annotate` 按下标回写（`curated-content-store.ts` 单语句 `jsonb_set`、逐项 `capturedAt` 锚、绝不动 `updated_at`）。

**替代**：串行判每张（A 方案）——尾延迟风险贴近角色总闸，且并发本可有界安全，故取并发。

### D3：新增 `post-image-form-profile.ts` 纯服务，感知层只抽 helper 不改行为

从 `cover-form-sensor.ts` 抽出「判一张」纯 helper（**当前单封面路径行为逐字节不变**），新模块 `post-image-form-profile.ts` 编排「封面先行 → 内页并发 → 归档三档 → gateReason 枚举」。依赖全注入、脱离网络/PG 可单测。感知服务本身红线不动。

### D4：渲染全有或全无 + 整帖预检降级

仅 `all_text_card` 档渲染全帖卡。**渲染器 + OSS 上传器可用性做整帖预检**（在扇出渲染**之前**）：不可用 → 整帖回落 `card_cover`/生成式（`renderer_unavailable`），**绝不半途裂帧**。这样只有「极少数真·单张 PNG 渲染中途失败」才退化单槽——而那条路正是既有 M<N 保序 + 生成式兜底的诚实降级，不是新设计选择。

`image-generator.ts` 把 `i===0` 判据换成「该槽有 `cardSet[i]` 即渲染」；`renderCoverCard` 泛化为按 `seq` 写 `${seq}.png`、`postKey = ${sourceId}#${seq}`。OSS 键无碰撞：一个槽要么 `${seq}.png`（卡）要么 `${seq}` 基名（生成式），绝不并存。**不改渲染器**：`render(copy, seed)` 本就按单卡；`accountId` 定色板+版式（STYLE 轴帧内一致），逐 `seq` 的 `postKey` 只定装饰（连贯不单调），每卡 1728×2304（DIMENSION 轴帧内一致）。

### D5：多卡文案一次调用，沿用同一防搬运产后校验

`all_text_card` 档发**一次** `buildCardSetPrompt`（新增），从**洗稿产物** `createdContent{title, content, tags}` + `ImageSetPlan.themes[i]{subject, intent}` 排出 N 张卡：`card[0]` 封面钩子卡、`card[1..N-1]` 正文段落卡，卡面短句以适配既有 5×2 行版式。**MUST 只喂洗稿产物，绝不喂 `referenceNote` 原文正文或原图**（对齐 `cover-card-writer` 现有 createdContent-only 输入）。每张卡过与封面卡**同一** `findViolation`（≥12 连续字符逐字重叠 / 原作者名 / 引流促销词 / 违禁词），一次收紧重试；**任一张仍违规 → 整帖放弃文字卡、回落生成式**并记 `carousel_copy_failed`。N 折校验是逐字泄漏的兜底。

**替代**：每卡一次 LLM 调用——N 倍成本 + 尾延迟，无收益，故取一次多卡。

### D6：gateReason 枚举穷举、每槽渲染状态入审计

形态档决策落诚实枚举：`all_text_card | card_cover | generative_cover_not_card | downgrade_inner_not_unanimous | downgrade_unknown_or_error | downgrade_over_cap | carousel_copy_failed | renderer_unavailable`。审计 `CoverFormAudit` 扩每槽 `form` + 帖级 `profile` + 每槽 `renderStatus`，面板 null-safe 解析旧行。降级用了生成图 SHALL NOT 标 `text_card`，unknown SHALL NOT 猜 `text_card`。

### D7：两阶段旗标，影子先行

- **阶段 0（`AIDCP_POST_FORM_PROFILE`，默认关）**：计算 + 记录 + 落审计 + 盖章形态档，**输出与今天逐字节一致**（deep-equal 锁死）。攒数据：`all_text_card` 实际频率、内页判定准确率（该视觉模型此前只在封面上验证过）。
- **阶段 1（`AIDCP_PUBLISH_TEXTCARD_CAROUSEL`，默认关）**：数据证明值得后才翻整帖渲染。若纯卡源稿罕见，阶段 1 可不建、本 change 作为诚实信号收尾。

阶段 0 基本增量、不动出图渲染分支，低风险先行；阶段 1 触最热文件，排在 `category-adaptive` 归档之后单写者串行。

## Risks / Trade-offs

- **内页视觉判定在非封面图上准确率未知** → 阶段 0 影子只记不渲，运营经面板/psql 核对 `sensedForm` 质量，达标才开阶段 1。
- **半途单张 PNG 渲染失败破坏帧内一致**（`all_text_card` 帖里出现 卡+照 混排）→ D4 把渲染器/OSS 可用性提为**整帖预检**，只剩真·中途失败退化单槽，走既有审计过的 M<N/生成式降级，绝不静默。
- **卡面文案意外逐字泄漏源文**（防搬运）→ MUST 强制 `buildCardSetPrompt` 输入源无关（只喂洗稿产物）+ N 折 `findViolation` 兜底；加一条验收断言锁死输入源无关。
- **成本膨胀**（内页多发视觉调用）→ 封面先行使普通帖零额外调用；`all_text_card` 才付费且有界并发 + 上限 K；判定复用零 TTL 逐项缓存命中即零调用。
- **与 `category-adaptive` 撞热点文件** → 二者改 `publish-multi-image` 的**不同需求**、可共存；阶段 1 单写者串行、排在其归档后；本 change 全程不碰 `render/text-card.ts` 与 `curated-content-store.ts`，从争用里摘掉两个热点。
- **能对齐形态、对不齐内容**（卡面是洗稿的话、非源卡复刻）→ 这是防搬运的必然，非缺陷；阶段 0 抽样人审确认可接受再开阶段 1。

## Migration Plan

1. 阶段 0 增量落地（新模块 + 增量字段 + 影子旗标 + 审计扩字段），全关时 deep-equal 锁死零回归 → 部署 dev（安全序列）→ 攒影子数据。
2. 数据评审（`all_text_card` 频率 + 内页判定准确率）：达标进阶段 1，否则收尾。
3. 阶段 1 在 `category-adaptive` 归档后单写者接线（渲染分支 + 多卡文案 + per-seq OSS 键），behind `AIDCP_PUBLISH_TEXTCARD_CAROUSEL`。
4. 回滚：任一阶段关旗标即回退到影子/现状；旗标级秒级可回滚，无需部署。

## Open Questions

- 内页判定上限 `K` 默认取 `maxImages`（9）是否合适，还是按成本设更低值再降级？（阶段 0 数据回答）
- `card[1..N-1]` 正文段落卡的信息切分粒度（按洗稿正文段落 vs 按 `ImageSetPlan.themes`）——阶段 0 先只记形态档、阶段 1 落文案时以抽样质量定稿。
- 混合源稿里「封面卡 + 少量卡内页 + 少量照片内页」是否值得第四档，还是一律 `card_cover`？当前按 YAGNI 归 `card_cover`，待数据反证再议。
