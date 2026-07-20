## MODIFIED Requirements

### Requirement: 客户端 onboarding 关键词向导经边缘发起的 WS 请求触发云端生成

Electron 客户端 SHALL 提供按维度选择关键词的人设向导——垂类（枚举快捷选 + 自定义自由文本）、兴趣（快捷标签多选 + 自由文本）、语气（枚举单选）与点赞倾向（正常 / 喜欢 / 更喜欢，默认正常）。点赞倾向 MUST 有真实输出映射：客户端 SHALL 以受控标记随 `keywordSelections` 发送，云端 SHALL 在生成兴趣关键词前剥离该标记，并把档位写入 `behavior_guidelines.like_affinity` 与匹配账号兴趣的 `like_principle`；MUST NOT 把内部标记写入身份或兴趣。除有明确映射的选择外，客户端 MUST NOT 提供对生成产物零影响的输入。

新版 Electron SHALL 经客户鉴权的环境级 HTTP 请求触发生成，主进程只提交由目标环境解析的 `envKey`、关键词、可选发言语言与 idempotency key；Cloud SHALL 由客户归属与持久绑定解析 `accountId`，请求体 MUST NOT 自报账号。旧版 Edge MAY 继续经运行中 core 发起 `persona.generate` WebSocket 请求，Cloud SHALL 从握手 session 取账号。两种入口 MUST 调用同一人设应用服务、共享按 `(accountId,idempotencyKey)` 的生成幂等、平台校验、输入上限、模型记账与失败语义。

HTTP 草稿生成 SHALL 使用足以覆盖 180 秒模型天花板的显式长超时；WebSocket 兼容入口继续使用 `timeoutMs ≥ 185s`。生成触发只要求 Cloud 能权威解析一个已存在账号，MUST NOT 要求目标环境此刻在线；无法解析持久绑定时 MUST 诚实拒绝且不调用模型。

#### Scenario: 停止环境通过客户鉴权触发生成

- **WHEN** 客户为自己拥有且已持久绑定账号的停止环境选定关键词与点赞倾向并点击生成
- **THEN** Electron 经具名 HTTP 桥提交 `envKey` 与受控输入，Cloud 解析绑定账号并生成草稿，MUST NOT 要求 core 在线

#### Scenario: 旧版运行中客户端继续兼容

- **WHEN** 旧版 Edge 在握手后发送 `persona.generate` WebSocket 请求
- **THEN** Cloud 仍从 session 账号处理并返回兼容响应，与 HTTP 入口使用相同生成规则

#### Scenario: 默认正常并在预览中可核对

- **WHEN** 客户首次打开人设向导且未主动调整点赞倾向
- **THEN** “正常”档被选中，预览摘要显示“点赞倾向：正常”，生成的人设以 `like_affinity=normal` 持久化

#### Scenario: 点赞倾向标记不污染人设兴趣

- **WHEN** Cloud 收到 `like_affinity:like_more` 或 `like_affinity:like_most` 受控标记
- **THEN** 生成器在构造身份/兴趣 prompt 前移除该标记，并只把其映射到 `behavior_guidelines`，MUST NOT 写入 identity、interests 或 seed keywords

#### Scenario: 绑定身份未知不触发付费生成

- **WHEN** 环境从未成功握手、绑定冲突、环境不归当前客户或账号行不存在
- **THEN** 客户 HTTP 入口 fail-closed 且不调用模型；旧 WS 入口仍要求握手 session 具有账号

#### Scenario: 超长或超量输入被诚实拒绝

- **WHEN** `keywordSelections` 某项超单项长度上限或总条数超上限
- **THEN** Cloud 诚实拒绝并且绝不把超限内容喂进 prompt，Edge 透传失败原因

### Requirement: 草稿经客户确认后走现有已校验写入通道落库，边缘不本地判成功

