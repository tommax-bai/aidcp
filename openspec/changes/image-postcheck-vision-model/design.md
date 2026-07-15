## Context

现版参照图路径已经能把最多 9 张有效图片交给 Wan 生图，也能诚实记录 provider 是否声称使用参考图；但 `ImageGenerator` 对每个槽传入同一整组图片，`ImagePromptComposer` 对每个槽套同一段 URL 指引和内容品类风格档。它缺少三个中间语义：原图是什么视觉类型、整组如何形成统一视觉语言、生成槽究竟应主要参照哪一张。因此“请求使用了图”与“结果忠于原图”之间没有可验证契约。

系统已有 `OpenAiCompatVisionClient`、`CoverFormSensor`、逐图形态缓存和 token usage 记账。新能力复用这些基础设施，但不扩大 `CoverFormSensor`：后者只回答文字卡门控所需的四分类；本 change 的分析结果服务于整组视觉规划和产后保真审计，是独立角色和独立缓存。

## Goals / Non-Goals

**Goals:**

- 对整组原图先建视觉模型，再规划输出；摄影与非摄影使用不同反推维度。
- 建立稳定的 source→slot→output 绑定，避免每槽共享整组参考图。
- 让源图视觉语言优先于硬编码内容品类风格，并保留 flag-off 等价行为。
- 让洗稿后的正文语义明确控制人物神态、视线、动作和肢体语言，避免主题在层间压缩成中性“端正人像”。
- 用产后视觉比较确认保真和高风险约束，失败时有界重试、不可用时诚实未核验。
- 缓存、记账、可审计、面板可解释；不增加 edge/protocol 变化。

**Non-Goals:**

- 不 OCR、不复制原图具体文案；相关能力由 `transcribe-textcard-image-text` 独立承接。
- 不在首版实现 UI/图表确定性重绘器。
- 不把视觉模型评分包装成人工验收或绝对原创证明。

## Decisions

### D1：一个编排角色，三阶段分析，而不是一个通用大 prompt

`VisualReferenceAnalyzer` 内部执行：

1. **Set pass**：看全部有效图，只输出顺序语义、统一性、风格簇及每图视觉类型，不在这一轮重复输出逐图公共细节。
2. **Specialist pass**：按 specialist family 分组，并按固定小批量有界并发调用；每批补齐逐图公共结构和类型专用字段，避免七至九张文字卡在一次大输出中触发超时。
3. **Aggregate**：纯代码校验和归一化为 `setStyleBible + styleClusters + frameSpecs`。

类型枚举：`portrait_photo | still_life_photo | scene_photo | illustration_3d | text_layout | ui_document | infographic_chart | collage_mixed`。

公共字段描述画幅、主色、色温、对比、密度、留白、视觉层级、情绪、材质、构图锚和禁止项。专用字段分别为：

- 摄影：镜头观感/等效焦段区间、机位、景深、对焦、自然/硬/柔/逆光、色彩处理、颗粒/锐度；人物摄影另输出可观察的表情、视线、头部角度、身体姿态、手势、姿态能量和情绪效价/唤醒度。只输出可从像素合理观察的区间，不伪造 EXIF/摄影师身份。
- 插画/3D：媒介、笔触/渲染、造型语言、轮廓、材质、光照模型、透视、细节等级。
- 文字卡/海报：网格、文本块占比、层级、对齐、字重对比、色块/装饰、留白；不输出具体文字。
- UI/文档：设备/视口、网格、组件密度、边框/圆角、层级、信息分区、背景；不抄界面内容。
- 图表信息图：图形类型、编码通道、轴/图例位置、标注密度、数据墨水比、叙事顺序；不读取具体数值。
- 拼贴/混合：区域划分、各区域类型、层叠/遮挡、统一色彩/纹理桥接方式。

### D2：分析缓存属于精选素材，不属于某次发布

`curated_content.visual_analysis JSONB` 保存完整分析和 provenance。cache key 由 schema version、provider、model、按顺序的 `{index,capturedAt,usableUrl}` 组成。图片重抓、排序或模型/schema 变化即失效；命中时零视觉调用。失败结果不写成 analyzed，允许下次重试；分析回写不更新内容 `updated_at`，避免扰乱精选排序。

