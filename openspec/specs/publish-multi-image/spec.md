# publish-multi-image Specification

## Purpose
TBD - created by archiving change publish-multi-image. Update Purpose after archive.
## Requirements
### Requirement: 配图张数由正文决定并夹在安全范围

图集选题角色 `ImageSetPlanner` SHALL watch `createdContent`、读正文（并在洗稿场景读源参照笔记有效图数）决定本帖配图张数与每张主题，写键 `imageSetPlan`。张数 SHALL 经规则**夹取**到安全范围：默认上限 9（`AIDCP_PUBLISH_MAX_IMAGES` 未设时的代码默认；env 可覆盖）、下界 ≥1（`wantImage === true` 时图文帖不能 0 张）、硬上限 MUST NOT 超过 9（平台上界）。

张数决策 SHALL 按是否洗稿分流：

- **洗稿帖**——触发含源参照笔记（`trigger.generateInput.referenceNote`）且其**有效图** ≥1 张（有效 = `ossUrl ?? sourceUrl` 可用，口径与生图参考图一致 `referenceImagesForGeneration`）：`imageCount` SHALL = `clamp(有效源图数, 1, 上限)`（对齐源稿体量）。选题角色 SHALL 要求 LLM 产出等量主题；主题不足 SHALL 由系统补齐至该数（图 0 恒封面/钩子位）。
- **非洗稿 / 无有效源图**：`imageCount` SHALL 取 LLM 读正文的判断值并 `clamp(1, 上限)`（维持内容驱动）。

选题角色 MUST NOT 调用图源、MUST NOT 产出万相 prompt（纯内容决策）；读源参照笔记 SHALL 经管线上下文快照，MUST NOT 因此把 `trigger` 加进 watchKeys（`createdContent` 就绪时 trigger 必在快照内）。源参照笔记的图 SHALL 仅用于「决定张数 + 作生图参考」，MUST NOT 被直接搬运当配图。

#### Scenario: 洗稿按源稿有效图数出等量图

- **WHEN** 洗稿触发含源参照笔记、其有效图为 N 张（N ≤ 上限），`ImageSetPlanner` 激活
- **THEN** `imageCount === N`、`themes` 长度 === N（不足由系统补齐、图 0 为钩子/封面位），产图数对齐源稿体量

#### Scenario: 源图数超上限被夹回

- **WHEN** 洗稿源有效图 > 上限（如 12 张、上限 9）
- **THEN** `imageCount` SHALL 夹回 `上限`（9），绝不超过平台上界

#### Scenario: 非洗稿内容定张数、规则夹安全范围

- **WHEN** 非洗稿（无源参照笔记 / 源无有效图），`createdContent` 就绪、`ImageSetPlanner` 激活
- **THEN** 产出 `imageSetPlan`（含 `wantImage` / `imageCount` / `themes` / `styleHint`），`imageCount` 取 LLM 判断值并 `clamp(1, AIDCP_PUBLISH_MAX_IMAGES≤9，默认 9)`；`themes` 长度与 `imageCount` 一致

#### Scenario: 越界张数被夹回

- **WHEN** LLM 给出 0 或 > 上限的张数 / 主题数
- **THEN** 规则 SHALL 夹回 `[1, 上限]`；`wantImage:true` 下永不产出 0 张

#### Scenario: 选题角色不碰图源与话术

- **WHEN** 为 `ImageSetPlanner` 写单测
- **THEN** 只需桩内容决策 LLM 与快照里的源参照笔记、无需桩图源；其依赖中不含 `ImageProvider`

### Requirement: N 张主题与画图指令分两决策角色规划且画面各异

