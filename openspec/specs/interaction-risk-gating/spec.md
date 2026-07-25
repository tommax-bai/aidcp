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

**计数 MUST 记录既成事实，且 MUST NOT 因策略事后重判而丢弃。** 一次动作的回执抵达时，它**已经发生**；此时再判一次「该账号现在还允许做这个吗」并据此**不写**计数，销毁的只有证据，改变不了已发生的事。因此：**「该不该做」MUST 在下发前判定**（那道预闸是唯一能真正阻止动作的地方）；**回执抵达后 MUST 无条件记录**，无论账号此刻的威胁态、配额余量或任何策略判定如何。这与上一段的 `MUST NOT 凭下发即记` 构成一对完整规则：**下发（意图）MUST NOT 计；做完了（既成事实）MUST 计。**

由此，任何**绕过预闸**而真实发生的动作（如运营手动命令按「操作员全权」裁决跳过配额闸）、以及任何在**预闸与回执之间**状态或配额发生变化的动作，其计数 MUST 与未绕过者一视同仁地累加。系统对自己**少报**真实活动量与**谎报**成功同属不诚实：前者是后者的镜像，且因计数器同时是配额分母的来源，少报会让后续闸门**误以为尚有余量**而放行更多真实动作。

**操作员手动动作 MUST 被记录，且 MUST NOT 被配额闸拦截。** 「跳过配额」指的是**不被拦下**，不是**不被记下**：手动动作同样被平台观察到，同样消耗该账号在平台眼里的活动预算。**「操作员全权」豁免的是权限，不是事实。** 因此任何以「人工授权 / 操作员全权」为由**跳过驱动 `record`** 的接线 MUST 改为照常记录（其**跳过闸**的豁免保持不变），且该记录 MUST 与自动动作一视同仁地累加、一视同仁地被后续闸读到。

**推论（一条必须被明确禁止的实现方式）**：一条路径若确实不该消耗预算，正确表达 MUST 是**在接线层显式不驱动 `record`**，MUST NOT 是「照常调用 `record` 但让它内部静默丢弃」——后者使「豁免」与「丢数」不可区分，读代码的人无法分辨这个 0 是设计还是 bug。

#### Scenario: 成功互动累加计数

- **WHEN** 云端收到 `action.completed{action:'like', ok:true}`
- **THEN** 该账号 like 的滑动窗计数 +1 并持久化，可被后续 `canDo` 配额判定读到

#### Scenario: 失败互动不计数

- **WHEN** 云端收到 `action.completed{action:'like', ok:false}`（如 `blocked_by_captcha`）
- **THEN** 该账号 like 计数不增加（只记真实发生的互动）

#### Scenario: 绕过预闸的真实动作照样计数

- **WHEN** 一次动作按产品裁决绕过了下发前的配额闸（如运营手动命令），在平台上真实完成，其回执抵达云端并驱动 `record`
- **THEN** 该动作照常记入计数，MUST NOT 因「此刻的配额已耗尽」而被丢弃
- **AND** 后续 `canDo` 读到的余量反映真实活动量

#### Scenario: 手动动作不被拦，但被记下

- **WHEN** 运营用手动命令触发一次动作，该账号该动作的配额已耗尽
- **THEN** 该动作 MUST 照常执行（手动跳过配额闸，操作员全权）
- **AND** 该动作 MUST 被记入计数（平台看见了它）
- **AND** 该账号后续的**自动**动作据此被闸拦下——手动动作消耗了自动预算，这是预期结果

#### Scenario: 飞行途中状态翻转不销毁证据

- **WHEN** 一次动作通过预闸后开始执行，执行期间账号因平台信号被降为 `restricted`，随后该动作的回执抵达
- **THEN** 该动作照常记入计数（它已经发生）
- **AND** 该账号后续动作仍被 `restricted` 正常拦截（拦的是未来，不是过去）

#### Scenario: 紧窗口的拒绝不得污染松窗口的账本

- **WHEN** 某账号在一小时内真实完成 N 次同一动作，而该动作的小时配额小于 N、日配额不小于 N
- **THEN** 当日计数为 N（每一次都记下）
- **AND** 日配额据此如实递减，MUST NOT 出现「日账本只记到小时上限、于是日闸误判尚有余量」

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

**此处「只返回 `false`」限定的是本要求所禁的那一类副作用——风控状态迁移——而 MUST NOT 被解读为「因此也不许把这次动作记进计数器」。** 二者是两个不同的问题，MUST 分别作答：返回值回答**「这个动作在策略内吗」**，计数器回答**「这个动作发生过吗」**。一次已经在平台上做完的动作，其**发生**不因策略事后判定它**不该发生**而改变；记录它 MUST NOT 被当作对它的许可，拒绝记录它也 MUST NOT 被当作对它的撤销。计数器的写入规则见「互动发生后必须按账号持久计数」。

