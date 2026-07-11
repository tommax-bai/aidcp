# interaction-risk-gating Specification

## Purpose
TBD - created by archiving change captcha-restrict-and-interaction-gating. Update Purpose after archive.
## Requirements
### Requirement: 云端必须在下发互动前依 RiskController 判定

云端 SHALL 在下发 `interaction.like` / `interaction.collect` / `interaction.follow` 之前调用 `RiskController.canDo(action)` 判定归属账号是否允许；判定为拒时 MUST NOT 下发该互动指令，并 MUST 以**真实的被拒结果**反映（不伪装成功）。被拒时 MUST NOT 扣减每会话 budget（budget 不得低于实际下发量而漂移）。`page.scroll` / `navigation.back` 等推进 / 返回指令 MUST NOT 受该闸拦截，以免浏览循环死锁。

#### Scenario: 允许时正常下发并计数

- **WHEN** 归属账号风控为 `normal` 且未超配额，云端决定点赞
- **THEN** 云端下发 `interaction.like` 并在成功后按账号计数

#### Scenario: 被拒时诚实跳过不假成功

- **WHEN** 归属账号为 `restricted`（或已超配额），云端的角色仍产出一次点赞意图
- **THEN** 云端不下发 `interaction.like`、不扣 budget，并如实记录"被风控拦截"（MUST NOT 上报 / 记录为成功互动）

#### Scenario: 推进指令不被风控闸拦

- **WHEN** 归属账号为 `restricted`
- **THEN** `page.scroll` / `navigation.back` 仍正常下发，浏览循环继续（仅互动被拦），不发生死锁

### Requirement: 互动发生后必须按账号持久计数

云端 SHALL 在收到 `action.completed{action∈{like,collect,follow}, ok:true}` 时驱动 `RiskController.record(action)`（经补发 `interaction.occurred` 或等效路径），使按账号的滑动窗计数真实累加并经 `PgRiskStore` 持久化；计数 MUST 反映真实成功互动，MUST NOT 凭下发即记（下发未必成功）。

#### Scenario: 成功互动累加计数

- **WHEN** 云端收到 `action.completed{action:'like', ok:true}`
- **THEN** 该账号 like 的滑动窗计数 +1 并持久化，可被后续 `canDo` 配额判定读到

#### Scenario: 失败互动不计数

- **WHEN** 云端收到 `action.completed{action:'like', ok:false}`（如 `blocked_by_captcha`）
- **THEN** 该账号 like 计数不增加（只记真实发生的互动）

### Requirement: 风控状态与计数必须持久化跨重启

云端 SHALL 以 `RiskController.create({store: PgRiskStore})` 构造风控控制器，使账号状态与滑动窗计数落库（既有 `risk_state` / `risk_counters` 表）并在启动时回放；MUST NOT 以无 store 的 `new RiskController()` 运行导致状态永远钉在 `normal` 且重启即失忆。

#### Scenario: 重启后保留 restricted

- **WHEN** 某账号被置 `restricted` 后云端进程重启
- **THEN** 启动回放后该账号仍为 `restricted`（状态自库恢复，而非回到 `normal`）

### Requirement: 账号风控终态仅云端单写，边缘不得自挡

账号风控终态 MUST 仅由云端 `RiskController` 单写。边缘 MUST NOT 持有互动前自判 / 自记风控的逻辑：移除 `EdgeClient.canDo` / `recordRiskAction` / `requestSessionBudget` 三个未被调用的死包装。`risk.canDo` / `risk.record` / `session.budget` 协议类型 MAY 保留为 reserved 通道（不接线），但边缘 MUST NOT 在浏览闭环里调用它们替云端做风控决策。

#### Scenario: 边缘不再保留自挡风控入口

- **WHEN** 审查边缘浏览闭环代码（`browse-session` / `edge-client`）
- **THEN** 找不到任何互动前 `risk.canDo` 自判或互动后 `risk.record` 自记的调用（风控判定全在云端）

#### Scenario: 被禁账号的 record 返回 false

- **WHEN** 一个 `frozen` / 超额账号触发 `RiskController.record`
- **THEN** `record` 返回 `false`（绝不自残），符合 `AC-RISK-*`，云端不把它当作成功互动

### Requirement: 安全限额数字可在管理后台按档位配置且 canDo 每次读最新

