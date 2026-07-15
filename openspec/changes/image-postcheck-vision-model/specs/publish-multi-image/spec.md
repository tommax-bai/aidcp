## ADDED Requirements

### Requirement: 参照图整组视觉反推 SHALL 按视觉类型使用独立维度

参照洗稿携带有效图片且视觉反推旗标开启时，系统 SHALL 先对整组图片做序列/统一性/风格聚类和逐图类型判断，再按摄影、插画/3D、文字卡/海报、UI/文档、图表信息图、拼贴/混合的类型专用维度批量分析，最终输出可校验的 `setStyleBible + styleClusters + frameSpecs`。摄影类 MAY 描述镜头观感、焦段区间、景深、对焦和光线；非摄影类 MUST 使用版式、媒介、造型、网格、信息层级、图形语法或区域结构等对应字段，MUST NOT 把所有图片硬套相机参数。分析 MUST NOT OCR 或输出原图具体文字、数值、作者/摄影师身份或伪造精确 EXIF。

分析结果 SHALL 按有序图片抓取锚、provider/model 和 schema version 缓存；缓存命中零调用，任一锚变化即重算。模型不可用或严格解析失败时 SHALL 标 `unavailable/partial` 并回落既有风格，MUST NOT 编造分析结果。旗标关闭时 SHALL 保持现版规划/提示词行为。

#### Scenario: 非摄影图不反推相机参数
- **WHEN** 整组中一张图被分类为 UI 截图、一张为信息图
- **THEN** 两张分别输出组件/网格/层级与图形编码/图例/叙事顺序字段，不输出虚构焦距、相机型号或摄影师风格

#### Scenario: 视觉反推不搬运原图文字
- **WHEN** 原图为带大段文字的海报或文字卡
- **THEN** frame spec 只描述文本块占比、层级、对齐、字重对比和装饰，不返回或进入生图 prompt 的原图具体文案

#### Scenario: 缓存锚变化触发重算
- **WHEN** 同一精选行图片 capturedAt、可用 URL、顺序、模型或 schema version 任一变化
- **THEN** 旧分析不得当作当前缓存命中；重算失败时显式 unavailable，不伪造 analyzed

### Requirement: 参照图 SHALL 按生成槽建立主参考绑定

逐槽绑定旗标开启时，系统 SHALL 按有效源图顺序建立 `slot i → source frame i` 的主参考绑定，每槽默认只把本槽主参考图交给 provider；附加风格/身份锚必须由显式策略授权，MUST NOT 再把整组参考图无差别传给每一个槽。对顺序敏感的多图 provider，系统 SHALL 明确图片角色并把主参考图放在最后。1/3/8/9 图均 SHALL 保持源图顺序、图 0 封面位和缺图后的既有 M<N 保序语义。

#### Scenario: 三图洗稿逐槽独立绑定
- **WHEN** 三张有效源图生成三个槽且绑定旗标开启
- **THEN** 槽 0/1/2 的 primary 分别为源图 0/1/2，任一槽请求均不携带另外两张未授权源图

#### Scenario: Wan 主参考图最后输入
- **WHEN** 某槽绑定一张 style anchor 和一张 primary 且由 Wan 多图生成
- **THEN** 请求中 style anchor 在前、primary 在最后，prompt 明确图序角色；审计记录该槽真实绑定

#### Scenario: 绑定旗标关闭保持旧行为
- **WHEN** 视觉反推可存在但逐槽绑定旗标关闭
- **THEN** provider 输入与现版整组参考图行为等价，审计标为 legacy_all，MUST NOT 假称已逐槽绑定

### Requirement: 源图视觉语言 SHALL 优先于内容品类通用风格

