## ADDED Requirements

### Requirement: 人审授权以持久记录为唯一权威，绝不以本机文件承载

发布与评论的人审授权 SHALL 以 `aidcp-api` 单写的持久授权记录为唯一权威事实。每条记录 MUST 至少含：不透明关联令牌 `requestId`、候选版本标识 `contentVersion`、决策人 `decidedBy`、决策渠道 `decidedVia`、决策时间 `decidedAt`、目标环境 `envKey`、执行目标 `executionTarget`、以及决策本身 `approved`。授权 MUST NOT 以本机文件、本机临时目录、进程内内存或任何共享路径作为权威载体。`executionTarget` MUST 由服务端从本机部署环境注入，MUST NOT 取自请求体；缺失或非法时写入 MUST 失败并返回可区分错误，MUST NOT 落一条 target 未知的授权。

#### Scenario: 授权落库含完整决策上下文
- **WHEN** 任一审批入口（飞书卡片、管理后台、客户端内审批、委托任务、排期免审）作出一次决策
- **THEN** 系统写入一条持久授权记录，含 `requestId`、`contentVersion`、`decidedBy`、`decidedVia`、`decidedAt`、`envKey`、`executionTarget` 与 `approved`，且 `decidedBy` 为真实决策主体，MUST NOT 用常量占位

#### Scenario: 执行目标缺失即拒绝写入
- **WHEN** 本机部署环境未提供合法 `executionTarget`
- **THEN** 授权写入失败并返回可区分错误，不落任何授权行，MUST NOT 以默认值补齐

#### Scenario: 红线反例——用本机文件承载授权（禁止）
- **WHEN** 有实现把「已授权」这一位写在本机文件、共享目录或进程内内存里，并由另一个服务读取
- **THEN** MUST 视为违规、不予合入；跨服务的授权传递 MUST 经持久记录、持久命令或窄内部查询

### Requirement: 唯一写出口、first-writer-wins 由部分唯一索引承担

全部审批入口 SHALL 收敛到同一个持久授权写出口。该出口 MUST 是 first-writer-wins 的原子写：同一 `requestId` 在任一时刻至多有一条非作废的活跃授权行，由数据库的部分唯一约束（活跃行唯一）保证，MUST NOT 依赖文件系统的 `O_EXCL` 或任何进程内互斥。首个写者 SHALL 得 `{written:true}`；后到者 SHALL 得 `{alreadyDecided:<首个决定的 approved>}`。写出口 MUST NOT 返回 `{published:true}` 或任何暗示平台动作已发生的字段。

#### Scenario: 并发双路授权只有一个写成功
- **WHEN** 飞书与管理后台对同一 `requestId` 几乎同时提交决定
- **THEN** 恰好一路得 `{written:true}`，另一路得 `{alreadyDecided}` 携首个决定值，表内该 `requestId` 的活跃授权行恰好一条

#### Scenario: 写出口不冒充发布成功
- **WHEN** 授权写入成功
- **THEN** 接口返回 `{written:true}`，MUST NOT 返回 `{published:true}`；平台是否真的发布由后续下发与真实回执决定

### Requirement: 作废是状态迁移而非删除，作废后可重新授权

授权作废 SHALL 表达为记录内状态迁移（活跃 → 作废）并附作废原因，MUST NOT 删除记录行。作废后同一 `requestId` SHALL 可再次授权并成为新的活跃行，保留历史轮次用于审计。作废原因 MUST 取自枚举集合（至少含版本过期、边缘离线、抢占退避耗尽、租约未确认），枚举外的原因 MUST 被拒绝。活跃读接口 MUST 只返回活跃行，MUST NOT 把历史轮次混入判定。

#### Scenario: 作废后重新审批可再次授权
- **WHEN** 某授权因版本过期被作废，运营随后对同一记录重新授权
- **THEN** 新授权成为活跃行并得 `{written:true}`，被作废的那一轮仍可在审计中查到其决策人、决策时间与作废原因

#### Scenario: 作废不擦除审计轨迹
- **WHEN** 任一作废路径执行
- **THEN** 原授权行保留并标记为作废 + 原因，MUST NOT 被物理删除；「谁在何时批准、又因何被作废」MUST 可追溯

### Requirement: 执行侧经持久命令与窄查询获知授权，两条路均 fail-closed

