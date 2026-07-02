# role-llm-config Specification

## Purpose
TBD - created by archiving change console-role-model-config. Update Purpose after archive.
## Requirements
### Requirement: 角色级模型与采样参数可配置，缺省回落绝不 brick

系统 SHALL 支持**按角色**与**按分类**覆盖文本模型名**与其所属厂商（provider）**及温度，落 PostgreSQL `role_config`（`role_id` 主键）/ `category_config`。**provider 跟模型同行**：写某层模型 MUST 同时写其 provider（二者作为一个原子单元），清空模型 MUST 同时清空该层 provider，纯温度覆盖 MUST NOT 写入 provider。任一角色/分类的任一字段**缺行 / 为空 / 无效**时，模型 MUST 回落到分类默认 → 全局 `textModel`、温度 MUST 回落到代码默认值（0），解析器 MUST NOT 抛错。解析"生效厂商"时 MUST 取自**贡献了生效模型那一层的同一行** provider；该 provider 为空或为注册表外的脏串时 MUST 归一回落 `dashscope`，MUST NOT 继承另一层的 provider。覆盖值 MUST 在调用时从共享内存镜像解析，使 `PUT` 后**无需重启即生效**（热加载）。写入 MUST 先持久化成功、再刷新内存镜像。

#### Scenario: 按角色覆盖模型+厂商即时生效
- **WHEN** 经 `PUT /api/roles/:roleId/config` 把某生成类角色的模型与 provider 改为火山方舟的一个可用模型
- **THEN** 该角色后续文本调用发往火山方舟端点、用新模型，其余角色不受影响，且无需重启进程

#### Scenario: 老覆盖行（无 provider）即便全局切厂商仍回落 dashscope
- **WHEN** 某角色存在历史模型覆盖（model 非空、provider 列为 NULL），而全局文本厂商已切到 `volcengine`
- **THEN** 该角色解析到 provider `dashscope`（与其 Qwen 模型名匹配），绝不把 Qwen 模型名发到火山方舟

#### Scenario: 纯温度覆盖不贡献 provider
- **WHEN** 某角色只覆盖了温度、未覆盖模型
- **THEN** 该层既不贡献模型也不贡献 provider，模型与厂商继续回落分类/全局，温度用其覆盖值

#### Scenario: 缺省回落不 brick
- **WHEN** 某角色在 `role_config` 无行，或其 `model` 字段为空
- **THEN** 该角色调用回落到分类默认 / 全局 `textModel` 及其 provider、温度回落代码默认 0，系统正常运行不报错

#### Scenario: 写库成功才刷新内存镜像
- **WHEN** `PUT` 写库失败（如数据库瞬断）
- **THEN** 内存镜像保持原值不变，绝不出现「镜像已变、库未变」的不一致

### Requirement: 角色目录白名单暴露，区分模型类型，遗留与纯规则角色不列

系统 SHALL 提供角色目录，**只列出现役且真正调用大模型的角色**，每项标注 `roleId`（带 `browse:` / `publish:` 前缀防撞键）、显示名、所属组、`llmKind`（`text` / `image` / `none`）与是否可调温度。纯规则角色与 v1 遗留路径角色 MUST NOT 出现在目录中。温度 MUST 仅对生成 / 改写类角色开放。

#### Scenario: 目录只含现役 LLM 角色
- **WHEN** 请求 `GET /api/roles`
- **THEN** 返回的角色均为现役且 `llmKind !== 'none'`，纯规则角色与 v1 遗留角色不在其中

#### Scenario: 判定类角色不开放温度
- **WHEN** 目录中一个判定类角色（如内容粗筛 / 关注判定）被读取
- **THEN** 其 `tunable.temperature` 为 false，前端据此不渲染温度输入

#### Scenario: 区分文本与图像角色
- **WHEN** 目录包含配图规划（文本）与配图生成（图像）两类角色
- **THEN** 前者 `llmKind: 'text'`、后者 `llmKind: 'image'`，且图像角色在本期不开放 per-role 模型覆盖

### Requirement: LLM 客户端按角色覆盖向后兼容，不传选项行为不变