客户确认草稿后，新版 Electron SHALL 经客户鉴权环境级 HTTP 请求提交目标 `envKey` 与确认后的 soul YAML；Cloud MUST 复核当前客户归属并解析持久绑定账号。旧版 Edge MAY 继续发送 `persona.persist` WebSocket 请求，Cloud 从握手 session 取账号。两种入口 MUST 复用同一人设应用服务与现有人设单写通道（soul 校验 + 外键守护 + 写库成功才刷内存镜像 + 绑定即热加载唤醒在线节点 + 首次绑定引导 + 诚实回执），MUST NOT 新造绕过校验的写路径。

Edge MUST 在请求发出前展示保存中状态，仅在 Cloud 成功回执后显示已保存/已更新；失败时 MUST 保留原人设与草稿并呈现真实 `reason`，MUST NOT 本地判成功。HTTP 保存不要求目标环境在线，成功回执只代表人设已持久化与热加载，MUST NOT 冒充浏览器已启动或首作已完成。

#### Scenario: 停止环境确认落库并绑定

- **WHEN** 客户在停止环境中确认合法草稿
- **THEN** Cloud 解析绑定账号、落 `persona_config`、刷新镜像并返回成功真态，目标 core 无需在线

#### Scenario: 保存失败保留原人设

- **WHEN** 归属/绑定在确认前变化，或 soul 非法、持久化失败
- **THEN** Edge 显示真实失败并保留原人设与可重试草稿，MUST NOT 显示成功

#### Scenario: 旧版 WebSocket 保存继续兼容

- **WHEN** 旧版 Edge 经 `persona.persist` 提交确认草稿
- **THEN** Cloud 继续从 session 账号调用同一单写服务并返回兼容回执

#### Scenario: 账号行缺失优雅回诚实失败

- **WHEN** 任一入口命中账号外键守护或权威绑定无法解析
- **THEN** Cloud 返回可区分的诚实失败、不落库、不刷镜像，向导可在账号身份落定后重试

#### Scenario: 空或非法人设被拒不落库

- **WHEN** 确认提交的 soul 为空、超限或结构非法
- **THEN** Cloud 诚实拒绝，MUST NOT 落库、MUST NOT 刷镜像

## ADDED Requirements

### Requirement: 已绑账号可查看当前人设并经确认流程整体调整

人设向导 SHALL 同时支持首次绑定与已绑账号调整。已绑账号打开时 SHALL 先看到当前真实人设摘要和完整定义入口；点击调整后 MAY 以当前人设可精确反向映射的语气、语言、内容标签与点赞倾向预填选择，并生成一份新的完整草稿。确认动作 SHALL 明示会整体替换当前人设；只生成或预览 MUST NOT 修改现有人设。

#### Scenario: 已绑账号生成新草稿不影响当前人设

- **WHEN** 客户为已绑账号点击调整并生成一份新草稿但尚未确认
- **THEN** 当前 `persona_config` 与运行时人设保持不变，界面同时保留当前摘要与待确认草稿语义

#### Scenario: 确认后整体替换

- **WHEN** 客户核对新草稿后点击确认且 Cloud 保存成功
- **THEN** 账号人设整体替换为新 soul，后续运行即时使用新人设

## REMOVED Requirements

### Requirement: 适用范围仅新号 onboarding 一次性

**Reason**: 客户现在需要在已绑账号上查看和调整人设；仍限制为新号一次性会与环境级离线管理目标直接冲突。

**Migration**: 旧客户端行为保持不变；新版客户端对已绑账号展示当前摘要，并通过相同的草稿确认与权威单写通道更新。

### Requirement: 生成 gate 判据不放宽但引导透明

**Reason**: `auth/cloud connected` gate 是旧 core→WebSocket 传输的偶然前置，不是 Cloud 生成人设的业务前置。

**Migration**: 新版客户端以客户登录、环境归属和持久账号绑定为 gate；只有 `binding_unknown` 等无法确认账号的状态才引导首次启动。旧版 WS 客户端继续沿用原 gate。
