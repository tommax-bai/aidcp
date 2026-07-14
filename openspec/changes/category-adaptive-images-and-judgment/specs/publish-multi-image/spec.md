## MODIFIED Requirements

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

## ADDED Requirements

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