云端的安全限额**数字**（每账号每动作的分钟 / 小时滑动突发配额，以及 Asia/Shanghai 自然日每日配额）SHALL 为可配置、可在管理后台按风控档位（conservative / normal / aggressive）编辑，且**每日上限与分钟 / 小时突发上限都 SHALL 独立可编辑**（突发上限 MUST NOT 仅由每日值派生）。云端 SHALL 把这些数字落库（新增 `quota_config` 表，迁移 `0010`，主键 `(tier, action)`，含 `daily` / `per_minute` / `per_hour` 三列）并维护内存镜像；`RiskController.canDo(action)` 经 `effectiveQuotas()` MUST **每次现读**当前生效数字（经注入的配额提供者读内存镜像），使管理后台改完即热加载生效、MUST NOT 需要重启进程。

绝不 brick（never-brick）：当配额提供者缺失、某 `(tier, action)` 缺行、或字段非有限非负整数时，`effectiveQuotas()` MUST 回落到代码写死默认（`quotas.ts` 的 `DAILY_QUOTAS` / `MINUTE_BURST_CAP` / `HOUR_BURST_CAP`），MUST NOT 抛错、MUST NOT 让风控闸失效。配额表为空（如迁移刚跑完）时行为 MUST 与现状逐位一致（零回归）。`warned` / `restricted` / `frozen` 状态对基准三档的缩放 / 清零语义 MUST 保持不变，只是基准三档数字来源改为提供者（缺值回落写死默认）。

#### Scenario: 后台改某档某动作每日上限，下一次 canDo 即按新值

- **WHEN** 管理后台把 `normal` 档 `comment_like` 的每日上限从 6 改为 4 并保存成功
- **THEN** 无需重启，该账号下一次 `canDo('comment_like')` 的自然日每日窗判定按 4 生效（命中即热加载）

#### Scenario: 分钟 / 小时突发上限独立可改、不由每日派生

- **WHEN** 管理后台单独调高某档某动作的分钟突发上限、不改其每日上限
- **THEN** `effectiveQuotas()` 的分钟窗数字按所配值生效，且每日窗数字不被该改动连带改变

#### Scenario: 缺行 / 非法值回落写死默认、绝不 brick

- **WHEN** 某 `(tier, action)` 在 `quota_config` 缺行，或其某窗口字段为非有限非负整数
- **THEN** `effectiveQuotas()` 对该动作回落 `quotas.ts` 写死默认、不抛错，风控闸照常工作

#### Scenario: 配额表为空时与现状逐位一致

- **WHEN** `quota_config` 表无任何行（如迁移刚跑完）
- **THEN** `effectiveQuotas()` 在每个状态 / 档位下产出的三窗口数字与改造前（`deriveWindowQuotas` 写死默认）逐位相同

### Requirement: 限额数字编辑绝不触碰风控状态单写路径

安全限额**数字**的编辑 MUST 只写 `quota_config` 表，MUST NOT 经由风控状态单写路径（`RiskController.setQuotaLevel` / `applySignal` / 状态机 / `risk_state` 表）。配额提供者注入 `effectiveQuotas()` 后 MUST 仅作只读读取，MUST NOT 写入或改变账号风控终态（`normal` / `warned` / `restricted` / `frozen`）或档位 `quotaLevel`。账号风控终态 MUST 仍仅由云端 `RiskController` 单写（既有不变量不被本配置通道动摇）。

#### Scenario: 改限额数字不改风控状态

- **WHEN** 管理后台保存新的限额数字
- **THEN** 写操作只落 `quota_config` 表，归属账号的 `risk_state`（status 与 quotaLevel）不被改写，`setQuotaLevel` / `applySignal` 不被调用

#### Scenario: 提供者只读、不写状态

- **WHEN** `effectiveQuotas()` 经配额提供者读取当前数字
- **THEN** 该读取不触发任何状态迁移 / 持久化写，风控终态单写路径不受影响

### Requirement: 管理后台限额页与 JWT 守卫的非乐观写

管理后台 SHALL 提供安全限额配置页（`/quotas` 路由 + 导航项），展示三档 × 全动作 × 三窗口（每日 / 分钟 / 小时）的当前生效值并可编辑。云端面板 API SHALL 提供 `GET /api/quotas`（回显当前生效值 + 审计字段，库缺行处以写死默认合成）与 `PUT /api/quotas`，二者 MUST 经 JWT 守卫。写为**非乐观**：服务端 MUST 先校验（有限非负整数 + 合理上限 + 合法 tier / action），任一字段非法时整块拒（4xx）、MUST NOT 部分落库、MUST NOT 假成功；写库成功后 MUST 回显服务端真态，管理后台以回显刷新（不本地假设成功）。