文本 LLM 客户端的调用入口 SHALL 接受可选的 per-call 覆盖选项（角色 / 模型 / 温度 / 超时）。**当调用方不传该选项时，请求行为 MUST 使用构造默认解析**（模型经现有解析、温度与超时用构造默认）。浏览侧与发布侧的注入 SHALL 统一到同一个 LLM 客户端接口（含单轮与多轮调用），各角色内部代码 MUST NOT 因此改动。

**构造默认请求超时 MUST 按 thinking 类模型的真实耗时定其天花板**：默认值 MUST ≥ 180s（thinking 模型复杂提示常需 60–150s+，短天花板会把合法慢调用误判超时中止）。该默认 MUST 经文档化的 env 旋钮可调，缺失/非法（非正数/超合理上限）时 MUST 回落安全默认、绝不 brick。per-call 传入的超时覆盖仍优先于构造默认（如探活用短超时不受本条影响）。

#### Scenario: 不传选项用构造默认（含新天花板）
- **WHEN** 任一现有调用未传 per-call 超时选项
- **THEN** 其超时取构造默认（≥180s 的 thinking 天花板），模型/温度经现有解析

#### Scenario: 传入角色即按角色解析
- **WHEN** 注入侧以绑定了某 `roleId` 的封装客户端发起调用
- **THEN** 该次请求按该角色的覆盖配置解析模型与温度，缺省回落全局 / 默认

#### Scenario: env 旋钮调天花板且非法值回落
- **WHEN** 部署经 env 设置模型调用超时天花板为一个合法正值
- **THEN** 客户端构造默认超时取该值；env 缺失或非法（0/负/超上限）时回落写死安全默认（≥180s），系统正常运行不 brick

#### Scenario: per-call 短超时仍覆盖构造默认
- **WHEN** 探活等路径显式传入短超时（如 8s）
- **THEN** 该次请求按传入短超时中止，不受构造默认天花板抬高影响

### Requirement: 无效模型名诚实拒绝，绝不静默假成功

模型名由运营自由输入（不维护白名单，且 MUST NOT 对模型名做格式校验——火山方舟接入点 id `ep-xxx` 须放行）。当 `PUT` 提交一个**非空**模型名时，系统 MUST 做保存前探活，且探活 MUST 用**所选 provider 的 baseUrl + 该 provider 的密钥**（绝不拿火山模型名去 DashScope 端点探）；仅探活通过后写入。探活失败 MUST 拒绝写入并返回**可辨认原因**：模型在该厂商不可用返回 `model_invalid`、该厂商密钥未配置返回 `provider_key_missing`（区分"改模型名"与"去配密钥并重启"）。无论何种失败 MUST NOT 落库、MUST NOT 假成功。空模型名 MUST 视作「保持回落」而非无效（不探活）。**provider 变更**（即便模型名不变）MUST 也触发重新探活。

#### Scenario: 火山模型名按火山探活通过才落库
- **WHEN** 把某角色 provider 设为火山方舟、填一个火山可用模型名保存
- **THEN** 系统用火山方舟的 baseUrl+密钥探活，通过后才写库

#### Scenario: 厂商密钥缺失探活给可区分原因
- **WHEN** 选了火山方舟但其密钥未配置，提交模型名保存
- **THEN** 系统返回 `provider_key_missing`（而非泛化的 `model_invalid`），不落库，提示去配置密钥并重启

#### Scenario: 接入点 id 不被格式校验误拒
- **WHEN** 提交火山方舟接入点 id（`ep-xxxx`）作为模型名
- **THEN** 系统不做格式校验、以探活为唯一判据；探活通过即可落库

#### Scenario: 空模型名视作回落
- **WHEN** 提交 `model` 为空字符串
- **THEN** 系统将该角色模型置为「回落」，并清空该层 provider，不视作无效错误

### Requirement: 角色配置面板接口受 JWT 守护且写非乐观

