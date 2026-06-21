## ADDED Requirements

### Requirement: 角色级模型与采样参数可配置，缺省回落绝不 brick

系统 SHALL 支持**按角色**覆盖文本模型名与温度，落 PostgreSQL `role_config` 表（`role_id` 主键）。任一角色的任一字段**缺行 / 为空 / 无效**时，模型 MUST 回落到全局 `textModel`、温度 MUST 回落到代码默认值（0），解析器 MUST NOT 抛错。覆盖值 MUST 在调用时从共享内存镜像解析，使 `PUT` 后**无需重启即生效**（热加载）。写入 MUST 先持久化成功、再刷新内存镜像。

#### Scenario: 按角色覆盖模型即时生效
- **WHEN** 经 `PUT /api/roles/:roleId/config` 把某生成类角色的模型改为另一可用模型
- **THEN** 该角色后续的文本调用使用新模型，其余角色不受影响，且无需重启进程

#### Scenario: 缺省回落不 brick
- **WHEN** 某角色在 `role_config` 无行，或其 `model` 字段为空
- **THEN** 该角色调用回落到全局 `textModel`、温度回落到代码默认 0，系统正常运行不报错

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

文本 LLM 客户端的调用入口 SHALL 接受可选的 per-call 覆盖选项（角色 / 模型 / 温度 / 超时）。**当调用方不传该选项时，请求行为 MUST 与改造前逐字一致**（模型经现有解析、温度与超时用构造默认）。浏览侧与发布侧的注入 SHALL 统一到同一个 LLM 客户端接口（含单轮与多轮调用），各角色内部代码 MUST NOT 因此改动。

#### Scenario: 不传选项零回归
- **WHEN** 任一现有调用未传 per-call 选项
- **THEN** 其使用的模型 / 温度 / 超时与改造前完全相同

#### Scenario: 传入角色即按角色解析
- **WHEN** 注入侧以绑定了某 `roleId` 的封装客户端发起调用
- **THEN** 该次请求按该角色的覆盖配置解析模型与温度，缺省回落全局 / 默认

### Requirement: 无效模型名诚实拒绝，绝不静默假成功

模型名由运营自由输入（不维护白名单）。当 `PUT` 提交一个**非空**模型名时，系统 MUST 做保存前探活（用该模型发一次轻量请求验证可用）并仅在探活通过后写入；探活失败 MUST 拒绝写入，返回诚实原因（`model_invalid`），MUST NOT 把无效名落库、MUST NOT 返回成功。空值 MUST 被视作「保持回落」而非无效（不探活）。

#### Scenario: 无效模型名探活失败被拒不落库
- **WHEN** 经 `PUT /api/roles/:roleId/config` 提交一个不存在的模型名，保存前探活失败
- **THEN** 系统返回 400 与 `model_invalid`，不写库、不刷镜像、绝不假成功

#### Scenario: 空模型名视作回落
- **WHEN** 提交 `model` 为空字符串
- **THEN** 系统将该角色模型置为「回落全局」，不视作无效错误

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

管理后台 SHALL 提供角色配置页：以列表呈现目录中每个角色（显示名 / 组 / 模型类型 / 当前生效模型 / 温度），支持按角色编辑模型与温度并保存。纯规则与遗留角色 MUST NOT 出现；判定类角色 MUST NOT 渲染温度输入。写操作 MUST 非乐观（round-trip 后据真态渲染）并使用诚实文案（已保存 / 模型名无效无法保存）。

#### Scenario: 列表只呈现可配角色
- **WHEN** 打开角色配置页
- **THEN** 仅列出现役 LLM 角色，纯规则 / 遗留角色不出现

#### Scenario: 非乐观保存
- **WHEN** 修改某角色模型并保存
- **THEN** 页面在服务端返回真态后再渲染，而非乐观更新；无效模型名时显示诚实错误且不改动列表显示

### Requirement: 大模型调用按角色可观测

系统 SHALL 在文本 LLM 出口为每次调用记录一行结构化日志，至少含角色标识、生效模型名与耗时，使运营改完配置后可验证是否真生效与成本变化。该日志 MUST NOT 含明文密钥或提示词正文等敏感内容。本期 MUST NOT 引入独立计费 / 统计面板。

#### Scenario: 调用记结构化日志
- **WHEN** 某角色发起一次文本模型调用
- **THEN** 出口记录一行含 `role` + 生效 `model` + 耗时的日志，不含密钥与提示词正文