### D3：每槽一个主参考，风格/身份锚必须显式授权

默认绑定为 `slot i → source frame i`。主参考图 role=`primary`，若未来策略需要跨槽统一，可显式附加 role=`style` 或 `identity`；首版不自动把真人身份图跨槽扩散。provider 仅收到本槽绑定，且 Wan 请求中辅助图在前、主参考图在最后，prompt 用“图1/图2”明确角色。缺失源图不挪用别槽图片，保持 M<N 的既有保序语义。

### D4：源风格优先，内容品类风格只兜底

当 frame spec 有效且源风格旗标开启时，prompt 由 frame spec 的构图/主体/视觉类型 + 所属 style cluster + set style bible 组成；内容品类风格档只补安全约束（no watermark、避免逐字复制等），不得覆盖源风格。分析关闭、不可用或低置信时完整回落现版品类风格。

文字卡仍由确定性 renderer 处理，但源风格可用时先从 frame/style bible 派生白名单设计令牌：内部色板键、版式、背景处理、装饰网格、要点卡形态、分页标记和中文词组断行。渲染器只接这些离散令牌与洗稿文案，不接原图 URL、像素、坐标或 OCR 文本；源风格关闭/不可用时仍逐字节回落现有账号模板。UI/文档、图表首版 route=`specialized_generative`，混合类 route=`region_guided_generative`；审计明确 `structuredRedraw=false`，不声称已结构化重绘。

### D4.1：正文视觉导演决定人物表演，参考图不决定人物身份

`ImageSetPlanner` 在现有一次模型调用内同时完成槽位选题和内容视觉导演，不新增串行模型调用。输入正文采用有界首/中/尾摘录，避免只读前 400 字丢失情绪转折；每槽输出：

- `narrativeMoment / emotion / emotionIntensity / action / environment / avoid`；
- 人物画面可选 `facialExpression / gazeDirection / headAngle / bodyLanguage`。

`ImagePromptComposer` 必须把该 brief 原样纳入提示词，并声明冲突优先级：参考图只约束视觉类型、景别、构图关系、光影、色调和材质；人物神态、视线、动作与姿态由正文 brief 决定。人物参考只作为抽象摄影锚，输出人物必须身份泛化为与来源人物无关的虚构主体，不得保留可识别五官、名人相似度、品牌 logo 或平台标识。

### D5：产后审计是视觉比较，不是 prompt 自证

`VisualFidelityAuditor` 输入主参考、生成图、期望 frame/style 摘要及本槽 `contentVisualBrief`，严格输出：

- `form/subject/composition/color/style` 五项 0–1 分；有正文 brief 时另输出 `contentAlignment`，核验叙事瞬间、情绪、神态、视线、动作和禁用姿态；
- `recognizableRealPerson/garbledText/watermark/copiedText/originalityRisk` 风险布尔或等级；
- `pass`、失败原因与可操作 retry guidance。

通过阈值由代码默认值 + env 可调；内容一致性与硬风险任一不通过都 fail。生成式失败只为该槽重生成一次，并把 audit guidance 附到第二次 prompt；确定性文字卡失败则以严格来源设计令牌重渲染一次。第二次仍失败则丢槽。首轮审计模型未配置、超时或解析失败时可按既有人审草稿链保留但状态必须为 `unverified`；若已有任一失败尝试，后续审计 `unverified` 必须丢槽，不能用不可用结果覆盖已知失败。确定性 renderer 成功只表示“渲染成功”，不得因此把视觉审计记为 `skipped` 或 `passed`。

### D6：角色、旗标与超时

- `AIDCP_REFERENCE_VISUAL_ANALYSIS`：执行并缓存反推；默认 off。
- `AIDCP_REFERENCE_VISUAL_BINDING`：启用逐槽绑定；默认 off，关时维持整组参考图旧行为。
- `AIDCP_REFERENCE_SOURCE_STYLE`：源风格优先；默认 off。
- `AIDCP_VISUAL_FIDELITY_AUDIT`：产后审计和有界重试；默认 off。
- `AIDCP_REFERENCE_VISUAL_TIMEOUT_MS`：单次视觉分析调用超时；整组轻量 pass 与 specialist 小批次共用，默认 120s。
- `AIDCP_REFERENCE_VISUAL_SPECIALIST_BATCH_SIZE`：单个 specialist 请求的图片上限，默认 3，非法值回落默认。
- 分析/审计 provider/model 分别可由独立 env 覆盖，默认 DashScope + `qwen3.7-plus`。

