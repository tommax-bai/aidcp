# content-schedule Specification

## Purpose
TBD - created by archiving change content-schedule-auto-publish. Update Purpose after archive.
## Requirements
### Requirement: 定时自动发帖只提议、绝不自动发送

内容排期触发的发帖 SHALL 复用现有发布管线的生成、待审草稿、授权信号与发布派发器。`review` 模式到点只**生成草稿并落待审**，真发 MUST 仍只在飞书人审 `approved===true` 后由发布派发器进行（AC-PUB）。`auto_approve` 模式 SHALL 表示运营已在后台对该账号自动发帖预授权：系统生成草稿后 MUST 写入同形 `approved===true` 授权信号（含当前内容版本），再由现有发布派发器执行；同时 MUST 发送飞书通知卡说明本次由后台免审配置自动授权。内容调度器 MUST NOT 新增任何绕过发布派发器、绕过版本闸、或绕过 `approved===true` 复核的发送路径。手动 `/publish` MUST 完全不受排期时段限制、随时可发，且不因排期免审配置而跳过其既有人审要求。

#### Scenario: review 模式到点只产草稿待审
- **WHEN** 某账号命中其发帖排期时段与错峰分钟、动作模式为 `review`、且各闸通过
- **THEN** 系统调用现有发帖触发机器生成草稿并落待审、发出飞书审批卡，绝不直接发送

#### Scenario: review 模式人审通过才发
- **WHEN** 排期产生的草稿在飞书被审批通过
- **THEN** 由现有发布派发器在 `approved===true` 后发送；未通过 / 超时 / 拒绝一律不发

#### Scenario: auto_approve 模式后台预授权后经 dispatcher 发送
- **WHEN** 某账号命中其发帖排期且动作模式为 `auto_approve`
- **THEN** 系统 SHALL 落待审草稿、写入当前版本的 `approved===true` 授权信号、触发现有发布派发器，并发送飞书免审通知卡

#### Scenario: 手动不受时段与免审配置影响
- **WHEN** 运营在排期时段外手动 `/publish`
- **THEN** 照常触发，绝不因内容时段格为「休眠」而被拦，也不因该账号排期发帖为 `auto_approve` 而跳过手动发布审批

### Requirement: 内容排期数据契约与 fail-closed 默认（未配即不自动）

系统 SHALL 用物理分离的全局活跃掩码、全局内容掩码与账号排期侧表承载排期。账号排期 SHALL 包含既有总开关、动作模式和日上限，并可分别保存 nullable `activeWeekMask` 与 `contentActiveMask` 覆盖；每个 NULL 字段独立表示继承对应全局值。合法账号覆盖优先，未配置层回落全局。全局内容掩码缺失/非法 SHALL 视作全 0（不自动）；账号内容覆盖非 NULL 但非法时亦 MUST fail-closed，不得回落全天允许。

账号没有排期行、总开关关闭、动作模式为 `off` 或日上限为 0 时，对应动作仍完全不自动；仅添加账号周历覆盖 MUST NOT 隐式打开总开关、动作模式或日上限。

#### Scenario: 两层分别继承

- **WHEN** 账号只配置活跃覆盖而内容覆盖为 NULL
- **THEN** 账号活跃时段使用账号覆盖，内容时段继承当前全局内容掩码

#### Scenario: 内容覆盖独立优先

- **WHEN** 账号内容覆盖为合法掩码而活跃覆盖为 NULL
- **THEN** 账号内容时段使用账号覆盖，活跃时段继承当前全局活跃掩码

#### Scenario: 仅添加排期不自动打开动作

- **WHEN** 未开启自动化的账号保存活跃与内容周历覆盖
- **THEN** 账号总开关、动作模式和日上限保持原值，内容调度器仍不触发对应动作

#### Scenario: 内容掩码缺失或非法时不自动

- **WHEN** 账号生效内容掩码缺失或非法
- **THEN** 判定为当前非活跃内容格、不触发，绝不回落全天允许

### Requirement: 自动内容时窗 ⊆ 活跃时段（休眠格绝不自动）

自动内容 SHALL 仅发生在同一账号的**生效活跃掩码与生效内容掩码都命中**的小时。控制台账号编辑器 SHALL 在结构上清除休眠格里的内容标记；Cloud 内容调度器 MUST 另以 `accountId` 读取账号生效活跃值并强制判定，不依赖 UI 正确性。两个账号在同一时刻可因覆盖不同得到不同结果。手动触发继续不受周历限制。

#### Scenario: 账号休眠格强制拦下自动内容

- **WHEN** 账号生效内容掩码当前为可自动、但该账号生效活跃掩码当前为休眠
- **THEN** 内容调度器 MUST NOT 为该账号触发发帖、评论、联系评论或其它排期动作

#### Scenario: 两账号内容闸独立

- **WHEN** 同一时刻账号 A 的生效活跃掩码为休眠、账号 B 为活跃，且两者内容掩码均命中
- **THEN** A 被拦，B 可继续经过其它调度闸，MUST NOT 以全局活跃布尔值统一放行或阻断

#### Scenario: 编辑器结构性保证

- **WHEN** 运营在账号三态周历把某活跃格切换为休眠
- **THEN** 该格内容标记随之清除，保存的自定义内容位为自定义活跃位子集

### Requirement: 时段配置前端一处编辑（三态网格），底层字段保持分离

浏览活跃时段与内容自动时段 SHALL 继续在管理后台“排期”页以同一三态周历组件编辑，底层字段保持物理分离和各自兜底极性。页面 SHALL 保留全局周历，并在账号表为每个真实账号提供“添加排期/编辑”入口、来源展示与“恢复全局”操作。账号无任一覆盖时显示“跟随全局”；存在覆盖时显示“账号自定义”。其它页面不得新增第二个排期写入口。

#### Scenario: 添加账号排期以当前全局为起点

- **WHEN** 运营对跟随全局的账号点击“添加排期”
- **THEN** 编辑器以当前全局生效活跃与内容时段初始化，保存后一次写入两个账号覆盖并回读真态

#### Scenario: 编辑账号排期

- **WHEN** 运营打开已有账号自定义排期
- **THEN** 编辑器回显该账号当前覆盖/继承组合，保存后仅该账号的生效排期改变

#### Scenario: 恢复全局

- **WHEN** 运营对账号执行“恢复全局”并确认
- **THEN** 两个账号掩码覆盖均清为 NULL，页面回读显示“跟随全局”，账号立即使用当前全局配置

#### Scenario: 全局编辑保持原入口

- **WHEN** 运营编辑顶部全局三态周历
- **THEN** 全局活跃与内容字段仍分别写入各自拥有端点，所有未覆盖账号随全局真态更新

### Requirement: 内容调度器按账号扇出并分钟错峰