#### Scenario: 合法编辑写库并回显真态

- **WHEN** 携带有效 JWT 的 `PUT /api/quotas` 提交合法的非负整数限额
- **THEN** 服务端校验通过、写 `quota_config` 成功、刷新内存镜像并回显含 `updatedAt` / `updatedBy` 的真态，前端据此刷新

#### Scenario: 非法值整块拒、绝不落库

- **WHEN** `PUT /api/quotas` 提交了负数 / 非整数 / 超上限的限额
- **THEN** 服务端返回 4xx 校验错、不写任何行、不假成功（保持配额配置一致、绝不部分落库）

#### Scenario: 未授权写被拒

- **WHEN** 无有效 JWT 调用 `GET /api/quotas` 或 `PUT /api/quotas`
- **THEN** 返回 401，不读 / 不写配额配置

### Requirement: 速率配额饱和是节奏背压、不是风控状态输入

账号威胁态（`normal` / `warned` / `restricted` / `frozen`）MUST 只由**平台可观测信号**驱动升级：验证码 → 强信号（`confirmed`）、未知阻断浮层 → 软信号（`light`）、运营手动信号（`manual_restrict` / `manual_freeze` / `operator_override_recover`）。

`RiskController.record(action)` 因**速率配额**耗尽而被 `canDo` 拒时 MUST 只返回 `false`（背压），MUST NOT 触发任何风控状态迁移——具体地：MUST NOT `applySignal`、MUST NOT 递增 `signal_count`、MUST NOT 刷新 `last_signal_at`、MUST NOT 把账号从 `normal` 推向 `warned` / `restricted`。`quota_exceeded` MUST NOT 作为风控信号种类存在于状态机升级逻辑与 `RiskSignalKind` 中。这里的速率配额包括分钟 / 小时滑动突发窗口与 Asia/Shanghai 自然日每日窗口。

此要求**强化**「被禁账号 `record` 返回 false（绝不自残）」既有红线：返 false 不变，只去掉「撞自己配额还自升状态」的自残副作用。

#### Scenario: 配额到顶被拒不升级风控态

- **WHEN** 某 `normal` 账号的某动作在任一配额窗口（分钟 / 小时滑动窗口或自然日每日窗口）配额耗尽，`record(action)` 被调用
- **THEN** `record` 返回 `false`，该账号风控态仍为 `normal`，`signal_count` 与 `last_signal_at` 均不变

#### Scenario: 反复撞同一配额不自锁

- **WHEN** 同一账号在短时间内连续多次撞同一配额（每次 `record` 均被拒）
- **THEN** 每次都返回 `false` 且风控态**始终**停在原状态，MUST NOT 出现 `normal→warned→restricted` 的自我升级

#### Scenario: 平台真实信号仍照常升级

- **WHEN** 边缘上报验证码 / 未知阻断浮层，云端据此对账号 `applySignal({kind:'confirmed'})` / `applySignal({kind:'light'})`
- **THEN** 威胁态照常升级（如 `normal`→`restricted` / `normal`→`warned`），证明去掉的只有「配额」这个假信号源、真信号驱动不受影响

### Requirement: 速率突发窗口饱和改道为低优先级运维告警

当 `RiskController.record(action)` 因**突发窗口**（小时或分钟）速率上限被拒时（`explain(action).reason` 为 `quota:hour` / `quota:minute`），云端 SHALL 发一条**低优先级运维告警**（经既有告警存储 `AlertStore.raise`，`type: pacing_saturation`，`severity` 取低档如 P2，带账号 + 动作 + 撞顶窗口），提示「该账号浏览 / 互动节奏过载、需调单场时长或停顿」。该告警 SHALL 按「账号 + 动作」冷却去重（冷却窗内同组合不重复落库）。

发该告警 MUST NOT 触碰风控状态单写路径（MUST NOT `applySignal` / `setQuotaLevel` / 改 `risk_state`）。**每日窗**（`quota:day`）饱和是预期的预算用尽，MUST NOT 触发该告警（只背压、静默）。

#### Scenario: 突发窗饱和发一条运维告警

- **WHEN** 某账号某动作撞小时（或分钟）突发上限、`record` 被拒
- **THEN** 云端经告警存储 raise 一条 `pacing_saturation` 低优先级告警（含账号 / 动作 / 窗口），可经 `GET /api/alerts` 与看板告警区读到

#### Scenario: 冷却窗内不重复告警