此要求**强化**「被禁账号 `record` 返回 false（绝不自残）」既有红线：返 false 不变，只去掉「撞自己配额还自升状态」的自残副作用。**同理，「记账时二次判策略、判不过就当没发生过」这个丢证据的副作用亦不在本红线保护之列**——自残指「凭空的信号把自己越限越死」；如实记下一次真实发生的动作**造不出任何假信号**，它只会让后续 `canDo` 更早拒绝（计数器只增、闸为 `count >= quota`），故在**收紧**方向上，MUST NOT 与本红线混为一谈。

#### Scenario: 配额到顶被拒不升级风控态

- **WHEN** 某 `normal` 账号的某动作在任一配额窗口（分钟 / 小时滑动窗口或自然日每日窗口）配额耗尽，`record(action)` 被调用
- **THEN** `record` 返回 `false`，该账号风控态仍为 `normal`，`signal_count` 与 `last_signal_at` 均不变

#### Scenario: 反复撞同一配额不自锁

- **WHEN** 同一账号在短时间内连续多次撞同一配额（每次 `record` 均被拒）
- **THEN** 每次都返回 `false` 且风控态**始终**停在原状态，MUST NOT 出现 `normal→warned→restricted` 的自我升级

#### Scenario: 平台真实信号仍照常升级

- **WHEN** 边缘上报验证码 / 未知阻断浮层，云端据此对账号 `applySignal({kind:'confirmed'})` / `applySignal({kind:'light'})`
- **THEN** 威胁态照常升级（如 `normal`→`restricted` / `normal`→`warned`），证明去掉的只有「配额」这个假信号源、真信号驱动不受影响

#### Scenario: 被拒仍返 false，但事实已记下

- **WHEN** 某账号某动作的配额已耗尽，而该动作**已经在平台上真实发生**（回执抵达），`record(action)` 被调用
- **THEN** `record` 返回 `false`（背压答案不变，红线不变）
- **AND** 该动作**已被记入**滑动窗计数并持久化（事实不因策略判定而消失）
- **AND** 风控态、`signal_count`、`last_signal_at` 均不变

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

Facebook group join SHALL be a rate-limited action alongside browse/like/collect/comment, subject to the existing minute/hour/day sliding-window quotas, the three quota tiers, and risk-state scaling (warned slows all actions; restricted/frozen stops joining). A brand-new account SHALL be throttled by selecting the conservative tier rather than a bespoke warmup function. Join attempts MUST be pre-gated before dispatch.

The join quota is a **risk budget**: it bounds how much join activity the platform observes from the account. It therefore SHALL count **join actions that actually reached the platform**, not joins that succeeded. A join action reaches the platform when the edge reports that it actually performed the click on the live page (`clicked: true`); whether the group then admits the account (`ok: true`), leaves the request awaiting an admin (`ok: false, reason: 'pending'`), or demands a questionnaire is the platform's answer to an action we already took, and MUST NOT determine whether that action counted.

This MUST NOT be conflated with counting on dispatch. **Dispatch is intent; a click is an accomplished fact.** The cloud MUST NOT count a join because it sent a command — a command may never arrive or never execute. It MUST count only the edge's after-the-fact report that the click really happened. An attempt that never reached the platform — a pre-click observation that the request was already pending, an account that was already a member, an observation-only (shadow) run, a navigation or login failure before the click — reports `clicked: false` and MUST NOT count.

Counting a reached-platform join against the quota MUST NOT mark that join as successful. Success and quota are separate questions with separate answers: the success ledger continues to recognise only a judgment-confirmed join, and a counted-but-unconfirmed join MUST NOT enter the display interaction ledger, MUST NOT be reported to the operator as a completed join, and MUST NOT satisfy any requirement that depends on membership.

A **quota-usage display** is not a membership claim, and the two MUST NOT be conflated. A surface whose subject is budget consumption — how much of an action's daily allowance the account has spent — reports **actions spent**; for joins that means join actions that reached the platform, and showing a pending-approval join there is correct, not an overclaim. The surfaces whose subject is membership — which groups the account actually belongs to — MUST continue to count only judgment-confirmed joins. The same word may therefore denote an action on a budget surface and a membership on a ledger surface; each surface MUST be honest about its own subject rather than forced to the other's meaning.

The recorded-action counter SHALL faithfully hold every join action that reached the platform, including one made outside the automatic gate and one whose account was throttled mid-flight — see "互动发生后必须按账号持久计数". The confirmed-join ledger remains an independent count answering a different question. Gates MAY enforce either or both against the cap; where both are enforced, that MUST be understood as belief in two honest measurements rather than as a defect to be unified away, and a gate MUST NOT be relaxed onto a count that is looser than one it already enforces.

#### Scenario: Join quota denial prevents dispatch
- **WHEN** the risk gate denies a join for an account that has exhausted its minute, hour, or day join quota
- **THEN** no join is dispatched and a quota-denied non-success outcome is recorded

