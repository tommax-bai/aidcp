# interaction-cooldown Specification

## Purpose

定义**动作冷却闸**的定位与边界：它是**兜底**，不是数量闸。

系统里有两套东西在管「一个账号能做多少互动」，本能力的存在理由就是把它们分清：

- **主闸 ＝ 风控配额**（`RiskController`：面板可配、热加载、三档、联动风控状态、PG 持久化）——**单独负责数量**。天花板 100% 由它决定。
- **兜底 ＝ 本能力**——只防**意外**爆发：同秒重入、同账号并行会话（N:1）同刻双发、重启后首发。这是主闸干不了的活：配额只数数量、不管间距，单场预算又是每会话各一份；冷却是唯一给出「最小间距」的机制。平时它应当完全隐形，只在异常里说话。

**本能力的宪法：兜底必须比主闸松**（逐动作 / 逐档位 / 逐窗口，`c ≤ L_W ÷ q_W`）。等价的运营口径是**主闸的每一个旋钮都必须真的能拧动**——冷却若在某窗口比主闸紧，那个旋钮就被焊死了：面板改了数字行为却纹丝不动，且**无日志、无告警**。

该定位是 change `cooldown-as-backstop-not-quota`（2026-07-17）对源 change `engagement-restraint` 原意（「压稀节奏、延缓配额触顶」）的**改判**。改判前四个动作全部违反上述不变量（`comment` 的 30 分钟冷却最大速率恰＝小时配额 2/h，把该旋钮焊死）。**本 Purpose 自归档日起逐字停留在 `TBD` 达数月——冷却在规范层面从未被定义过它是干什么的，这正是它漂移成主闸的制度原因。**
## Requirements
### Requirement: 每动作类型按账号的最小间隔冷却（云端、内存）

**定位（本要求的存在理由）**：冷却闸是**兜底**，只防**意外**爆发——同秒重入、同账号并行会话同刻双发、重启后首发。它 MUST NOT 表达任何数量策略。「一个账号能做多少互动」由**主闸**（`RiskController` 的风控配额：面板可配、热加载、三档、联动风控状态、PG 持久化）**单独负责**。

**不变量（兜底必须比主闸松）**：对每个受冷却约束的动作、每个可达档位、每个窗口 W（分钟 / 小时 / 日），冷却值 `c` MUST ≤ `L_W ÷ q_W`（`L_W` 为窗口长度，`q_W` 为该窗口配额）。取等合格：冷却取等放行、配额为半开窗且 `count >= quota` 才拒 ⇒ 以 `c = L_W / q_W` 等间隔跑时窗内恒为 `q_W - 1 < q_W`，该窗口配额可无限跑满、不被削。

**等价的运营口径**：**主闸的每一个旋钮都必须真的能拧动。** 冷却若在窗口 W 上比主闸紧，那个旋钮就被焊死了——面板改了它行为却不变，且无日志、无告警。

云端 SHALL 维护一道**按账号、按动作类型**的最小间隔冷却闸，覆盖 `like` / `collect` / `follow` / `comment` 四个真实互动。冷却判定 MUST 全部在云端进行（边缘不持有任何冷却策略）；冷却记录 MAY 为进程内内存态（无需持久化、无需迁移、不经协议下发）。同一账号的不同动作类型 MUST 各自独立计时；不同账号之间 MUST 互不影响。某动作类型若未配置冷却时长，MUST 视为不冷却（放行）。

**当前取值：四动作统一 15 秒。** 该数值 MUST 被理解为上述不变量的**派生结果**，而非独立事实：`15s = 60s ÷ max(四动作的分钟爆发上限) = 60 ÷ 4`（`like`）——即「不焊死任何旋钮」的**最大**统一值。变更该值时 MUST 重新验算不变量，MUST NOT 将其当作可自由调整的策略旋钮。

唯一例外：详情语义确认命中的账号结构化 `mandatory_interactions` 规则所列 `like` / `comment` SHALL 跳过对应动作冷却。**理由**：冷却被拦时是丢弃而非排队（见「诚实抑制」需求），而 mandatory 是运营对指定内容类别的显式授权、且为每帖一次性机会——兜底 MUST NOT destroy 一次已授权的机会。例外 MUST 只随本篇 typed mandatory context 生效，MUST NOT 按账号名、自由文本或全局开关扩散。强制互动仍受 `RiskController` 硬闸与真实成功回执约束（例外只跳过兜底，MUST NOT 跳过主闸）。

#### Scenario: 同一动作两次之间未到间隔被抑制
- **WHEN** 某账号刚成功 `like` 后仍在该动作冷却窗内，角色又对另一篇普通笔记产出 `like` 意图，且该笔记未命中结构化强制规则
- **THEN** 冷却闸判定未到点，该 `like` MUST 被抑制（见「诚实抑制」需求）