系统 SHALL 提供一个云端单进程、每分钟心跳的内容调度器（命令式触发器，MUST NOT 进角色注册表、MUST NOT 走事件总线）。自动发帖每次心跳 SHALL 遍历完成欢迎握手且能从 `edgeId=ads-<envKey>` 得到完整环境身份的在线账号；部署目标 SHALL 由 Cloud 严格解析本地 `AIDCP_DEPLOY_ENV=dev|ol` 注入，MUST NOT 接受 Edge 自报 target。对每个账号按闸序判定：排期启用 ∧ 有效且当前活跃的内容格 ∧ 当前分钟命中该账号错峰偏移 ∧ 未达日上限 ∧ 风控状态为 normal。错峰偏移 SHALL 为 `hash(accountId + 本地日期 + 动作) % 60` 得到的分钟（纯函数、无状态、可复现；逐日变化、账号间错开）。心跳 MUST 有重入护栏（上轮未完即跳过本轮），且对 `(账号, 动作, 小时格)` 幂等；其中自动发帖 MUST 在数据库中原子占位，跨进程与进程重启后同格也 MUST NOT 重复触发，评论类动作继续按既有进程内幂等执行。

#### Scenario: 命中偏移分钟才尝试
- **WHEN** 当前小时是某账号活跃内容格，但当前分钟不等于该账号的错峰偏移
- **THEN** 本分钟不触发；仅在分钟等于偏移时尝试

#### Scenario: 账号间错峰
- **WHEN** 多个账号在同一活跃小时格
- **THEN** 各账号按其 `hash(账号+日期+动作)%60` 落在不同分钟触发，绝不在同一刻齐发

#### Scenario: 同小时格不重复
- **WHEN** 同一账号在同一发帖小时格已被任一 Cloud 进程原子占位，或占位进程随后重启
- **THEN** 任何 Cloud 进程在该小时格内 MUST NOT 再次启动该账号的自动发帖

#### Scenario: 在线身份不完整时关闭自动发帖
- **WHEN** 在线连接未完成欢迎握手、缺少账号，或其 `edgeId` 不能严格解析出非空 `envKey`
- **THEN** 该连接 MUST NOT 进入自动发帖扫描，且人工发布与其它连接能力保持原行为

#### Scenario: Cloud target 无效时不启动调度
- **WHEN** Cloud 的 `AIDCP_DEPLOY_ENV` 缺失或不是 `dev|ol`
- **THEN** 自动内容调度器 MUST NOT 启动，并留下可诊断的 fail-closed 日志

### Requirement: 排期发帖全局串行且不阻塞心跳

发帖成本记账已改为逐调用显式携带账号（见 `publish-account-attribution`），全局串行的原因由此消灭。内容调度器下发发帖前 SHALL 经**账号粒度**的自主单飞闸——同账号同刻至多一轮自主发帖生成，跨账号可并行、受全局并发生成帽约束（见 `publish-generation-concurrency`）；参照洗稿轮在途 MUST NOT 使该账号的排期发帖让槽（洗稿是白天交互高峰、放任让位会让活跃账号被持续饿槽）。心跳触发发帖 MUST 为「发起即返回」（fire-and-forget + 忙闲标志），MUST NOT `await` 整条生成管线，以免单分钟心跳被阻塞数分钟、其它账号被饿死、错峰被击穿。分钟错峰机制治理平台侧协同指纹，与云端并发正交，MUST NOT 随串行闸退役而删除。

#### Scenario: 同账号自主单飞、跨账号并行
- **WHEN** 账号 A 的自主发帖生成中，账号 B 同分钟也命中发帖且全局帽未满
- **THEN** B 正常触发并与 A 并行生成；若 A 再次命中，A 本槽顺延（同账号自主单飞）

#### Scenario: 洗稿在途不让排期槽
- **WHEN** 某账号有洗稿轮生成中、其排期时段格与错峰分钟命中
- **THEN** 该账号排期发帖照常触发（受全局帽与自主单飞约束），MUST NOT 因洗稿在途而让掉本小时槽

#### Scenario: 全局帽满让槽
- **WHEN** 全局并发生成数已达帽值时某账号排期命中
- **THEN** 该账号本槽顺延（本小时不发、下一槽再评估），MUST NOT 排队等待

#### Scenario: 心跳不等生成
- **WHEN** 一次发帖触发进入耗时数分钟的生成管线
- **THEN** 心跳立即返回并继续评估其它账号，绝不因等待该生成而跳过后续账号

### Requirement: 排期发帖与旧单账号自动扳机互斥

当内容调度器开启时，系统 SHALL 无条件、在启动期确定性地关闭旧的单账号自动发帖定时器；二者 MUST NOT 并存。理由：现有全局单跑闸只挡并发双跑、挡不住旧定时器与新错峰分钟**错时**叠加造出同日两次独立草稿导致超发。MUST NOT 保留「旧定时器作 fallback」的并存路径。

#### Scenario: 开新即关旧
- **WHEN** 内容调度器随进程启动被开启
- **THEN** 旧单账号自动发帖定时器被确定性关闭，二者不同时运行

#### Scenario: 无错时双触发
- **WHEN** 同一账号已由内容调度器触发过当日发帖
- **THEN** 不存在另一条旧扳机在别的分钟再触发一次

### Requirement: 发帖日上限对在途草稿原子

发帖日上限判定 SHALL 计入「今日已发历史」与「今日在途**自主来源**未审草稿的真实条数」之和（`posted + pendingAutonomousCount >= cap`），MUST NOT 只读已发历史、MUST NOT 把多份在途只按布尔计 1。理由：只读已发有 TOCTOU——自动路径造出的多张草稿都获批即超发；多候选世界按真实条数计才原子。**参照洗稿来源**的在途草稿（人工发起的候选、按来源血缘区分）MUST NOT 计入排期日上限——候选不是消耗，其堆积由每账号在途帽独立约束（见 `publish-generation-concurrency`），洗稿候选 MUST NOT 把日上限内的排期发帖堵死。已发计数 SHALL 来自持久发送历史（按账号、服务器本地日历日），MUST NOT 依赖重启即清零的内存计数器。

#### Scenario: 自主在途草稿按条数计入上限
- **WHEN** 某账号今日已有一张自主来源在途待审草稿、日上限为 1
- **THEN** 内容调度器 MUST NOT 再为其触发第二张自主草稿，即使第一张尚未发送

#### Scenario: 洗稿候选不堵排期
- **WHEN** 某账号有三份洗稿来源的待审草稿（帽内）、日上限为 1 且今日自主已发 0
- **THEN** 排期发帖照常可触发当日的一张自主草稿，MUST NOT 被洗稿候选占位堵死

#### Scenario: 重启不超发
- **WHEN** 云端重启后内存幂等态丢失
- **THEN** 日上限仍由持久已发计数 + 持久在途台账保证不越限

### Requirement: 每次触发都回诚实结果卡，绝不静默假成功

内容调度器每次触发发帖 SHALL 回一张飞书结果卡，如实呈现结果：已发起草稿待审 / 本槽无新素材本次不发 / 发帖全局排队本槽顺延 / 触发失败（带原因）。系统 MUST NOT 在无素材时硬凑内容假装发帖、MUST NOT 静默吞掉失败或空槽。

#### Scenario: 空槽如实回报
- **WHEN** 触发发帖但内容侦察判定无新素材
- **THEN** 回一张卡明示「本槽无新素材、本次不发」，绝不硬造内容、绝不静默

#### Scenario: 失败可见
- **WHEN** 一次触发因某原因失败
- **THEN** 回一张卡带失败原因，绝不静默假成功

### Requirement: 定时自动评论复用命令式评论管线、只提议不越审