#### Scenario: A join that reached the platform counts even when approval is pending
- **WHEN** the edge reports a join in which it performed the click and the request is left awaiting group-admin approval
- **THEN** the account's join quota counter increases by one
- **AND** the join is NOT recorded as a successful or confirmed join
- **AND** the operator is not told the group was joined

#### Scenario: An attempt that never reached the platform does not count
- **WHEN** the edge reports a join outcome in which it did not perform the click — the request was already pending before this attempt, the account was already a member, the run was observation-only, or navigation or login failed first
- **THEN** the account's join quota counter does not increase
- **AND** no successful join interaction is recorded

#### Scenario: Dispatch alone still never counts
- **WHEN** the cloud dispatches a join command and no edge report of an actual click is received
- **THEN** the account's join quota counter does not increase
- **AND** the quota is never spent on intent that the edge did not confirm as actuated

#### Scenario: A quota-usage display shows actions spent, not memberships
- **WHEN** an operator views a per-account quota-usage display after the account performed one join click that is awaiting group-admin approval
- **THEN** the join budget shows one action spent against the cap
- **AND** the surfaces that report group membership still show zero groups joined and one request awaiting approval
- **AND** neither surface is required to adopt the other's meaning

#### Scenario: Only verified join counts as a successful join
- **WHEN** a join attempt returns anything other than a judgment-confirmed join
- **THEN** no successful join interaction is recorded for that account
- **AND** the success ledger's count of groups joined today is unchanged

#### Scenario: A join made outside the automatic gate still counts
- **WHEN** an operator's manual join bypasses the pre-dispatch quota gate by design, performs the click, and its receipt reaches the cloud while the hour window is already saturated
- **THEN** the account's join quota counter increases by one
- **AND** the automatic join loop reads that true count and does not resume on a short one

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

### Requirement: 配额闸默认不做账号年龄冷启动爬坡（直接走安全限额配置）

`effectiveQuotas()` 的每日 / 分钟 / 小时窗口配额 MUST 直接采用**安全限额配置**（经注入的配额提供者读 `quota_config` 表，缺值 / 缺行回落 `quotas.ts` 写死默认三档），MUST NOT 按账号年龄（`accounts.created_at` 现算的「入库天数」）压低为逐日爬坡的冷启动天花板。新账号自第一天起即按其风控档位（conservative / normal / aggressive）的安全限额浏览与互动；浏览（`view`）MUST NOT 被封顶在某个低于安全 `view` 配额的冷启动值（例如 Facebook 旧曲线第 7 天的 `view=70`）。

逐日爬坡 MAY 作为 opt-in 机制在代码中保留（曲线数据与 clamp 逻辑不删除），且 SHALL 有且仅有两条互相独立的启用路径，**缺省两条都关**：

1. **进程级全局路径**（既有）：仅当运维显式设 `AIDCP_COLDSTART_RAMP=true` 时启用，起点取 `accounts.created_at`。生产接线默认与 `RiskController` 的类默认 MUST 一致为「关」，MUST NOT 出现「类默认开、服务默认关」的口径分裂。
2. **账号级慢启动路径**（本 change 新增）：仅当该账号 `accounts.slow_start_since` 非 NULL 时对**该账号**启用，起点取 `slow_start_since` 自身。

anchor（起点）解析 MUST 严格按「谁开用谁的起点」的优先级：账号级非 NULL → 用 `slow_start_since`；否则 env 全局开且 `created_at` 存在 → 用 `created_at`；否则不叠任何 clamp。两条路径的起点 MUST NOT 以 OR / AND / min 或任何其它方式合成——合成会把未开慢启动的账号按 `created_at` 夹回冷启动天花板，即本要求首段禁止的那个行为。

账号级慢启动的起点 MUST NOT 取 `accounts.created_at`。该列语义是「该 accountId 第一次握手连上本云端库的时刻」（`DEFAULT now()`，且账号重连时 `ON CONFLICT DO NOTHING` 保留原值），既非平台注册时间、亦非首次运行时间；以它为起点会使导入的老号被当作第 1 天、复活的旧号被当作已毕业。

`AIDCP_SLOW_START_DISABLED=true` MUST 作为全局停用闸：置真时无视所有账号级 `slow_start_since`、全体不叠 clamp，且对外投影 MUST 如实标注该原因。

冷启动天花板的平台曲线选择 MUST 建立在**已确认的平台**之上。当账号平台无法确认时，MUST NOT 回落到任一平台的曲线（含默认小红书曲线），MUST 不叠 clamp 并如实标注不可用原因。

慢启动是 `effectiveQuotas()` 的**输入**，不是账号风控状态：它 MUST NOT 写入 `risk_state`、MUST NOT 经 `setQuotaLevel` / `applySignal` 或风控终态单写链，MUST NOT 改变账号威胁态。

