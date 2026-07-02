## MODIFIED Requirements

### Requirement: 精品门槛与每账号每日评论上限（后台可配、与风控配额取小）

系统 SHALL 让 `CommentAppraiser` 仅在笔记过**精品门槛**时才可能评论。精品门槛 MUST 包含一道**可确定性判定的硬门槛**：该门槛的阈值 SHALL **按内容品类 / 账号可配**（可表达为热度绝对下限、或收藏/点赞比例、或百分位），并按品类给出合理默认；MUST NOT 对所有品类 / 账号写死同一组绝对值（例如固定 `likeCount>1000` **且** `collectCount>300`），以免系统性排除「高赞低藏」的情感 / 颜值类正当爆帖。为控成本，该硬门槛 SHALL 尽量在**最便宜阶段（调 LLM 之前）**确定性判定，MUST NOT 退化为宽松纯 OR 让过多笔记落到昂贵 LLM 判定。任一不满足门槛 MUST 直接 `comment.skipped`、不进入撰写 / 去 AI 味 / 审批。硬门槛之上，现有 LLM 精品判定（高热度 + 高价值）与飞书人审继续叠加（门槛为必要非充分条件）。此外系统保留**按账号、可持久化的每日评论上限配置**（运营在 console 后台读写、经面板 `/api` 下发）；**实际生效每日上限 = min(运营配置上限, 风控安全配额)**，"今日已评数" MUST 复用风控按账号按天计数。数量、门槛与阈值 MUST 在评估阶段就判定：超上限 / 不达门槛 / LLM 判不值得 MUST 直接走"不评论 → 进主页评估"分支，MUST NOT 进入撰写 / 去 AI 味 / 审批。

#### Scenario: 达到每日上限即停止评论
- **WHEN** 某账号当日已评数 ≥ min(运营配置上限, 风控配额)
- **THEN** `CommentAppraiser` MUST emit `comment.skipped{reason:'daily_cap_reached'}`，当日不再评论，直接进"是否进主页评估"

#### Scenario: 运营配置不可越过风控安全线
- **WHEN** 运营把每日上限配成高于风控 `comment` 安全配额
- **THEN** 生效上限 MUST 取风控安全配额（取小），MUST NOT 因运营配置突破封号安全线

#### Scenario: 未达品类/账号硬门槛不评
- **WHEN** 笔记未达该品类 / 账号解析出的硬门槛（按详情页真实点赞 / 收藏量或其比例）
- **THEN** `CommentAppraiser` MUST emit `comment.skipped{reason:'below_comment_threshold'}`，在调 LLM 之前即跳过，不进入撰写

#### Scenario: 高赞低藏爆帖不再被固定绝对值一律排除
- **WHEN** 一篇情感 / 颜值类高赞低藏笔记（如高点赞、收藏绝对值不高）进入评估
- **THEN** 硬门槛按其品类 / 账号口径判定（比例 / 品类默认），MUST NOT 仅因「收藏绝对值未过固定 300」就必然判未达门槛

#### Scenario: 门槛边界严格判定
- **WHEN** 笔记指标恰好等于解析出的阈值边界
- **THEN** MUST 视为未达门槛、不评（「超过」语义为严格大于，等于不算达标）

#### Scenario: 达门槛仍需过 LLM 与人审
- **WHEN** 笔记通过品类 / 账号硬门槛
- **THEN** 该笔记仅**通过硬门槛**进入后续判定，是否真评论仍由 LLM 精品判定 + 飞书人审决定（门槛是必要非充分条件）
