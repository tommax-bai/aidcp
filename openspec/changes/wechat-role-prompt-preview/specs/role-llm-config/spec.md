## MODIFIED Requirements

### Requirement: 角色 prompt 在后台只读可见，忠实渲染且优雅降级

系统 SHALL 让现役 LLM / 视觉模型角色的 prompt 或模型文本指令在管理后台**只读可见**：经只读接口 `GET /api/roles/:roleId/prompt`（与其它 `/api/*` 一样受 JWT 守护）返回该角色 prompt 的**忠实渲染**——调用该角色**真实的** prompt 构建逻辑、传入最小合法示例数据与人设渲染得到，使运营看到的就是线上真用的指令文字与人设（占位的实时数据或图片以明示标注）。

**忠实渲染 SHALL 覆盖浏览侧、命令式/独立浏览侧、interaction、发布侧文本与视觉模型角色**：

- 浏览侧事件驱动文本角色经其角色实例的真实构建逻辑渲染。
- 命令式评论任务或其它独立调用中的文本 LLM 角色（如评论搜索词生成、评论搜索笔记甄选、Facebook 加群判定、Facebook 定向评论撰写）即使不注册在 `RoleDispatcher`，只要现役调用大模型，也 SHALL 登记在角色目录并经其真实 `previewPrompt` / prompt 构建逻辑渲染，MUST NOT 因“不在事件驱动角色集”而不可预览。
- **interaction 文本角色**（包括视频号收件箱意图分类、模板润色、回复风险复核）SHALL 经运行时实际使用的 prompt 构建函数与最小合法示例输入渲染，MUST NOT 被错误当作发布侧角色或返回“暂不支持预览”。
- **发布侧文本角色 SHALL 经其真实的 `build*Prompt` 构建函数 + 最小合法示例输入渲染**（示例输入以明示占位约定构造，MUST NOT 改动任何 `build*Prompt` 的现有逻辑）。发布侧文本角色 MUST NOT 因「集中在源码文件」而被整类判为不可预览。
- 发布侧话题生成 / 话题评判角色 SHALL 与其它发布侧文本角色同样可预览：分别经 `buildTopicGenerationPrompt` / `buildTopicEvaluationPrompt` 加最小合法示例输入渲染，MUST NOT 在角色目录可配但 prompt 预览缺席。
- **正文去 AI 味改写角色**（发帖前经注入的后处理器调大模型重写）SHALL 可只读预览：其重写 prompt MUST 抽为**单一共享构建函数**，供线上重写调用与只读预览**同源取用**（MUST NOT 手抄第二份，防漂移）；抽取 MUST **逐字保留**原 prompt 文本（含既有笔误），线上行为零变化。该角色 SHALL 登记进角色目录，且其重写调用 MUST 带上其角色标识以按后台配置解析模型/温度（否则模型配置为静默 no-op、违反诚实红线）。
- **现役但此前漏登记的 LLM 角色**（如评论点赞择选，开关开启时现役）SHALL 登记进角色目录，使其可只读预览且可按角色配模型；该类角色若因运行时开关或依赖未注册，其预览 SHALL 诚实返回「暂不支持预览」而非伪造。
- **vision 角色** SHALL 展示实际发送给视觉模型的文本指令；多阶段视觉角色 SHALL 展示各实际阶段的文本指令并明确分段，MUST NOT 读取或泄露真实业务图片，也 MUST NOT 因 `llmKind='vision'` 错报为“不调用大模型”。

角色目录与预览来源 MUST 保持完整一致：每个登记为现役且调用文本、图像或视觉模型的角色，都 MUST 有真实预览来源或由运行时注册状态给出诚实不可用原因；新增非浏览模型角色时，目录级自动化测试 MUST 要求其预览返回 `available:true` 且非空，防止只进目录、不进预览。

该接口 MAY 接受**可选**查询参数 `accountId`：

