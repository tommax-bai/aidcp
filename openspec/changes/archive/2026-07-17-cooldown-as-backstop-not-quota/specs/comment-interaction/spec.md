## MODIFIED Requirements

### Requirement: 精品门槛与每账号每日评论上限（后台可配、与风控配额取小）

系统 SHALL 让普通评论的 `CommentAppraiser` 仅在笔记过**精品门槛**时才可能评论。精品门槛 MUST 包含一道**可确定性判定的硬门槛**：该门槛的阈值 SHALL **按内容品类 / 账号可配**（可表达为热度绝对下限、或收藏/点赞比例、或百分位），并按品类给出合理默认；MUST NOT 对所有品类 / 账号写死同一组绝对值（例如固定 `likeCount>1000` **且** `collectCount>300`），以免系统性排除「高赞低藏」的情感 / 颜值类正当爆帖。**通用默认地板** SHALL 为：`likeCount > 300` **且**（`collectCount > 100` **或** `likeCount > 10000` 超高热豁免），边界均为严格大于。**无「收藏」概念的平台**（如 Facebook）SHALL **只放宽收藏合取项**、保留主门槛 `likeCount > 300`。普通评论任一不满足门槛 MUST 直接 `comment.skipped`，硬门槛之上继续叠加 LLM 精品判定与飞书人审；实际生效每日上限仍为运营配置与风控安全配额取小。

详情全文确认命中的结构化 `mandatory_interactions` 规则若含 `comment`，则是上述**普通评论策略的唯一显式例外**：`CommentAppraiser` MUST 跳过会话 comments 软预算、普通每日策略闸、热度门槛、评论冷却与“要不要评”LLM，但在撰写前 MUST 经过可解释的 `RiskController.explain('comment')` 硬风控预检。预检拒绝时不得撰写、不得发免审通知；预检放行才 emit `comment.appraised` 并携规则上下文。预检不是配额预占，评论下发前仍 MUST 再经过同一硬风控，真实成功才计数。

**该例外中「跳过评论冷却」一项的理由 MUST 与 `interaction-cooldown` 同源**：冷却是**兜底**（防意外爆发），其抑制语义是**丢弃而非排队**；mandatory 是运营对指定内容类别的显式授权、且为每帖一次性机会 ⇒ 兜底 MUST NOT destroy 一次已授权的机会。该理由 MUST NOT 表述为「授权动作不该被数量约束挡」——冷却不表达数量策略，数量由 `RiskController` 主闸单独负责，而本例外**不跳过主闸**（预检 ＋ 下发前二次判均保留）。

#### Scenario: 达到每日上限即停止普通评论
- **WHEN** 某账号当日已评数 ≥ min(运营配置上限, 风控配额)，且本篇未命中结构化强制规则
- **THEN** `CommentAppraiser` MUST emit `comment.skipped{reason:'daily_cap_reached'}`，当日不再发起普通评论

#### Scenario: 运营配置不可越过风控安全线
- **WHEN** 运营把每日上限配成高于风控 `comment` 安全配额
- **THEN** 生效上限 MUST 取风控安全配额（取小），MUST NOT 因运营配置突破封号安全线

#### Scenario: 未达硬门槛的普通帖子不评
- **WHEN** 普通帖子未达该品类 / 账号硬门槛且无 mandatory context
- **THEN** `CommentAppraiser` MUST emit `comment.skipped{reason:'below_comment_threshold'}`，在调 LLM 之前即跳过

#### Scenario: 无收藏平台按放宽收藏合取项入普通候选
- **WHEN** 一篇普通 Facebook 帖 `likeCount = 500`、`collectCount = 0`
- **THEN** 收藏合取项恒真、主门槛满足，该帖进入普通 LLM 精品判定

#### Scenario: 低热度强制帖子绕过普通门槛与判定
- **WHEN** 一篇 Facebook 帖 `likeCount = 0` 但全文确认命中 actions 含 comment 的结构化规则
- **THEN** `CommentAppraiser` 不检查软预算/普通每日策略闸/冷却/热度、不调用评论判定 LLM，但必须先过硬风控预检，放行后才进入撰写

#### Scenario: 例外的理由不得与兜底定位冲突
- **WHEN** 有人以「冷却是数量约束、已授权动作不该被数量约束挡」为由解释本例外
- **THEN** MUST 拒绝该表述——冷却不表达数量策略；本例外的唯一正当理由是「兜底丢弃不排队，MUST NOT destroy 已授权的一次性机会」
