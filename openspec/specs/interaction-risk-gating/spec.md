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

云端的安全限额**数字**（每账号每动作的滑动窗配额）SHALL 为可配置、可在管理后台按风控档位（conservative / normal / aggressive）编辑，且**每日上限与分钟 / 小时突发上限都 SHALL 独立可编辑**（突发上限 MUST NOT 仅由每日值派生）。云端 SHALL 把这些数字落库（新增 `quota_config` 表，迁移 `0010`，主键 `(tier, action)`，含 `daily` / `per_minute` / `per_hour` 三列）并维护内存镜像；`RiskController.canDo(action)` 经 `effectiveQuotas()` MUST **每次现读**当前生效数字（经注入的配额提供者读内存镜像），使管理后台改完即热加载生效、MUST NOT 需要重启进程。

绝不 brick（never-brick）：当配额提供者缺失、某 `(tier, action)` 缺行、或字段非有限非负整数时，`effectiveQuotas()` MUST 回落到代码写死默认（`quotas.ts` 的 `DAILY_QUOTAS` / `MINUTE_BURST_CAP` / `HOUR_BURST_CAP`），MUST NOT 抛错、MUST NOT 让风控闸失效。配额表为空（如迁移刚跑完）时行为 MUST 与现状逐位一致（零回归）。`warned` / `restricted` / `frozen` 状态对基准三档的缩放 / 清零语义 MUST 保持不变，只是基准三档数字来源改为提供者（缺值回落写死默认）。

#### Scenario: 后台改某档某动作每日上限，下一次 canDo 即按新值

- **WHEN** 管理后台把 `normal` 档 `comment_like` 的每日上限从 6 改为 4 并保存成功
- **THEN** 无需重启，该账号下一次 `canDo('comment_like')` 的每日窗判定按 4 生效（命中即热加载）

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

`RiskController.record(action)` 因**滑动窗速率配额**耗尽而被 `canDo` 拒时 MUST 只返回 `false`（背压），MUST NOT 触发任何风控状态迁移——具体地：MUST NOT `applySignal`、MUST NOT 递增 `signal_count`、MUST NOT 刷新 `last_signal_at`、MUST NOT 把账号从 `normal` 推向 `warned` / `restricted`。`quota_exceeded` MUST NOT 作为风控信号种类存在于状态机升级逻辑与 `RiskSignalKind` 中。

此要求**强化**「被禁账号 `record` 返回 false（绝不自残）」既有红线：返 false 不变，只去掉「撞自己配额还自升状态」的自残副作用。

#### Scenario: 配额到顶被拒不升级风控态

- **WHEN** 某 `normal` 账号的某动作在任一滑动窗（分钟 / 小时 / 天）配额耗尽，`record(action)` 被调用
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