角色配置接口（`GET /api/roles`、`GET /api/roles/:roleId/config`、`PUT /api/roles/:roleId/config`）MUST 与其它 `/api/*` 一样受 JWT 守护。写接口 MUST 非乐观——返回服务端写后真态（含生效值 + `updatedBy` + `updatedAt`），MUST NOT 返回乐观假态。温度写入 MUST 仅对可调温度的角色放行且校验取值区间，越权或越界 MUST 被拒。

#### Scenario: 未鉴权被拒
- **WHEN** 未带有效 JWT 请求任一 `/api/roles*`
- **THEN** 返回 401，不读不写

#### Scenario: 写后回真态含审计字段
- **WHEN** `PUT /api/roles/:roleId/config` 成功
- **THEN** 返回服务端持久化后的真实生效配置与 `updatedBy` / `updatedAt`，使并发覆盖对前端可见

#### Scenario: 判定类角色拒改温度
- **WHEN** 对一个不可调温度的角色提交 `temperature`
- **THEN** 系统拒绝该字段并报因，不写入温度

### Requirement: 后台角色配置页

管理后台 SHALL 提供角色配置页：以列表呈现目录中每个角色（显示名 / 组 / 模型类型 / 当前生效模型 / 温度），支持按角色编辑模型与温度并保存；并以分类默认表支持按分类编辑默认模型。纯规则与遗留角色 MUST NOT 出现；判定类角色 MUST NOT 渲染温度输入。写操作 MUST 非乐观（round-trip 后据真态渲染）并使用诚实文案（已保存 / 模型名无效无法保存）。

编辑弹窗（角色级与分类默认两处一致）MUST 满足：

- **预填当前生效值**：打开编辑时模型名与厂商 SHALL 带出**当前生效值**（含从上层继承来的值），使运营看到现值再改，不出现「厂商已填而模型名空白」的不一致。
- **显式「模型来源」二态（继承 / 自定义）**表达覆盖 vs 回落，MUST NOT 靠"字符串/厂商有没有变"隐式推断：
  - **继承**：该行不自设模型、跟随上层默认（角色→分类默认→全局默认；分类→全局默认）。保存 SHALL 送清除语义（空模型名 → 清除本行覆盖、回落），使继承行原样保存**绝不被误钉成覆盖**。
  - **自定义**：为该行单独锁定模型；保存 SHALL 按当前值建 / 改覆盖（服务端按厂商探活，无效诚实拒绝）。SHALL 支持把一个当前**继承来的值固定为覆盖**（冻结、不再随上层变动）。
- **诚实闸**：自定义态未填模型名 MUST 被前端拦下（无意义空覆盖），MUST NOT 退化成静默回落；「只改厂商不改模型」MUST NOT 被静默丢弃——带当前值落库、由服务端探活、无效诚实报错。
- **思考「开启」自愈**：当「开启」因切换来源 / 换模型 / 换厂商变为不可用时，已选中的 `on` MUST 被收回 `default`，MUST NOT 呈现「禁用却仍选中」的误导态、MUST NOT 把不支持思考的组合静默存成 `on`。

以上为纯前端编辑体验约束，MUST NOT 改动面板 API 契约、角色/分类模型解析与四层回落语义、思考三态出口翻译、边-云协议 / 风控 / 边缘。

#### Scenario: 列表只呈现可配角色
- **WHEN** 打开角色配置页
- **THEN** 仅列出现役 LLM 角色，纯规则 / 遗留角色不出现

#### Scenario: 非乐观保存
- **WHEN** 修改某角色模型并保存
- **THEN** 页面在服务端返回真态后再渲染，而非乐观更新；无效模型名时显示诚实错误且不改动列表显示

#### Scenario: 编辑弹窗预填当前生效值
- **WHEN** 打开一个当前模型为继承（该行无覆盖）的角色 / 分类的编辑弹窗
- **THEN** 厂商与模型名一并带出当前生效值（继承来的值），不出现模型名空白，与列表「当前生效模型」一致

#### Scenario: 继承态原样保存不被误钉成覆盖
- **WHEN** 一个继承行以「模型来源=继承」保存（未切到自定义）
- **THEN** 保存送清除语义（空模型名）、该行仍保持继承、随上层默认变动，绝不被悄悄钉成本行覆盖