- **WHEN** 冷却窗内同一账号同一动作再次撞同一突发窗
- **THEN** 不重复 raise 告警（去重压制刷屏）

#### Scenario: 每日窗饱和不发告警

- **WHEN** 某账号某动作只是撞到**每日**上限（当日预算用尽）、`record` 被拒
- **THEN** 只返回 `false` 背压，MUST NOT raise `pacing_saturation` 告警

#### Scenario: 告警绝不改风控态

- **WHEN** `pacing_saturation` 告警被 raise
- **THEN** 归属账号的 `risk_state`（status 与 quotaLevel）不被改写，`applySignal` / `setQuotaLevel` 不被调用

### Requirement: 限频闸与计数按连接真实账号解析，绝不钉死 default

云端的互动前限频闸与互动后计数 SHALL 按**发起该决策的连接的真实账号**解析其 `RiskController`（经 per-account 控制器注册表），MUST NOT 钉死在 `default` 控制器上。当连接带有真实 `accountId` 时，闸判定与记账 MUST 同落到该真实账号；MUST NOT 出现「闸看 `default` 而记账看真实账号」的分叉，致真实账号限频形同失效。握手缺失 `accountId` 的连接 MUST NOT 被静默映射成 `default` 账号计入其配额。

#### Scenario: 闸与记账落在同一真实账号
- **WHEN** 账号 A 的连接产生一次点赞意图
- **THEN** 限频判定读 A 的控制器、成功后计数也累加到 A，两者一致，不读 `default` 控制器

#### Scenario: 多账号在线时限频各按其账号
- **WHEN** 账号 A、账号 B 各有连接在线并各自互动
- **THEN** A 的互动只计入 A 的配额、B 的只计入 B 的，互不串算，任一账号超限只拦它自己

### Requirement: 单场会话上限（时长 + 互动预算）可在管理后台按账号配置且运行时每次现读

云端的**单场会话上限**——① 单场时长上限（`max_duration_min`）；② 单场互动预算（`likes` / `collects` / `follows` / `searches` / `comments` / `comment_likes` 六项）——SHALL 为可配置、可在管理后台**按账号**编辑。云端 SHALL 把这些数字落库（新增 `session_config` 表，迁移 `0015`，主键 `account_id`，含 `max_duration_min` 与六个 `budget_*` 列）并维护内存镜像。浏览闭环调度器的时长解析（疲劳乘子用）、会话监测体的到点判定、以及单场互动预算的初始化 / 重置 MUST 经注入的**按账号提供者**（`sessionDurationMsFor(accountId)` / `sessionBudgetFor(accountId)`）**每次现读**当前生效值，使管理后台改完即热加载、MUST NOT 需要重启进程。

绝不 brick（never-brick）：当提供者缺失、账号缺行、或某字段非有限非负整数（时长还需 `>= 1`）时，运行时 MUST 逐项回落代码写死默认（时长 `10` 分钟；互动预算 `likes:10` / `collects:5` / `follows:3` / `searches:5` / `comments:2` / `comment_likes:3`），MUST NOT 抛错、MUST NOT 让浏览闭环崩溃。`session_config` 表为空（如迁移刚跑完）时行为 MUST 与现状逐位一致（严格零回归）。会话内的「已发生计数 = 初始预算 − 当前剩余」比率闸 MUST 以会话开始时的预算快照为 `init`，会话中途的配置改动 MUST NOT 影响本场已在进行的比率闸（新值于下一场会话生效）。

#### Scenario: 后台改某账号单场时长，下一场会话即按新值

- **WHEN** 管理后台把某账号的 `max_duration_min` 从 10 改为 20 并保存成功
- **THEN** 无需重启，该账号下一次会话的时长上限按 20 分钟生效（疲劳乘子与会话监测体到点判定均现读新值）

#### Scenario: 后台改某账号某项互动预算，下一场会话即按新值

- **WHEN** 管理后台把某账号的单场 `likes` 预算从 10 改为 6 并保存成功
- **THEN** 无需重启，该账号下一场会话 reset 后的点赞预算为 6，预算耗尽即不再下发点赞

#### Scenario: 账号缺行 / 非法值回落写死默认、绝不 brick

- **WHEN** 某账号在 `session_config` 缺行，或其某字段为非有限非负整数
- **THEN** 运行时对该账号 / 该字段回落写死默认（时长 10min、预算 `freshBudget` 数字），不抛错，浏览闭环照常驱动

#### Scenario: 配置表为空时与现状逐位一致

