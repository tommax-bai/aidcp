# publish-textcard-cover — 从「仅封面文字卡」扩展为「帖级形态档 + 轮播渲染」

## MODIFIED Requirements

### Requirement: 执行分支与诚实降级链

文字卡渲染器 SHALL 作为可注入依赖挂在配图执行角色上。渲染前 SHALL 对「渲染器 + OSS 上传器可用」做**整帖预检**：不可用时整帖 SHALL 走既有降级档（`card_cover` 或生成式），MUST NOT 半途只渲染部分槽而破坏帧内一致。

当帖级形态档为 `all_text_card` 且卡面文案集 `cardSet` 与渲染依赖俱备时，**凡对应 `cardSet[i]` 非空的槽** SHALL 由本地渲染 + 字节直传 OSS 产出（键 `${seq}.png`，`postKey=${sourceId}#${seq}`）；`card_cover` 档 SHALL 仅 0 号封面槽渲染（行为与现版一致）、其余槽走生成式。每槽渲染 + 直传 SHALL 在进入该槽每图超时槽机制**之前独立结算**（内层闸 env `AIDCP_TEXTCARD_RENDER_TIMEOUT_MS`，默认 30s），成功即替换该槽产出（不前插、不移位，seq/imageCount/内页序全不变）；某槽渲染失败 SHALL 立即以**完整每图槽预算**用计划内恒在的该槽生成式提示词走生图路径（角色总闸公式相应加渲染超时项），且**只降级该槽**、不影响其余已渲染或待渲染槽。渲染与生成式双失败 SHALL 沿用既有少图保序语义（封面由首张成功槽顶上，全失败走既有纯文字降级判定）。执行角色 SHALL 只依据配图计划（含形态档与 `cardSet`）与注入依赖可用性行事，SHALL NOT 二次读取环境旗标（防决策/执行裂脑）。所有渲染卡 SHALL 与生成式配图同尺寸（1728×2304 == `AIDCP_SEEDREAM_IMAGE_SIZE`）、同账号色板版式族，守帧内一致；OSS 键 SHALL 无碰撞（一个槽要么 `${seq}.png` 卡、要么 `${seq}` 基名生成式，绝不并存）。

#### Scenario: 封面档渲染成功替换封面槽
- **WHEN** 形态档为 `card_cover`、封面渲染成功
- **THEN** 0 号槽为渲染卡 OSS URL、内页 seq 与数量不变、审计 `renderStatus='rendered'` 且带主题键；其余槽为生成式

#### Scenario: 轮播档整帖每槽渲染成文字卡
- **WHEN** 形态档为 `all_text_card`、渲染器/OSS 整帖预检通过、`cardSet` N 张俱全
- **THEN** 每一槽（0..N-1）均由本地渲染 + 直传 OSS 产出（键 `${seq}.png`）、同尺寸同风格族、审计每槽 `renderStatus='rendered'`，无任何槽落回生成式

#### Scenario: 渲染失败以完整槽预算走生成式（只降级该槽）
- **WHEN** 某槽渲染超时或 OSS 直传失败
- **THEN** 立即用该槽生成式提示词走生图路径且享有完整每图槽预算（不因先渲染被挤占）、审计该槽 `renderStatus='render_failed_generative'`，其余槽不受影响，无任何静默环节

#### Scenario: 渲染器/OSS 不可用整帖预检降级
- **WHEN** 渲染器工厂未就绪或 OSS 上传器缺失
- **THEN** 整帖落 `gateReason='renderer_unavailable'`、降级到 `card_cover`（若封面卡文案就位）或生成式，MUST NOT 出现「部分槽卡 + 部分槽生成」的裂帧半成品

#### Scenario: 双失败沿既有少图语义
- **WHEN** 某槽渲染与生成式封面双失败
- **THEN** 该槽诚实落空、复用既有 M<N 保序过滤、审计 `renderStatus='render_failed_none'`，与现版降级语义一致

## ADDED Requirements

### Requirement: 帖级形态档判定（封面先行、内页有界并发、三档归类）

系统 SHALL 在洗稿发布出图前计算**每帖一个**帖级形态档（post-level form profile），取代「仅感知第一张封面」的单点判定，并 SHALL 由独立纯服务编排（依赖全注入、脱离网络/PG 可单测）。判定 SHALL **封面先行（cover-gated）**：封面判出非 `text_card`（或无参照图）→ 直接 `generative` 档、**零额外判定调用**。仅封面判为 `text_card` 时，SHALL 对其余有效源图**并发、有界**判形态（每张独立超时，复用感知层超时闸；判定张数上限 `K`，默认 = `maxImages`；有效源图数 > K SHALL 降级而非猜）。据此 SHALL 归入三档之一并落诚实 `gateReason`：`generative`（普通帖）；`card_cover`（封面 `text_card` 但内页未一致高置信全 `text_card`，= 现版「卡封面 + 生图内页」行为、MUST NOT 回退）；`all_text_card`（封面 `text_card` **且**每张有效源图判 `text_card` 且置信 ≥ `AIDCP_COVER_FORM_MIN_CONFIDENCE`）。内页判定 SHALL 复用感知层严格解析（`form ∈ 枚举 + confidence ∈ [0,1]` 否则 error、无负缓存、绝不默认成功）与逐项按下标回写通道（单语句 CAS、逐项 capturedAt 锚、绝不动 updated_at）。任一未知 / 出错 / 低置信 / 超上限 SHALL 使 `all_text_card` 不成立、降级到安全档，MUST NOT 把缺失或不确定猜成 `all_text_card`。`gateReason` 枚举 SHALL 穷举：`all_text_card | card_cover | generative_cover_not_card | downgrade_inner_not_unanimous | downgrade_unknown_or_error | downgrade_over_cap | carousel_copy_failed | renderer_unavailable`。