#### Scenario: 把继承值固定为覆盖
- **WHEN** 运营在一个继承行切到「自定义」、保留预填的当前生效值并保存
- **THEN** 建立一条等值的本行覆盖（该行自此冻结、不再随上层默认变动），前端 round-trip 后据真态显示为已覆盖

#### Scenario: 自定义态空模型名被诚实拦下
- **WHEN** 运营选「自定义」但把模型名清空并点保存
- **THEN** 前端拦下并提示（需填模型名或切回继承），MUST NOT 提交，MUST NOT 退化成静默回落

#### Scenario: 思考「开启」不可用时自动收回
- **WHEN** 运营已选「开启」，随后切换模型来源 / 改到一个不支持非流式思考的模型或厂商，使「开启」变为不可用
- **THEN** 已选中的 `on` 自动收回 `default`，选择器不呈现「禁用却仍选中」，保存不会把不支持思考的组合静默存成 `on`

### Requirement: 大模型调用按角色可观测

系统 SHALL 在文本 LLM 出口为每次调用记录一行结构化日志，至少含角色标识、**生效厂商（provider）**、生效模型名与耗时，使运营改完配置后可验证是否真生效与成本变化、并能区分同名模型来自哪个厂商。该日志 MUST NOT 含明文密钥或提示词正文等敏感内容。本期 MUST NOT 引入独立计费 / 统计面板，token 用量按模型名聚合可暂不加 provider 维度（同名跨厂商归并列为已知限制，靠日志 provider 可回溯）。

#### Scenario: 调用记结构化日志含厂商
- **WHEN** 某角色发起一次文本模型调用
- **THEN** 出口记录一行含 `role` + `provider` + 生效 `model` + 耗时的日志，不含密钥与提示词正文

### Requirement: 角色 prompt 在后台只读可见，忠实渲染且优雅降级

系统 SHALL 让现役 LLM 角色的 prompt 在管理后台**只读可见**：经只读接口 `GET /api/roles/:roleId/prompt`（与其它 `/api/*` 一样受 JWT 守护）返回该角色 prompt 的**忠实渲染**——调用该角色**真实的** prompt 构建逻辑、传入最小合法示例数据与人设渲染得到，使运营看到的就是线上真用的指令文字与人设（占位的实时数据以明示标注）。

**忠实渲染 SHALL 覆盖浏览侧与发布侧两类文本角色**：

- 浏览侧文本角色经其角色实例的真实构建逻辑渲染。
- **发布侧文本角色 SHALL 经其真实的 `build*Prompt` 构建函数 + 最小合法示例输入渲染**（示例输入以明示占位约定构造，MUST NOT 改动任何 `build*Prompt` 的现有逻辑）。发布侧文本角色 MUST NOT 因「集中在源码文件」而被整类判为不可预览。
- **正文去 AI 味改写角色**（发帖前经注入的后处理器调大模型重写）SHALL 可只读预览：其重写 prompt MUST 抽为**单一共享构建函数**，供线上重写调用与只读预览**同源取用**（MUST NOT 手抄第二份，防漂移）；抽取 MUST **逐字保留**原 prompt 文本（含既有笔误），线上行为零变化。该角色 SHALL 登记进角色目录，且其重写调用 MUST 带上其角色标识以按后台配置解析模型/温度（否则模型配置为静默 no-op、违反诚实红线）。
- **现役但此前漏登记的 LLM 角色**（如评论点赞择选，开关开启时现役）SHALL 登记进角色目录，使其可只读预览且可按角色配模型；该类角色若因运行时开关未注册，其预览 SHALL 诚实返回「暂不支持预览」而非伪造。

该接口 MAY 接受**可选**查询参数 `accountId`：

