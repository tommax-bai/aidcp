## ADDED Requirements

### Requirement: 客户可按已授权环境离线读取、生成和保存账号人设

客户鉴权 API SHALL 提供按 `envKey` 定位的单账号人设读取、草稿生成和确认保存接口，且这些接口 MUST NOT 要求目标环境的 core、浏览器或边云 WebSocket 在线。每次请求 SHALL 以当前客户令牌复核客户状态与环境归属，再通过权威持久绑定解析真实 `accountId`；客户端请求体 MUST NOT 接受 `accountId`、客户选择器、环境归属或平台自报字段，响应 MUST 回显 `envKey` 但 MUST NOT 暴露 `accountId`。

绑定解析的 `environment_not_owned`、`binding_unknown`、`binding_conflict` 与 `binding_unavailable` MUST 保持可区分并 fail-closed，MUST NOT 把任一失败伪装成 `missing` 或成功空结果。Cloud SHALL 以账号权威平台校验 Facebook 发言语言，以既有人设应用服务执行生成幂等、soul 校验、持久化和首次绑定引导。

#### Scenario: 停止环境读取已有人设

- **WHEN** 客户按自己拥有、已持久绑定账号且当前 core 停止的环境请求人设
- **THEN** API 返回该账号当前真实人设、结构化摘要与更新时间，响应回显 `envKey` 且不含 `accountId`

#### Scenario: 未设置与读取失败严格区分

- **WHEN** 已绑定账号确实没有 `persona_config` 行
- **THEN** API 返回 `state=missing` 且不返回任何默认模板作为当前人设
- **AND** 绑定未知、绑定冲突或存储不可用 MUST 返回各自失败，MUST NOT 返回 `state=missing`

#### Scenario: 环境未启动仍可生成草稿

- **WHEN** 客户为自己已绑定的停止环境提交有界关键词、有效幂等键和平台允许的发言语言
- **THEN** Cloud 以绑定账号记账并生成未落库草稿，目标环境无需启动
- **AND** 同账号同幂等键重试 MUST NOT 重复调用模型或重复记账

#### Scenario: 确认保存走既有单写通道

- **WHEN** 客户为自己已绑定环境确认提交合法非空 soul YAML
- **THEN** Cloud 经既有账号人设校验与持久化单写通道保存，返回写后真态并即时热加载
- **AND** 非法、空白或超限内容被诚实拒绝，库与内存镜像保持原状

#### Scenario: 非所有者无法借环境键访问人设

- **WHEN** 客户提交不属于自己的 `envKey` 读取、生成或保存人设
- **THEN** 三种操作均 fail-closed，不返回人设正文、摘要、账号键或可用于判断他人绑定状态的成功结果