源风格旗标开启且本槽 frame spec 可用时，提示词 SHALL 以本槽构图/主体/类型、所属风格簇和整组 style bible 为主；内容品类通用风格只补安全/合规约束，不得覆盖源风格。分析关闭、不可用或低置信时 SHALL 完整回落现版内容品类风格。文字卡 SHALL 继续使用确定性渲染，但 frame spec 可用时 SHALL 通过白名单设计令牌继承来源色板、背景处理、网格/装饰、信息卡形态、分页和层级；渲染器 MUST NOT 接收原图 URL、像素、坐标或 OCR 文本。UI/文档、图表、混合类在没有结构化重绘器时 SHALL 诚实标为 specialized/region-guided generative，MUST NOT 标为 deterministic redraw。

#### Scenario: 源风格覆盖通用品类风格
- **WHEN** 美食内容源图实际为冷色硬光、高对比极简静物，而通用品类档建议暖色生活感
- **THEN** 生图提示以源图冷色硬光、高对比极简构图为主，只保留 no-watermark/no-copy 等安全约束

#### Scenario: 分析不可用回落现版
- **WHEN** 本槽视觉分析 unavailable 或低置信
- **THEN** 使用现版品类风格并在审计标明 fallback，MUST NOT 编造源图风格

#### Scenario: 文字卡继承抽象版式而不搬运文本
- **WHEN** 一组参考图被识别为带薄荷色背景、细网格、圆角信息卡和分页标记的文字知识卡，且源风格旗标开启
- **THEN** 确定性渲染 SHALL 使用对应内部色板、网格、信息卡和分页令牌重排洗稿文案，不得继续使用无关账号色板，也不得读取或复制原图具体文案

#### Scenario: 大图集 specialist 有界分批
- **WHEN** 七至九张参考图属于同一文字卡 specialist family
- **THEN** 整组 pass SHALL 保持轻量，逐图公共结构和专用字段 SHALL 按固定小批量有界并发分析，MUST NOT 把全部大字段塞入一次易超时调用

### Requirement: 洗稿正文语义 SHALL 驱动逐槽人物表演

系统 SHALL 从洗稿后的标题、tone 与有界首/中/尾正文摘录中，为每个配图槽生成 `contentVisualBrief`，至少包含叙事瞬间、情绪、情绪强度、动作、环境和禁用项；人物画面 SHALL 进一步明确表情、视线、头部角度和肢体语言。最终生图提示 MUST 把参考图的职责限制为视觉类型、镜头/景别、构图、光影、色调与材质，把人物神态、动作和姿态交由正文 brief 决定；冲突时正文语义优先。人物参考 MUST 身份泛化，MUST NOT 复刻来源真人/名人五官、品牌 logo 或平台标识。

#### Scenario: 脆弱与行动力不生成证件照式人物
- **WHEN** 正文表达“脆弱、容易被触动，但能自我消化并保持行动力”，参考图是居中头肩人像
- **THEN** 本槽 brief SHALL 明确对应的复杂情绪、眼神/嘴角/肩颈状态和禁用的正面端坐/标准商业微笑；生成 prompt 保留参考图景别、光影和色调，但 MUST NOT 让参考图的中性姿态覆盖正文人物表演

#### Scenario: 长正文保留情绪转折
- **WHEN** 正文超过视觉导演输入上限且情绪结论位于中段或结尾
- **THEN** 系统 SHALL 使用确定性的首/中/尾有界摘录而不是只截前 400 字，确保视觉 brief 能看到叙事转折，同时保持模型输入有界

#### Scenario: 人物反推字段独立于摄影参数
- **WHEN** frame kind 为 `portrait_photo`
- **THEN** specialist SHALL 除镜头/光影字段外，输出可观察的表情、视线、头部角度、身体姿态、手势、姿态能量和情绪效价/唤醒度；这些字段描述来源画面，不得被当作覆盖正文 brief 的人物表演指令

### Requirement: 高风险配图产后视觉校验

