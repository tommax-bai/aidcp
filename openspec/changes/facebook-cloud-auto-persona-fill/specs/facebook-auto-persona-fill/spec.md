## ADDED Requirements

### Requirement: 客户端只提交无账号 ID 的 Facebook 补齐意图

客户在 Facebook 批量创建中启用自动补齐后，Edge SHALL 经 customer-auth 提交一次带平台、版本化自动策略和整批发言语言的补齐意图，MUST NOT 提交账号 ID 列表、客户端人设状态、账号凭据、cookie、2FA 或代理资料。Cloud SHALL 以鉴权令牌中的客户身份确定范围，MUST NOT 接受请求体自报客户或账号选择器。

#### Scenario: 正常创建无账号 ID 的补齐运行
- **WHEN** 已登录客户完成 Facebook 批量创建并保留自动补齐选项
- **THEN** Edge 只提交 `facebook`、受支持策略和发言语言，Cloud 从令牌与权威环境归属建立运行，请求和响应均不含账号 ID 清单或敏感导入资料

#### Scenario: 绕过界面提交账号选择器
- **WHEN** 调用方在补齐意图中附带 `accountId`、`accountIds`、`envKeys`、`userId` 或其他未允许字段
- **THEN** Cloud 以 `bad_request` 拒绝，MUST NOT 创建运行或生成人设

### Requirement: Cloud 快照当前客户 Facebook 环境并延迟解析真实账号

Cloud SHALL 在建立运行时快照该客户当前权威归属的全部 Facebook 环境。已有有效环境→账号绑定的目标 SHALL 立即进入缺失人设检查；尚未绑定的目标 SHALL 保持 `waiting_binding`，并在该环境后续成功握手、Cloud 建立真实绑定后继续。处理时 MUST 复核当前客户归属、Facebook 平台、账号主表存在和跨客户争用，MUST NOT 从环境名、导入文本或客户端投影猜测账号。

#### Scenario: 已绑定账号立即进入处理
- **WHEN** 运行快照包含一个当前客户拥有、已绑定有效 Facebook 账号的环境
- **THEN** Cloud 以服务端绑定得到账号并检查其人设，不要求 Edge 再提供账号 ID

#### Scenario: 新环境尚未登录
- **WHEN** 运行快照包含一个尚无账号绑定的 Facebook 环境
- **THEN** 目标保持等待且不生成；该环境首次登录握手建立绑定后，Cloud 自动继续同一目标

#### Scenario: 归属撤销或绑定冲突
- **WHEN** 目标处理时环境已不归该客户、平台不符、账号悬空或存在跨客户绑定冲突
- **THEN** Cloud fail-closed 等待或记录具名失败，MUST NOT 为该账号写人设

### Requirement: 自动补齐只创建缺失人设且绝不覆盖

Cloud SHALL 在生成前检查目标账号是否已有有效人设，并在写入时使用数据库原子 create-if-missing。已有有效人设 SHALL 记录为 `skipped_existing`；生成在途期间人工新增的人设也 MUST 保留，自动产物 MUST NOT 覆盖。只有真实插入成功才可触发账号已绑投影和运行唤醒。

#### Scenario: 运行建立前已有人工人设
- **WHEN** 目标账号已有有效 `persona_config`
- **THEN** Cloud 跳过该账号，不调用模型、不更新人设内容或审计字段

#### Scenario: 生成期间人工先完成人设
- **WHEN** 自动生成已开始但在落库前人工写入同账号人设
- **THEN** 原子 create-if-missing 返回未创建，Cloud 保留人工人设并把自动目标记录为已跳过

### Requirement: 自动策略显式、有界且按账号差异化

Cloud SHALL 只接受受支持的 `facebook_auto_v1` 策略和 `zh-CN/en/vi` 发言语言。该策略 SHALL 从版本化受控方向池按账号稳定选择非空关键词，并用账号相关差异化种子调用现有 PersonaGenerator；产物 MUST 通过现有 soul 校验。未知策略、非法语言、模型失败或非法产物 MUST fail-closed，不得回落默认/模板人设。

#### Scenario: 两个账号使用同一批设置
- **WHEN** 同一运行处理两个缺失人设的 Facebook 账号
- **THEN** 两者共享所选发言语言，但按各自账号种子选择/生成人设，MUST NOT 复制同一份固定 persona 文本

#### Scenario: 非法策略或语言
- **WHEN** 请求携带未知策略或不受支持的发言语言
- **THEN** Cloud 在建运行前拒绝，且不调用模型、不写任何人设

### Requirement: 补齐运行持久、幂等并诚实记录结果

Cloud SHALL 持久化运行及每个环境目标，按客户和 Idempotency-Key 去重；重复请求 MUST 返回同一运行而不重复快照或计费。Cloud 重启后 SHALL 恢复未终结运行，陈旧 `running` 目标可回到待处理。目标模型/写入失败 SHALL 有界重试并最终记录失败；API 接受运行只表示已排队，MUST NOT 表述为人设已设置。

#### Scenario: 网络重试重复提交
- **WHEN** Edge 以相同客户和 Idempotency-Key 重试创建补齐运行
- **THEN** Cloud 返回同一运行的幂等接受态，不创建第二组目标、不重复调用模型

#### Scenario: Cloud 在运行中重启
- **WHEN** Cloud 在目标等待绑定或生成过程中重启
- **THEN** 启动恢复会继续未终结运行；已成功或已跳过目标不重复写入

#### Scenario: 个别账号生成失败
- **WHEN** 一个目标超过有界尝试仍无法生成或持久化合法人设
- **THEN** 该目标保持未设置并记录失败原因，其他目标继续，运行不得把该目标宣称成功