配图指令角色 `ImagePromptComposer` SHALL watch `imageSetPlan`、把每个主题翻成一条**各不相同**的文生图 prompt（叙事递进、不重复画面），共享一份**按内容品类选定的风格档**（模板常量派生，MUST NOT 由 LLM 产出），写键 `imagePlan`（`imagePrompts: string[]`）。风格档 SHALL 由本帖 `imageSetPlan.category` 经 `resolveStyleProfile()` 解析得到，并在本帖图 1..N 之间**逐字复用同一档**（保「图集帧内一致」不变量）；图 0（封面位）SHALL 用该档的封面变体。指令角色 SHALL 仍是决策角色（有自己的超时/降级），MUST NOT 调用图源。去重护栏 SHALL 丢弃归一化后近似的 prompt（命中即丢、不补不复用），但 SHALL **永远保留第 0 个**（封面位），使 `wantImage:true` 时 `imagePrompts` 恒非空。

#### Scenario: 主题翻成各异指令、共享本帖品类风格档
- **WHEN** `imageSetPlan.wantImage === true` 且含 N 个主题
- **THEN** `ImagePromptComposer` 产出 `imagePlan.imagePrompts`（N 条各异 prompt，每条 = 主题语义 + 本帖品类风格档），风格档取自 `resolveStyleProfile(imageSetPlan.category)` 而非 LLM 输出，图 1..N 逐字复用同一档

#### Scenario: 去重护栏丢近似但保住封面位
- **WHEN** LLM 产出的若干 prompt 归一化后近似
- **THEN** 护栏丢弃近似项、不补不复用，但第 0 个（封面位）恒保留；最终 `imagePrompts.length ≥ 1`

#### Scenario: 指令角色不碰图源
- **WHEN** 为 `ImagePromptComposer` 写单测
- **THEN** 只需桩话术 LLM、无需桩图源；其依赖中不含 `ImageProvider`（决策/执行解耦红线）

### Requirement: 并行出图且每张独立计时绝不清零已成功图

配图生成角色 `ImageGenerator` SHALL 按 `imagePlan.imagePrompts` **并行**调图源生成（`Promise.allSettled`），全部 settle 后把成功的真实 URL 按**规划顺序**收进 `imageDirective.imageUrls`（[0] 为钩子图/封面位）。计时 SHALL **下沉到每张图**：每张独立超时（env `AIDCP_PUBLISH_PER_IMAGE_TIMEOUT_MS`），某张超时 / 失败 SHALL 只丢该张、不影响其余张，MUST NOT 把已成功生成的图整体清零。并发上限 SHALL 可经 env `AIDCP_PUBLISH_IMAGE_CONCURRENCY` 配置（防图源突发限流）。角色级总闸 SHALL 设为 ≈ 每图超时 + 余量（并行下 wall-clock 为最慢单张、非各张相加），且即便触发 SHALL 用"已 settle 的成功 URL"构造产出、MUST NOT 返回空产出丢弃已成功图。失败那张 MUST NOT 进入 `imageUrls`（不补空、不复用别张 URL）。

例外（textcard-cover-form / textcard-carousel-form-parity）：当配图计划携带帖级形态档与卡面文案集 `cardSet` 且渲染依赖（渲染器、OSS 上传器）经**整帖预检**俱备时，**凡对应 `cardSet[i]` 非空的槽** MAY 由注入的确定性文字卡渲染器产出以替换该槽结果（不前插、不移位）——`card_cover` 档仅 0 号封面槽如此，`all_text_card` 档为每一槽（键 `${seq}.png`）。每槽渲染 + 字节直传 SHALL 在进入该槽每图超时槽机制**之前独立结算**（独立内层闸，默认 30s），某槽渲染失败后 SHALL 以**完整每图槽预算**用计划内恒在的该槽生成式提示词走图源路径（角色级总闸公式相应加渲染超时项，MUST NOT 让渲染耗时挤占生成式兜底的每图预算），且**只降级该槽**、不牵连其余槽。渲染器 MUST NOT 实现生图提供方接口、MUST NOT 进入图源路由表；所有渲染卡与生成式配图 SHALL 同尺寸（帧内一致）；其余各张与全部失败语义不变。

#### Scenario: 部分图超时只丢该张、保留已成功
- **WHEN** 并行生成中第 k 张超时 / 失败，其余张成功
- **THEN** `imageDirective.imageUrls` 含所有成功张的真实 URL（按规划顺序）、不含第 k 张，不因单张失败清零或中断其余张