- 给定 `accountId` 时，对**浏览侧事件驱动角色与消费账号人设的命令式角色**系统 SHALL 按**该账号的人设**忠实渲染（人设经按账号解析注入，MUST NOT 改动任何角色既有 `buildPrompt`/`previewPrompt` 的逻辑）。
- 给定 `accountId` 时，对**发布侧文本角色**系统 SHALL 使用该账号人设填充预览示例输入，使后台看到的账号定位与生产发布链一致；生产发布链仍由入口人设闸保证未绑账号不会运行。
- interaction、独立无 persona 角色与视觉角色不消费账号人设时，系统 MUST NOT 因 `accountId` 把其 prompt 冒充为所选账号人设，也 MUST NOT 设置虚假的 persona 回落标记。
- 给定的 `accountId` **没有配置人设**且该角色实际消费 persona 时，系统 MUST 诚实回落到示例人设渲染，并以**明示标注**告知「该账号未配人设，运行会被拒绝，预览用示例人设」，MUST NOT 把示例人设冒充为该账号人设。
- **不传** `accountId` 时，需要 persona 的角色 SHALL 渲染示例人设；不消费 persona 的角色 SHALL 标注无人设来源；返回体新增字段 MUST 为可选，未升级查看器 MUST 仍能正常显示。

**图像角色（配图生成执行）SHALL 展示其发给文生图模型的「有效图片指令」预览**：即「配图指令」角色按正文产出的主体描述（示例占位）+ 系统统一追加的固定风格基底（按内容品类选取，每张图被强制施加的风格/负向约束），返回 `available:true` + prompt，并以说明标注「这是文生图图片指令、非大模型文本 prompt；配图用全局图片模型生成」。图像/视觉角色 MUST NOT 附人设来源段、MUST NOT 因 `accountId` 加人设标注。**纯规则 / 不调模型角色** SHALL 返回「不可预览」标注而非 prompt。

本能力 MUST 为**纯只读**：MUST NOT 提供任何写/改 prompt 的接口或路径，`accountId` 仅作渲染口径、MUST NOT 改写任何账号的人设或状态。渲染 MUST NOT 改动任何角色既有 prompt 构建逻辑（线上 prompt 行为零变化）。单个角色渲染失败 MUST 降级为「预览不可用 + 原因」、MUST NOT 抛出、MUST NOT 连累浏览/interaction/发布闭环。未知 `roleId` SHALL 返回 404。

#### Scenario: 文本角色 prompt 只读可见

- **WHEN** 已鉴权请求 `GET /api/roles/:roleId/prompt`，该 roleId 是一个现役文本 LLM 角色
- **THEN** 返回 `available:true` 且 `prompt` 为该角色忠实渲染的 prompt 文本（需要人设的角色包含其真实或明示示例人设），不含任何写入能力

#### Scenario: 命令式与独立浏览角色忠实渲染

- **WHEN** 已鉴权请求评论搜索词生成、评论搜索笔记甄选、Facebook 加群判定或 Facebook 定向评论撰写角色的 prompt 预览
- **THEN** 返回 `available:true` 且 `prompt` 来自该角色真实预览逻辑；该角色不需要被注册进 `RoleDispatcher`

#### Scenario: 视频号收件箱三个角色忠实渲染

- **WHEN** 已鉴权分别请求 `reply_intent_classifier`、`reply_polisher`、`reply_risk_reviewer` 的 prompt 预览
- **THEN** 三者均返回 `available:true` 与非空 prompt，内容来自各自运行时实际 prompt 构建函数及明示示例输入，不再返回“暂不支持预览”

#### Scenario: 发布侧文本角色忠实渲染

- **WHEN** 已鉴权请求某发布侧文本角色（包括封面文字卡文案）的 prompt 预览
- **THEN** 返回 `available:true` 且 `prompt` 为经其真实 `build*Prompt` + 示例输入渲染的真实 prompt 文本，实时数据以明示占位标注；`build*Prompt` 逻辑不被改动

#### Scenario: 发布话题角色可只读预览

- **WHEN** 已鉴权请求话题生成或话题相关性评判角色的 prompt 预览
- **THEN** 返回 `available:true` 且 `prompt` 分别来自真实话题生成 / 话题评判 prompt 构建函数与最小合法示例输入

#### Scenario: 正文去 AI 味改写可只读预览且与线上同源

