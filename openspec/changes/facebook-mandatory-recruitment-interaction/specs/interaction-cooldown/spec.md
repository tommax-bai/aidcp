## MODIFIED Requirements

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

### Requirement: 评论冷却前置到评估阶段、避免白走人审

普通评论（comment）的冷却 SHALL 在**评论评估阶段**（`CommentAppraiser`，与数量闸 / 热度阈值同处的最便宜阶段）就判定：未到 comment 冷却点 MUST emit `comment.skipped{reason:'cooldown'}` 直接进「是否进主页评估」，MUST NOT 进入撰写 / 去 AI 味 / 飞书人审（避免页面久留 + 占用人工却最终被抑制）。

详情确认命中的结构化 mandatory comment 是唯一例外：`CommentAppraiser` MUST 识别随事件透传的规则上下文并跳过评论冷却；该例外 MUST NOT 影响未命中规则的普通评论。

#### Scenario: 普通评论冷却中在评估阶段即跳过
- **WHEN** 某账号上次成功评论不足 30 分钟，又在一篇未命中强制规则的笔记上进入评论评估
- **THEN** `CommentAppraiser` MUST emit `comment.skipped{reason:'cooldown'}`，不付撰写 / 人审成本，直接进「是否进主页评估」

#### Scenario: 强制评论不被普通冷却否决
- **WHEN** 本篇评论带有全文确认的 mandatory context 且规则 actions 含 comment
- **THEN** `CommentAppraiser` 跳过冷却并继续强制评论支线；其它安全闸与真实回执要求不变