- **WHEN** `session_config` 表无任何行（如迁移刚跑完）
- **THEN** 任意账号的单场时长 = 10min、单场互动预算 = `{likes:10,collects:5,follows:3,searches:5,comments:2,comment_likes:3}`，与改造前逐位相同

#### Scenario: 会话中途改预算不动本场比率闸

- **WHEN** 某场会话进行中，管理后台改了该账号的单场 `likes` 预算
- **THEN** 本场会话的「已发生点赞 = 初始预算 − 当前剩余」仍以本场开始时的初始预算为基准计算，不被中途改动扰动；新值于下一场会话生效

### Requirement: 单场会话上限的存储与编辑绝不触碰风控状态单写路径

单场会话上限的存储与编辑 MUST 只写 `session_config` 表，MUST NOT 经由风控状态单写路径（`RiskController.setQuotaLevel` / `applySignal` / 状态机 / `risk_state` 表）。注入的单场上限提供者 MUST 仅作只读读取，MUST NOT 写入或改变账号风控终态（`normal` / `warned` / `restricted` / `frozen`）或档位 `quotaLevel`。账号风控终态 MUST 仍仅由云端 `RiskController` 单写（既有不变量不被本配置通道动摇）。本能力 MUST NOT 经 WebSocket 协议 v2（不动两份 `protocol.ts` / `command-bridge.ts` / `docs/protocol.md`）。

#### Scenario: 改单场上限不改风控状态

- **WHEN** 管理后台保存新的单场时长 / 互动预算
- **THEN** 写操作只落 `session_config` 表，归属账号的 `risk_state`（status 与 quotaLevel）不被改写，`setQuotaLevel` / `applySignal` 不被调用

#### Scenario: 提供者只读、不写状态

- **WHEN** 调度器 / 会话监测体经提供者读取单场上限
- **THEN** 该读取不触发任何状态迁移 / 持久化写、不经协议下发，风控终态单写路径不受影响

### Requirement: 单场会话上限不再来自人设

单场会话上限的运行时来源 SHALL 唯一为安全限额层（`session_config` 表 + 提供者，缺值回落写死默认）。人设（`Soul`）MUST NOT 再承载 `session_limits`——`src/soul/types.ts` 的 `session_limits` 字段、`src/soul/loader.ts` 的 `parseSessionLimits` 校验、`src/soul/soul.yaml` 的对应段 SHALL 被移除。移除 MUST 在确认运行时已无任何 `soul.session_limits` 读取后进行（`grep -rn "session_limits" src/` 仅余历史定义、无运行时读点）。管理后台人设页 MUST NOT 展示或提供 `session_limits` 的编辑入口（消除「能改却无效」的误导）。人设此后只承载身份 / 兴趣 / 行为偏好。

#### Scenario: 时长解析不再读人设

- **WHEN** 浏览闭环调度器与会话监测体解析单场时长上限
- **THEN** 取值来自注入的单场上限提供者（按当前账号），不再读取 `soul.session_limits.max_duration_min`；提供者缺失时回落写死默认 10min

#### Scenario: 人设不再含 session_limits

- **WHEN** 加载任意账号人设
- **THEN** `Soul` 不含 `session_limits` 字段，人设加载器不解析该段，人设页不展示该编辑区，且运行时无任何 `soul.session_limits` 读取

#### Scenario: 删除前无残留读点

- **WHEN** 准备从人设删除 `session_limits`
- **THEN** 全部单场时长读点已迁至提供者，`grep -rn "session_limits" src/` 无运行时读取，删除后浏览闭环不 brick（回落写死默认）

### Requirement: 单场会话上限为全局配置（时长 + 互动预算），取代按账号维度

云端的**单场会话上限**——① 单场时长上限（`max_duration_min`）；② 单场互动预算（`likes` / `collects` / `follows` / `searches` / `comments` / `comment_likes` / `join_groups` 七项）——SHALL 为可在管理后台编辑的**全局单例配置**：**无账号维度、无 `default`、无按账号覆盖**，一份配置管所有账号（单行表，参照模型配置单行 `id=1 CHECK` 模式）。运行时——浏览闭环时长解析（疲劳乘子用）、会话监测体到点判定、单场互动预算的初始化 / 重置——MUST 经**无账号参数的全局提供者**（`sessionDurationMs()` / `sessionBudget()`）**每次现读**当前生效值，使管理后台改完即热加载、MUST NOT 需要重启进程。