#### Scenario: 红线——总闸超时清零已成功图（反例）
- **WHEN** 任一实现让角色级总闸 `Promise.race` 在 `allSettled` 结算前到点即返回空产出，丢弃已生成成功的 URL
- **THEN** MUST 视为违规、不予合入（已成功图绝不被外层超时清零；总闸须 ≥ 每图超时 + 余量、超时也返回已 settle 结果）

#### Scenario: 生成角色单测只桩图源
- **WHEN** 为 `ImageGenerator` 写单测
- **THEN** 只需桩图源、无需桩任何 LLM；并行计时、保序累积、部分成功收集逻辑可脱离真实图源验证

#### Scenario: 文字卡渲染独立结算不挤占生成式兜底预算
- **WHEN** 某槽先尝试文字卡渲染并在 30s 内层闸耗尽后失败，随即落回生成式提示词走图源
- **THEN** 生成式兜底享有完整每图槽预算（渲染耗时不计入），不出现「渲染 30s + 图源轮询尾部 + OSS 转存 > 每图槽」导致兜底图在收尾前被总闸砍掉的尾部回归

#### Scenario: 轮播档每槽渲染键不碰撞
- **WHEN** `all_text_card` 档整帖渲卡，每槽写 OSS 键 `${seq}.png`
- **THEN** 各槽键互不碰撞、且与生成式基名 `${seq}` 不并存（一个槽只有一种产出），imageUrls 按规划顺序收齐 N 张渲染卡

### Requirement: 部分成功诚实发已成图全失败诚实失败并记真实附着数

发布 SHALL 按真实图数诚实收敛：生成成 M 张（`imageDirective.imageUrls.length === M`）时，`M ≥ 1` SHALL 照常发布该 M 张、`M === 0` SHALL 诚实判 `failed`（判据为成功图数组为空，不再以单图 URL 判定）。下发上传 SHALL 按真实成功上传条数 K 记账（取代"任一图失败即整体降级"）：`K ≥ 1` 即有效帖、发已成功的 K 张；`K === 0` 才 `failed`。记录 SHALL 落**真实附着张数**（`images_attached_count`），`images_attached` 派生为 `count > 0`。`submit_publish` 成功后任何超时 MUST NOT 把记录翻成 `failed`。

#### Scenario: 想要 N 张成 M 张（M≥1）照发 M 张
- **WHEN** 计划 N 张、实际生成成功 M 张（1 ≤ M < N）
- **THEN** 发布按 M 张继续，失败那 N−M 张不补空、不复用 URL；记录 `images_attached_count` 反映真实附着数

#### Scenario: 全部生成失败（M=0）诚实失败
- **WHEN** `imageDirective.imageUrls.length === 0`
- **THEN** 执行端落库 `status='failed'`、`images_attached=false`、`images_attached_count=0`，MUST NOT 发审批卡、MUST NOT 下发任何指令、MUST NOT 走纯文字必败路径

#### Scenario: 上传按真实成功数 K 记账
- **WHEN** 下发 M 张上传、边缘成功上传 K 张（1 ≤ K ≤ M）
- **THEN** 帖子有效、`images_attached_count = K`；仅当 K===0 才判 failed

#### Scenario: 红线——附着数虚报或提交后翻失败（反例）
- **WHEN** 任一实现把 `images_attached_count` 记为计划数 M（而非真实 K）、或在 `submit_publish` 成功后因超时把已发布记录翻成 `failed`
- **THEN** MUST 视为违规、不予合入（附着数必须如实、提交成功不可静默翻失败）

### Requirement: 多图封面恒取成功序列首张且本期不引入封面索引

多图封面 SHALL 恒取成功生成序列的第一张（`imageUrls[0]`，即钩子图），由 `CoverSelector` 产出。本 change MUST NOT 引入封面索引字段、MUST NOT 改动命令序列的 `set_cover` 触发条件（保持仅 `images.length > 1` 才下发的现状），从而 MUST NOT 提前接通"选非首图 → 真正下发 set_cover"这条会踩边缘未校准设封面操作的路径。选非首图当封面 / 美学或 LLM 选封面 / 边缘设封面 DOM 真机校准 SHALL 留待独立后续 change。

