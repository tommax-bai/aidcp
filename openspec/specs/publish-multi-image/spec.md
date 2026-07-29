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

### Requirement: 洗稿正文语义 SHALL 按画面类型驱动逐槽表达

系统 SHALL 从洗稿后的标题、tone 与有界首/中/尾正文摘录中，为每个配图槽生成 `contentVisualBrief`，至少包含叙事瞬间、情绪、情绪强度、动作、环境和禁用项，并包含一个判别式 `categoryBrief`。分类 SHALL 覆盖人物、文字卡、图表信息图、场景摄影、静物、插画/3D、UI/文档和混合拼贴；每类字段 SHALL 描述正文要表达的具体内容而不是参考图风格。最终提示 MUST 把参考图职责限制为视觉类型、景别/网格、构图、光影、色调、材质与抽象风格，把具体人物表演、文字层级、关系结构、场景事件、物件状态、视觉隐喻、界面任务和分区叙事交由正文分类 brief 决定；冲突时正文语义优先。人物参考 MUST 身份泛化，MUST NOT 复刻来源真人/名人五官、品牌 logo 或平台标识。

#### Scenario: 脆弱与行动力不生成证件照式人物
- **WHEN** 正文表达“脆弱、容易被触动，但能自我消化并保持行动力”，参考图是居中头肩人像
- **THEN** 本槽 brief SHALL 明确对应的复杂情绪、眼神/嘴角/肩颈状态和禁用的正面端坐/标准商业微笑；生成 prompt 保留参考图景别、光影和色调，但 MUST NOT 让参考图的中性姿态覆盖正文人物表演

#### Scenario: 长正文保留情绪转折
- **WHEN** 正文超过视觉导演输入上限且情绪结论位于中段或结尾
- **THEN** 系统 SHALL 使用确定性的首/中/尾有界摘录而不是只截前 400 字，确保视觉 brief 能看到叙事转折，同时保持模型输入有界

#### Scenario: 人物反推字段独立于摄影参数
- **WHEN** frame kind 为 `portrait_photo`
- **THEN** specialist SHALL 除镜头/光影字段外，输出可观察的表情、视线、头部角度、身体姿态、手势、姿态能量和情绪效价/唤醒度；这些字段描述来源画面，不得被当作覆盖正文 brief 的人物表演指令

#### Scenario: 文字卡表达正文信息结构
- **WHEN** 目标画面为 `text_layout`
- **THEN** 分类 brief SHALL 给出核心结论、信息层级、重点词、阅读顺序、信息密度和卡片结构；确定性卡面文案 SHALL 使用同一首/中/尾正文语义并继续通过防搬运校验，MUST NOT 只生成一个大标题和无意义留白

#### Scenario: 图表不编造数据
- **WHEN** 目标画面为 `infographic_chart` 且正文只描述方向/关系而没有可靠数值
- **THEN** 分类 brief SHALL 给出主张、对象、关系和方向，并明确无数值表达政策；生成提示 MUST NOT 编造百分比、坐标值或样本量

#### Scenario: UI 不虚构产品能力
- **WHEN** 目标画面为 `ui_document`
- **THEN** 分类 brief SHALL 给出用户任务、界面状态、组件层级、操作路径、信息重点和概念/真实边界；生成提示 MUST 把未由正文支持的界面标为概念示意，不得暗示不存在的已上线功能

#### Scenario: 其余视觉类型使用独立内容维度
- **WHEN** 目标画面为场景摄影、静物、插画/3D 或混合拼贴
- **THEN** 分类 brief SHALL 分别描述事件痕迹/空间关系、物件使用状态/生活痕迹、隐喻/象征/叙事阶段、分区职责/阅读顺序，MUST NOT 统一退化为泛化情绪与装饰词

### Requirement: 自主创作 SHALL 先规划图集叙事和逐槽职责

自主创作稿件没有来源图片提供序列结构时，系统 SHALL 在逐槽类型化 brief 之前或同一次规划调用内生成文章级图集策略，至少包含整组叙事弧、连续性规则和类型组合理由；每槽 SHALL 使用固定 `slotRole` 表达封面钩子、语境、问题、解释、证据、过程、对比、行动或结论职责。槽位职责、视觉类型、具体内容、风格来源和生成路由 MUST 分字段保存，MUST NOT 混成单一风格描述。模型漏字段/无效枚举/调用失败时 SHALL 有确定性保守兜底，且不得声称模型策略完整可用。

#### Scenario: 原创多图形成叙事而不是重复插图
- **WHEN** 自主创作正文规划出多于一张图片
- **THEN** 图 0 SHALL 为 `cover_hook`，其余槽按正文语义承担语境、问题、解释、证据、过程、对比、行动或结论；系统 SHALL 给出整组叙事弧与连续性规则，MUST NOT 仅以不同措辞重复同一槽位职责