产后审计旗标开启且槽位存在主参考图时，系统 SHALL 用视觉 / 多模态模型比较主参考与生成图，输出形态、主体、构图、色彩、风格五项分数；生成式槽存在 `contentVisualBrief` 时还 SHALL 输出 `contentAlignment`，核验叙事瞬间、情绪、神态、视线、动作和禁用姿态。确定性文字卡继续由既有卡面文案合规链核验内容，视觉保真审计 MUST NOT 为计算 `contentAlignment` 去 OCR 卡面文字，但 metadata 仍 SHALL 保留该槽正文 brief。系统同时核验来源真人/名人身份相似、乱码、画内水印、逐字复制与原创风险；清晰露脸的虚构人物本身 MUST NOT 被误判为可识别真人风险。内容不一致、硬风险或阈值不通过 SHALL 丢弃该次结果：生成式带审计指导有界重生成一次，确定性文字卡以严格来源设计令牌有界重渲染一次；第二次仍不过 SHALL 丢弃该槽。MUST NOT 因 prompt 写了 `faceless`/`no text`、provider 声称 `referenceStatus='used'` 或文字卡 renderer 返回成功就假定保真/合规。首轮视觉模型不可用时 MUST 标 `unverified` 并诚实保留原因；已有失败尝试后，后续 `unverified` MUST 丢槽，MUST NOT 用未知结果覆盖已知失败。合规 AI 标识仍走既有发布声明 / 元数据链路，MUST NOT 由模型在画面内绘制水印。

#### Scenario: 高风险图未过产后校验即重生成
- **WHEN** 一张含真人或封面文字的图产后校验判为「像可识别真人 / 名人」或「文字乱码」
- **THEN** 该张 MUST 丢弃并重生成，MUST NOT 因 prompt 含 faceless/no-text 约束就当作已合规照用

#### Scenario: 无真人无文字图不调视觉模型
- **WHEN** 产后审计旗标关闭、普通发布或参照洗稿槽没有主参考图
- **THEN** 系统不调用视觉保真审计，按现版产图；审计如实标 skipped/none，不伪造 pass

#### Scenario: 视觉模型不可用时诚实降级
- **WHEN** 产后校验所需的视觉模型不可用（未接入 / 超时 / 报错）
- **THEN** 系统 MUST 显式声明该张 `unverified` 并记录原因，MUST NOT 让校验静默返回 pass 当作已保真/合规

#### Scenario: 已知硬风险后审计超时不得放行
- **WHEN** 首次审计已判定可识别真人、乱码、水印、复制或高原创风险，重生成后的第二次审计超时/报错/不可解析
- **THEN** 该槽 MUST 丢弃并保留 failed + unverified 两次记录，MUST NOT 因第二次状态未知而把图片放回最终 imageUrls

#### Scenario: 二次仍不通过则丢槽
- **WHEN** 某槽首次审计失败并重生成一次，第二次仍存在硬风险或低于阈值
- **THEN** 该槽不进入最终 imageUrls，审计保留两次结果与丢弃原因，其余槽按既有保序语义继续

#### Scenario: 确定性文字卡也进入保真审计
- **WHEN** 文字卡 renderer 成功生成 PNG，产后审计旗标开启且槽位存在主参考图
- **THEN** 系统 SHALL 比较主参考与该 PNG 的形态/构图/色彩/风格，正文 brief 只存审计 metadata 而不触发 OCR 式 `contentAlignment`；首次失败以严格来源令牌重渲染一次，第二次仍失败则丢槽，MUST NOT 以 `deterministic text-card renderer` 为由直接标 skipped

### Requirement: 视觉参考和保真结果 SHALL 可审计

发布 metadata SHALL 逐槽持久化风格来源、内容视觉 brief、生成路由、source→slot→output 绑定、provider 参考使用状态、视觉审计状态/分数/风险/尝试次数，并区分 `used`（provider 声称消费参考图）与 `passed`（生成后视觉与正文语义审计通过）。历史记录无新字段时读取 SHALL null-safe。模型不可用、旗标关闭、路由降级和槽位丢弃均 MUST 有诚实状态，不得统一包装为成功。

#### Scenario: provider used 不等于保真 passed
- **WHEN** provider 返回 `referenceStatus='used'` 但产后视觉审计失败
- **THEN** metadata 同时记录 used 与 failed/retried/discarded，控制台不得展示“参考保真通过”
