## MODIFIED Requirements

### Requirement: 角色 prompt 在后台只读可见，忠实渲染且优雅降级

系统 SHALL 让现役 LLM 角色的 prompt 在管理后台**只读可见**：经只读接口 `GET /api/roles/:roleId/prompt`（与其它 `/api/*` 一样受 JWT 守护）返回该角色 prompt 的**忠实渲染**——调用该角色**真实的** prompt 构建逻辑、传入最小合法示例数据与人设渲染得到，使运营看到的就是线上真用的指令文字与人设（占位的实时数据以明示标注）。

该接口 MAY 接受**可选**查询参数 `accountId`：

- 给定 `accountId` 时，系统 SHALL 按**该账号的人设**忠实渲染（人设经按账号解析注入，MUST NOT 改动任何角色既有 `buildPrompt`/`previewPrompt` 的逻辑）。
- 给定的 `accountId` **没有配置人设**时，系统 MUST 诚实回落到系统默认人设渲染，并在返回体以**明示标注**（如可选标志位与说明）告知「该账号未配人设，预览用默认人设」，MUST NOT 把默认人设冒充为该账号人设。
- **不传** `accountId` 时，系统 SHALL 渲染系统默认人设，行为与本扩展前**逐字一致**（向后兼容）。
- 返回体为支持上述标注新增的字段 MUST 为**可选**字段，未升级的查看器 MUST 仍能正常显示。

本能力 MUST 为**纯只读**：MUST NOT 提供任何写/改 prompt 的接口或路径，`accountId` 仅作渲染口径、MUST NOT 改写任何账号的人设或状态。渲染 MUST NOT 改动任何角色既有 `buildPrompt` 的逻辑（线上 prompt 行为零变化）。单个角色渲染失败 MUST 降级为「预览不可用 + 原因」、MUST NOT 抛出、MUST NOT 连累浏览/发布闭环。未知 `roleId` SHALL 返回 404；非 LLM（图像/纯规则）角色 SHALL 返回「不可预览」标注而非 prompt。

#### Scenario: 文本角色 prompt 只读可见

- **WHEN** 已鉴权请求 `GET /api/roles/:roleId/prompt`，该 roleId 是一个现役文本 LLM 角色
- **THEN** 返回 `available:true` 且 `prompt` 为该角色忠实渲染的 prompt 文本（含其真实指令片段与真实人设），不含任何写入能力

#### Scenario: 按选定账号人设预览

- **WHEN** 已鉴权请求某文本角色预览并带 `?accountId=<已配人设的账号>`
- **THEN** 返回 `available:true`，prompt 用**该账号人设**渲染，返回体标注所用账号为该账号且未触发默认回落

#### Scenario: 选定账号未配人设诚实回落标注

- **WHEN** 已鉴权请求带 `?accountId=<未配人设的账号>` 的预览
- **THEN** 渲染仍成功（`available:true`，用系统默认人设），且返回体以明示标志与说明告知「该账号未配人设、用了默认人设」，绝不把默认人设标注为该账号人设

#### Scenario: 不传 accountId 行为不变

- **WHEN** 已鉴权请求预览且不带 `accountId`
- **THEN** 渲染系统默认人设，返回体与本扩展前逐字一致，旧查看器正常显示

#### Scenario: 未鉴权被拒

- **WHEN** 未带有效 JWT 请求 `GET /api/roles/:roleId/prompt`
- **THEN** 返回 401，不返回任何 prompt

#### Scenario: 渲染失败优雅降级不崩

- **WHEN** 某角色的 prompt 渲染过程抛错
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
