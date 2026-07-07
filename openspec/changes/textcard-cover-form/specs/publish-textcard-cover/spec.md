# publish-textcard-cover — 发布管线封面形态决策、执行分支与影子模式

## ADDED Requirements

### Requirement: 封面形态决策角色恒写键且门禁零智能

系统 SHALL 新增发布管线决策角色 `CoverCardWriter`：watch `[createdContent, postCategory]` waitAll、与图集选题角色并行。内部顺序 SHALL 为：参照图存在 → 感知（**仅由感知旗标门控、先于且独立于渲染旗标执行**，影子模式在此完成注解与审计落盘）→ 渲染旗标 → 形态与置信 → 渲染出口与 OSS 上传器可用；任一门禁不过 SHALL 零文案 LLM 调用、写生成式兜底并记门禁原因（gateReason）。全过 SHALL 调一次文本模型产出卡片文案 `CoverCardCopy{title, bullets 0-5, tags ≤3}`。该角色 SHALL 恒写管线键 `coverCardPlan`（含 LLM 失败时的默认兜底输出，fallback 'skip'），下游合流 SHALL NOT 因此挂死。角色闸 SHALL ≈240s（感知 30s + 一次文案 180s + 余量）；文案违规重试 SHALL 只在角色闸剩余预算内执行一次，预算不足直接回落生成式。提示词组装角色 SHALL waitAll 扩三键、把决策原样盖章透传进配图计划，且即使决策为 text_card 也照常产出 0 号生成式封面提示词（降级兜底就位）、其余组装逻辑不变。

#### Scenario: 渲染旗标关但影子感知照跑
- **WHEN** 感知旗标开、渲染旗标关（影子模式），洗稿发布含参照图笔记
- **THEN** 感知照常执行且注解/审计照落，随后门禁在渲染旗标处落 `gateReason='flag_off'`、零文案 LLM 调用、恒写生成式兜底，封面走生成式

#### Scenario: 文案 LLM 失败恒写兜底
- **WHEN** 门禁全过但卡片文案 LLM 超时/失败
- **THEN** 恒写生成式兜底键、`gateReason='copy_llm_failed'`，绝不因文字卡失败丢整帖配图或挂死下游合流

#### Scenario: 缺失绝不猜形态
- **WHEN** 感知返回 unknown（失败/低置信/未感知）或行无参照图
- **THEN** 分别落 `form_unknown` / `no_reference_images`、封面走生成式，绝不把缺失猜成 text_card

### Requirement: 卡面文案独立与产后校验（防搬运）

卡片文案提示词 SHALL 只喂洗稿后的标题/正文/标签，SHALL NOT 包含原笔记正文或原图任何文本。产后校验器（可读原文但原文不入生成 prompt）SHALL 断言：卡面标题不等于原笔记标题（去空白标点归一化后）；卡面任一文本行与原标题/正文无 ≥12 连续字符逐字重叠；卡面不含原作者名/平台水印词/二维码/联系方式/价格促销用语；并通过既有违禁词闸。违规 SHALL 带更紧约束重试一次（角色闸剩余预算内），仍违规 SHALL 回落生成式并审计违规原因。

#### Scenario: 逐字重叠违规重试后回落
- **WHEN** 文案模型产出的某要点与原正文存在 12 字以上连续逐字片段
- **THEN** 判违规、带紧约束重试一次；仍违规则封面回落生成式且审计记录违规原因

#### Scenario: 引流卡面拒发
- **WHEN** 卡面文案含微信号或价格促销词
- **THEN** 拒绝并走同一重试/回落链，绝不发布引流卡面

### Requirement: 执行分支与诚实降级链

文字卡渲染器 SHALL 作为可注入依赖挂在配图执行角色上。决策为 text_card 且文案、渲染器、OSS 上传器俱备时，0 号封面槽 SHALL 由本地渲染 + 字节直传 OSS 产出：渲染+直传 SHALL 在进入每图超时槽机制**之前独立结算**（内层闸 env `AIDCP_TEXTCARD_RENDER_TIMEOUT_MS`，默认 30s），成功即替换 0 号槽产出（不前插、不移位，seq/imageCount/内页序全不变）；失败 SHALL 立即以**完整每图槽预算**用计划内恒在的 0 号生成式提示词走生图路径（角色总闸公式相应加渲染超时项）。双失败 SHALL 沿用既有少图保序语义（封面由首张成功内页顶上，全失败走既有纯文字降级判定）。执行角色 SHALL 只依据配图计划与注入依赖可用性行事，SHALL NOT 二次读取环境旗标（防决策/执行裂脑）。

#### Scenario: 渲染成功替换封面槽
- **WHEN** 渲染成功
- **THEN** 0 号槽为渲染卡 OSS URL、内页 seq 与数量不变、审计 `renderStatus='rendered'` 且带主题键

#### Scenario: 渲染失败以完整槽预算走生成式
- **WHEN** 渲染超时或 OSS 直传失败
- **THEN** 立即用 0 号生成式提示词走生图路径且享有完整每图槽预算（不因先渲染被挤占）、审计 `renderStatus='render_failed_generative'`，无任何静默环节

#### Scenario: 双失败沿既有少图语义
- **WHEN** 渲染与生成式封面双失败
- **THEN** 0 号槽诚实落空、复用既有 M<N 保序过滤、审计 `renderStatus='render_failed_none'`，与现版降级语义一致

### Requirement: 旗标、影子模式与零回归

感知与渲染两枚旗标 SHALL 默认关闭；两枚全关时管线行为 SHALL 与现版等价（仅多恒写的管线键与常量审计字段，验收 SHALL 用 deep-equal 断言锁死）。感知开 + 渲染关 SHALL 构成影子模式（注解与审计照落、封面照走生成式）。行无参照图或参照图开关关闭时 SHALL 自然落 `no_reference_images`，无需第二开关。新增审计结构 `CoverFormAudit{coverForm, sensedForm, sensedSource, gateReason, renderStatus, renderMeta?}` SHALL 与参照图审计并列落 ImageDirective 与发布元数据，面板 SHALL null-safe 解析（旧行为 null 不报错）。审计诚实红线：降级用了生成图 SHALL NOT 标为 text_card，unknown SHALL NOT 猜成 text_card。

#### Scenario: 全关零回归 deep-equal
- **WHEN** 两枚旗标全关跑全管线验收测试
- **THEN** 配图指令除新增常量字段外与现版 deep-equal，且新管线键恒被写（防合流挂死）

#### Scenario: 影子模式可核准确率
- **WHEN** 感知开渲染关，洗稿发布含参照图笔记
- **THEN** 形态注解落素材行、审计带 sensedForm/gateReason，封面仍为生成式，运营可经面板 API / psql 核对判定质量

#### Scenario: 旧记录 null-safe
- **WHEN** 面板读取无新审计字段的历史发布记录
- **THEN** 审计字段解析为 null、不报错
