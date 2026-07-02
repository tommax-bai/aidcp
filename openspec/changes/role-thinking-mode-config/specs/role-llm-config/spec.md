## ADDED Requirements

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