本要求 MUST NOT 改变既有不变量：安全限额**数字**不变；`warned` 的缩放、`restricted` / `frozen` 的互动清零 / 归零语义仍照常作用于安全限额基准；账号风控终态（`normal` / `warned` / `restricted` / `frozen`）MUST 仍仅由云端 `RiskController` 单写。与本机制无关的「重启防 burst 静默期」（进程重启后首次成功前的临时抑制）MUST NOT 受本要求影响。

#### Scenario: 新号默认按安全配额浏览、不被冷启动压低

- **WHEN** 某 Facebook 账号建号未满 7 天（历史冷启动窗口内）、`AIDCP_COLDSTART_RAMP` 未设为 `true`、该账号 `slow_start_since` 为 NULL，`effectiveQuotas()` 被调用
- **THEN** 其 day 窗口 `view` 配额等于该账号风控档位的安全 `view` 限额（如 aggressive 写死默认 `300`），MUST NOT 被压到冷启动第 7 天的 `70`

#### Scenario: 冷启动全局路径仅在显式 opt-in 时生效

- **WHEN** 运维显式设 `AIDCP_COLDSTART_RAMP=true`
- **THEN** 逐日养号爬坡按 `created_at` 起点重新生效，`effectiveQuotas() = min(冷启动当日天花板, 风控缩放安全限额)`（原机制供养号需要时回退，行为与开启前一致）

#### Scenario: 账号级慢启动独立于全局开关生效

- **WHEN** `AIDCP_COLDSTART_RAMP` 未设为 `true`，但某账号 `slow_start_since` 为 3 天前
- **THEN** 该账号 `effectiveQuotas() = min(该平台曲线第 4 天天花板, 风控缩放安全限额)`
- **AND** 同云端其它 `slow_start_since` 为 NULL 的账号逐位不受影响

#### Scenario: 两条路径不合成起点

- **WHEN** `AIDCP_COLDSTART_RAMP=true` 且某账号 `slow_start_since` 为今天、而其 `created_at` 为 30 天前
- **THEN** 该账号按 `slow_start_since` 算作第 1 天，MUST NOT 因 `created_at` 已过 7 天窗口而被判毕业、MUST NOT 取两者之中任一合成值

#### Scenario: 慢启动起点绝不取入库时间

- **WHEN** 某账号 `slow_start_since` 为 NULL 且 `AIDCP_COLDSTART_RAMP` 未设为 `true`，无论其 `created_at` 为何值
- **THEN** MUST 不叠任何冷启动 clamp，`effectiveQuotas()` 与本 change 前逐位相同

#### Scenario: 平台无法确认时不 clamp 也不回落曲线

- **WHEN** 某账号 `slow_start_since` 非 NULL，但其平台无法确认（元数据解析失败或平台字段不可信）
- **THEN** MUST NOT 按小红书曲线或任何其它平台曲线 clamp，`effectiveQuotas()` 与不开慢启动逐位相同
- **AND** 对外投影 MUST 标注该账号当前不适用慢启动及其原因

#### Scenario: 开关改动无需重启即生效

- **WHEN** 某账号的 `slow_start_since` 被写入或清空，而该账号的 `RiskController` 实例已存在于进程内且不被重建
- **THEN** 同一实例的下一次 `effectiveQuotas()` MUST 反映新值
- **AND** MUST NOT 要求重启进程、驱逐 controller 缓存或重新解析账号元数据

#### Scenario: 全局停用闸无视账号级开关

- **WHEN** `AIDCP_SLOW_START_DISABLED=true`，而若干账号 `slow_start_since` 非 NULL
- **THEN** 全体账号 MUST 不叠 clamp，`effectiveQuotas()` 与不开慢启动逐位相同
- **AND** 对外投影 MUST 如实标注「本云端已全局停用慢启动」，MUST NOT 把停用显示成未开启

#### Scenario: 慢启动只收紧不放宽

- **WHEN** 某账号开启慢启动，与同一账号同一时刻未开启慢启动相比
- **THEN** 其 `effectiveQuotas()` 的每个窗口每个动作 MUST 逐位小于或等于未开启时的值
- **AND** MUST NOT 断言必然严格更小——曲线与档位取更严者，档位数字可经 `quota_config` 热编辑，故某些档位下部分动作可能逐位相等

#### Scenario: 关闭冷启动不动风控缩放语义

- **WHEN** 冷启动关闭（默认）且账号为 `warned` 或 `restricted`
- **THEN** `warned` 的缩放与 `restricted` 的互动清零仍照常作用于安全限额基准，账号威胁态单写不变量不受影响；MUST NOT 因关闭冷启动而放宽被限账号的互动闸

#### Scenario: 慢启动不进风控单写链

- **WHEN** 某账号的慢启动被开启或关闭
- **THEN** 其 `risk_state` 的 `status` 与 `quotaLevel` MUST 逐位不变，MUST NOT 触发任何风控状态迁移或持久化写

### Requirement: 慢启动状态投影必须与实际 clamp 同源同格