#### Scenario: 规则命中动作跳过冷却
- **WHEN** 某帖全文确认命中该账号结构化规则中的 `like + comment`，而 like / comment 均仍在普通冷却窗内
- **THEN** 本帖两个强制动作均不被冷却否决；规则上下文之外的其它帖子仍照常冷却
- **AND** 两个强制动作仍 MUST 各自通过 `RiskController` 主闸

#### Scenario: 到间隔后放行
- **WHEN** 某账号上次成功 `follow` 已过该动作冷却窗，角色再次产出 `follow` 意图
- **THEN** 冷却闸放行，该 `follow` 正常进入后续下发

#### Scenario: 动作类型之间互不冷却
- **WHEN** 某账号刚成功 `like`（like 处于冷却中），随后对同篇或他篇产出 `collect` / `follow` / `comment` 意图
- **THEN** like 的冷却 MUST NOT 抑制 collect / follow / comment（各类型独立计时）

#### Scenario: 账号之间互不影响
- **WHEN** 账号 A 的 `like` 处于冷却中，账号 B 产出 `like` 意图
- **THEN** 账号 B 的 `like` MUST NOT 因账号 A 的冷却被抑制

#### Scenario: 冷却值削掉主闸窗口配额即为违规
- **WHEN** 某动作的冷却值 `c` 使某窗口 W 的配额不可达（等价地 `c > L_W / q_W`）
- **THEN** 该取值 MUST 视为违反本要求、不予合入——因为它把主闸在该窗口的旋钮焊死了

### Requirement: 未到冷却点的互动诚实抑制——不下发、不计数、不假成功

当冷却闸判定某互动未到点时，系统 MUST 诚实跳过：MUST NOT 下发该互动指令、MUST NOT 扣减每会话预算、MUST NOT 触发风控计数、MUST NOT 以任何方式记录/上报为成功互动。被抑制 MUST 以可观测的中性原因（如 `cooldown`）记录，便于区分「按冷却跳过」与「找不到目标 / 被风控拒」，且日志 MUST NOT 写成「失败」。该语义为红线「MUST NOT 静默假成功」的延伸。

**丢弃语义的条件式不变量**：冷却抑制**直接丢弃该次意图、不排队、不补发**。这是可接受代价，**当且仅当**冷却取值可证明不削主闸的任一窗口配额（见上一要求的不变量）。若某次变更使冷却在任一窗口成为 binding 者，则「丢弃而不排队」将**永久吃掉合法互动意图**、使面板配额无法被逼近——该变更 MUST 被视为违规，或 MUST 同批把丢弃改为排队。

#### Scenario: 被冷却抑制不下发不扣预算

- **WHEN** 某 `collect` 意图被冷却闸判定未到点
- **THEN** 系统 MUST NOT 下发 `xiaohongshu.note.collect`、MUST NOT 扣减 collect 预算、MUST NOT 计数，并以原因 `cooldown` 如实记录

#### Scenario: 红线反例——被冷却却假报成功（禁止）

- **WHEN** 有实现在冷却未到点时仍记一次成功互动 / 仍扣预算 / 仍下发指令
- **THEN** MUST 视为违规、不予合入；被冷却抑制 MUST 等价于一次诚实跳过

#### Scenario: 冷却成为 binding 者时丢弃语义即不再可接受

- **WHEN** 某次变更把某动作的冷却调大到在任一窗口比主闸紧（即削掉了该窗口的配额）
- **THEN** MUST 视为违规、不予合入——因为「丢弃不排队」会把合法互动意图永久吃掉，使面板配额无法被逼近，且无日志无告警

### Requirement: 冷却时间戳在真实成功时落、follow 排除 already_followed

冷却时间戳 SHALL 在**互动真实发生**时落，而非在下发时落——与「计数挂真回执」同一时机：仅当边缘真回执 `action.completed{ok:true}`（评论同理 `ok:true`）驱动该动作记账时，才更新该账号该动作的冷却时间戳。`follow` 的 `already_followed` 良性 no-op MUST NOT 重置 follow 冷却（与「no-op 不烧配额」同口径）。下发后失败（找不到目标 / 验证码 / 未生效）MUST NOT 落冷却时间戳（一次失败不应白占一个冷却窗）。

#### Scenario: 仅真实成功才起算冷却

- **WHEN** 某 `like` 下发后边缘回执 `ok:true`
- **THEN** 该账号 like 的冷却时间戳更新，后续该动作冷却窗内的 like 被抑制

