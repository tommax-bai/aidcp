## RENAMED Requirements

- FROM: `### Requirement: 自动发帖执行环境冻结并约束恢复下发`
- TO: `### Requirement: 自动发帖执行归属按部署目标冻结并约束恢复下发`

## MODIFIED Requirements

### Requirement: 内容调度器按账号扇出并分钟错峰

系统 SHALL 提供一个云端单进程、每分钟心跳的内容调度器（命令式触发器，MUST NOT 进角色注册表、MUST NOT 走事件总线）。自动发帖每次心跳 SHALL 遍历完成欢迎握手的在线账号；**账号必须连着引擎才执行排期，但 MUST NOT 要求解析出浏览器环境标识**——环境标识不再是自动发帖的前置条件。部署目标 SHALL 由 Cloud 严格解析本地 `AIDCP_DEPLOY_ENV=dev|ol` 注入，MUST NOT 接受 Edge 自报 target。对每个账号按闸序判定：排期启用 ∧ 有效且当前活跃的内容格 ∧ 当前分钟命中该账号错峰偏移 ∧ 未达日上限 ∧ 风控状态为 normal。错峰偏移 SHALL 为 `hash(accountId + 本地日期 + 动作) % 60` 得到的分钟（纯函数、无状态、可复现；逐日变化、账号间错开）。心跳 MUST 有重入护栏（上轮未完即跳过本轮），且对 `(账号, 动作, 小时格)` 幂等；其中自动发帖 MUST 在数据库中原子占位，跨进程与进程重启后同格也 MUST NOT 重复触发，评论类动作继续按既有进程内幂等执行。小时格占位的唯一性 SHALL 由 `(账号, 动作)` 决定，浏览器环境标识 MUST NOT 参与该唯一性判定。

#### Scenario: 命中偏移分钟才尝试
- **WHEN** 当前小时是某账号活跃内容格，但当前分钟不等于该账号的错峰偏移
- **THEN** 本分钟不触发；仅在分钟等于偏移时尝试

#### Scenario: 账号间错峰
- **WHEN** 多个账号在同一活跃小时格
- **THEN** 各账号按其 `hash(账号+日期+动作)%60` 落在不同分钟触发，绝不在同一刻齐发

#### Scenario: 同小时格不重复
- **WHEN** 同一账号在同一发帖小时格已被任一 Cloud 进程原子占位，或占位进程随后重启
- **THEN** 任何 Cloud 进程在该小时格内 MUST NOT 再次启动该账号的自动发帖

#### Scenario: 环境标识不完整不再关闭自动发帖
- **WHEN** 某在线连接已完成欢迎握手并带有账号，但其 `edgeId` 解析不出非空 `envKey`
- **THEN** 该账号照常进入自动发帖扫描，MUST NOT 因缺少环境标识被跳过

#### Scenario: 未完成握手或缺账号仍不进入扫描
- **WHEN** 在线连接未完成欢迎握手，或不能确定它属于哪个账号
- **THEN** 该连接 MUST NOT 进入自动发帖扫描，且人工发布与其它连接能力保持原行为

#### Scenario: Cloud target 无效时不启动调度
- **WHEN** Cloud 的 `AIDCP_DEPLOY_ENV` 缺失或不是 `dev|ol`
- **THEN** 自动内容调度器 MUST NOT 启动，并留下可诊断的 fail-closed 日志

### Requirement: 自动发帖执行归属按部署目标冻结并约束恢复下发

自动发帖在成功占位后 SHALL 将 Cloud 本地 `executionTarget` 和 `hourCell` 作为不可变执行归属传入发布管线，并持久化到候审记录元数据。已升级 Cloud 的候审扫描与按记录恢复下发 SHALL 仅处理未带自动排期归属的历史/人工稿件，或 `executionTarget` 与当前 Cloud 一致的自动稿件；target 不匹配 MUST 在任何 Edge 写操作前跳过，且不得改写稿件或审批状态。

浏览器环境标识 MUST NOT 参与执行归属判定：下发时 MUST NOT 要求实际在线的 Edge 与触发时刻的环境一致，账号在哪个环境在线即从哪个环境下发。历史稿件元数据中已冻结的环境标识 SHALL 保持可读、MUST NOT 参与判定，且 MUST NOT 因本变更被迁移或作废。

#### Scenario: 自动稿件记录部署目标与小时格
- **WHEN** dev Cloud 成功占位并生成自动候审稿件
- **THEN** 稿件元数据包含 `executionTarget=dev` 和命中的 `hourCell`，且这些值不接受 Edge 覆盖

#### Scenario: 归属元数据保存失败时关闭该轮
- **WHEN** 自动发帖无法把完整执行归属写入候审记录
- **THEN** 该稿件 MUST NOT 保持为可下发状态，并返回诚实失败结果

#### Scenario: 其它 target 不得恢复下发
- **WHEN** ol Cloud 扫描或被直接唤醒处理一条 `executionTarget=dev` 的自动稿件
- **THEN** ol Cloud 在任何 Edge 写操作前跳过该稿件，不改变其审批和稿件状态

#### Scenario: 换了浏览器环境照常下发
- **WHEN** 某自动稿件触发时账号在线于环境 A，审批恢复时该账号只在线于环境 B，且部署目标一致
- **THEN** Cloud 从环境 B 正常下发该稿件，MUST NOT 因环境不同而跳过；日志如实记录实际下发环境

#### Scenario: 历史稿件带旧环境标识仍照常下发
- **WHEN** 一条历史自动稿件的元数据里带着旧的环境标识，而当前在线环境与之不同
- **THEN** 该标识不参与判定，稿件按部署目标一致即可下发，且其元数据不被改写

#### Scenario: 历史与人工稿件兼容
- **WHEN** 候审记录没有自动排期执行归属元数据
- **THEN** 当前 Cloud 继续按既有审批与下发规则处理，不因本变更额外阻断