云端对外投影的慢启动状态（下发客户端的 `state` / `day` / `binding`）与 `applyColdStartClamp` 实际采用的天数 MUST 由**同一个 anchor 解析函数**与**同一次时钟读取**得出，MUST NOT 各自独立计算。任何「投影说第 7 天、clamp 已按第 8 天放行」的错位 MUST 不可能出现。

`binding` SHALL 如实表达「本次 clamp 是否至少收紧了一项配额」：当曲线天花板在所有窗口所有动作上均不严于风控缩放后的档位配额时，`binding` MUST 为 false。投影 MUST NOT 在 `binding` 为 false 时宣称配额已被压低。

#### Scenario: 投影天数与 clamp 天数逐格相等

- **WHEN** 某账号开启慢启动、处于第 1 至第 8 天中任一天
- **THEN** 投影的 `day` 与该次 `effectiveQuotas()` 内 clamp 采用的天数 MUST 相等
- **AND** 第 8 天时投影 MUST 为毕业态且 clamp MUST 放行，两者同时发生

#### Scenario: 曲线不比档位更严时如实标注

- **WHEN** 某小红书账号处于 conservative 档、开启慢启动且处于第 5 至 7 天，此时曲线上界在 view / like / comment / publish 上均不低于该档位配额
- **THEN** `binding` MUST 为 false
- **AND** 投影 MUST NOT 表述为「配额已被压低」

### Requirement: 慢启动起点写入时对齐运营自然日

写入 `slow_start_since` 时 MUST 将其对齐到该时刻所属运营自然日（上海时区）的起点，使勾选当天整天计为第 1 天。天数递进与「今日进展」计数窗口 MUST 同相，MUST NOT 出现「上限已按新的一天放开、而当日计数尚未清零」的窗口。

#### Scenario: 深夜勾选不在次日夜间跳档

- **WHEN** 运营于某日 23:50 开启某账号慢启动
- **THEN** `slow_start_since` 存为该日 00:00（上海时区）
- **AND** 次日 23:51 该账号仍处于第 2 天（自次日 00:00 起即为第 2 天），MUST NOT 在当日计数未清零时把上限抬到下一天的天花板

#### Scenario: 天数换档与计数清零同时发生

- **WHEN** 某开启慢启动的账号跨过运营自然日边界
- **THEN** 其 `day` 递增与当日计数窗口清零 MUST 发生在同一时刻

### Requirement: 浏览会话启动时 MUST 现问一次 view 配额，被拒即当场休眠

浏览会话的每一次(重)启动，云端 MUST 在派发首个浏览事件**之前**向该账号的权威风控账本现问一次 `view` 配额，被拒即**当场进入浏览额度休眠**，MUST NOT 等到 `open_note` 前那道闸才发现。

本要求是既有要求「临时 view 配额不阻止会话启动」的**补充而非推翻**：会话照常启动、照常保持，只是刹车提前踩死。两者对 `quota:minute` / `quota:hour` 的净行为一致（睡满即自动重驱）；差别只在 `quota:day` —— 睡到次日却仍要先开一次浏览器、扫一屏卡、跑两次模型才发现，是纯空转。

**现问 MUST 是无状态重算，MUST NOT 依赖跨连接保存的休眠标记副本。** 权威配额账本按账号持久且跨连接共用；休眠标记是每连接重建的纯派生量。以副本驱动行为 = 权威事实与派生状态漂移。

🔴 **红线一：MUST NOT 因 view 配额拒绝启动会话。** 被拒的正确反应是**休眠**，不是 `session.end`、不是拒签。此为既有要求「view 配额已满时不打开下一篇笔记」的反向不变量，一刀切的「会话级配额闸」会当场破坏它。

🔴 **红线二：现问 MUST 落在会话(重)启动的统一收口，MUST NOT 只补在重连一条路径上。** 该收口覆盖四个入口（边缘 hello / 绑人设自启 / 续场 / 面板手动）；只补重连 = 另外三个入口照旧空转。

🔴 **红线三：刹车 MUST 先于首个浏览事件的派发装上。** 事件派发是进程内同步的，下游角色链可能在该次派发内即走到命令下发口。装在派发之后 ⇒ 首批命令从刹车底下漏出，且为间歇性、测试可全绿。

「清掉旧场的陈旧休眠」与「按最新事实重新装上休眠」MUST 并存且**先清后问**：清是为同连接内的重启路径（对象未重建、标记可能陈旧），问是为全部路径。MUST NOT 以「不要清」替代「重新问」——重连路径上调度组件整体重建，标记出生即为假，「不要清」没有作用对象、是零效果补丁。

#### Scenario: 日额度耗尽的账号重连后不再唤醒浏览器
- **WHEN** 某账号 `view` 的日窗口已耗尽，其边缘已让位（浏览器关闭、云端连接保留），随后边缘重连并触发会话重启
- **THEN** 云端 MUST 在派发首个浏览事件前判定该账号无 view 额度并当场进入浏览额度休眠
- **AND** 云端 MUST NOT 下发任何非豁免浏览命令（含空闲看门狗的推进指令）
- **AND** 该边缘的浏览器 MUST 保持停放，直至休眠窗口释放