#### Scenario: 下发失败不起算冷却

- **WHEN** 某 `follow` 下发后边缘回执 `ok:false`（如 `no_target` / `blocked_by_captcha`）
- **THEN** 该账号 follow 的冷却时间戳 MUST NOT 更新（下次 follow 不因这次失败被冷却）

#### Scenario: already_followed 不重置冷却

- **WHEN** 某 `follow` 回执 `ok:true, reason:'already_followed'`
- **THEN** follow 冷却时间戳 MUST NOT 更新（良性 no-op 不算一次真关注）

### Requirement: 冷却闸只拦四类互动、不拦推进、不写风控终态

冷却闸 SHALL 只作用于 `{platform}.note.like` / `xiaohongshu.note.collect` / `{platform}.user.follow` / `{platform}.note.comment` 的下发判定；`{platform}.feed.scroll` / `navigation.back` / `{platform}.note.open` / `xiaohongshu.profile.open` 等推进 / 导航指令 MUST NOT 被冷却闸拦截（避免浏览循环死锁，与既有「推进指令不被风控闸拦」同口径）。冷却闸为**附加只读兜底闸**（只防意外爆发，不表达数量策略——数量由 `RiskController` 主闸单独负责）：MUST NOT 写 `risk_state`、MUST NOT 调用 `RiskController.setQuotaLevel` / `applySignal`、MUST NOT 改变账号风控终态或档位；账号风控终态仍仅由 `RiskController` 单写。

#### Scenario: 推进指令不被冷却拦

- **WHEN** 某账号多个互动类型都处于冷却中
- **THEN** `{platform}.feed.scroll` / `navigation.back` / `{platform}.note.open` / `xiaohongshu.profile.open` 仍正常下发，浏览循环继续，不死锁

#### Scenario: 冷却不触碰风控终态

- **WHEN** 冷却闸抑制了一次互动
- **THEN** 该账号 `risk_state`（status 与 quotaLevel）MUST NOT 被改写，`setQuotaLevel` / `applySignal` MUST NOT 被调用

### Requirement: 评论冷却前置到评估阶段、避免白走人审

普通评论（comment）的冷却 SHALL 在**评论评估阶段**（`CommentAppraiser`，与数量闸 / 热度阈值同处的最便宜阶段）就判定：未到 comment 冷却点 MUST emit `comment.skipped{reason:'cooldown'}` 直接进「是否进主页评估」，MUST NOT 进入撰写 / 去 AI 味 / 飞书人审（避免页面久留 + 占用人工却最终被抑制）。

详情确认命中的结构化 mandatory comment 是唯一例外：`CommentAppraiser` MUST 识别随事件透传的规则上下文并跳过评论冷却；该例外 MUST NOT 影响未命中规则的普通评论。

#### Scenario: 普通评论冷却中在评估阶段即跳过
- **WHEN** 某账号上次成功评论后仍在评论冷却窗内，又在一篇未命中强制规则的笔记上进入评论评估
- **THEN** `CommentAppraiser` MUST emit `comment.skipped{reason:'cooldown'}`，不付撰写 / 人审成本，直接进「是否进主页评估」

#### Scenario: 强制评论不被普通冷却否决
- **WHEN** 本篇评论带有全文确认的 mandatory context 且规则 actions 含 comment
- **THEN** `CommentAppraiser` 跳过冷却并继续强制评论支线；其它安全闸与真实回执要求不变

### Requirement: 兜底不变量 MUST 由算术保证，而非文档纪律

「兜底必须比主闸松」MUST NOT 仅靠文档与评审维持。主闸的**取值路径**（`canDo` 与面板 catalog 共同的那一个取值口）SHALL 对**受冷却约束动作**的分钟配额夹 `MINUTE_BURST_CAP`，使「面板把 `perMinute` 配大到让冷却反超主闸」在算术上不可能发生。

夹 MUST 落在**取值口单点**，MUST NOT 落在写路径：库内 SHALL 原样保留运营填写的值（不替运营改写），生效值与面板显示值取同一夹后结果 ⇒ 「显示的＝生效的」，且回滚只需去掉夹、已落库行从不被改写。

🔴 **红线一（窗口轴）：只夹 `perMinute`，MUST NOT 夹 `perHour` / `daily`。** 分钟窗是受冷却约束动作中唯一可能被冷却反超的窗口（其分钟爆发上限蕴含的速率恒 ≥ 小时爆发上限）；夹时 / 日窗既无必要，又会当场砍掉正在生效的运营配置。