排期触发的评论 SHALL 复用现有命令式评论任务管线（persona 闸、边端在线检查、有界任务、异步结果卡），但边缘占用 MUST 拆为两个任务租约阶段：prepare 租约执行搜索/读取并在获得目标快照后释放；云端撰写与审批/预授权期间不持有边缘租约；仅当评论获得授权后申请 commit 租约、按稳定 `noteId` 重开复检并提交，随后释放。账号未开启全局评论免审时，`review` 模式真发 MUST 仍只在人审 approved 后进行，未接线 / 超时 / 拒绝一律不发；`auto_approve` 模式 SHALL 表示运营已后台预授权该账号自动评论。账号显式 `auto_approve_all` 时 MUST 覆盖排期来源模式为免审。有效免审模式 MUST 不发审批按钮卡、不等待人工点击，撰写完成后直接进入既有 commit 流程；飞书免审通知仅作旁路记录，缺失或失败不阻止提交，也不回退按钮审批。评论任务可能诚实产出 0 条（无强相关目标），系统 MUST NOT 为凑数硬评、MUST NOT 把「未找到目标」报成成功。手动 `/comment` MUST 完全不受排期时段限制，也不受**排期自身**免审配置影响，但 SHALL 服从账号全局免审覆盖。

#### Scenario: review 模式到点自动发起评论任务
- **WHEN** `source_rules` 账号命中其评论排期时段与错峰分钟、动作模式为 `review`、且各闸通过
- **THEN** 系统调用现有命令式评论入口发起一次任务；prepare 读取目标后释放边缘，人审通过才重新获得 commit 租约并真发

#### Scenario: auto_approve 模式评论直接免审
- **WHEN** 某账号命中评论排期且有效模式为 `auto_approve`，评论已完成撰写并通过本地内容闸
- **THEN** 系统 SHALL 继续既有 commit 租约与提交验证并旁路发送飞书免审通知卡，MUST NOT 等待通知或发送带同意/不发按钮的审批卡

#### Scenario: 账号全局免审覆盖排期 review
- **WHEN** 账号显式 `auto_approve_all`，排期来源模式仍为 `review`
- **THEN** 本次有效模式为 `auto_approve`，直接继续提交且不等待按钮审批；通知失败不改变授权

#### Scenario: 人审等待不独占边缘
- **WHEN** 排期评论已完成目标读取、正在等待人审或处理后台预授权
- **THEN** edge 不持有该评论任务租约，可继续浏览或处理更高优先级任务；授权后必须重新抢占并复检目标

#### Scenario: 诚实空槽
- **WHEN** 评论任务搜索甄选后无强相关目标
- **THEN** 本次不评，结果卡如实报「未找到强相关目标」，绝不硬凑、绝不染绿

#### Scenario: 手动只服从账号全局覆盖而非排期模式
- **WHEN** 运营在排期时段外对 `source_rules` 账号手动 `/comment`，而排期评论为 `auto_approve`
- **THEN** 照常触发且仍需人审；若账号本身为 `auto_approve_all`，则直接免审

### Requirement: 评论动作三闸——单飞、原子日上限、自动路径配额

排期评论 SHALL 过三道动作专属闸：① 单飞——该账号评论任务在跑（isRunning）时 MUST NOT 重复触发；② 原子日上限——判定 = 今日已发评论数（互动记录按账号、服务器本地日历日）+（在跑 ? 1 : 0），达上限 MUST NOT 触发；已发计数 SHALL 来自持久互动记录，MUST NOT 依赖重启即清零的内存计数器；③ 配额——自动路径 MUST 过 `canDo('comment')` 风控配额（手动 `/comment` 跳配额是因为人逐条掌控；自动无人在场），被拒 SHALL 回黄色卡如实说明、本槽不触发。

#### Scenario: 在跑不重触发
- **WHEN** 该账号一个评论任务尚未结束、下一个排期分钟到来
- **THEN** 本槽跳过，不叠加第二个任务

#### Scenario: 日上限计入在跑
- **WHEN** 日上限为 1 且该账号今日已发 0 条但有任务在跑
- **THEN** 不再触发（已发 0 + 在跑 1 ≥ 1）

#### Scenario: 配额拒绝如实回报
- **WHEN** `canDo('comment')` 返回 false
- **THEN** 不触发评论任务，回一张黄色卡说明「配额拒绝、本槽未触发」，绝不静默

### Requirement: 调度器动作循环与每动作幂等

内容调度器 SHALL 按动作循环判定（发帖、加群、评论、联系评论各自的开关 / 日上限 / 错峰分钟及专属准入），幂等键 SHALL 为「账号 × 动作 × 小时格」——一个动作的触发 MUST NOT 吞掉同账号同小时另一动作的排期槽。同一账号同一 tick SHALL 至多触发一个动作（防同分钟双动作抢边端）；错峰分钟按「账号 + 本地日期 + 动作」哈希，动作间自然岔开。加群 MUST 继续复用该心跳与账号单飞，MUST NOT 新增第二个 cron 或绕开评论/加群的物理边端互斥。

#### Scenario: 动作幂等互不干扰
- **WHEN** 某账号发帖已在本小时格触发过、加群或评论的错峰分钟随后到来且各闸通过
- **THEN** 对应动作照常触发（幂等键按动作独立），发帖不再重复

#### Scenario: 同 tick 至多一动作
- **WHEN** 哈希偶发使同账号两动作命中同一分钟
- **THEN** 本 tick 只触发其一，另一动作顺延（不并发抢边端）

### Requirement: 定时自动联系评论经同一评论机器、带独占刹车

排期触发的联系评论 SHALL 复用命令式评论任务机器并带 `injectContact`（缺联系方式 fail-closed、注入在授权前 verbatim、结果卡自补全部沿用）；账号未开启全局评论免审时，`review` 模式真发 MUST 仍只在人审 approved 后进行，`auto_approve` 模式 SHALL 使用后台预授权并旁路发送飞书免审通知。账号显式 `auto_approve_all` 时 MUST 覆盖联系评论来源模式为免审。免审通知缺失或失败 MUST NOT 阻止提交或回退按钮审批。该动作 SHALL 过四道闸：① 单飞与评论动作共用（同一评论机器按账号 isRunning，互斥天然成立）；② **每日自动尝试上限**——判定与记录基于持久 attempts 记录（触发回执 ok 即记一条，按账号、服务器本地日历日），被人审拒 / 无强相关目标的尝试同样占额度（保守方向），MUST NOT 依赖内存计数器；③ 自动路径 MUST 过 `canDo('comment')` 配额（手动 `/comment --contact` 仍跳配额）；④ 联系评论日上限硬上限 SHALL 为 10（越界整块拒；与发帖 / 评论的 50 刻意分开）。触发被拒（配额 / 缺联系方式 / 离线 / 在跑）SHALL 回黄色卡如实说明，MUST NOT 静默。手动 `/comment --contact` MUST 完全不受排期时段限制，也不受**排期自身**免审配置影响，但 SHALL 服从账号全局免审覆盖。

#### Scenario: review 模式到点自动发起联系评论任务
- **WHEN** `source_rules` 账号命中其联系评论排期时段与错峰分钟、动作模式为 `review`、且各闸通过
- **THEN** 系统以 injectContact 调用命令式评论入口发起一次任务；联系方式在人审卡前 verbatim 接入，人审通过才发

