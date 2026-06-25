## MODIFIED Requirements

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

### Requirement: 大模型调用按角色可观测

系统 SHALL 在文本 LLM 出口为每次调用记录一行结构化日志，至少含角色标识、**生效厂商（provider）**、生效模型名与耗时，使运营改完配置后可验证是否真生效与成本变化、并能区分同名模型来自哪个厂商。该日志 MUST NOT 含明文密钥或提示词正文等敏感内容。本期 MUST NOT 引入独立计费 / 统计面板，token 用量按模型名聚合可暂不加 provider 维度（同名跨厂商归并列为已知限制，靠日志 provider 可回溯）。

#### Scenario: 调用记结构化日志含厂商
- **WHEN** 某角色发起一次文本模型调用
- **THEN** 出口记录一行含 `role` + `provider` + 生效 `model` + 耗时的日志，不含密钥与提示词正文