- 给定 `accountId` 时，对**浏览侧**角色系统 SHALL 按**该账号的人设**忠实渲染（人设经按账号解析注入，MUST NOT 改动任何角色既有 `buildPrompt`/`previewPrompt` 的逻辑）。
- 给定的 `accountId` 在浏览侧**没有配置人设**时，系统 MUST 诚实回落到系统默认人设渲染，并以**明示标注**告知「该账号未配人设，预览用默认人设」，MUST NOT 把默认人设冒充为该账号人设。
- **发布侧**正文人设当前为构建函数**内置默认**、**不随账号切换**：给定 `accountId` 时系统 MUST 仍按内置默认渲染，并以说明诚实标注「发布侧 prompt 的人设为内置默认、不随账号切换」；MUST NOT 设置 `personaFallback`（该语义仅指「本应按账号但该账号未配」，发布侧不适用），MUST NOT 伪造账号维度或来源段。
- **不传** `accountId` 时，系统 SHALL 渲染系统默认人设，行为与本扩展前**逐字一致**（向后兼容）。
- 返回体为支持上述标注新增的字段 MUST 为**可选**字段，未升级的查看器 MUST 仍能正常显示。

**图像角色（配图生成执行）SHALL 展示其发给文生图模型的「有效图片指令」预览**：即「配图指令」角色按正文产出的主体描述（示例占位）+ 系统统一追加的固定风格基底（`IMAGE_STYLE_BASE`，每张图被强制施加的风格/负向约束），返回 `available:true` + prompt，并以说明标注「这是文生图图片指令、非大模型文本 prompt；配图用全局图片模型生成」。图像角色 MUST NOT 附人设来源段、MUST NOT 因 `accountId` 加人设标注（图片指令无账号人设）。**纯规则 / 不调模型角色** SHALL 返回「不可预览」标注而非 prompt。

本能力 MUST 为**纯只读**：MUST NOT 提供任何写/改 prompt 的接口或路径，`accountId` 仅作渲染口径、MUST NOT 改写任何账号的人设或状态。渲染 MUST NOT 改动任何角色既有 `buildPrompt`/`build*Prompt` 的逻辑（线上 prompt 行为零变化）。单个角色渲染失败 MUST 降级为「预览不可用 + 原因」、MUST NOT 抛出、MUST NOT 连累浏览/发布闭环。未知 `roleId` SHALL 返回 404。

#### Scenario: 文本角色 prompt 只读可见

- **WHEN** 已鉴权请求 `GET /api/roles/:roleId/prompt`，该 roleId 是一个现役文本 LLM 角色
- **THEN** 返回 `available:true` 且 `prompt` 为该角色忠实渲染的 prompt 文本（含其真实指令片段与真实人设），不含任何写入能力

#### Scenario: 发布侧文本角色忠实渲染

- **WHEN** 已鉴权请求某发布侧文本角色（如发布选题侦察 / 技术帖文案创作 / 发布审批裁决）的 prompt 预览
- **THEN** 返回 `available:true` 且 `prompt` 为经其真实 `build*Prompt` + 示例输入渲染的真实 prompt 文本，实时数据以明示占位标注；`build*Prompt` 逻辑不被改动

#### Scenario: 正文去 AI 味改写可只读预览且与线上同源

- **WHEN** 已鉴权请求正文去 AI 味改写角色的 prompt 预览
- **THEN** 返回 `available:true` 且 `prompt` 为共享构建函数渲染的重写指令，与线上重写实际所用文本逐字一致（同一构建函数）；该角色在目录中且其重写调用按角色解析模型配置

#### Scenario: 现役漏登记角色补入目录后可预览可配

- **WHEN** 评论点赞择选角色在开关开启（现役、已注册）时被请求预览
- **THEN** 返回 `available:true` 的忠实渲染 prompt，且该角色在目录中可按角色配模型；若开关关闭未注册，则预览诚实返回「暂不支持预览」，绝不伪造

#### Scenario: 发布侧带 accountId 诚实标注不随账号切

- **WHEN** 已鉴权请求某发布侧文本角色预览并带 `?accountId=<任一账号>`
- **THEN** 仍按内置默认人设渲染，返回体说明标注「发布侧人设为内置默认、不随账号切换」，且不设置 `personaFallback`、不附来源段，绝不伪造该账号人设