#### Scenario: auto_approve 模式联系评论只通知不等审批
- **WHEN** 某账号命中联系评论排期且有效模式为 `auto_approve`
- **THEN** 系统 SHALL 在撰写出含联系方式的拟发评论后继续既有提交链路并旁路发送飞书免审通知，MUST NOT 因通知失败阻止提交或降级为无联系方式评论

#### Scenario: 全局免审不绕自动联系评论刹车
- **WHEN** `auto_approve_all` 账号命中联系评论排期但已达尝试上限或 `canDo('comment')` 拒绝
- **THEN** 本槽仍被拒并如实回卡，MUST NOT 因免审绕过额度或配额

#### Scenario: 尝试即占额度（保守方向）
- **WHEN** 联系评论任务开跑后因无强相关目标或人审拒绝而未发出
- **THEN** 该次尝试仍计入当日上限；当日尝试数达上限后不再触发

#### Scenario: 重启不超发
- **WHEN** 云端重启后内存态丢失
- **THEN** 当日尝试计数来自持久 attempts 记录，不清零、不越限

#### Scenario: 联系评论硬上限
- **WHEN** 提交联系评论日上限为 11
- **THEN** 整块拒绝（越 10 上限），绝不部分落库

### Requirement: 排期动作支持关、审批、免审三档

内容排期的自动发帖、自动评论、自动联系评论 SHALL 分别支持三档模式：`off`（不自动触发）、`review`（自动触发但每条仍需飞书审批）、`auto_approve`（自动触发且由后台配置视为预授权，飞书只发通知）。账号级 `autoEnabled=false` 仍 SHALL 作为总闸使所有动作等价不触发。为兼容既有数据，系统 SHALL 能从旧 boolean 字段推导模式：旧开 = `review`，旧关 = `off`；新写入模式时 MUST 同步旧 boolean 可读状态。

#### Scenario: 旧数据按审批模式兼容
- **WHEN** 某账号旧数据 `post_enabled=true` 且没有新 `post_mode`
- **THEN** 系统 SHALL 将自动发帖展示和执行为 `review` 模式，继续走飞书审批

#### Scenario: 免审不等于总闸开启
- **WHEN** 某账号 `autoEnabled=false` 且某动作模式为 `auto_approve`
- **THEN** 内容调度器 MUST NOT 触发该动作

#### Scenario: 新模式同步旧布尔视图
- **WHEN** 运营把自动评论设置为 `auto_approve`
- **THEN** 服务端 SHALL 持久化 `comment_mode='auto_approve'`，并使旧 `comment_enabled` 视图为 true

### Requirement: Facebook 排期发帖复用 review 待审路径并检查素材池

内容排期触发 Facebook 发帖 SHALL 复用既有发布管线的生成、待审草稿、授权信号与发布派发器。MVP 中 Facebook 排期发帖 MUST 使用 `review` 路径：到点只生成待审草稿并发审批卡，真发仍只在人审批准后执行。触发前 MUST 检查该账号具备 Facebook publish 能力、风险状态允许、排期闸通过、且素材池有 `available` 图片组；素材不足时本槽 SHALL 不生成草稿并发送诚实结果卡。`auto_approve` 对 Facebook publish 在本 change 中 MUST 保持禁用或 fail-closed，除非后续 change 明确开启。

#### Scenario: 排期命中且素材充足生成待审草稿
- **WHEN** Facebook 账号命中排期发帖时段、风险状态 normal、publish 能力可用、且素材池有 `available` 图片组
- **THEN** 内容调度器 SHALL 触发 Facebook 发布草稿生成，锁定素材池图片组，落待审草稿并发送审批卡，MUST NOT 直接提交

#### Scenario: 素材不足返回诚实结果卡
- **WHEN** Facebook 账号排期发帖命中但素材池没有 `available` 图片组
- **THEN** 内容调度器 SHALL 不生成草稿、不调用 edge，并回一张结果卡说明图片素材不足

#### Scenario: Facebook auto_approve 保持关闭
- **WHEN** 运营或配置尝试让 Facebook 排期发帖走 `auto_approve`
- **THEN** 系统 SHALL fail-closed 或降级为需要 review 的待审路径并明确提示，MUST NOT 在本 change 中免审自动提交 Facebook 帖子

### Requirement: 排期评论在 edge 接管失败前如实报告未开始

排期评论在 prepare 或 commit 阶段**未能取得 edge 租约**时，SHALL 产出 `not_started` 的非成功结果。该判定 MUST **与具体租约错误码无关**：凡「租约未取得、任务体未执行、零条评论业务命令下发」的失败，一律归为 `not_started`——包括但不限于 acquire 超时、edge 离线、连接断开、浏览器控制面不可用（`edge_unhealthy`）、浏览器停泊唤不醒（`browser_wake_failed`）。实现 MUST NOT 依赖一张逐码枚举的白名单，因为新增租约错误码时类型检查不会提示遗漏（向联合类型增补成员是变宽而非变窄）；判定 SHALL 以「任务体是否已经执行过」为准，仅把**释放阶段**的失败（`release_timeout`，发生在评论可能已真实发出之后）排除在 `not_started` 之外。

对应飞书结果卡 MUST 明确本次未搜索、未选中笔记、未发布评论，并给出可审计的接管失败原因；MUST NOT 使用“已选中笔记”“发布未确认”等仅适用于已进入候选或提交阶段的措辞。该结果 MUST NOT 被记录为已评论、已发布或候选已选中。

接管失败原因 SHALL 按**处置语义**分档呈现，MUST NOT 把语义相反的失败混为一句话：浏览器控制面不可用（边端在线、连接正常，但浏览器驱不动）MUST 与边端离线／失联可辨识区分；浏览器停泊唤不醒 MUST 标明为可恢复。

`not_started` 结果 MUST 触发排期小时格回流（归还本小时名额、打开小时内重试窗），MUST NOT 因为被误分类为阶段性失败而使该账号本小时的排期名额零动作白烧。

#### Scenario: prepare acquire 超时

- **WHEN** 自动排期评论在搜索候选前等待 edge acquire 超时
- **THEN** 结果卡显示浏览器未能接管且本次未搜索、未选中、未发布，零条评论业务命令被下发

#### Scenario: 浏览器控制面不可用

- **WHEN** 自动排期评论申请租约时 edge 回 `cdp_unhealthy`（云端得到 `edge_unhealthy`）
- **THEN** 结果为 `not_started`，结果卡明确本次未搜索、未选中、未发布，且原因标明为「边端在线但浏览器控制面不可用」而非「边端离线」
- **AND** 排期小时格被归还，MUST NOT 白烧该账号本小时的评论名额

#### Scenario: 新增租约错误码不需要改判定

- **WHEN** 未来新增一个发生在租约取得阶段的错误码，且未在任何白名单里登记
- **THEN** 该失败仍被归为 `not_started`（默认偏向诚实），MUST NOT 因为「不认识这个码」而被写成发布阶段失败

#### Scenario: 释放阶段失败不得改写为未开始

- **WHEN** 评论任务体已执行完毕，仅在释放租约时超时（`release_timeout`）
- **THEN** 该失败 MUST NOT 被归为 `not_started`（评论可能已真实发出），MUST NOT 因此归还小时格并触发重复评论

#### Scenario: 已进入流程后的失败保持阶段语义