#### Scenario: 分钟窗临时耗尽时会话照开、短睡后自动重驱
- **WHEN** 某账号 `view` 仅因 `quota:minute` 临时耗尽，此时会话(重)启动
- **THEN** 云端 MUST 启动会话并当场进入浏览额度休眠
- **AND** 云端 MUST NOT 结束会话
- **AND** 休眠 MUST 按权威账本返回的重试时长安排，到期重判通过后自动下发一次恢复浏览的推进指令

#### Scenario: 红线——配额被拒不得拒签会话
- **WHEN** 会话启动时 `view` 配额被拒（任一窗口）
- **THEN** 会话 MUST 仍被启动并保持活跃
- **AND** 云端 MUST NOT 因此下发 `session.end`，MUST NOT 阻断手动或定时的笔记创作、发布、手动评论

#### Scenario: 同连接内续场时先清陈旧休眠再按最新事实重判
- **WHEN** 同一连接内的会话重启（续场 / 面板手动 / 绑人设自启），且该调度组件上残留着上一场装的休眠标记
- **THEN** 云端 MUST 先清除该陈旧标记，再向权威账本现问一次并据最新结果决定是否重新装上休眠
- **AND** 若权威账本此时判定额度可用，会话 MUST 正常开跑（陈旧标记 MUST NOT 把新场压住）

### Requirement: 浏览额度休眠期扣下的命令 MUST 留下可观测记录

浏览额度休眠期在命令下发统一出口被扣下的每一类命令，云端 MUST 打印可观测记录（至少含账号、动作、扣下原因），MUST NOT 静默丢弃。

记录 MUST 节流：日窗休眠可长达数小时，其间存活探针会周期性产生被扣命令，逐条打印会按车队规模放大成日志洪水。节流 MUST NOT 退化为「不打」——**宁可少打，不可不打**。

本要求是「MUST NOT 静默假成功 / 静默丢弃」红线在本闸上的落点：该出口的其他抑制支（评论支线在途、评论迁移在途）均已打印，唯独浏览额度休眠支为裸丢弃；当该支从边角路径升为主刹车后，不补记录等于把静默丢弃从偶发扶正为常态。

#### Scenario: 休眠期扣下推进指令时留下记录
- **WHEN** 账号处于浏览额度休眠，存活探针产生一条推进指令并抵达命令下发统一出口
- **THEN** 该指令 MUST 被扣下（不下发）
- **AND** 云端 MUST 留下一条含账号、动作与「浏览额度休眠」原因的记录

#### Scenario: 长休眠期的记录不得逐条打印
- **WHEN** 账号处于长达数小时的日窗浏览额度休眠，其间被扣命令反复产生
- **THEN** 记录 MUST 被节流
- **AND** 该轮休眠 MUST 至少留下一条可定位到账号与原因的记录

### Requirement: 视频号入站回复的风险状态与数量准入必须解耦

视频号平台已确认的评论/私信回复 SHALL 继续作为真实动作事实记录，最终风险状态仍 SHALL 仅由 Cloud `RiskController` 单写。发送前对 `RiskController` 的读取 SHALL 保留风险状态和未知拒因的 fail-closed 语义，但 MUST NOT 使用通用 `comment`/`dm_reply` 的 `quota:*` 结果重复限制 interaction 域已经独立计数的回复数量。记录动作返回的通用 quota 内/外结果 MUST NOT 被呈现为视频号专用策略结论。

#### Scenario: 平台确认后记账但不恢复重复数量闸
- **WHEN** 视频号回复获得平台确认
- **THEN** Cloud 恰好一次记录该真实动作事实
- **AND** 后续视频号数量准入仍只读取 interaction 专用限速

### Requirement: 搜索按既成平台事实接入账号风险单写路径

`search` SHALL 是 `RiskAction` 的完整成员，受 `RiskController.explain/canDo/record`、分钟/小时滑动窗口、Asia/Shanghai 自然日窗口、配额配置、风控状态缩放与可选慢启动控制。搜索下发前 SHALL 由 Cloud 权威 `RiskController` 预闸；Edge 证明 `actuated=true` 后，回执 SHALL 无条件驱动同一控制器记录事实，MUST NOT 在回执阶段二次 `canDo` 后丢弃证据。Cloud `RiskController` 仍是最终账号风险状态和计数的单写者。

#### Scenario: 搜索预闸阻止尚未发生的动作

- **WHEN** 自治搜索意图产生，但该账号 `search` 的任一配额窗口已饱和
- **THEN** Cloud 不下发搜索命令，并回报/记录具体配额拒因

#### Scenario: 已发生搜索不因配额到顶而丢证据

