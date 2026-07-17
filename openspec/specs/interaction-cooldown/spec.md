# interaction-cooldown Specification

## Purpose
TBD - created by archiving change engagement-restraint. Update Purpose after archive.
## Requirements
### Requirement: 每动作类型按账号的最小间隔冷却（云端、内存）

云端 SHALL 维护一道**按账号、按动作类型**的最小间隔冷却闸，覆盖 `like` / `collect` / `follow` / `comment` 四个真实互动，固定最小间隔为 like=2 分钟、collect=5 分钟、follow=10 分钟、comment=30 分钟。冷却判定 MUST 全部在云端进行（边缘不持有任何冷却策略）；冷却记录 MAY 为进程内内存态（无需持久化、无需迁移、不经协议下发）。同一账号的不同动作类型 MUST 各自独立计时；不同账号之间 MUST 互不影响。某动作类型若未配置冷却时长，MUST 视为不冷却（放行）。

唯一例外：详情语义确认命中的账号结构化 `mandatory_interactions` 规则所列 `like` / `comment` SHALL 跳过对应动作冷却，因为该规则是运营员对指定内容类别的显式确定性动作授权；例外 MUST 只随本篇 typed mandatory context 生效，MUST NOT 按账号名、自由文本或全局开关扩散。强制互动仍受 `RiskController` 硬闸与真实成功回执约束。

#### Scenario: 同一动作两次之间未到间隔被抑制
- **WHEN** 某账号刚成功 `like` 后不到 2 分钟，角色又对另一篇普通笔记产出 `like` 意图，且该笔记未命中结构化强制规则
- **THEN** 冷却闸判定未到点，该 `like` MUST 被抑制（见「诚实抑制」需求）

#### Scenario: 规则命中动作跳过冷却
- **WHEN** 某帖全文确认命中该账号结构化规则中的 `like + comment`，而 like / comment 均仍在普通冷却窗内
- **THEN** 本帖两个强制动作均不被冷却否决；规则上下文之外的其它帖子仍照常冷却

#### Scenario: 到间隔后放行
- **WHEN** 某账号上次成功 `follow` 已过 10 分钟，角色再次产出 `follow` 意图
- **THEN** 冷却闸放行，该 `follow` 正常进入后续下发

#### Scenario: 动作类型之间互不冷却
- **WHEN** 某账号刚成功 `like`（like 处于冷却中），随后对同篇或他篇产出 `collect` / `follow` / `comment` 意图
- **THEN** like 的冷却 MUST NOT 抑制 collect / follow / comment（各类型独立计时）

#### Scenario: 账号之间互不影响
- **WHEN** 账号 A 的 `like` 处于冷却中，账号 B 产出 `like` 意图
- **THEN** 账号 B 的 `like` MUST NOT 因账号 A 的冷却被抑制

### Requirement: 未到冷却点的互动诚实抑制——不下发、不计数、不假成功

当冷却闸判定某互动未到点时，系统 MUST 诚实跳过：MUST NOT 下发该互动指令、MUST NOT 扣减每会话预算、MUST NOT 触发风控计数、MUST NOT 以任何方式记录/上报为成功互动。被抑制 MUST 以可观测的中性原因（如 `cooldown`）记录，便于区分「按冷却跳过」与「找不到目标 / 被风控拒」，且日志 MUST NOT 写成「失败」。该语义为红线「MUST NOT 静默假成功」的延伸。

#### Scenario: 被冷却抑制不下发不扣预算

- **WHEN** 某 `collect` 意图被冷却闸判定未到点
- **THEN** 系统 MUST NOT 下发 `interaction.collect`、MUST NOT 扣减 collect 预算、MUST NOT 计数，并以原因 `cooldown` 如实记录

#### Scenario: 红线反例——被冷却却假报成功（禁止）

- **WHEN** 有实现在冷却未到点时仍记一次成功互动 / 仍扣预算 / 仍下发指令
- **THEN** MUST 视为违规、不予合入；被冷却抑制 MUST 等价于一次诚实跳过