#### Scenario: 按选定账号人设预览（浏览侧）

- **WHEN** 已鉴权请求某浏览侧文本角色预览并带 `?accountId=<已配人设的账号>`
- **THEN** 返回 `available:true`，prompt 用**该账号人设**渲染，返回体标注所用账号为该账号且未触发默认回落

#### Scenario: 选定账号未配人设诚实回落标注（浏览侧）

- **WHEN** 已鉴权请求带 `?accountId=<未配人设的账号>` 的浏览侧文本角色预览
- **THEN** 渲染仍成功（`available:true`，用系统默认人设），且返回体以明示标志与说明告知「该账号未配人设、用了默认人设」，绝不把默认人设标注为该账号人设

#### Scenario: 不传 accountId 行为不变

- **WHEN** 已鉴权请求预览且不带 `accountId`
- **THEN** 渲染系统默认人设，返回体与本扩展前逐字一致，旧查看器正常显示

#### Scenario: 图像角色展示有效图片指令

- **WHEN** 已鉴权请求配图生成执行（图像角色）的 prompt 预览
- **THEN** 返回 `available:true` 且 `prompt` 为「示例主体描述 + 固定风格基底」的有效图片指令（固定风格基底可见），返回体说明标注其为文生图图片指令、用全局图片模型生成；不附来源段

#### Scenario: 图像角色带 accountId 不加人设标注

- **WHEN** 已鉴权请求图像角色预览并带 `?accountId=<任一账号>`
- **THEN** 仍返回 `available:true` 的图片指令，保留其图片指令说明（不被「不随账号切换」的人设标注覆盖），不设 `personaFallback`、不附来源段

#### Scenario: 未鉴权被拒

- **WHEN** 未带有效 JWT 请求 `GET /api/roles/:roleId/prompt`
- **THEN** 返回 401，不返回任何 prompt

#### Scenario: 渲染失败优雅降级不崩

- **WHEN** 某角色（浏览或发布）的 prompt 渲染过程抛错
- **THEN** 该角色返回 `available:false` 与失败原因，接口不抛、进程不崩，其它角色预览与浏览/发布闭环不受影响；若渲染前临时切换了预览账号口径，账号 MUST 在失败路径上仍被还原

#### Scenario: 只读无写

- **WHEN** 审查 prompt 可见能力的接口面
- **THEN** 只存在读取路径（GET），不存在任何修改 prompt 或人设的写路径（本期不开放编辑）

### Requirement: prompt 预览可标注账号人设来源段，尽力而为且绝不误标

在只读 prompt 预览（`GET /api/roles/:roleId/prompt`）之上，系统 MAY 标注 prompt 中**来自账号人设**的段，使运营在查看器里能区分「该角色独有指令」与「来自账号人设的共享段」。该标注 MUST 满足：

- **不改构建逻辑**：MUST NOT 改动任何角色 `buildPrompt` 的逻辑（线上 prompt 行为零变化）；人设段经预览层用**当次渲染所用的同一份人设**（即选定 `accountId` 的人设；不传时为系统默认人设）重新派生 + 在**已渲染** prompt 里**精确定位**得到，MUST NOT 手抄第二份人设文本（避免与真实 `buildPrompt` 漂移）。
- **尽力而为 + 诚实回落**：人设在某些角色里会被运行时内容拆成多片段，系统 SHALL 尽力标注**全部**人设片段；任一片段无法**唯一**定位（在 prompt 中出现 0 次或多于一次）、或切出的各段拼接后不与原 prompt **逐字相等**时，系统 MUST 对该角色回落为**不标注的扁平 prompt**（`available:true` + 说明），MUST NOT 伪造或猜测人设段的位置。
- **绝不误标**：MUST NOT 把非人设文本标注为来自人设（误标等同软性「静默假成功」）。
- **向后兼容**：返回体 MUST 保留扁平 prompt 字段；来源段以**可选字段**附加，未升级的查看器 MUST 仍能正常显示扁平 prompt。
- **不连累闭环**：单个角色标注失败 MUST NOT 抛出、MUST NOT 影响其它角色预览或浏览/发布闭环。