#### Scenario: 封面取首张
- **WHEN** `imageDirective.imageUrls` 含 M(≥1) 张成功图
- **THEN** `CoverSelector` 产出封面 = `imageUrls[0]`、`hasCover = true`；下发 `cover` 指向该首张

#### Scenario: 本期不接通非首图封面
- **WHEN** 审视本 change 的封面选择与下发
- **THEN** 不存在 `coverIndex` 字段、命令序列 `set_cover` 触发条件未改（平台默认首图即封面，单图与多图均不依赖真正下发 set_cover 即可正确）

### Requirement: 参考图使用状态必须如实持久化

当参照洗稿触发输入携带原文参考图时，配图生成链路 SHALL 将图片 provider 对参考图的真实使用状态汇总为发布审计字段并持久化。审计字段 MUST 至少包含请求参考图数量、可用参考图数量、生成图数量、状态枚举（`used` / `unsupported` / `unavailable` / `skipped` / `none`）以及 provider 是否声称实际使用参考图。provider 不支持参考图时 MUST 记录 `unsupported`，MUST NOT 把“传了 URL 给文生图 prompt”标记为已使用参考图。普通发布或未携带参考图时 SHALL 记录 `none` 或不展示，MUST NOT 编造参考图审计。

DashScope/Wanxiang provider 在使用支持图像输入的 Wan 2.7 image 模型且收到可用参考图 URL 时，SHALL 将参考图作为图片输入提交给 Wan 2.7，而不是只把 URL 写进文本 prompt。只有 provider 请求确实包含图片输入且返回真实新图 URL 时，系统 MAY 标记参考图状态为 `used`。若参考图请求因密钥缺失、provider 拒绝、任务失败、超时或缺少结果 URL 而未产出真实新图，系统 SHALL 标记为 `unavailable` 或保留失败状态，MUST NOT 标记为 `used`。

#### Scenario: provider 不支持参考图时记录 unsupported
- **WHEN** 参照洗稿携带 2 张可用参考图，图片 provider 返回 `referenceStatus='unsupported'`
- **THEN** 发布记录的参考图审计显示 requestedCount=2、usableCount=2、status=`unsupported`、providerClaimedUsed=false，MUST NOT 显示为 `used`

#### Scenario: provider 实际使用参考图时记录 used
- **WHEN** 参照洗稿携带参考图，图片 provider 返回 `referenceStatus='used'`
- **THEN** 发布记录的参考图审计显示 status=`used` 且 providerClaimedUsed=true

#### Scenario: 无参考图不伪造审计
- **WHEN** 普通发布或参照洗稿选择仅文本参照
- **THEN** 发布记录不显示“已使用参考图”，审计状态为 `none` 或空值

#### Scenario: Wanxiang 使用图片输入生成参考图
- **WHEN** 当前图片厂商为 `dashscope`、图片模型为 Wan 2.7 image 模型、且 `ImageGenerator` 向 provider 传入可用 `referenceImages`
- **THEN** Wanxiang provider 的提交请求包含这些参考图 URL 作为 `image` content，并包含生成指令作为 `text` content
- **AND** 成功返回真实新图 URL 时 provider 返回 `referenceStatus='used'`、`referenceUsed=true`

#### Scenario: Wanxiang 参考图请求失败不伪装 used
- **WHEN** Wanxiang 参考图请求因缺密钥、HTTP 错误、任务失败、轮询超时或响应缺少图片 URL 而未生成真实新图
- **THEN** provider 返回 `referenceStatus='unavailable'`、`referenceUsed=false`，该张图按既有失败语义不进入 `imageUrls`

### Requirement: 配图生成支持可选参考图且失败诚实