- **WHEN** 排期评论已经取得租约并在候选选择、撰写或提交阶段失败
- **THEN** 系统保留对应阶段的真实失败说明，不把该失败改写成 `not_started`

### Requirement: 内容排期必须尊重委托任务 ownership 并避免双重执行

`ContentScheduler` 在触发发帖、评论或联系评论前 SHALL 查询同账号动作族的 DelegatedTask ownership。存在 queued/planning/waiting_approval/executing 的冲突委托时，本 tick MUST 诚实跳过且不得启动第二个 scheduler；委托 worker 同样必须尊重已在途排期/scheduler ownership。busy 跳过不得被计为平台尝试或成功。

#### Scenario: 委托发布等待人审时排期不再生成第二稿
- **WHEN** 同账号已有一个用户委托发布处于 `waiting_approval`
- **THEN** 该账号排期发帖 tick 跳过并记录 ownership 原因
- **AND** MUST NOT 生成另一份自动候选来争用同一发布槽

### Requirement: 账号自动化管理视图按平台筛选并只呈现真实支持动作

控制台 SHALL 保留统一的账号自动化入口，并提供默认“全部平台”的平台筛选。筛选与表格行 MUST 使用 Cloud 返回的同一规范化平台值；“全部平台” SHALL 只展示平台、账号、账号分组、总开关、时段来源、已启用动作摘要与最近更新/问题等跨平台公共信息，MUST NOT 展示所有平台动作列的并集。选择单个平台后，控制台 SHALL 仅为该平台目录行中服务端声明的 `availableActions` 渲染可编辑动作、模式和日上限，MUST NOT 由前端自行推断平台能力。

#### Scenario: 默认全部平台展示公共摘要
- **WHEN** 运营进入账号自动化页且未选择特定平台
- **THEN** 页面展示所有平台账号的公共摘要，并且不把发帖、评论、联系评论等平台专属列拼成一个超宽并集

#### Scenario: 选择 Facebook 只展示 Facebook 行与受支持动作
- **WHEN** 运营把平台筛选切换为 Facebook
- **THEN** 表格只包含规范化平台为 `facebook` 的账号，且每行只展示 Cloud 为 Facebook 声明支持的动作、模式和上限

#### Scenario: 无自动化动作的平台仍诚实可见
- **WHEN** 某平台账号存在但其 `availableActions` 为空
- **THEN** 该账号在对应平台视图和全部平台摘要中仍可见，并明确显示暂无可配置自动化动作而不是伪造开关

### Requirement: 平台筛选作用于同一账号集合

页面的行计数、空态、动作摘要及后续任何批量操作 SHALL 基于同一平台过滤结果，MUST NOT 出现表格只视觉过滤但批量写仍作用于其它平台账号的情况。

#### Scenario: 平台筛选后的空态和计数一致
- **WHEN** 当前目录没有规范化平台为 `wechat_channels` 的账号且运营选择视频号
- **THEN** 表格、计数和空态均基于空集合，任何可用批量操作也不得包含其它平台账号

### Requirement: 本能力覆盖发帖、评论、联系评论与 Facebook 自动加群，声明已知缺口

本能力 SHALL 覆盖定时自动**发帖**、定时自动**评论**、定时自动**联系评论**以及 Facebook 定时自动**加群**。联系评论继续带既有独占刹车、尝试型持久日上限、联系方式闸、单飞和自动路径配额。Facebook 自动加群 SHALL 只从账号当前分组映射目标池认领，带默认关闭的每账号开关、动作时段、运营日上限、全局 kill switch、RiskController 日额度、会话额度、账号单飞、真实成员账本和 scheduled 审计来源。系统 SHALL 继续声明小时级协同指纹、评论目标首屏命中率、共用联系方式指纹残留，以及账号分组仍为字符串标签、同一群即便映射多组也只允许一个账号归属等已知限制。

#### Scenario: 联系评论带刹车纳入
- **WHEN** 运营为某账号开启自动联系评论
- **THEN** 开启须过联系方式闸（无联系方式 → 硬拒；联系方式与其它账号共用 → 放行但回带风险警告，绝不静默），运行受尝试型日上限 / 错峰 / 人审约束

#### Scenario: Facebook 自动加群带完整刹车纳入
- **WHEN** 运营为一个已分组 Facebook 账号开启自动加群
- **THEN** 只有每账号配置、有效交集时窗、运营/风控日额度、会话额度、全局 kill switch、分组候选和账号单飞全部通过时才可触发一次既有加群链

#### Scenario: 已知缺口有声明
- **WHEN** 审阅本变更的风控与数据模型残留
- **THEN** 设计文档明确列出小时级协同指纹、首屏甄选、联系方式指纹、字符串分组标签和一群全局单账号归属限制及其压制手段

### Requirement: Facebook 自动加群按账号独立配置且默认关闭

系统 SHALL 为 Facebook 账号提供独立 `join_group` 自动化配置：动作开关、受限非负整数每日上限、可选 168 位动作周历覆盖、更新人/时间以及最近一次 scheduled 执行结果。无配置行、开关关闭、日上限为 0、非 Facebook 账号或全局 kill switch 关闭任一 SHALL 完全不触发自动加群。该动作 SHALL 聚合进统一账号自动化目录，但其领域配置 MUST 与通用发帖/评论字段分开持久化。最近结果 MUST 来自带 `scheduled` 来源的真实审计，不能用人工结果或 membership 更新时间猜测。

自动加群日上限的硬上限 SHALL 为 50（越界整块拒）。三个动作的硬上限 SHALL 各自独立、MUST NOT 相互推导：发帖与评论为 50、**联系评论为 10**、自动加群为 50。联系评论那个 10 是刻意与其余动作分开的既有约定，本要求 MUST NOT 被读作把它一并抬高。

硬上限 SHALL 只约束**运营可配置的天花板**，MUST NOT 改变生效值的计算规则：既有的「账号配置 MUST NOT 提高 RiskController 日额度或会话额度」保持不变，实际每日准入仍取账号配置与风控日额度的较小者，并逐次通过 `canDo('join_group')` 与剩余会话预算。因此抬高硬上限本身 SHALL NOT 使任何账号的实际加群量增加；增量只能来自运营对风控配额与会话预算的显式调整。

硬上限的事实源 SHALL 是契约层单一常量，写前校验、后台输入框上限下发与配置表约束三处 MUST 全部由它派生或与它逐字一致；任一处漂移 SHALL 被视为缺陷，MUST NOT 依赖「写入端更严即安全」来掩盖。

**「默认关闭」的适用范围**：本要求标题所称的默认关闭，SHALL 理解为「系统不会凭空为一个没有配置行的账号触发自动加群」。它 SHALL NOT 被读作「任何账号在任何情况下都必须以关闭状态起步」——真正首次登记的 Facebook 账号会被种入开启状态的配置行（见「新登记 Facebook 账号种入自动化默认配置」）。对**仍然没有配置行**的账号，本要求第一段的「无配置行即完全不触发」逐字保留、不受种入影响。

#### Scenario: 未配置账号不自动加群
- **WHEN** Facebook 账号没有自动加群配置行，即使全局 kill switch、风险额度和群目标都可用
- **THEN** 内容调度器不认领目标、不导航、不点击，也不记录一次伪执行

#### Scenario: 最近结果只取自动来源
- **WHEN** 账号最新审计是人工指定 URL 加群，而更早有一条 scheduled 自动结果
- **THEN** 账号自动化页显示更早的 scheduled 结果，不把人工结果冒充成自动执行结果