- **WHEN** Edge 回报一次 `actuated=true` 的搜索，而该账号回执时 search 配额已饱和
- **THEN** `RiskController.record('search')` 仍把该事实写入计数，后续预闸据此拒绝更多搜索

#### Scenario: 操作员搜索绕过权限闸但仍计数

- **WHEN** 操作员明确授权一次搜索，产品规则允许其绕过自动配额预闸，且 Edge 证明平台动作已发生
- **THEN** 该搜索照常记入账号 search 计数；“操作员全权”MUST NOT 被解释为免记事实

### Requirement: 搜索配额参与配置、投影与慢启动全量映射

`RISK_ACTIONS` 的所有穷举映射 SHALL 包含 search，包括三档 daily 默认、minute/hour burst、`quota_config` 读写与校验、effective quota、daily usage、dashboard action totals、慢启动区间、restricted/frozen 清零和 PG action 约束。任一配额提供者缺值或非法 SHALL 回落 search 代码默认，MUST NOT 抛错或静默放开。

#### Scenario: 配额热更新立即影响搜索预闸

- **WHEN** 运营通过既有配额配置端点修改某档位 search 的 daily/minute/hour 数值
- **THEN** 对应账号后续 `RiskController.canDo('search')` 现读新值，无需进程重启

#### Scenario: PG 可持久保存 search 事实

- **WHEN** Cloud 记录一次已执行搜索
- **THEN** `risk_counters` 的 action 约束接受 `search`，今日聚合与窗口查询可读到该事实

### Requirement: 账号风险状态的写入者在任一时刻全局唯一

The system SHALL 保证：对任一 `accountId`、任一时刻，`risk_state` 的写入者唯一。「唯一」的判据 MUST 是**跨进程**的，MUST NOT 只在单进程内成立。

该不变量由三条机制共同保证，三条都是 MUST：

1. **每 target 单实例**：承载风控写路径的自动化进程对每个 `executionTarget` MUST 单实例，并 MUST 在启动时以数据库层的互斥手段（会话级 advisory lock，键含 `executionTarget`）取得「自动化写者锁」。取不到锁 MUST 在有界等待后拒绝启用风控写路径并告警，MUST NOT 降级为无锁继续写。持锁连接断开即视为写权丢失，MUST 停止下发新的互动命令并告警，MUST NOT 静默继续写 `risk_state`。
2. **账号归属唯一**：每个账号在任一时刻 MUST 只归属一个 `executionTarget`（见 `same-account-parallel-safety`）。
3. **条件写 + 诚实拒绝**：`risk_state` 的每一次写 MUST 带属主谓词（写方的 `executionTarget` 必须等于该账号的归属 target），影响行数为 0 时 MUST 作为显式失败上报，MUST NOT 返回成功、MUST NOT 重试覆盖、MUST NOT 通过放宽谓词绕过。

写失败为「非属主」时，该进程 MUST 驱逐本地缓存的该账号控制器并告警；下次解析该账号 MUST 从库重新加载状态与计数。

`risk_counters` 属于 append-only 的既成事实账本，MUST NOT 加属主谓词、MUST NOT 按 `executionTarget` 分裂成多份。同一账号的当日额度 MUST 只有一份：归属变更前后飞在半路的回执 MUST 记进同一本账，MUST NOT 因换了写入进程而各算一份。

#### Scenario: 同一 target 的第二个实例拒绝启动

- **WHEN** 某 `executionTarget` 已有一个自动化进程持有写者锁，运维以滚动或蓝绿方式启动第二个同 target 实例
- **THEN** 第二个实例在有界等待后取不到写者锁，MUST 拒绝启用风控写路径并以非零码退出，MUST 产生指明「另一实例正持锁」的告警
- **AND** 它 MUST NOT 以无锁方式启动风控写路径或 outbox apply

#### Scenario: 非属主进程的状态写被数据库拒绝

- **WHEN** 某账号归属 `ol`，而 `dev` 的进程（例如经面板首页汇总物化的陈旧控制器）尝试写该账号的 `risk_state`
- **THEN** 该写的影响行数为 0，MUST 作为 `risk_state_not_owned` 显式失败上报，附带真实归属 target
- **AND** 该账号刚被 `ol` 写下的 `restricted` MUST 保持不变，MUST NOT 被陈旧的 `normal` 覆盖

#### Scenario: 拒绝后驱逐缓存而不是重试

- **WHEN** 一次状态写因非属主被拒
- **THEN** 该进程 MUST 从控制器缓存中移除该账号并告警
- **AND** MUST NOT 重试同一次写，MUST NOT 在移除后立刻用同一份陈旧内存状态重建控制器

#### Scenario: 归属变更不清零也不翻倍当日额度

- **WHEN** 某账号当日已在 `dev` 上完成 N 次点赞，随后归属被显式改为 `ol`
- **THEN** `ol` 上该账号当日点赞计数 MUST 包含这 N 次
- **AND** MUST NOT 出现「换 target 后当日额度从零开始」或「两个 target 各得一份完整额度」