发布配图链路 SHALL 支持可选参考图输入。参考图输入 MUST 从 `referenceNote.images` 派生，经过账号隔离、数量上限和可用 URL 过滤后进入图片计划/生成链路。图片选题与提示词角色 MAY 使用参考图元数据或引用来调整图集节奏和视觉约束，但 MUST NOT 调用图源；只有 `ImageGenerator` 可把参考图传给 `ImageProvider` 执行生成。

`ImageProvider.generate` SHALL 扩展可选参考图参数，并对 provider 支持情况诚实回报。支持参考图的 provider MAY 走图像参考/编辑端点生成新图；不支持参考图的 provider MUST 返回明确状态或触发显式 prompt-only 降级。无论哪种路径，最终 `imageDirective.imageUrls` 仍只包含真实生成成功的新图 URL，失败那张不进数组，不补空、不复用原图、不伪造。

#### Scenario: 参考图进入生成执行层

- **WHEN** `ImagePlan` 含可用 `referenceImages`
- **THEN** `ImageGenerator` 调用 `ImageProvider.generate(prompt, { referenceImages })` 或等价契约，由 provider 决定具体 API 形态

#### Scenario: 决策角色不调图源

- **WHEN** `ImageSetPlanner` 或 `ImagePromptComposer` 读取视觉参考信息
- **THEN** 它们只能产出主题、提示词或计划元数据，MUST NOT 下载图片、上传图片或调用图片 provider

#### Scenario: provider 不支持参考图时诚实降级

- **WHEN** 当前选中图片 provider 不支持参考图输入
- **THEN** 系统 MUST 标记参考图未使用或 prompt-only 降级，MUST NOT 在审计中声称已参考图片

#### Scenario: 单张参考生成失败只丢该生成图

- **WHEN** 某张图片生成因参考图不可用、provider 失败或超时而失败
- **THEN** 该生成图不进入 `imageUrls`，其它成功生成图保留，部分成功和全失败语义沿用既有多图能力

#### Scenario: 红线反例 - 原图充当生成成功图

- **WHEN** provider 参考生成失败，有实现把原笔记参考图 URL 塞进 `imageDirective.imageUrls` 充数
- **THEN** MUST 视为违规，不予合入；`imageUrls` 只能包含本次真实生成的新图 URL

### Requirement: 配图风格按内容品类自适应（帖内一致、帖间有别）

系统 SHALL 以「内容品类 → 风格档」注册表取代任何**全局单一固定风格常量**。系统 SHALL 由一个**独立的品类判定步骤**（发布侧、读正文、单一职责，一帖判一次）判出本帖 `category`（取自固定字面枚举，含一个安全兜底档）并写入管线状态，供配图选题与质量评审**复用同一值**；分类失败 / 未知 MUST 回落兜底档、MUST NOT 阻断配图（绝不 brick）。每档 `StyleProfile` SHALL 覆盖媒介/风格族、色板、光线、构图、质感、人物策略、比例与封面变体。风格档 MUST 仍为模板常量派生、MUST NOT 由 LLM 产出。风格作用域 SHALL 收敛为「每帖一档、帖内逐字复用、帖间因品类而异」——**不得**再对所有帖、所有品类施加同一段风格。

#### Scenario: 不同品类帖得到不同风格档
- **WHEN** 两篇不同品类（如美食 vs 干货）的帖分别进入配图链路
- **THEN** 各自 `imageSetPlan.category` 不同、`resolveStyleProfile` 返回不同风格档，两帖配图风格明显不同；而同一帖内图 1..N 共享同一档、风格一致

#### Scenario: 未知品类安全回落不阻断
- **WHEN** 品类判定无法判定品类或产出枚举外的值
- **THEN** `imageSetPlan.category` 回落到兜底档、配图照常进行，MUST NOT 因分类失败而不配图或报错

### Requirement: 配图主体中文直喂、去第二风格源、竖版比例