🔴 **红线二（动作轴）：只夹受冷却约束的动作，MUST NOT 夹风控动作全集。** 夹的立论只覆盖有冷却的动作。对无冷却动作夹爆发上限既无依据，又有真实伤害：某些动作的分钟爆发上限为 `0`，那是「该动作无默认曲线语义」的**占位**、不是真上限 ⇒ 夹了会把运营显式配置的额度永久压成 `0`，而配额 `0` 即硬拒 ⇒ 该功能静默停摆、无日志无告警。

两条红线是同一陷阱的两个轴：**「对称地都夹一下」看着整齐，实为回归。**

受冷却约束的动作全集 SHALL 从冷却取值表**派生**（而非在各处手写字面量），使新增冷却动作自动纳入夹的作用域与不变量回归断言。

#### Scenario: 面板把分钟配额配到让冷却反超主闸
- **WHEN** 运营给某受冷却约束动作的 `perMinute` 填入超过其分钟爆发上限的值
- **THEN** 生效值 MUST 被夹到该上限（冷却因此仍不 binding）；库内 MUST 原样保留运营填的值；面板显示的 MUST 是夹后的生效值

#### Scenario: 红线——不得夹无冷却动作（占位上限为 0 者尤甚）
- **WHEN** 某动作不受冷却约束，且其分钟爆发上限为 `0`（占位语义），运营通过配额覆盖显式为其配置非零额度
- **THEN** 该额度 MUST 原样生效，MUST NOT 被夹成 `0`——否则等于把主闸旋钮焊死，正是本能力要根除的病

#### Scenario: 红线——不得夹时 / 日窗
- **WHEN** 运营把某动作的 `perHour` 配成高于其小时爆发上限，且该配置正在生效
- **THEN** 该值 MUST 原样生效，MUST NOT 被夹

### Requirement: 重启冷启动静默期同受兜底不变量约束

云端进程重启后，冷却记录（内存态）清零 ⇒ 兜底对「每账号每动作在本进程内的第一发」是瞎的。系统 SHALL 维护一道重启冷启动静默期补上这一发：静默窗内，某账号某动作若在本进程尚无成功记录，MUST 被拒（与冷却同构地诚实抑制）。

静默期是**兜底的一部分**，MUST 同受「兜底必须比主闸松」不变量约束。**默认 15 秒**，MAY 由环境变量调整（0 = 关闭；非法值 MUST 回落默认）。静默期 MUST NOT 写风控终态。

静默期 MUST NOT 被当作数量约束使用：其原始立论「冷却内存态、重启清零 ⇒ burst」已被主闸的持久化抵消（风控配额计数落 PG 并于启动回灌 ⇒ 重启后主闸完好、窗口地板照旧）。

#### Scenario: 静默期不得比主闸紧
- **WHEN** 静默期取值使某动作在某窗口的主闸配额不可达
- **THEN** 该取值 MUST 视为违规——否则病灶只是从冷却搬到静默期

#### Scenario: 重启后首发被静默期兜住
- **WHEN** 云端刚重启，某账号某动作在本进程尚无成功记录，角色即刻产出该动作意图
- **THEN** 静默窗内 MUST 拒；窗口过后恢复正常冷却语义

### Requirement: 评论路径的闸门覆盖必须如实记载

系统存在四条产出评论的路径，它们经过的闸门**不同**。本要求 MUST 如实记载该事实，MUST NOT 声称「所有评论路径都经过冷却」或「跨路径共享的主闸已完好覆盖」：

| 路径 | 主闸（风控配额） | 冷却（兜底） |
|---|---|---|
| 浏览闭环普通评论 | 查 | **查** |
| mandatory 强制评论 | 查（评估前只读预检 ＋ 下发前二次判） | 不查（例外，见「最小间隔冷却」要求） |
| 排期 / 联系 / 引流自动评论 | 查 | 不查 |
| 手动 `/comment` | **不查**（操作员全权，2026-07-10 用户定案） | 不查 |

自动评论旁路（第三行）不查冷却 **MUST NOT 被视为缺陷**：兜底防意外爆发、主闸负责数量，该路径已过主闸。给它补冷却等于把兜底重新升格成主闸，方向相反。

#### Scenario: 不得把旁路缺冷却当作缺陷修复
- **WHEN** 有人提出「排期评论绕过了评论冷却，应补上冷却查询」
- **THEN** MUST 拒绝——该路径已过主闸（评论配额 ＋ 日上限），补冷却违反冷却的兜底定位

#### Scenario: 不得把手动路的豁免记载成完好覆盖
- **WHEN** 有文档 / 提案称「任何评论路径都必过风控主闸」
- **THEN** MUST 修正为「主闸覆盖四条路中的三条；手动 `/comment` 按用户定案豁免」——已知的显式豁免 MUST NOT 被写成完好

