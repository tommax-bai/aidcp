## MODIFIED Requirements

### Requirement: LLM 客户端按角色覆盖向后兼容，不传选项行为不变

文本 LLM 客户端的调用入口 SHALL 接受可选的 per-call 覆盖选项（角色 / 模型 / 温度 / 超时）。**当调用方不传该选项时，请求行为 MUST 使用构造默认解析**（模型经现有解析、温度与超时用构造默认）。浏览侧与发布侧的注入 SHALL 统一到同一个 LLM 客户端接口（含单轮与多轮调用），各角色内部代码 MUST NOT 因此改动。

**构造默认请求超时 MUST 按 thinking 类模型的真实耗时定其天花板**：默认值 MUST ≥ 180s（thinking 模型复杂提示常需 60–150s+，短天花板会把合法慢调用误判超时中止）。该默认 MUST 经文档化的 env 旋钮可调，缺失/非法（非正数/超合理上限）时 MUST 回落安全默认、绝不 brick。per-call 传入的超时覆盖仍优先于构造默认（如探活用短超时不受本条影响）。

配置/覆盖的 `timeoutMs` MUST 是**调用方 Promise 的硬结算 deadline**，不得仅表示“向底层 HTTP 发出 abort 请求”：即使 fetch 忽略 signal、永不 resolve/reject，文本客户端也 MUST 在 deadline 到达时以稳定超时错误 reject，并执行统一失败终局；底层 Abort 仍 SHALL best-effort 执行以释放网络资源。迟到的底层 resolve/reject MUST NOT 产生第二次终局、重复记账或 unhandled rejection。

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

#### Scenario: fetch 忽略 Abort 仍按 deadline reject
- **WHEN** 注入的 fetch 永不 settle 且完全忽略 `AbortController.signal`
- **THEN** 文本客户端 MUST 在 `timeoutMs` 到达时以稳定超时错误 reject，统一失败终局恰好执行一次；迟到分支不得重复终局或产生未处理 rejection

### Requirement: 大模型调用按角色可观测

系统 SHALL 在文本 LLM 出口为每次调用记录不含正文的**开始记录**与一行结构化**终局记录**。开始记录至少含账号、角色标识、**生效厂商（provider）**、生效模型名与 deadline；终局记录至少含相同调用维度、耗时、成功/失败、是否 deadline 超时，以及请求最后到达的阶段（请求已发起 / 已收到响应头 / 已解析响应体）。若已从响应头取得厂商请求 ID，终局 SHALL 一并记录，便于供应商侧追查。日志 MUST NOT 含明文密钥、提示词或响应正文等敏感内容。本期 MUST NOT 引入独立计费 / 统计面板，token 用量按模型名聚合可暂不加 provider 维度（同名跨厂商归并列为已知限制，靠日志 provider 可回溯）。

#### Scenario: 正常调用记录开始与终局阶段
- **WHEN** 某角色发起一次文本模型调用并成功收到可解析响应
- **THEN** 出口记录开始元数据，并在终局记录 `role` + `provider` + 生效 `model` + 耗时 + 成功 + 已解析响应体阶段；两者均不含密钥与 prompt/响应正文

#### Scenario: deadline 日志指出最后阶段
- **WHEN** 调用在请求已发起后未取得响应头，或取得响应头后响应体永不结算
- **THEN** 超时终局 MUST 分别记录最后阶段为“请求已发起”或“已收到响应头”、`timedOut=true`，并在已取得时携厂商请求 ID