### Requirement: 冷却时间戳在真实成功时落、follow 排除 already_followed

冷却时间戳 SHALL 在**互动真实发生**时落，而非在下发时落——与「计数挂真回执」同一时机：仅当边缘真回执 `action.completed{ok:true}`（评论同理 `ok:true`）驱动该动作记账时，才更新该账号该动作的冷却时间戳。`follow` 的 `already_followed` 良性 no-op MUST NOT 重置 follow 冷却（与「no-op 不烧配额」同口径）。下发后失败（找不到目标 / 验证码 / 未生效）MUST NOT 落冷却时间戳（一次失败不应白占一个冷却窗）。

#### Scenario: 仅真实成功才起算冷却

- **WHEN** 某 `like` 下发后边缘回执 `ok:true`
- **THEN** 该账号 like 的冷却时间戳更新，后续 2 分钟内的 like 被抑制

#### Scenario: 下发失败不起算冷却

- **WHEN** 某 `follow` 下发后边缘回执 `ok:false`（如 `no_target` / `blocked_by_captcha`）
- **THEN** 该账号 follow 的冷却时间戳 MUST NOT 更新（下次 follow 不因这次失败被冷却）

#### Scenario: already_followed 不重置冷却

- **WHEN** 某 `follow` 回执 `ok:true, reason:'already_followed'`
- **THEN** follow 冷却时间戳 MUST NOT 更新（良性 no-op 不算一次真关注）

### Requirement: 冷却闸只拦四类互动、不拦推进、不写风控终态

冷却闸 SHALL 只作用于 `interaction.like` / `interaction.collect` / `interaction.follow` / `interaction.comment` 的下发判定；`page.scroll` / `navigation.back` / `note.open` / `profile.open` 等推进 / 导航指令 MUST NOT 被冷却闸拦截（避免浏览循环死锁，与既有「推进指令不被风控闸拦」同口径）。冷却闸为**附加只读节奏闸**：MUST NOT 写 `risk_state`、MUST NOT 调用 `RiskController.setQuotaLevel` / `applySignal`、MUST NOT 改变账号风控终态或档位；账号风控终态仍仅由 `RiskController` 单写。

#### Scenario: 推进指令不被冷却拦

- **WHEN** 某账号多个互动类型都处于冷却中
- **THEN** `page.scroll` / `navigation.back` / `note.open` / `profile.open` 仍正常下发，浏览循环继续，不死锁

#### Scenario: 冷却不触碰风控终态

- **WHEN** 冷却闸抑制了一次互动
- **THEN** 该账号 `risk_state`（status 与 quotaLevel）MUST NOT 被改写，`setQuotaLevel` / `applySignal` MUST NOT 被调用

### Requirement: 评论冷却前置到评估阶段、避免白走人审

普通评论（comment）的冷却 SHALL 在**评论评估阶段**（`CommentAppraiser`，与数量闸 / 热度阈值同处的最便宜阶段）就判定：未到 comment 冷却点 MUST emit `comment.skipped{reason:'cooldown'}` 直接进「是否进主页评估」，MUST NOT 进入撰写 / 去 AI 味 / 飞书人审（避免页面久留 + 占用人工却最终被抑制）。

详情确认命中的结构化 mandatory comment 是唯一例外：`CommentAppraiser` MUST 识别随事件透传的规则上下文并跳过评论冷却；该例外 MUST NOT 影响未命中规则的普通评论。

#### Scenario: 普通评论冷却中在评估阶段即跳过
- **WHEN** 某账号上次成功评论不足 30 分钟，又在一篇未命中强制规则的笔记上进入评论评估
- **THEN** `CommentAppraiser` MUST emit `comment.skipped{reason:'cooldown'}`，不付撰写 / 人审成本，直接进「是否进主页评估」

#### Scenario: 强制评论不被普通冷却否决
- **WHEN** 本篇评论带有全文确认的 mandatory context 且规则 actions 含 comment
- **THEN** `CommentAppraiser` 跳过冷却并继续强制评论支线；其它安全闸与真实回执要求不变