配图 prompt 的**主体描述** SHALL 保留中文直喂原生文生图模型（Seedream），MUST NOT 先把中文主体整句翻成英文（风格/光学 token 可用英文）。图源客户端 MUST NOT 在正文之外再拼接一个与风格档冲突的**第二风格源**（如把 `imageStyle` 枚举以「，风格：<enum>」二次并入）。出图比例 SHALL 为竖版（贴平台信息流），且**同一帖全部图同比例**（守帧内一致）；改动 `defaultSize` 前 MUST 先核实线上实跑模型允许的合法尺寸串，MUST NOT 传入会被 provider 拒绝的尺寸。

#### Scenario: 主体保留中文、无第二风格源
- **WHEN** 为某中文主题构造文生图 prompt 并下发
- **THEN** 主体以中文出现在 prompt 中；下发给 provider 的文本中不含与风格档冲突的第二风格拼接

#### Scenario: 竖版比例且全帖统一
- **WHEN** 一帖生成多张图
- **THEN** 各张使用同一竖版尺寸（provider 合法值），MUST NOT 出现同帖不同比例

### Requirement: 配图真人与封面文字分级

系统 SHALL 以**分级**取代一刀切的「无真人 / 无文字」：默认无人 / 静物；生活感场景 SHALL 优先用无脸匿名人体（背影 / 局部 / 剪影 / POV）；需清晰人物 SHALL 用「明确非写实虚拟人物」，MUST NOT 生成写实真实人物正脸。封面文字 SHALL 默认留白由后期程序化叠字（MUST NOT 依赖模型渲染中文长标题）。合规 AI 标识 SHALL 走既有发布声明 / 元数据链路，MUST NOT 由模型在画面内绘制水印。

> 注：对「含真人 / 含封面文字」高风险图的**产后视觉校验**（乱码 / 像不像真人）需新接视觉模型，已从本 change 拆出至独立 change `image-postcheck-vision-model`（视觉模型选型 + 成本/延迟决策待定）。本档只声明**已实装**的分级默认（faceless / no-text / no-watermark 风格档）与 AI 元数据链路；产后校验条文不在本 change 落地，避免 spec 声称未实装的行为（守「无声假成功」红线）。

#### Scenario: 需人物时用非写实虚拟人物、不出写实真脸
- **WHEN** 某品类风格档要求画面出现清晰人物
- **THEN** prompt 指向明确非写实虚拟人物，产出不含写实真实人物正脸

### Requirement: 万相参考图生成默认使用 1K 输出规格

当当前图片 provider 为 DashScope/Wanxiang 且生成请求包含至少一张可用参考图时，系统 SHALL 默认向 Wanxiang 提交 `size = "1K"`，以降低参考洗稿配图的像素与传输负担。系统 MUST 保留显式运行时尺寸覆盖能力；该默认值变更 MUST NOT 改变无参考图 Wanxiang 请求、Seedream 请求或确定性文字卡的既有尺寸语义。

#### Scenario: 带参考图且未配置覆盖时使用 1K

- **WHEN** Wanxiang 生成请求包含可用参考图，且未提供构造参数或 `AIDCP_WANXIANG_REFERENCE_IMAGE_SIZE` 环境覆盖
- **THEN** 提交给 Wanxiang 的请求参数包含 `size = "1K"`

#### Scenario: 显式参考图尺寸覆盖优先于 1K 默认值

- **WHEN** Wanxiang 生成请求包含可用参考图，且运行时显式配置 `AIDCP_WANXIANG_REFERENCE_IMAGE_SIZE = "2K"`
- **THEN** 提交请求使用 `size = "2K"`，系统 MUST NOT 将其改写为 `1K`

#### Scenario: 无参考图请求保持既有默认

- **WHEN** Wanxiang 生成请求不包含可用参考图，且未配置普通图片尺寸覆盖
- **THEN** 提交请求继续使用既有 `size = "1024*1024"`，不受参考图默认值变更影响

#### Scenario: 其它图片路线尺寸不变

- **WHEN** 发布配图走 Seedream provider 或确定性文字卡渲染路线
- **THEN** 该路线继续使用其既有尺寸配置与输出尺寸，不读取 Wanxiang 参考图尺寸默认值