绝不 brick（never-brick）：当全局配置缺失、或某字段非有限非负整数（时长还需 `>= 1`）时，运行时 MUST 逐项回落代码写死默认（时长 `10` 分钟；互动预算 `likes:10` / `collects:5` / `follows:3` / `searches:5` / `comments:2` / `comment_likes:3` / `join_groups:1`），MUST NOT 抛错、MUST NOT 让浏览闭环崩溃。配置表为空（如迁移刚跑完）时行为 MUST 与回落默认逐位一致。会话内的「已发生计数 = 初始预算 − 当前剩余」比率闸 MUST 以会话开始时的预算快照为 `init`，会话中途的配置改动 MUST NOT 影响本场已在进行的比率闸（新值于下一场会话生效）。

Facebook 加群调度在执行真实 `join_group` 前 MUST 同时检查每日/minute/hour 风控配额与单场 `join_groups` 剩余预算；当单场 `join_groups` 剩余为 0 时，MUST 不下发 edge `group.join`，MUST 记录可审计的非成功结果，MUST NOT 写入 membership `joined_at`，MUST NOT 记录 `join_group` 成功风控事件。单场 `join_groups` 只在 judgment-confirmed `joined` 且 edge 执行成功后扣减；`already_member`、`gated`、`pending`、shadow、登录/验证码阻断、导航失败、执行失败或不确定结果 MUST NOT 扣减。

单场会话上限的存储与编辑 MUST 只写自己的单行表、MUST NOT 经由风控状态单写路径（`RiskController.setQuotaLevel` / `applySignal` / 状态机 / `risk_state` 表），MUST 仅作只读读取、MUST NOT 改写账号风控终态或档位。本能力 MUST NOT 经 WebSocket 协议 v2。

**取代说明**：本要求**取代**先前由 `session-limits-to-quota-layer` 引入的「单场会话上限可在管理后台**按账号**配置」要求——账号维度被取消（设计决策 2026-06-24「按账号」→ 2026-06-27「全局通用」翻转）；现有 `account_id='default'` 行的值经前向迁移搬成全局行，已设的 30min 保留生效、零数据丢失。归档协调见本 change 的 design.md。

#### Scenario: 后台改全局单场时长，所有账号下场即按新值

- **WHEN** 管理后台把全局 `max_duration_min` 从 10 改为 30 并保存成功
- **THEN** 无需重启，**所有账号**下一场会话的时长上限按 30 分钟生效（疲劳乘子与会话监测体到点判定均现读新全局值），不再有按账号差异、也不再回落写死 10min

#### Scenario: 后台改全局某项互动预算，所有账号下场即按新值

- **WHEN** 管理后台把全局单场 `likes` 预算从 10 改为 6 并保存成功
- **THEN** 无需重启，**所有账号**下一场会话 reset 后的点赞预算为 6，预算耗尽即不再下发点赞

#### Scenario: 后台改全局加群预算，所有账号下场即按新值

- **WHEN** 管理后台把全局单场 `join_groups` 预算从 1 改为 2 并保存成功
- **THEN** 无需重启，**所有账号**下一场会话 reset 后的加群预算为 2，预算耗尽即不再下发真实加群

#### Scenario: 全局配置缺失 / 非法值回落写死默认、绝不 brick

- **WHEN** 全局单场上限配置缺失（表空），或某字段为非有限非负整数（或时长 < 1）
- **THEN** 运行时逐项回落写死默认（时长 10min、预算 `likes:10/collects:5/follows:3/searches:5/comments:2/comment_likes:3/join_groups:1`），不抛错，浏览闭环照常驱动

#### Scenario: 会话中途改预算不动本场比率闸

- **WHEN** 某场会话进行中，管理后台改了全局单场 `likes` 预算
- **THEN** 本场会话的「已发生点赞 = 初始预算 − 当前剩余」仍以本场开始时的初始预算为基准计算，不被中途改动扰动；新值于下一场会话生效

#### Scenario: 单场加群预算耗尽不下发真实加群

- **WHEN** 某账号当前会话的 `join_groups` 剩余预算为 0，且每日/minute/hour `join_group` 配额仍未耗尽
- **THEN** Facebook 加群调度 MUST 不下发 edge `group.join`，并返回/记录单场预算耗尽的非成功结果

#### Scenario: 只有确认成功加群扣减单场加群预算

- **WHEN** Facebook 加群尝试返回 `joined` 且 edge 执行成功
- **THEN** 当前会话 `join_groups` 剩余预算扣减 1
- **AND** `already_member`、`gated`、`pending`、shadow、失败或不确定结果不扣减该预算