#### Scenario: 连续人设角色标注来源段

- **WHEN** 已鉴权请求某个把人设作为连续片段构建的文本角色的 prompt 预览
- **THEN** 返回体在保留扁平 prompt 的同时附带分段信息，人设片段被标为来自账号人设，且各段拼接后与扁平 prompt 逐字相等

#### Scenario: 切换账号后按该账号人设重新派生来源段

- **WHEN** 已鉴权请求带 `?accountId=<某账号>` 且该账号人设被该角色作为连续片段构建
- **THEN** 来源段依据**该账号**的人设派生与定位（与当次渲染同源），两道诚实闸（唯一定位 + 拼接等值）对当次 prompt 一并判定；不过闸则回落扁平不标注

#### Scenario: 人设被运行时内容拆开的角色

- **WHEN** 某角色的人设被运行时内容拆成多个片段（如搜索/无收获场景）
- **THEN** 系统尽力标注全部可唯一定位的人设片段；其中任一片段无法唯一定位时，该角色回落为不标注的扁平 prompt，`available:true` 且不伪造位置

#### Scenario: 人设值与正文撞字不误标

- **WHEN** 某人设片段的文本在 prompt 正文或示例数据里出现多于一次（歧义）
- **THEN** 系统不标注该角色（回落扁平），MUST NOT 把首次出现处误标为来自人设

#### Scenario: 未升级查看器向后兼容

- **WHEN** 旧版查看器读取带来源段的预览返回体
- **THEN** 仍能用扁平 prompt 字段正常显示，不因新增的可选来源段字段而出错

### Requirement: 角色 / 分类可配思考模式三态，缺省回落 default 绝不 brick

系统 SHALL 支持**按角色**与**按分类**覆盖"思考模式（thinking）"，取值为三态之一：`default`（不干预、跟模型走）/ `off`（强制关思考）/ `on`（强制开思考），落 PostgreSQL `role_config` / `category_config` 的可空列。任一角色 / 分类的思考模式**缺行 / 为空 / 非法值**时，解析 MUST 回落：角色层无值取分类层、分类层无值取 `default`；解析器 MUST NOT 抛错。覆盖值 MUST 在调用时从共享内存镜像解析，使 `PUT` 后**无需重启即生效**（热加载）；写入 MUST 先持久化成功、再刷新内存镜像。思考模式覆盖 MUST 与模型 / 温度 / 厂商覆盖相互独立（写思考模式 MUST NOT 改动模型 / provider / 温度，反之亦然）。

#### Scenario: 按角色设 off 即时生效
- **WHEN** 经面板把某判定类角色的思考模式设为 `off`
- **THEN** 该角色后续文本调用按"关思考"翻译发起，其余角色不受影响，且无需重启进程

#### Scenario: 角色无值回落分类，分类无值回落 default
- **WHEN** 某角色未设思考模式、其所属分类设为 `on`
- **THEN** 该角色解析到 `on`；若分类也未设，则解析到 `default`

#### Scenario: 非法值回落 default 不 brick
- **WHEN** 存储中某行思考模式为空串或注册表外脏串
- **THEN** 解析回落 `default`（发起时不发任何 thinking 参数），系统正常运行不报错

#### Scenario: 思考模式与模型覆盖相互独立
- **WHEN** 某角色只设思考模式、未覆盖模型 / 温度
- **THEN** 该层只贡献思考模式，模型 / provider / 温度继续按既有规则回落，互不串写

### Requirement: 模型出口按厂商翻译思考三态，default 态请求逐字零回归

文本模型出口 SHALL 按**解析出的 provider 与模型**把思考三态翻译成对应厂商的请求参数：`off` / `on` 时按厂商加入相应 thinking 字段（DashScope Qwen 系用 `enable_thinking`、DashScope DeepSeek 系用其思考开关参数、火山方舟豆包用 `thinking.type`）；**`default` 态 MUST NOT 加入任何 thinking 相关字段**，请求体与本 change 前逐字一致。翻译 MUST 集中在单一纯函数内、可用注入的假 fetch 断言请求体形状；无法识别的 provider / 模型组合在 `on` 分支 MUST 失败安全（不加参数），MUST NOT 发出可能被厂商拒绝的字段。出口保持**非流式**、仍**只读 `content`**，本要求 MUST NOT 改变该两点。

