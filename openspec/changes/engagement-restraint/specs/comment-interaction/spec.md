## MODIFIED Requirements

### Requirement: 精品门槛与每账号每日评论上限（后台可配、与风控配额取小）

系统 SHALL 让 `CommentAppraiser` 仅在笔记过**精品门槛**时才可能评论。精品门槛 MUST 包含一道**可确定性判定的硬数值阈值**：仅当详情页 `likeCount > 1000` **且** `collectCount > 300`（均严格大于）时该笔记才达门槛；任一不满足 MUST 直接 `comment.skipped`、不进入撰写 / 去 AI 味 / 审批。硬数值阈值之上，现有 LLM 精品判定（高热度 + 高价值）与飞书人审继续叠加（阈值为必要非充分条件）。此外系统保留**按账号、可持久化的每日评论上限配置**（运营在 console 后台读写、经面板 `/api` 下发）；**实际生效每日上限 = min(运营配置上限, 风控安全配额)**，"今日已评数" MUST 复用风控按账号按天计数。数量、阈值与门槛 MUST 在评估阶段就判定：超上限 / 不达数值阈值 / LLM 判不值得 MUST 直接走"不评论 → 进主页评估"分支，MUST NOT 进入撰写 / 去 AI 味 / 审批。

#### Scenario: 达到每日上限即停止评论
- **WHEN** 某账号当日已评数 ≥ min(运营配置上限, 风控配额)
- **THEN** `CommentAppraiser` MUST emit `comment.skipped{reason:'daily_cap_reached'}`，当日不再评论，直接进"是否进主页评估"

#### Scenario: 运营配置不可越过风控安全线
- **WHEN** 运营把每日上限配成高于风控 `comment` 安全配额
- **THEN** 生效上限 MUST 取风控安全配额（取小），MUST NOT 因运营配置突破封号安全线

#### Scenario: 未达硬数值阈值不评
- **WHEN** 笔记 `likeCount ≤ 1000` 或 `collectCount ≤ 300`（按详情页真实点赞 / 收藏量）
- **THEN** `CommentAppraiser` MUST emit `comment.skipped{reason:'below_comment_threshold'}`，在调 LLM 之前即跳过，不进入撰写

#### Scenario: 阈值边界严格大于
- **WHEN** 笔记 `likeCount === 1000` 或 `collectCount === 300`（恰好等于）
- **THEN** MUST 视为未达门槛、不评（「超过」语义为严格大于，等于不算达标）

#### Scenario: 达数值阈值仍需过 LLM 与人审
- **WHEN** 笔记 `likeCount > 1000` 且 `collectCount > 300`
- **THEN** 该笔记仅**通过硬数值阈值**进入后续判定，是否真评论仍由 LLM 精品判定 + 飞书人审决定（阈值是必要非充分条件）