#### Scenario: 改单场上限不改风控状态

- **WHEN** 管理后台保存新的全局单场时长 / 互动预算
- **THEN** 仅写单场上限单行表，账号风控终态（`normal` / `warned` / `restricted` / `frozen`）与档位 `quotaLevel` MUST 不被改变，风控状态仍仅由 `RiskController` 单写

### Requirement: 每日配额窗口按本地自然日计算

云端风控 SHALL 将 `day` 配额窗口定义为 Asia/Shanghai 本地自然日（00:00:00 至次日 00:00:00），而不是最近 24 小时滑动窗口。`minute` 与 `hour` 配额窗口 SHALL 继续使用滑动窗口，用于短时突发保护。所有 `RiskController.explain(action)`、`canDo(action)`、`dailyRemaining(action)`、`quotaReleaseAfterMs(action,'day')` 与 UI `dailyUsage.windows.day` 的饱和 / 恢复时间 MUST 使用同一自然日口径。

#### Scenario: 昨天的浏览不占今天每日配额

- **WHEN** 某账号昨天 17:59 已经浏览到 150 次，今天 00:00 后仅浏览 76 次
- **THEN** `RiskController.explain('view')` MUST 按今天自然日计数，允许继续浏览，MUST NOT 因最近 24 小时达到 150 而返回 `quota:day`

#### Scenario: 今日每日配额满后等下个本地午夜恢复

- **WHEN** 某账号在 Asia/Shanghai 当天自然日内 `view` 已达到 day quota
- **THEN** `RiskController.explain('view')` MUST 返回 `allowed:false` 与 `reason:'quota:day'`
- **AND** 其 `retryAfterMs` / `quotaReleaseAfterMs('view','day')` MUST 指向下一个 Asia/Shanghai 本地 00:00，而不是最早事件的 24 小时滑出时间

#### Scenario: 分钟和小时仍按滑动窗口限突发

- **WHEN** 某账号在一分钟或一小时内达到对应 burst quota
- **THEN** `RiskController.explain(action)` MUST 继续按滑动窗口返回 `quota:minute` 或 `quota:hour`，其释放时间仍为最早相关事件滑出该窗口的时间

### Requirement: Facebook automatic comments are pre-gated and counted only after verified success

Facebook scheduled comment attempts SHALL call the cloud risk gate before dispatch and again before submit when practical. Success counting SHALL happen only after server-confirmed verification returns `ok:true`. Failed, skipped, shadow, validator-rejected, login-blocked, checkpointed, or ambiguous attempts MUST NOT call `record('comment')` as success.

#### Scenario: Quota denial prevents dispatch
- **WHEN** `canDo('comment')` denies a Facebook scheduled comment attempt
- **THEN** the trigger does not dispatch the edge comment work and records/returns a quota-denied non-success outcome

#### Scenario: Only verified success records risk
- **WHEN** Facebook edge execution returns verified `ok:true`
- **THEN** cloud records one `comment` interaction for that account; any non-success return records no successful interaction

### Requirement: Facebook automatic comments must not use manual-comment quota bypass

Facebook scheduled comment accounts SHALL NOT be placed into xhs/manual comment collections that skip risk recording or quotas. Automatic Facebook comments have no human-in-loop approval at submit time and MUST use the normal automatic interaction safety gates.

#### Scenario: Manual bypass is not used
- **WHEN** a Facebook scheduled comment succeeds
- **THEN** it is counted through the automatic `interaction.occurred -> RiskController.record('comment')` path and is not skipped due to a manual-comment account set

### Requirement: Facebook group join is a first-class rate-limited action

Facebook group join SHALL be a rate-limited action alongside browse/like/collect/comment, subject to the existing minute/hour/day sliding-window quotas, the three quota tiers, and risk-state scaling (warned slows all actions; restricted/frozen stops joining). A brand-new account SHALL be throttled by selecting the conservative tier rather than a bespoke warmup function. Join attempts MUST be pre-gated before dispatch, and a join MUST count against the quota only after a verified join.

#### Scenario: Join quota denial prevents dispatch
- **WHEN** the risk gate denies a join for an account that has exhausted its minute, hour, or day join quota
- **THEN** no join is dispatched and a quota-denied non-success outcome is recorded

#### Scenario: Only verified join counts
- **WHEN** a join attempt returns anything other than a judgment-confirmed join
- **THEN** no successful join interaction is recorded for that account