#### Scenario: default 态请求体零回归
- **WHEN** 某角色思考模式解析为 `default`（或未注入思考解析器的旧路径 / 单测）
- **THEN** 请求体只含 `{model, messages, temperature}`、非流式，与改造前逐字一致

#### Scenario: 豆包 off/on 翻译为 thinking.type
- **WHEN** 某绑定火山方舟豆包模型的角色思考模式为 `off`（或 `on`）
- **THEN** 请求体加入 `thinking:{type:'disabled'}`（或 `'enabled'`），非流式发起，仍只读 `content`

#### Scenario: DeepSeek on 非流式可用
- **WHEN** 某绑定 DashScope DeepSeek 模型的角色（如发布审批）思考模式为 `on`
- **THEN** 请求体加入 DeepSeek 的开思考参数、非流式发起，最终答案取自 `content`（推理内容落 `reasoning_content`、系统不读）

### Requirement: DashScope Qwen 的"开启"绝不发出会 400 的请求

由于出口为非流式而 DashScope Qwen 系开思考必须配流式，系统 MUST NOT 对"当前绑定为 DashScope Qwen 模型"的角色以 `on` 发出 `enable_thinking:true` 的非流式请求。防护 MUST 双层：① 后台前端在角色 / 分类**当前绑定为 DashScope Qwen 模型**时，`on` 选项 MUST 禁用并给出可读说明；② 出口在发起时 MUST 兜底——遇 DashScope Qwen + `on` 时回落 `default`（不加 thinking 字段）并告警一次，绝不发出会被厂商以 400 拒绝的字段。`on` 值本身 MAY 被写库保存（存意图），可行性在**发起时**按当时模型判定。

#### Scenario: 前端禁用 Qwen 角色的开启选项
- **WHEN** 后台打开一个当前绑定 DashScope Qwen 模型的角色配置
- **THEN** "开启"三态选项为禁用态并说明需流式支持，运营无法把它设为 `on`

#### Scenario: 出口对遗留 Qwen+on 兜底回落
- **WHEN** 某行历史遗留思考模式 `on` 且其生效模型解析为 DashScope Qwen
- **THEN** 该次请求不加任何 thinking 字段（等价 default）、非流式正常发起并成功，同时记一次告警，绝不 400

#### Scenario: 重绑到 DeepSeek 后 on 自动生效
- **WHEN** 某角色思考模式存为 `on`、其模型由 Qwen 改绑到 DashScope DeepSeek
- **THEN** 后续请求按 DeepSeek 开思考翻译生效，无需重设思考模式

### Requirement: 面板读写思考模式维度，非法值拒绝缺省视作 default

面板 API SHALL 在角色目录 / 角色配置 / 分类配置的读接口回带 `thinkingMode`，并在对应 `PUT` 接受可选 `thinkingMode`。提交值 MUST 校验属于 `{default, off, on}`：非法值 MUST 拒绝写入且不假成功；缺省 / 未传 MUST 视作 `default`（不写覆盖或写空）。写入 MUST 先持久化成功再刷新内存镜像；库写失败 MUST 保持内存镜像原值不变。

#### Scenario: 读接口回带思考模式
- **WHEN** 请求角色目录 / 某角色配置 / 某分类配置
- **THEN** 响应包含该层生效的 `thinkingMode`（未设时为 `default`）

#### Scenario: 非法思考模式值被拒绝
- **WHEN** `PUT` 提交一个不属于 `{default, off, on}` 的 `thinkingMode`
- **THEN** 系统拒绝写入、返回可辨认原因，绝不落库、绝不假成功

#### Scenario: 写库失败不污染内存镜像
- **WHEN** 写思考模式时数据库瞬断
- **THEN** 内存镜像保持原值，绝不出现"镜像已变、库未变"的不一致