#### Scenario: 日上限可配到 50
- **WHEN** 运营为某 Facebook 账号把自动加群日上限设为 50
- **THEN** 写前校验放行、配置表约束放行、后台输入框允许输入该值，配置成功落库

#### Scenario: 超过 50 整块拒
- **WHEN** 运营把自动加群日上限设为 51
- **THEN** 写入被整块拒绝并回可诊断原因，MUST NOT 静默截断为 50 落库

#### Scenario: 抬高硬上限不放大实际加群量
- **WHEN** 某账号自动加群日上限配为 50，而该账号当前风控档位的 `join_group` 日额度为 3
- **THEN** 当日至多加入 3 个群，超出后不认领、不点击并记录可诊断拒因，MUST NOT 因账号配置为 50 而突破风控额度

#### Scenario: 联系评论硬上限不受本次抬升影响
- **WHEN** 运营把联系评论日上限设为 11
- **THEN** 写入仍被整块拒绝（其硬上限保持 10），MUST NOT 因自动加群硬上限抬到 50 而放宽

#### Scenario: 存量无行账号仍不自动加群
- **WHEN** 一个已存在但从未配过自动加群的 Facebook 账号上线
- **THEN** 它仍然没有配置行，因而不触发任何自动加群——种入只作用于真正新登记的账号

### Requirement: Facebook 自动加群时窗为公共时窗与动作时窗交集

自动加群 SHALL 只在账号有效活跃时段、账号有效内容自动时段和可选加群动作时段的交集内触发。动作时段为空 SHALL 表示跟随公共内容时段；非空 MUST 为合法 168 位掩码并只能进一步收窄。任一必需公共内容掩码缺失或非法 SHALL 沿用内容排期 fail-closed；手动 `/comment --join[=<url>]` 不受自动时段和每账号自动开关限制，但仍受其既有人工/物理闸。

#### Scenario: 动作时段收窄公共时段
- **WHEN** 公共内容时段允许周一 09:00，自动加群动作时段在该格为 0
- **THEN** 周一 09:00 不触发自动加群，即使其它闸都通过

#### Scenario: 动作时段跟随公共时段
- **WHEN** 自动加群动作时段为空且公共活跃/内容时段当前格均允许
- **THEN** 当前格可继续进入加群的额度、分组候选和错峰判定

### Requirement: 自动加群运营上限只能收紧风控与会话额度

自动加群每日准入 SHALL 要求今日已加入数小于 `min(账号配置 dailyCap, RiskController 当前日 join_group 额度)`；每次执行另 MUST 通过既有 `canDo('join_group')` 与剩余 session `join_groups` 预算。账号配置 MUST NOT 提高 RiskController 日额度或会话额度，达到任一上限时 SHALL 不认领、不点击并记录/呈现可诊断拒因。

#### Scenario: 运营 cap 小于风控 cap
- **WHEN** 账号自动加群 cap 为 1、风控日额度为 3，且今日已成功加入 1 个群
- **THEN** 当日不再自动认领目标

#### Scenario: 会话额度耗尽仍拦截
- **WHEN** 账号配置和风控日额度尚有余量但当前会话 `join_groups` 预算为 0
- **THEN** 本次自动加群不执行并诚实记录 session budget 拒因

### Requirement: 排期页可就地补齐缺失的账号联系方式

当内容排期目录判定账号未配置联系方式时，控制台 SHALL 将“未配联系方式”提示呈现为可操作入口；运营点击后 MUST 能在不离开排期页的情况下输入并保存该账号的联系方式。保存 MUST 复用账号联系方式的权威写入端点；非空内容 MUST 原样传递（含 emoji、换行与首尾空白），全空白输入 MUST NOT 发起写请求。

#### Scenario: 点击缺失提示直接出现编辑器
- **WHEN** 运营在排期表点击某账号的“未配联系方式”提示
- **THEN** 控制台在当前排期页展示该账号的多行联系方式编辑器及保存、取消操作，不导航到其它页面

#### Scenario: 非空联系方式按原文保存
- **WHEN** 运营输入一段 `trim()` 后非空、且包含换行或首尾空白的联系方式并点击保存
- **THEN** 控制台向该账号既有联系方式端点原样提交输入内容，不裁剪或改写正文

#### Scenario: 全空白输入不写入
- **WHEN** 运营只输入空格或换行并点击保存
- **THEN** 控制台提示需要输入联系方式、保持编辑器可继续修改，且不发起写请求

### Requirement: 联系方式门禁仅随确认真态变化

排期页发起联系方式保存时 SHALL 在首次等待网络回执前展示进行中状态，并 MUST 保持自动联系评论模式与日上限控件处于缺失联系方式的禁用状态。只有权威写入端点确认返回非空联系方式后，控制台 SHALL 将该排期行更新为已配置、解除联系方式缺失门禁并重取服务端目录真态。写入失败 MUST 保留草稿与编辑入口、保持门禁关闭，并展示可读的失败原因，不得把“已请求”显示成“已配置”。

#### Scenario: 保存等待期间不提前解锁
- **WHEN** 运营点击保存且账号联系方式端点尚未返回
- **THEN** 保存操作显示进行中，自动联系评论模式与日上限仍因缺少联系方式而禁用

#### Scenario: 服务端确认后解除门禁
- **WHEN** 账号联系方式端点成功返回非空联系方式
- **THEN** 控制台关闭编辑器、移除该行缺失提示、解除联系方式缺失门禁，并重取排期目录和账号目录

#### Scenario: 保存失败保留可重试状态
- **WHEN** 账号联系方式端点返回失败
- **THEN** 控制台保留运营已输入的草稿与打开的编辑器、继续禁用自动联系评论，并展示映射后的失败原因供直接重试

### Requirement: 自动发帖执行环境冻结并约束恢复下发

自动发帖在成功占位后 SHALL 将该次在线身份的 `envKey`、Cloud 本地 `executionTarget` 和 `hourCell` 作为不可变执行归属传入发布管线，并持久化到候审记录元数据。已升级 Cloud 的候审扫描与按记录恢复下发 SHALL 仅处理未带自动排期归属的历史/人工稿件，或 `executionTarget` 与当前 Cloud 一致的自动稿件；自动稿件实际下发的在线 Edge 还 MUST 精确匹配冻结的 `edgeId=ads-<envKey>`。target 或 envKey 不匹配 MUST 在任何 Edge 写操作前跳过，且不得改写稿件或审批状态。

#### Scenario: 自动稿件记录实际触发环境
- **WHEN** dev Cloud 通过在线环境 `envKey=A` 成功占位并生成自动候审稿件
- **THEN** 稿件元数据包含 `executionTarget=dev`、`envKey=A` 和命中的 `hourCell`，且这些值不接受 Edge 覆盖

#### Scenario: 归属元数据保存失败时关闭该轮
- **WHEN** 自动发帖无法把完整执行归属写入候审记录
- **THEN** 该稿件 MUST NOT 保持为可下发状态，并返回诚实失败结果

#### Scenario: 其它 target 不得恢复下发
- **WHEN** ol Cloud 扫描或被直接唤醒处理一条 `executionTarget=dev` 的自动稿件
- **THEN** ol Cloud 在任何 Edge 写操作前跳过该稿件，不改变其审批和稿件状态