角色恒写管线键，未触发写 `none/disabled`，异常写 `unavailable`，避免 waitAll 挂死。所有调用经现有 usage hook 记账，绝不硬编码厂商价格。

## Data Flow

```text
referenceNote.images
  -> cache lookup / VisualReferenceAnalyzer
  -> lightweight set pass + bounded specialist batches
  -> setStyleBible + styleClusters + frameSpecs
rewritten title/body/tone
  -> ImageSetPlanner as content visual director (slot theme + contentVisualBrief)
reference analysis + contentVisualBrief
  -> ImagePromptComposer (content performance first; source camera/style; category fallback)
  -> text-card design tokens (palette/grid/cards/pagination; no source pixels or OCR)
  -> ImagePlan.referenceBindings[slot]
  -> ImageGenerator / deterministic renderer / provider (slot-local refs, primary last)
  -> VisualFidelityAuditor (reference vs output)
  -> bounded regenerate or rerender / discard
  -> ImageDirective + publish metadata + console audit
```

## Failure and honesty matrix

| Failure | Runtime behavior | Audit truth |
|---|---|---|
| analyzer disabled | existing planning/generation | `analysis.status=disabled` |
| analyzer unavailable/invalid JSON | category style fallback；状态继续透传到执行审计 | `unavailable` + reason，不得降成 `none` |
| cached analysis stale | recompute; failure does not reuse stale as current | provenance shows current failure |
| binding disabled | exact legacy all-reference behavior | binding mode=`legacy_all` |
| provider does not support refs | existing fallback/failure semantics | `unsupported/unavailable`, never `used` |
| deterministic text-card rendered | compare against the slot primary reference | `passed/failed/unverified`, never automatic `skipped` |
| auditor unavailable | no fake pass; keep draft under existing human approval semantics | `unverified` + reason |
| retry audit unavailable after a prior failure | discard slot; do not let unknown override known failure | failed + unverified attempts retained, final `discarded` |
| audit fail twice | discard slot, preserve remaining order | attempts and fail reasons retained |

## Risks / Trade-offs

- **视觉模型会把不可观察信息说得过实**：schema 禁止具体相机型号、摄影师姓名和精确 EXIF，只允许“观感/区间/推测”。
- **多类型组增加延迟**：先整组一次、再按 family 批量；并发上限与总图数上限沿现有 9 图约束。
- **源风格可能包含平台水印或侵权元素**：风格只提取抽象视觉属性；禁止项、无水印、无逐字复制及原创风险审计仍优先。
- **自动相似度与原创性冲突**：审计同时要求结构/风格保真和不逐字复刻，分项展示而不是单一“越像越好”。
- **正文情绪与参考人物姿态冲突**：参考图只保留摄影语言，人物表演以正文 brief 为准；身份始终泛化，不把“内容提到某人”理解为允许复刻其脸。
- **与 OCR change 都会读取图片/扩精选行**：字段、角色和用途完全分离；视觉分析不得输出文本，OCR 不参与视觉风格 prompt。

## Migration / Rollout

1. 加可选列、类型、角色和审计字段，四旗标全关；目标测试与 flag-off deep-equal。
2. dev 只开分析影子，观察真实 1/3/8/9 图的分类、分组调用、缓存命中、耗时与账单。
3. 开逐槽绑定，再开源风格；与现版同素材做人工 A/B，关注错图参照和风格漂移。
4. 开产后审计，观察首过率、重试率、丢槽率和 `unverified`；阈值调整必须保留审计记录。
5. 秒级回滚：对应旗标 off；新列和历史 metadata 惰性保留、旧读路径 null-safe。

## Open Questions

- UI/图表确定性重绘器后续应接 HTML/SVG、设计模板还是专门图表渲染服务；本 change 不冒进。
- 真人身份锚何时允许跨槽，需要单独的隐私/授权策略，首版不自动启用。
- 真实样本 A/B 的最终阈值需由 dev 样本确定，自动评分不能替代人工判断。