- **WHEN** 已鉴权请求正文去 AI 味改写角色的 prompt 预览
- **THEN** 返回 `available:true` 且 `prompt` 为共享构建函数渲染的重写指令，与线上重写实际所用文本逐字一致（同一构建函数）；该角色在目录中且其重写调用按角色解析模型配置

#### Scenario: 现役漏登记角色补入目录后可预览可配

- **WHEN** 评论点赞择选角色在开关开启（现役、已注册）时被请求预览
- **THEN** 返回 `available:true` 的忠实渲染 prompt，且该角色在目录中可按角色配模型；若开关关闭未注册，则预览诚实返回「暂不支持预览」，绝不伪造

#### Scenario: 发布侧带 accountId 使用账号人设预览

- **WHEN** 已鉴权请求消费 persona 的发布侧文本角色预览并带 `?accountId=<已配人设账号>`
- **THEN** 预览示例输入使用该账号人设，返回体标注所用账号为该账号且不触发示例人设回落；生产发布链仍不因预览发生任何状态迁移

#### Scenario: 不消费 persona 的角色不伪造人设来源

- **WHEN** 已鉴权请求 interaction、Facebook 加群判定或视觉角色预览并带 `?accountId=<任一账号>`
- **THEN** prompt 仍可忠实预览，但不标为所选账号人设、不设置 `personaFallback`、不附人设来源段

#### Scenario: 按选定账号人设预览（浏览侧）

- **WHEN** 已鉴权请求某消费 persona 的浏览侧文本角色预览并带 `?accountId=<已配人设的账号>`
- **THEN** 返回 `available:true`，prompt 用**该账号人设**渲染，返回体标注所用账号为该账号且未触发示例人设回落

#### Scenario: 选定账号未配人设诚实回落标注

- **WHEN** 已鉴权请求带 `?accountId=<未配人设的账号>` 的、实际消费 persona 的文本角色预览
- **THEN** 渲染仍成功（`available:true`，用示例人设），且返回体以明示标志与说明告知「该账号未配人设、运行会被拒绝、用了示例人设」，绝不把示例人设标注为该账号人设

#### Scenario: 不传 accountId 行为兼容

- **WHEN** 已鉴权请求预览且不带 `accountId`
- **THEN** 需要 persona 的角色渲染示例人设，不消费 persona 的角色不附人设来源，返回体保持向后兼容，旧查看器正常显示

#### Scenario: 图像角色展示有效图片指令

- **WHEN** 已鉴权请求配图生成执行（图像角色）的 prompt 预览
- **THEN** 返回 `available:true` 且 `prompt` 为「示例主体描述 + 固定风格基底」的有效图片指令（固定风格基底可见），返回体说明标注其为文生图图片指令、用全局图片模型生成；不附来源段

#### Scenario: 视觉角色展示真实文本指令

- **WHEN** 已鉴权请求封面形态感知、整组视觉反推或视觉保真审核角色的 prompt 预览
- **THEN** 返回 `available:true` 与实际发送给视觉模型的非空文本指令；多阶段角色明确展示各真实阶段，图片仅用明示占位且不读取真实业务图片

#### Scenario: 目录与预览来源完整一致

- **WHEN** 自动化测试遍历角色目录中的所有非浏览现役模型角色
- **THEN** 每个角色的预览都返回 `available:true` 与非空 prompt；新增角色只进入目录但未提供真实预览来源时测试失败

#### Scenario: 未鉴权被拒

- **WHEN** 未带有效 JWT 请求 `GET /api/roles/:roleId/prompt`
- **THEN** 返回 401，不返回任何 prompt

#### Scenario: 渲染失败优雅降级不崩

- **WHEN** 某角色的 prompt 渲染过程抛错
- **THEN** 该角色返回 `available:false` 与失败原因，接口不抛、进程不崩，其它角色预览与运行闭环不受影响；若渲染前临时切换了预览账号口径，账号 MUST 在失败路径上仍被还原

#### Scenario: 只读无写

- **WHEN** 审查 prompt 可见能力的接口面
- **THEN** 只存在读取路径（GET），不存在任何修改 prompt 或人设的写路径（本期不开放编辑）