#### Scenario: 不得改投后来连接的其它浏览器环境
- **WHEN** 自动稿件冻结 `envKey=A`，但审批恢复时该账号只在线于 `envKey=B`
- **THEN** Cloud 在任何 Edge 写操作前跳过，不把该稿改投 B，且保留原审批和稿件状态

#### Scenario: 历史与人工稿件兼容
- **WHEN** 候审记录没有自动排期执行归属元数据
- **THEN** 当前 Cloud 继续按既有审批与下发规则处理，不因本变更额外阻断

### Requirement: Unified account automation exposes Facebook rule mode without treating it as a content action

The unified account automation catalog and Facebook-filtered view SHALL expose the account's fixed rule-mode configuration, effective mode, collecting progress, the current round's position in the fixed two-round cycle and latest round summary. The write path SHALL validate Facebook support on the server and return authoritative readback. The rule configuration MUST remain a distinct domain record and MUST NOT be encoded as a `post`, `comment`, `contact_comment` or `join_group` mode, daily cap or hour-cell trigger. The all-platform summary MAY show that rule mode is enabled but MUST NOT expose an unsupported rule editor for other platforms.

The behaviour summary rendered for an account MUST describe the cadence that its stored rule definition actually encodes. It MUST NOT display a cadence taken from compiled-in constants when the stored definition differs.

#### Scenario: Facebook view exposes rule mode
- **WHEN** the operator filters account automation to Facebook
- **THEN** each Facebook row shows the fixed rule-mode toggle, behavior summary, both cadence tiers and authoritative runtime status

#### Scenario: Other platform views have no rule control
- **WHEN** the operator filters account automation to Xiaohongshu or WeChat Channels
- **THEN** no Facebook rule-mode control is rendered and a forged server write remains rejected

#### Scenario: Rule mode is not an hourly content action
- **WHEN** the account reaches the configured number of confirmed rule views outside any content-action hash minute
- **THEN** the rule round may be created from its count trigger without consuming or fabricating an hourly `content_schedule` fire key

#### Scenario: Join-contact frequency is reported as its own tier
- **WHEN** the operator inspects a Facebook account running rule mode
- **THEN** the view distinguishes the view-to-like tier from the round-to-join-contact tier and MUST NOT present a single combined counter

### Requirement: Facebook rule mode inherits only the effective weekly active window

Rule-mode session start, resume and safe stop SHALL use the same account-effective weekly active window as normal browsing. Rule mode MUST NOT require the content-active mask, a content action mode, daily content cap or per-action hash-minute offset. Slow-start precedence, account pause and all runtime gates remain additional independent conditions.

#### Scenario: Active browse cell permits counting
- **WHEN** a Facebook account has rule mode enabled, slow start is not active and its effective weekly active cell is active
- **THEN** the account may start or resume rule browsing subject to the remaining admission gates

#### Scenario: Content mask does not authorize sleeping browse
- **WHEN** a content-active cell is set but the account's effective weekly active cell is sleeping
- **THEN** rule mode does not start or count views

#### Scenario: Content action off does not disable rule mode
- **WHEN** all scheduled `post`, `comment`, `contact_comment` and `join_group` modes are off but the Facebook rule and weekly active cell are enabled
- **THEN** rule browsing may run because its count trigger is independent of content action scheduling

### Requirement: 新登记 Facebook 账号种入自动化默认配置

系统 SHALL 在一个账号**真正被首次登记进主表**时，为 Facebook 账号种入一份自动化默认配置，使其无需运营逐项手工配置即可进入既有各道闸的判定。

**触发判据** SHALL 是「本次登记真的插入了一行新账号」。系统 MUST NOT 用「配置侧表没有该账号的行」作为判据——一个早已存在、只是从未被配置过的账号同样满足后者，用它会把种入扩散到存量账号，与本要求的范围相反。

**平台过滤** SHALL 为：

- `facebook` → 种入排期侧表与自动加群配置表两行。
- 其余平台（含小红书与视频号）→ **不种入任何行**。视频号在平台动作目录中四个动作全部不支持，为其写入任何正日上限都 MUST 被写前校验整块拒绝。
- 登记调用方**未显式声明平台**时 SHALL NOT 种入。账号登记的平台参数可缺省并回落，按回落值种配置等同于给一个平台未知的账号写一份可能错误的默认值。此时系统 SHALL 留下可检索日志说明「因平台未声明而未种入」。

**种入取值** SHALL 为：账号总开关开；自动发帖开、审批模式 `review`、日上限 5；自动评论开、审批模式 `auto_approve`、日上限 20；**自动联系评论开、审批模式 `auto_approve`、日上限 5**；自动加群开、日上限 20。

**联系评论被种入的前置条件 SHALL 被记录并保持有效**：种入它曾被明确禁止，理由是带「先加群再评论」标记的复合动作**只挂在联系评论上**，种它等同于让新账号具备「加入新群后同一轮立即于该群评论」这一会招致平台警告的形态。该前置已由排期路径与复合动作的解耦解除——排期联系评论改走已加入群账本的选群口，因而受预热期与单群冷却约束。

上述因果 MUST NOT 被删成一句「联系评论默认开」：**若将来有任何改动让排期联系评论重新携带「先加群」标记，本条种入默认值 MUST 同时被撤回**。两者是一对绑定的前提与结论，不是两件独立的配置。

**联系评论的两条已知后果** SHALL 被如实记录、MUST NOT 被读作缺陷：

- 排期路径缺联系方式时 SHALL fail-closed（本次不发，绝不降级成不带联系方式的普通评论——该降级只有固定规则模式会显式声明）。因此刚登记、尚未配置联系方式的账号会按其错峰分钟收到诚实的未发提示，直到运营补上配置。
- 联系评论的自动路径 SHALL 继续通过评论配额闸，因而与普通评论**竞争同一配额池**。其日上限取值 MUST 考虑这一竞争，MUST NOT 被当作一个独立于普通评论的额度。

**审批模式** SHALL 逐动作分别取值，MUST NOT 相互推导：

- **发帖 SHALL 取 `review`**。这不是选择——Facebook 排期发帖在既有要求里就 MUST 走 `review` 路径，免审对它保持禁用或 fail-closed。
- **评论与联系评论 SHALL 取 `auto_approve`**（用户 2026-07-29 决定）。其可达性依赖既有的环境级评论审批策略只能**升权**这一性质：策略为缺省值时来源模式被逐字沿用，只有策略读取失败才 fail-closed 回 `review`。本要求 MUST NOT 被实现成「绕过该策略」——它只是提供了一个免审的来源模式。

由此产生的后果 SHALL 被如实记录、MUST NOT 被读作疏漏：新登记账号一旦绑定人设并通过其余各闸，其自动评论与联系评论会直接发到平台、无人过目。发帖不受影响，仍逐条待人审。

**失败语义**：种入失败 MUST NOT 阻断账号登记，SHALL 被捕获并留下可检索的具名日志。系统 SHALL NOT 提供自动补种路径（理由见 `accounts-master-data` 同名约束）。

**种入 SHALL NOT 改变生效值的计算规则**：每日准入仍取账号配置与风控日额度的较小者，每次执行仍需通过逐动作准入与剩余会话预算；账号总开关、两张时段周历、人设绑定、边缘在线与风控状态各闸逐一保留。种入只移除「运营尚未配置」这一道闸。

