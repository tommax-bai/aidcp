## Why

洗稿出图目前只对**封面（0 号槽）**判形态、只在封面槽渲染文字卡，内页各槽恒走生成式配图。张数虽已由 `rewrite-image-count-parity` 对齐源稿，但当源稿是**纯文字卡轮播**（例如「把 AI 记忆从云端搬去本地教程」，源图整帧全是排版文字卡）时，产物只有第一张是文字卡、其余全变 AI 图——**帧内形态自相矛盾**，明显不像同一篇的图集。缺口是「判定」与「渲染」两端都被写死成封面独占（`cover-form-sensor.ts` 只判第一张即停、`image-generator.ts` 只有 0 号槽走文字卡分支），而非张数问题。

## What Changes

- **形态判定：仅封面 → 帖级形态档（cover-gated 有界扇出）**。封面判出非文字卡 → 直接 `generative` 档、**零额外判定调用**（普通帖不多花一分钱）；封面判为文字卡才对**其余有效源图并发、有界（上限 K、每张独立超时）**判形态。据此把整帖归入三档之一：`generative`（普通帖）/ `card_cover`（卡封面 + 生图内页，= **今天的行为，明确不回退**，守小红书原生合法版式）/ `all_text_card`（**每张源图一致且高置信全是文字卡**才成立）。任一未知 / 出错 / 低置信 / 超上限 → 降级到既有安全档，**绝不猜 text_card**，每个分支落诚实 `gateReason`。

- **渲染：全有或全无、整帖统一**。仅 `all_text_card` 档才把**每一槽**都渲染成文字卡；渲染前对「渲染器 + OSS 上传器可用」做**整帖预检**（不可用 → 整帖回落 `card_cover`/生成式，不半途裂帧）。文案由**一次多卡调用**从**洗稿产物**（标题/正文/标签 + 图集选题主体）排出 N 张卡：0 号封面钩子卡、1..N-1 号正文段落卡。**防搬运红线不变**：文案提示词只喂洗稿产物、**绝不喂源稿正文或源图任何文本**（源卡文字自始至终不被 OCR / 采集）；每张卡过与封面卡**同一套**产后校验（≥12 连续字符逐字重叠 / 原作者名 / 引流促销 / 违禁词），一次收紧重试；**任一张仍违规 → 整帖放弃文字卡、退回生成式**并如实记因。

- **两阶段上线（影子先行，不可省）**。阶段 0（旗标 `AIDCP_POST_FORM_PROFILE`）：只判定 + 记录 + 落审计，**输出与今天逐字节一致**（deep-equal 锁死），攒两类数据——纯卡源稿实际出现频率、判定模型用在**内页**图上的准确率（该模型此前只在封面上验证过）。阶段 1（旗标 `AIDCP_PUBLISH_TEXTCARD_CAROUSEL`）：数据证明值得后才翻开整帖渲染；若纯卡源稿罕见，阶段 1 可不建、本 change 作为诚实信号收尾。

- **不做（Non-Goals，守既有不变量与 YAGNI）**：不在照片槽上凭空捏文字卡；不把「卡封面 + 照片内页」的混合帖抹成全卡；不复刻源卡文字（永远是我们自己洗的话重排）；不改渲染器 `render/text-card.ts`（本就按单卡设计、可复用）与素材回写 `curated-content-store.ts`（回写本就按下标、TOCTOU 安全）；不引入封面索引、不改 `set_cover` 触发条件；不动张数对齐机制。

## Capabilities

### New Capabilities
<!-- 无新增独立能力：本 change 是对既有两条能力的需求修正，按 YAGNI 不新造能力/抽象。 -->

### Modified Capabilities
- `publish-textcard-cover`：封面形态决策**从「仅感知第一张、封面独占」扩展为「帖级形态档」**——新增内页源图有界并发判形态、三档归类（`generative`/`card_cover`/`all_text_card`）、`all_text_card` 档的多卡文案（沿用同一防搬运产后校验）、整帧统一渲染与整帖预检降级、`AIDCP_POST_FORM_PROFILE`（影子）与 `AIDCP_PUBLISH_TEXTCARD_CAROUSEL`（渲染）两枚旗标及零回归。**保留**既有封面独占语义为其中 `card_cover` 档、诚实降级链、影子红线。
- `publish-multi-image`：「并行出图且每张独立计时」需求**放宽**——文字卡本地渲染分支从「仅 0 号槽」推广为「凡该槽有对应卡面文案（`cardSet[i]`）即渲染，其余槽走生成式」，仍守每张独立计时、部分成功诚实收敛、帧内一致（同尺寸同风格族）、封面恒取首张、失败张不补空不复用。**新需求，与活跃 change `category-adaptive-images-and-judgment` 修改的是本能力不同需求，可共存、按序归档。**

## Impact

- **aidcp-cloud（`src/publish-agent/`）**：`cover-form-sensor.ts`（抽出「判一张」纯helper、扩内页有界并发判定，红线不变）、**新增 `post-image-form-profile.ts`**（帖级形态档计算，封面先行 + 并发扇出 + gateReason 枚举 + 上限 K）、`roles/cover-card-writer.ts`（消费形态档；`all_text_card` 时一次多卡文案 + N 折产后校验 + 整帖回落）、`prompts.ts`（新增 `buildCardSetPrompt`，只喂洗稿产物）、`roles/image-generator.ts`（把 `i===0` 判据换成「该槽有 `cardSet[i]` 即渲染」、`renderCoverCard` 泛化为按 seq 写 `${seq}.png`；渲染器/OSS 预检前置）、`roles/image-prompt-composer.ts`（盖章透传形态档，增量字段）、`types.ts`（增量 `formProfile`/`gateReason` 枚举/`cardSet?`）、`server.ts`（接两枚旗标、审计扩每槽 form + profile + 渲染状态）。
- **不改（复用现状）**：`src/render/text-card.ts`（渲染契约本就是单卡 `render(copy, seed)`）、`src/cache/curated-content-store.ts`（`reference_images` 逐项 `formGuess` 回写通道已在、按下标、单语句 CAS）。
- **协议 / DB**：不改协议（AC-PROTO 无关）、不改 DB 结构（形态档为每帖运行时派生，不落库；内页 `formGuess` 复用既有 JSONB 逐项字段）。
- **管理后台（aidcp-console）**：前端不入范围；审计新字段 null-safe 复用既有解析。
- **排期 / 热点文件**：阶段 0 基本是**增量**（新模块 + 增量字段 + 影子旗标），不动出图渲染分支，低风险可先走并攒 go/no-go 数据。阶段 1 触碰最热文件（`image-generator.ts`/`image-prompt-composer.ts`/`prompts.ts`/`cover-form-sensor.ts`），**必须单写者串行、排在 `category-adaptive-images-and-judgment` 归档之后**（同改 `publish-multi-image` 能力的不同需求，可共存按序归档）。每批改后 `test:acceptance` → `test` → `typecheck` 全绿（AC-PUB/AC-PROTO/AC-RISK 必过）；部署走安全序列、绝不碰同机 isales。
