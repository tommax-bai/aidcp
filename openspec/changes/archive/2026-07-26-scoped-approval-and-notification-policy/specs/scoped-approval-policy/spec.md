## ADDED Requirements

### Requirement: 账号级评论审批覆盖持久化、审计且默认不扩权

Cloud SHALL 以账号主键持久化评论审批覆盖模式 `source_rules|auto_approve_all`，无行 SHALL 等价 `source_rules`。写入 MUST 只接受受内部 JWT 守护的后台请求，校验账号存在、枚举合法，并以 UPSERT 后回读真态返回 `updatedBy` 与 `updatedAt`。初始化、读取、缺行或非法存量值 MUST fail-safe 回落 `source_rules`，MUST NOT 静默扩大评论写权限。

#### Scenario: 存量账号保持来源规则
- **WHEN** 某账号没有评论审批策略行
- **THEN** 其有效账号模式为 `source_rules`，各评论来源保持变更前审批行为

#### Scenario: 全局免审写后回真态
- **WHEN** 已鉴权管理员为存在账号保存 `auto_approve_all`
- **THEN** Cloud 持久化后返回含操作人和更新时间的写后真态，MUST NOT 乐观返回未落库状态

#### Scenario: 策略不可读不扩权
- **WHEN** 策略表初始化失败、单次读取异常或读到未知枚举
- **THEN** 本次解析回落 `source_rules` 并记录具名退化原因，MUST NOT 按全局免审执行

### Requirement: 账号全局免审统一覆盖所有评论来源但不绕安全闸

Cloud SHALL 在评论进入授权等待前统一解析有效模式：账号策略为 `auto_approve_all` 时结果 MUST 为 `auto_approve`；否则沿用来源提供的 `review|auto_approve`，来源未提供时为 `review`。该覆盖 MUST 应用于普通浏览、排期、联系评论、mandatory、飞书 `/comment` 与结构化委托评论。自动批准 MUST 直接授权，并把账号、目标和拟提交终稿旁路发送到无按钮通知口；通知缺失或失败只记日志，MUST NOT 阻止提交、延迟提交或回退为审批卡。该模式 MUST NOT 绕过风险、自动化配额、去重、目标复核、平台确认或真实终态记录，手工命令已有的风险覆盖语义也不得因本策略改变。

#### Scenario: 飞书手工评论服从账号全局免审
- **WHEN** 运营对 `auto_approve_all` 账号发送精确 `/comment`
- **THEN** 评论不等待第二次按钮审批，直接进入既有提交链
- **AND** 免审通知失败时只记日志，MUST NOT 阻止评论或产生审批卡

#### Scenario: 来源局部免审继续生效
- **WHEN** 账号为 `source_rules`，排期或 mandatory 来源已合法提供 `auto_approve`
- **THEN** 该来源仍按既有预授权执行并旁路通知，MUST NOT 被账号默认收紧

#### Scenario: 全局免审不伪造评论成功
- **WHEN** 账号全局免审已授权但目标复核失败、Edge 提交失败或平台未确认
- **THEN** 系统按真实失败终态收敛，MUST NOT 因已授权记录评论成功

### Requirement: 分组级稿件审核入口策略持久化且默认双通道

Cloud SHALL 以 `group_label` 为主键持久化 `client_and_feishu|client_only`，无行 SHALL 等价 `client_and_feishu`。写入 MUST 校验分组存在并回读带审计字段的真态。策略初始化、读取、缺行或非法值 MUST 向 `client_and_feishu` 回落。

#### Scenario: 存量分组保持双通道
- **WHEN** 某分组没有稿件审核入口策略行
- **THEN** 其有效策略为 `client_and_feishu`，既有客户端与飞书入口均保留

#### Scenario: 策略读取失败保留飞书可见性
- **WHEN** 生成 review 稿件时分组策略读取失败
- **THEN** Cloud 仍发送飞书审批卡并记录回退原因，MUST NOT 静默隐藏稿件

### Requirement: 仅客户端策略必须以可证明客户归属为前提

对无 `originChatId` 的 `review` 稿件，Cloud SHALL 先持久化 `pending_approval`，再解析当前账号分组和客户可审批归属。仅当分组为 `client_only`，且存在启用客户、活跃环境、admin 环境授权范围与权威账号绑定共同证明该账号可经 customer-auth HTTP 读取和审批时，Cloud 才 MUST 抑制飞书按钮卡并记录 `suppressed_by_client_only_policy`。账号无分组、客户被禁用、归属不可证或查询异常时 MUST 回退发送飞书卡。WebSocket 或自动化引擎是否在线 MUST NOT 作为 HTTP 稿件可达性的判据。

#### Scenario: 可达账号只进入客户端主动审核入口
- **WHEN** 无来源会话的 review 稿件属于 `client_only` 分组且客户审批归属可证明
- **THEN** 稿件保持 `pending_approval` 并出现在客户端队列，Cloud 不发送飞书按钮卡

#### Scenario: 归属不可证回退飞书
- **WHEN** 分组为 `client_only` 但账号没有可证明的启用客户活跃环境绑定
- **THEN** Cloud 发送飞书审批卡并记录具名回退原因

#### Scenario: 客户端暂时离线不触发回退
- **WHEN** 客户审批归属可证明但其 Edge 当前离线或浏览引擎未启动
- **THEN** Cloud 仍按 `client_only` 抑制按钮卡，因为稿件队列是持久 HTTP 数据面

### Requirement: 后台配置面必须展示策略真态与运行时回退边界

Console SHALL 在账号配置中直接提供“按来源规则 / 全局免审”选择，不为全局免审增加解释性告警或 Tooltip；在分组通知配置中提供“客户端+飞书 / 仅客户端”选择，并展示该分组活跃账号的客户审批归属覆盖情况。保存 MUST 以 Cloud 写后真态刷新。选择 `client_only` 且覆盖不完整时界面 MUST 明示未覆盖账号运行时仍会回退飞书；路由说明 MUST 如实表达审批卡按来源会话、账号团队群及默认群解析。

#### Scenario: 覆盖不完整时不宣称完全静默
- **WHEN** 管理员选择 `client_only`，但分组内存在客户审批归属不可证账号
- **THEN** Console 显示回退警告和覆盖数量，MUST NOT 宣称该分组所有稿件都不再发飞书

#### Scenario: 策略保存非乐观
- **WHEN** Cloud 拒绝策略写入或返回失败
- **THEN** Console 保留服务端原真态并展示失败，MUST NOT 本地切换后宣称保存成功