#### Scenario: 新 Facebook 账号被种入默认配置
- **WHEN** 一个此前不存在的 Facebook 账号首次登记，且登记方已声明平台
- **THEN** 该账号获得排期行（总开关开、发帖 `review`/5、评论 `auto_approve`/20、联系评论 `auto_approve`/5）与自动加群行（开、20）

#### Scenario: 种入的联系评论不带任何加群副作用
- **WHEN** 一个被种入联系评论的新账号命中其联系评论槽位
- **THEN** 系统从该账号已加入群账本中选群并评论，不加入任何新群；刚加入未满预热期的群不会被选中

#### Scenario: 缺联系方式时诚实不发
- **WHEN** 一个被种入联系评论的新账号尚未配置联系方式
- **THEN** 本次不发任何评论，回一条说明未配置联系方式的诚实提示，MUST NOT 降级成不带联系方式的普通评论

#### Scenario: 种入的免审评论仍受环境级策略读取失败的 fail-closed 保护
- **WHEN** 某个被种入免审评论的账号在发评论时，环境级评论审批策略读取失败
- **THEN** 该次评论回落为需人审，MUST NOT 因来源模式是免审就直接发出

#### Scenario: 非 Facebook 平台不被种入
- **WHEN** 一个新的小红书账号或视频号账号首次登记
- **THEN** 系统不为其种入任何排期行或自动加群行

#### Scenario: 平台未声明时不种入
- **WHEN** 一个新账号经不带平台参数的登记入口首次登记
- **THEN** 系统不种入任何配置，并留下说明「因平台未声明而未种入」的可检索日志

#### Scenario: 存量账号不被种入
- **WHEN** 一个已在主表中、且从未被配置过的 Facebook 账号再次登记或握手
- **THEN** 系统不种入任何配置，该账号维持既有的「无配置行即不自动」行为

#### Scenario: 种入不等于立即开跑
- **WHEN** 一个新 Facebook 账号刚被种入默认配置，但尚未绑定人设
- **THEN** 该账号仍被既有启动闸拦住、不产生任何平台动作

### Requirement: Facebook scheduled contact comment joins a new group before commenting

排期的 Facebook 联系评论 SHALL NOT 先加群。它 MUST NOT 携带「先加群」标记，MUST 走既有的正常定向评论路径，其评论容器 MUST 由**已加入群账本的选群口**给出。

这条约束的理由是机制性的，MUST 随要求一起保留：选群口是预热期与单群冷却唯一生效的地方。一旦评论容器被外部钉死（例如钉死成刚加入的那个群），选群口根本不会被调用，两道闸就结构性失效——**不是被绕过一次，而是永远不参与判定**。

加群 SHALL 只由独立的自动加群动作驱动（见「Standalone Facebook automatic join remains join-only」）。系统 MUST NOT 保留任何「开启联系评论即隐式加群」的路径：那条路径不查每账号加群开关、不查加群日上限、也不查加群动作时段，等于让一个动作的开关去驱动另一个动作。

选定容器之后，目标选择 SHALL 继续遵循既有的 Facebook 关键词规则：配了关键词走群内搜索，没配则取该群第一条可评帖。既有的联系方式闸、尝试型日上限、评论风控闸、审批、去重、服务端校验、账号单飞与诚实结果回执 SHALL 全部保持不变。

以下三条路径 SHALL 继续使用「先加群再评论」的复合动作，本要求 MUST NOT 被读作把它们一并拆掉：飞书手动命令、委托任务、以及固定规则模式的轮次（后者另由 `facebook-rule-mode` 规定）。

非 Facebook 的排期联系评论 SHALL 保持其既有的不加群行为。

#### Scenario: 排期联系评论从账本选群，不加新群
- **WHEN** 某 Facebook 账号命中已开启的排期联系评论槽位且各前置闸通过
- **THEN** 系统不加任何新群，改从该账号已加入群账本中选出一个满足预热期与冷却的群，在其中选帖、撰写、审批并提交联系评论

#### Scenario: 账本里没有合规群时诚实空转
- **WHEN** 该账号已加入的群全部不满足预热期或仍在冷却中
- **THEN** 本次不评论、不加群，并如实回报无可用目标，MUST NOT 为了有事可做而去加一个新群

#### Scenario: 刚加入的群不会在同一轮被评论
- **WHEN** 独立自动加群动作刚刚为某账号确认加入了一个新群
- **THEN** 该群在满足预热期之前不会被排期联系评论选中

#### Scenario: 手动与规则模式仍先加群
- **WHEN** 运营发出带加群参数的手动评论命令，或固定规则模式命中其加群轮次
- **THEN** 系统仍执行「先加群、确认加入后在该群评论」的复合动作

#### Scenario: Non-Facebook contact comments do not acquire join semantics
- **WHEN** a non-Facebook account hits its existing scheduled contact-comment slot
- **THEN** the system uses the existing contact-comment path without `joinFirst`

### Requirement: Standalone Facebook automatic join remains join-only

The independent scheduled Facebook `join_group` action SHALL continue to invoke only the Facebook group-join scheduler. Enabling or executing that action MUST NOT implicitly start post selection, composition, approval, or either ordinary or contact comment submission.

#### Scenario: Standalone automatic join has no comment side effect
- **WHEN** the independent Facebook automatic-join action confirms a new membership
- **THEN** it records the join outcome and ends without opening a group post or creating a comment

### Requirement: Facebook scheduled contact comment is labeled 加群评论（联系）

旧名「加群评论（联系）」MUST NOT 继续用于该动作：拆分后它不再加群，旧名会让运营以为开启它就会加群，进而在真正的自动加群开关关着时把「不加群」误判成系统故障。

Facebook 侧的控制台动作名与排期执行 / 结果通知 SHALL 改用与其它平台**一致**的联系评论名，MUST NOT 再为 Facebook 保留一个特例名。具体字面量由各呈现面各自的既有通用名决定（排期执行与结果通知为「联系评论」，控制台排期表沿用其既有通用列名），本要求约束的是「不再有 Facebook 特例」，而不是统一到某一个字符串。内部动作键、接口字段与持久化结构 SHALL 保持 `contact_comment` 兼容。

固定规则模式面板中描述其轮次的文案 SHALL NOT 被本要求波及——规则模式仍然先加群，那里的措辞依然准确。

清空全部 Facebook 搜索关键词 MUST 被接受，不报错、也不给禁用态警告。控制台 MUST NOT 增加「当前使用群内首帖」一类的显式当前模式标签。

#### Scenario: Facebook 自动化页不再出现加群特例名
- **WHEN** 运营把自动化页筛选到 Facebook
- **THEN** 该动作的列名与控件用与其它平台一致的联系评论名，页面上不再出现「加群评论（联系）」

#### Scenario: 规则模式文案不受影响
- **WHEN** 运营查看某账号的固定规则模式面板
- **THEN** 其中关于加群轮次的说明保持原样，仍如实描述「先加群再评论」

#### Scenario: Empty keywords show no first-post mode status
- **WHEN** an operator clears and saves all Facebook comment search keywords
- **THEN** the save is accepted and the configuration dialog shows no “当前使用群内首帖” status or empty-keyword error

