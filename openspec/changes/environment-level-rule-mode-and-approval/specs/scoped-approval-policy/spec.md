## MODIFIED Requirements

### Requirement: 账号级评论审批覆盖持久化、审计且默认不扩权

Cloud SHALL 以**环境**主键持久化评论审批覆盖模式 `source_rules|auto_approve_all`，无行 SHALL 等价 `source_rules`。写入 MUST 接受两类且仅两类来源：受内部 JWT 守护的后台请求，以及经 customer-auth 鉴权、对**自有环境**发起的客户请求；两类写入 MUST 校验环境存在与归属、枚举合法，并以 UPSERT 后回读真态返回 `updatedBy` 与 `updatedAt`，其中客户来源的操作人身份 MUST 与后台管理员可区分。`accountId` MUST NOT 由任何写入方提交，也 MUST NOT 作为写入目标选择器。环境尚未绑定账号时 MUST 允许保存与读取，并如实标注当前没有执行对象。

初始化、读取、缺行或非法存量值 MUST fail-safe 回落 `source_rules`，MUST NOT 静默扩大评论写权限。

#### Scenario: 存量环境保持来源规则
- **WHEN** 某环境没有评论审批策略行
- **THEN** 其有效模式为 `source_rules`，各评论来源保持变更前审批行为

#### Scenario: 全局免审写后回真态
- **WHEN** 已鉴权管理员为存在环境保存 `auto_approve_all`
- **THEN** Cloud 持久化后返回含操作人和更新时间的写后真态，MUST NOT 乐观返回未落库状态

#### Scenario: 客户对自有环境写入留可区分审计
- **WHEN** 已登录客户对自己拥有的环境保存 `auto_approve_all`
- **THEN** Cloud 持久化后返回写后真态，且 `updatedBy` 标识为客户来源，MUST NOT 复用管理员署名

#### Scenario: 非所有者客户写入 fail-closed
- **WHEN** 已登录客户对不属于自己的环境提交策略写入
- **THEN** Cloud 拒绝写入，MUST NOT 修改任何策略行，MUST NOT 泄露该环境的账号身份或现有策略

#### Scenario: 未绑定环境可预设免审
- **WHEN** 所有者为尚未绑定账号的自有环境保存 `auto_approve_all`
- **THEN** Cloud 持久化该环境策略并如实标注当前没有执行对象，MUST NOT 伪造绑定或生效评论行为

#### Scenario: 策略不可读不扩权
- **WHEN** 策略表初始化失败、单次读取异常或读到未知枚举
- **THEN** 本次解析回落 `source_rules` 并记录具名退化原因，MUST NOT 按全局免审执行

### Requirement: 账号全局免审统一覆盖所有评论来源但不绕安全闸

Cloud SHALL 在评论进入授权等待前统一解析有效模式：先由执行账号反查其当前绑定环境，该环境策略为 `auto_approve_all` 时结果 MUST 为 `auto_approve`；否则沿用来源提供的 `review|auto_approve`，来源未提供时为 `review`。反查得不到唯一环境——绑定未知、绑定冲突、跨客户争用或环境注册表不可读——MUST 回落 `source_rules`，MUST NOT 沿用任何账号键存量值扩权。该覆盖 MUST 应用于普通浏览、排期、联系评论、mandatory、飞书 `/comment` 与结构化委托评论。自动批准 MUST 直接授权，并把账号、目标和拟提交终稿旁路发送到无按钮通知口；通知缺失或失败只记日志，MUST NOT 阻止提交、延迟提交或回退为审批卡。该模式 MUST NOT 绕过风险、自动化配额、去重、目标复核、平台确认或真实终态记录，手工命令已有的风险覆盖语义也不得因本策略改变。

#### Scenario: 飞书手工评论服从环境全局免审
- **WHEN** 运营对绑定在 `auto_approve_all` 环境上的账号发送精确 `/comment`
- **THEN** 评论不等待第二次按钮审批，直接进入既有提交链
- **AND** 免审通知失败时只记日志，MUST NOT 阻止评论或产生审批卡

#### Scenario: 来源局部免审继续生效
- **WHEN** 环境为 `source_rules`，排期或 mandatory 来源已合法提供 `auto_approve`
- **THEN** 该来源仍按既有预授权执行并旁路通知，MUST NOT 被环境默认收紧

#### Scenario: 环境换绑后新账号继承免审
- **WHEN** 已设为 `auto_approve_all` 的环境从账号 A 换绑为账号 B
- **THEN** 账号 B 的评论按 `auto_approve` 解析，账号 A 不再因该环境免审，MUST NOT 要求重启

#### Scenario: 反查不到唯一环境不扩权
- **WHEN** 执行账号绑定未知、绑定冲突、跨客户争用或环境注册表不可读
- **THEN** 本次解析回落 `source_rules` 并记录具名退化原因，MUST NOT 按全局免审执行

#### Scenario: 全局免审不伪造评论成功
- **WHEN** 全局免审已授权但目标复核失败、Edge 提交失败或平台未确认
- **THEN** 系统按真实失败终态收敛，MUST NOT 因已授权记录评论成功

### Requirement: 后台配置面必须展示策略真态与运行时回退边界

Console SHALL 在**环境**配置中直接提供“按来源规则 / 全局免审”选择，不为全局免审增加解释性告警或 Tooltip；在分组通知配置中提供“客户端+飞书 / 仅客户端”选择，并展示该分组活跃账号的客户审批归属覆盖情况。环境未绑定账号时 SHALL 仍可配置并如实标注当前没有执行对象。保存 MUST 以 Cloud 写后真态刷新。选择 `client_only` 且覆盖不完整时界面 MUST 明示未覆盖账号运行时仍会回退飞书；路由说明 MUST 如实表达审批卡按来源会话、账号团队群及默认群解析。

#### Scenario: 覆盖不完整时不宣称完全静默
- **WHEN** 管理员选择 `client_only`，但分组内存在客户审批归属不可证账号
- **THEN** Console 显示回退警告和覆盖数量，MUST NOT 宣称该分组所有稿件都不再发飞书

#### Scenario: 策略保存非乐观
- **WHEN** Cloud 拒绝策略写入或返回失败
- **THEN** Console 保留服务端原真态并展示失败，MUST NOT 本地切换后宣称保存成功

#### Scenario: 环境维度呈现不冒充账号维度
- **WHEN** 管理员在 Console 查看某环境的评论审批策略
- **THEN** 界面标明该配置作用于环境、由当前绑定账号执行
- **AND** MUST NOT 呈现为「该账号自带的设置」，也 MUST NOT 在换绑后仍展示旧账号署名为当前生效者