#### Scenario: Restricted state stops joining
- **WHEN** an account's risk state is restricted or frozen
- **THEN** the join loop for that account does not dispatch, inheriting the same state scaling as other interactions

### Requirement: Join and comment share the per-account single-flight and activity budget

Facebook join and Facebook comment for the same account SHALL be dispatched under the same per-account single-flight so the physically single-slot edge is never asked to do both at once, and their combined daily activity SHALL be bounded against platform tolerance. The worst-case aggregate of the join daily cap plus the comment daily cap MUST be a considered value, not two independently-spent caps.

#### Scenario: One account never joins and comments simultaneously
- **WHEN** an account has both a pending join slot and a pending comment slot in the same tick
- **THEN** only one is dispatched, held by the same per-account single-flight lock used for commenting

### Requirement: Scaled risk quotas must round upward

When cloud computes scaled window quotas for reduced risk states, it SHALL round scaled
quota values upward after multiplication. The scaling operation MUST still clamp negative
or non-finite effective outputs to zero, and a zero scaling factor MUST still produce zero.

`warned` accounts SHALL continue to use conservative baseline quotas scaled by `0.7` and
SHALL continue to pause publish actions. However, a positive baseline quota such as a
minute-window quota of `1` MUST NOT become `0` solely because of fractional scaling.

#### Scenario: warned keeps sparse interaction windows available

- **WHEN** an account is in `warned` and the conservative baseline minute quota for an
  interaction action is `1`
- **THEN** the effective minute quota for that action is `1`, not `0`
- **AND** `canDo(action)` is not rejected merely because `0 >= 0` on an empty minute
  window

#### Scenario: frozen scaling still stops all actions

- **WHEN** a quota window is scaled by factor `0`
- **THEN** the effective quota remains `0`

### Requirement: 浏览打开前必须先过 view 配额闸

云端 SHALL 在把候选卡片下发为 `open_note` 之前，按该连接的真实账号调用
`RiskController.explain('view')` 或等效只读判定。判定拒绝时，云端 MUST NOT 下发
`open_note`，MUST NOT 伪造成功浏览，MUST 进入浏览额度休眠而不是下发 `session.end`。
若拒绝原因为 `quota:minute`、`quota:hour`、`quota:day`，云端 SHOULD 按滑动窗口释放时间安排重判；
无可计算释放时间时，云端 MAY 以保守周期重判，直到判定恢复或会话被其它正常终止条件结束。

该闸用于阻止新的笔记详情被打开；既有 `note.detail` 到达后的 `record('view')` 计数路径
仍作为真实成功浏览的记账来源保留。浏览额度休眠期间，普通浏览推进、打开和互动命令 MUST 被扣住；
窗口释放后，云端 SHOULD 发送一次轻量恢复指令重新驱动浏览闭环。该休眠只作用于浏览闭环，不得影响
定时或手动的笔记创作、发帖生成、发帖审批或发帖下发；这些流程不需要前置浏览。点赞、收藏、关注、
评论等浏览衍生行为不会被主动触发，因为休眠期间没有新的笔记详情被打开。

#### Scenario: view 配额已满时不打开下一篇笔记

- **WHEN** 账号的 `RiskController.explain('view')` 返回 rejected
- **AND** 浏览角色产出一条 `content.valuable` 候选
- **THEN** 云端 MUST NOT 下发 `open_note`
- **AND** 云端 MUST NOT 下发 `session.end`
- **AND** 云端 MUST 进入浏览额度休眠并安排后续重判

#### Scenario: view 配额可用时照常打开笔记

- **WHEN** 账号的 `RiskController.explain('view')` 返回 allowed
- **AND** 浏览角色产出一条 `content.valuable` 候选
- **THEN** 云端照常下发 `open_note`

#### Scenario: view 配额窗口释放后恢复浏览

- **WHEN** 浏览额度休眠到期
- **AND** 账号的 `RiskController.explain('view')` 返回 allowed
- **THEN** 云端 SHOULD 解除浏览休眠
- **AND** 云端 SHOULD 下发一次恢复浏览的推进指令

#### Scenario: 临时 view 配额不阻止会话启动

- **WHEN** 账号因 `quota:minute` 或 `quota:hour` 临时无法新增 view
- **THEN** 云端 MAY 启动或保持浏览会话
- **AND** 云端 MUST 在 `open_note` 前进入浏览额度休眠
- **AND** 云端 MUST NOT 因临时 view 配额拒绝阻断手动或定时笔记创作、发布