#### Scenario: 类型组合服从内容而非表面多样
- **WHEN** 正文最适合全部使用文字卡或同一摄影类型形成连续叙事
- **THEN** 系统 MAY 重复同一视觉类型，但每槽职责和内容 MUST 不同；系统 MUST NOT 为凑齐多种类型而编造数据、UI、人物或场景

#### Scenario: 原创类型决定诚实生成路由
- **WHEN** 自主创作槽选择文字卡、UI/文档、图表信息图或混合拼贴
- **THEN** 计划 SHALL 分别记录确定性文字卡、类型专用生成或分区引导路由；未接结构化 UI/图表绘制器时 MUST NOT 标记为 deterministic redraw

### Requirement: 高风险配图产后视觉校验

产后审计旗标开启且槽位存在主参考图时，系统 SHALL 用视觉 / 多模态模型比较主参考与生成图，输出形态、主体、构图、色彩、风格五项分数；生成式槽存在 `contentVisualBrief` 时还 SHALL 输出 `contentAlignment`，并按 `categoryBrief.kind` 核验人物表演、文字信息结构、图表关系、场景事件、静物状态、插画隐喻、UI 任务或拼贴分区。确定性文字卡继续由既有卡面文案合规链核验内容，视觉保真审计 MUST NOT 为计算 `contentAlignment` 去 OCR 卡面文字，但 metadata 仍 SHALL 保留该槽正文 brief。系统同时核验来源真人/名人身份相似、乱码、画内水印、逐字复制与原创风险；清晰露脸的虚构人物本身 MUST NOT 被误判为可识别真人风险。内容不一致、硬风险或阈值不通过 SHALL 丢弃该次结果：生成式带审计指导有界重生成一次，确定性文字卡以严格来源设计令牌有界重渲染一次；第二次仍不过 SHALL 丢弃该槽。MUST NOT 因 prompt 写了 `faceless`/`no text`、provider 声称 `referenceStatus='used'` 或文字卡 renderer 返回成功就假定保真/合规。首轮视觉模型不可用时 MUST 标 `unverified` 并诚实保留原因；已有失败尝试后，后续 `unverified` MUST 丢槽，MUST NOT 用未知结果覆盖已知失败。合规 AI 标识仍走既有发布声明 / 元数据链路，MUST NOT 由模型在画面内绘制水印。

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

### Requirement: 自主创作配图 SHALL 支持无参考图内容视觉核验

自主创作审计旗标开启且槽位存在有效 `contentVisualBrief` 时，系统 SHALL 在没有主参考图的情况下用视觉模型比较生成结果与 `slotRole`、目标类型、公共 brief 和分类 brief，并显式记录 `auditMode=content_alignment`。形态分 SHALL 表示目标类型匹配，主体/构图/色彩/风格/内容一致性 SHALL 相对正文语义评估；来源复制检查 SHALL 标为 `not_applicable`，MUST NOT 伪造参考图比较或来源保真结论。内容错位、乱码、水印、可识别真人或高风险不通过时 SHALL 有界重生成/重渲染一次，第二次仍失败则丢槽；首轮视觉模型不可用时 SHALL `unverified` 并保留图片进入既有人审草稿链。

#### Scenario: 原创图片按类型和正文核验
- **WHEN** 自主创作生成一个 `infographic_chart` 槽且正文没有可靠数字
- **THEN** 内容审计 SHALL 检查输出是否为无数值关系表达、是否编造数字以及是否体现分类 brief 的关系和方向；不得因不存在参考图而直接 skipped

#### Scenario: 原创审计不伪造复制结论
- **WHEN** 内容审计只有生成图、槽位职责和正文 brief，没有来源图片
- **THEN** metadata SHALL 记录 `copyCheck=not_applicable`，控制台不得显示“未复制来源”或“参考保真通过”

#### Scenario: 原创审计可独立回滚
- **WHEN** `AIDCP_AUTONOMOUS_VISUAL_AUDIT` 关闭
- **THEN** 自主创作保持类型化规划和生成，但不调用无参考图视觉审计；参照洗稿的 `AIDCP_VISUAL_FIDELITY_AUDIT` 行为不受影响

### Requirement: 视觉参考和保真结果 SHALL 可审计

发布 metadata SHALL 逐槽持久化图集策略、槽位职责、风格来源、公共内容视觉 brief、判别式分类 brief、生成路由、source→slot→output 绑定、provider 参考使用状态、审计模式、复制检查适用性、视觉审计状态/分数/风险/尝试次数，并区分 `used`（provider 声称消费参考图）、`reference_fidelity`（有来源比较）与 `content_alignment`（仅正文/类型核验）。控制台 SHALL 按分类使用可读标签与字段展示，不得只显示原始 JSON；历史记录无新字段时读取 SHALL null-safe。模型不可用、旗标关闭、路由降级和槽位丢弃均 MUST 有诚实状态，不得统一包装为成功。

#### Scenario: provider used 不等于保真 passed
- **WHEN** provider 返回 `referenceStatus='used'` 但产后视觉审计失败
- **THEN** metadata 同时记录 used 与 failed/retried/discarded，控制台不得展示“参考保真通过”