### Requirement: 配额判定依据的计数必须与库内事实一致

配额准入判定所依据的计数 SHALL 与 `risk_counters` 的库内事实一致。系统 MUST 具备检出二者偏差的机制，MUST NOT 让「内存计数只在控制器创建时回放一次、此后只累加本进程自己写的那些」这一事实成为不可观测的默认状态。

具体要求：

- 控制器建立时 MUST 从库回放当日窗口计数；账号归属被本实例占位成功、或归属变更后重新解析控制器时，MUST 强制重放，MUST NOT 复用可能陈旧的内存值。
- 系统 MUST 周期性地把内存计数与库内当日总量对账。判据 MUST 是「偏差是否为零」，MUST NOT 引入容忍阈值。
- 偏差非零 MUST 告警（含 accountId、动作、内存值、库值）并以库为准重建该账号计数，MUST NOT 静默沿用偏差计数继续做准入判定。

#### Scenario: 外部写入的计数行被对账检出

- **WHEN** 某账号的 `risk_counters` 中出现一行不是由本进程内存计数产生的当日记录
- **THEN** 下一次对账 MUST 检出偏差并告警
- **AND** 该账号的内存计数 MUST 被以库为准重建，重建后与库内当日总量逐项相等

#### Scenario: 归属占位后强制重放

- **WHEN** 某账号首次在本 target 上握手成功并被本实例占位归属
- **THEN** 该账号的计数 MUST 从库重放一次
- **AND** MUST NOT 直接使用握手前可能已存在的内存计数

#### Scenario: 对账不放宽到阈值

- **WHEN** 内存计数与库内当日总量相差 1
- **THEN** 系统 MUST 按偏差处理（告警 + 重建）
- **AND** MUST NOT 因差值小而判为一致

### Requirement: 边缘确认的真实动作必须先落持久 outbox 再推进

云端 SHALL 在收到边缘对真实平台动作的确认回执后，**先把该既成事实同步提交进一张带 `execution_target` 的持久 outbox 表，再推进浏览闭环**。该路径 MUST NOT 依赖进程内事件总线上的 fire-and-forget 异步写，MUST NOT 以「异常只记日志」的方式吞掉记账失败。

具体要求：

- outbox 行 MUST 带 `execution_target`（服务端注入），worker MUST 只认领本 target 的行；MUST 带去重键，边缘重发同一回执信封 MUST 只产生一行。
- 认领 MUST 使用认领令牌 + 租约 + 跳锁，并 MUST 在进程启动时回收租约过期的在途行——与委托任务 worker 同一范式。
- apply MUST 在单个数据库事务内同时完成「写入计数」与「标记 outbox 行已应用」，且 MUST 由数据库唯一约束保证 exactly-once，MUST NOT 用进程内集合去重。
- 内存计数 MUST 只在 apply 成功时递增，且 MUST 只有这一条递增路径（回执处理时 MUST NOT 先加一次）。
- 入队失败 MUST 视为本次记账失败：MUST 告警，并 MUST 使该账号停止继续下发自动互动命令，MUST NOT 当作无事发生继续浏览闭环。
- 重试 MUST 有界；超限 MUST 转入死信并告警，MUST NOT 静默丢弃。outbox 积压量与死信量 MUST 可被读取。

#### Scenario: 崩在回执与记账之间不丢账

- **WHEN** 边缘确认了一次真实点赞，云端提交了 outbox 行，随后进程在 apply 之前崩溃并重启
- **THEN** 重启后该行被回收并 apply，该次点赞 MUST 出现在计数里
- **AND** 该次点赞 MUST 只被计入一次

#### Scenario: 重复投递只记一次

- **WHEN** 边缘因重连重发了同一条动作确认信封
- **THEN** outbox MUST 只保留一行，计数 MUST 只增加一次

#### Scenario: 入队失败不静默继续

- **WHEN** 一次真实动作已被边缘确认，但 outbox 入队因数据库不可写而失败
- **THEN** 系统 MUST 告警并停止对该账号继续下发自动互动命令
- **AND** MUST NOT 把这次已发生的动作当作不存在而继续浏览闭环

#### Scenario: 超限进死信且可见

- **WHEN** 某条 outbox 行的 apply 连续失败达到重试上限
- **THEN** 该行 MUST 转入死信状态并产生告警
- **AND** 死信数量 MUST 可被读取，MUST NOT 被静默删除

#### Scenario: 记账不改变判定语义

- **WHEN** 一次动作的回执抵达时该账号配额已耗尽
- **THEN** 该动作 MUST 照常入队并最终计入（既成事实照记，与既有「绝不因策略事后重判而丢弃」一致）
- **AND** 节奏饱和告警所依据的判定 MUST 仍取自写入前的判定值，MUST NOT 改为读取含这一笔的新状态