`aidcp-automation` SHALL 经两条路获知授权：其一为 `aidcp-api` 在授权落库同事务写出的持久命令（至少一次投递、消费侧按 `requestId` 与轮次去重）；其二为下发前对授权状态的窄内部查询。执行侧 MUST NOT 直接读写授权表，MUST NOT 依赖与写方共享文件系统或共享进程。授权查询超时、不可达或返回异常时，执行侧 MUST 按未授权处理：不下发任何平台动作、不写任何终态、并把该记录标记为待下发且附「授权状态不可读」原因。

#### Scenario: 命令驱动通过即切
- **WHEN** 一条授权落库并写出对应持久命令
- **THEN** 执行侧消费该命令后触发一次下发；重复投递被去重，MUST NOT 造成重复发布

#### Scenario: 授权查询不可读时不下发也不烧稿
- **WHEN** 下发前的授权查询超时或返回错误
- **THEN** 执行侧不下发任何平台动作、稿件保持待审、授权保持活跃、记录附「授权状态不可读」原因，MUST NOT 置为失败终态、MUST NOT 按缺省放行

#### Scenario: 红线反例——执行侧直读授权表（禁止）
- **WHEN** 执行侧绕过内部接口直接查询或写入授权表
- **THEN** MUST 视为违规、不予合入；授权表的唯一写者与唯一直接读者是其所有者服务

### Requirement: 已批准待下发是独立可见状态，绝不静默停滞

授权记录 SHALL 携带独立于稿件业务态的下发进度：待下发、下发中、已消费、已作废。授权通过即进入待下发，并 MUST 在管理后台与客户端投影中与「待审批」**可区分地**呈现，且 MUST 携带决策时间与自决策起的等待时长。任何已知下发阻塞（边缘离线、浏览器槽位等待、账号熔断、验证码暂停、授权状态不可读）MUST 落到可读的阻塞原因并出现在同一投影上。待下发且无任何阻塞原因的记录超过阈值时，系统 MUST 主动告警——「没有原因的长时间待下发」即执行侧失联的形态。系统 MUST NOT 把已批准待下发呈现为与未审批不可区分的状态。

#### Scenario: 下发侧不可用时用户看到待下发而非待审批
- **WHEN** 运营批准通过后，执行侧整体不可用
- **THEN** 界面显示「已批准·待下发」并给出等待时长与可读阻塞原因；MUST NOT 显示为「待审批」，MUST NOT 无任何变化

#### Scenario: 无原因长时间待下发触发告警
- **WHEN** 某授权处于待下发、无任何阻塞原因、且超过配置阈值
- **THEN** 系统发出告警指明该记录与其账号，MUST NOT 只写日志

#### Scenario: 阻塞解除后原因被清除
- **WHEN** 边缘恢复在线或浏览器槽位释放
- **THEN** 该记录的阻塞原因被清空并按正常路径进入下发中，MUST NOT 遗留过期的阻塞文案

#### Scenario: 红线反例——授权成功即报业务成功（禁止）
- **WHEN** 有实现把「授权已受理」「命令已投递」或「已进入下发中」呈现为发布成功
- **THEN** MUST 视为违规、不予合入；只有平台真实回执才能表达发布已发生

### Requirement: 迁移期影子写不得成为第二事实源

在过渡窗口内，授权写出口 MAY 在持久记录写入成功后再 best-effort 写出同路径同格式的本机信号文件，供尚未迁移的本机消费者使用。该影子写 MUST 由显式开关控制、MUST 在持久写之后执行、且其失败 MUST NOT 影响授权写出口的返回值或抛出异常。读侧 MUST 一律只信持久记录；MUST NOT 存在任何「读文件回填记录」的逻辑。关闭影子写 MUST 是一次独立、可单独回滚的变更，且前置条件是已确认无任何读者。

#### Scenario: 影子写失败不影响授权
- **WHEN** 持久授权写入成功但本机文件写入失败
- **THEN** 授权仍然成立并返回 `{written:true}`，失败只记日志；MUST NOT 回滚授权、MUST NOT 向审批人报错

#### Scenario: 红线反例——从文件回填授权（禁止）
- **WHEN** 有实现在持久记录缺失时读取信号文件并据此认定已授权
- **THEN** MUST 视为违规、不予合入；这会重新造出第二事实源并让拆分后的失效重新变得不可见