#### Scenario: 封面非文字卡零额外判定
- **WHEN** 封面判出 `photo`/`illustration`/`other` 或无参照图
- **THEN** 帖级形态档 = `generative`、`gateReason='generative_cover_not_card'`（或既有 `no_reference_images`）、**未对内页发起任何判定调用**

#### Scenario: 纯文字卡轮播源稿归 all_text_card
- **WHEN** 封面 `text_card` 且其余每张有效源图均判 `text_card`、置信均 ≥ 阈值、有效源图数 ≤ K
- **THEN** 形态档 = `all_text_card`、`gateReason='all_text_card'`，据此后续整帖渲卡

#### Scenario: 混合源稿不猜成全卡（守原生版式）
- **WHEN** 封面 `text_card` 但某内页判 `photo`（或任一内页 unknown/低置信/出错）
- **THEN** 形态档 = `card_cover`、落 `downgrade_inner_not_unanimous`（或 `downgrade_unknown_or_error`），保持「卡封面 + 生图内页」，MUST NOT 在照片槽捏造文字卡

#### Scenario: 超上限降级而非猜
- **WHEN** 有效源图数 > K
- **THEN** 形态档降级（非 `all_text_card`）、落 `downgrade_over_cap`，绝不对未判定的槽假定为 `text_card`

### Requirement: 轮播多卡文案独立生成与整帖诚实回落（防搬运）

`all_text_card` 档 SHALL 由**一次**多卡文案调用从**洗稿产物**（`createdContent{title, content, tags}` + 图集选题主体 `themes[i]{subject, intent}`）排出 N 张卡：`card[0]` 封面钩子卡、`card[1..N-1]` 正文段落卡，卡面短句 SHALL 适配既有卡片版式。多卡文案提示词 MUST 只喂洗稿产物，SHALL NOT 包含 `referenceNote` 原文正文、原标题或原图任何文本（源卡文字自始至终不 OCR、不采集、不入生成上下文）。**每一张**卡 SHALL 过与封面卡**同一套**产后校验（卡面标题 ≠ 原标题归一化后；任一文本行与原标题/正文无 ≥12 连续字符逐字重叠；不含原作者名/平台水印/二维码/联系方式/价格促销词；通过既有违禁词闸），违规 SHALL 带更紧约束重试一次（角色闸剩余预算内）；**任一张仍违规 SHALL 整帖放弃文字卡、回落生成式**并落 `gateReason='carousel_copy_failed'`，MUST NOT 只替换违规张而保留其余卡（防裂帧）、MUST NOT 发布含逐字搬运的卡。

#### Scenario: 多卡文案一次生成整帖卡面
- **WHEN** 形态档 `all_text_card`、渲染依赖就位
- **THEN** 一次调用产出 N 张卡（[0] 封面钩子、[1..N-1] 正文段落），每张过产后校验通过，整帖渲卡

#### Scenario: 卡面只喂洗稿产物不喂源文
- **WHEN** 组装多卡文案提示词
- **THEN** 输入仅含洗稿产物与图集选题主体，断言不含 referenceNote 原文/原图任何文本（验收锁死输入源无关）

#### Scenario: 任一张逐字搬运整帖回落
- **WHEN** N 张中某张与原正文存在 ≥12 连续字符逐字重叠、重试后仍违规
- **THEN** 整帖放弃文字卡、回落生成式、落 `carousel_copy_failed`，绝不只替换该张而保留其余卡

### Requirement: 轮播旗标、影子先行与零回归

系统 SHALL 以两枚**默认关闭**的旗标分阶段推出：`AIDCP_POST_FORM_PROFILE`（阶段 0，影子）门控**帖级形态档的计算 + 记录 + 审计**；`AIDCP_PUBLISH_TEXTCARD_CAROUSEL`（阶段 1，渲染）门控 `all_text_card` 档的**整帖渲卡**。两枚全关时管线行为 SHALL 与现版等价（含既有封面文字卡链路），验收 SHALL 用 deep-equal 断言锁死。`AIDCP_POST_FORM_PROFILE` 开、`AIDCP_PUBLISH_TEXTCARD_CAROUSEL` 关时 SHALL 构成轮播影子模式：形态档与每槽内页形态照算照落审计、封面/内页照现版行为出图（`all_text_card` 不触发整帖渲卡），供运营核对纯卡源稿频率与内页判定准确率。审计结构 SHALL 扩展为携带**帖级 `formProfile`、每槽 `form`、每槽 `renderStatus`**，与既有 `CoverFormAudit` 字段并列落 ImageDirective 与发布元数据，面板 SHALL null-safe 解析（旧行为 null 不报错）。审计诚实红线不变：降级用了生成图 SHALL NOT 标 `text_card`，unknown/未判定 SHALL NOT 猜 `text_card`/`all_text_card`。

#### Scenario: 两枚新旗标全关零回归 deep-equal
- **WHEN** `AIDCP_POST_FORM_PROFILE` 与 `AIDCP_PUBLISH_TEXTCARD_CAROUSEL` 均关，跑全管线验收
- **THEN** 配图指令与现版 deep-equal（含既有封面文字卡链路），无新增运行时行为

#### Scenario: 轮播影子模式只判不渲
- **WHEN** `AIDCP_POST_FORM_PROFILE` 开、渲染旗标关，洗稿纯卡源稿发布
- **THEN** 形态档判 `all_text_card` 并落审计（每槽 form + profile + gateReason），但**内页照现版走生成式**、不触发整帖渲卡，运营可经面板/psql 核对判定质量

#### Scenario: 旧记录 null-safe
- **WHEN** 面板读取无 `formProfile`/每槽 `form` 字段的历史发布记录
- **THEN** 新字段解析为 null、不报错
