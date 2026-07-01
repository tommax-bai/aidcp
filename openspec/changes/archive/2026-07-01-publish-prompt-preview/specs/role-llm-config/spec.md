## MODIFIED Requirements

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
