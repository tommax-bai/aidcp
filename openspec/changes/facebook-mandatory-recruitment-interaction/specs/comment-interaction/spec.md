## MODIFIED Requirements

### Requirement: 精品门槛与每账号每日评论上限（后台可配、与风控配额取小）

系统 SHALL 让普通评论的 `CommentAppraiser` 仅在笔记过**精品门槛**时才可能评论。精品门槛 MUST 包含一道**可确定性判定的硬门槛**：该门槛的阈值 SHALL **按内容品类 / 账号可配**（可表达为热度绝对下限、或收藏/点赞比例、或百分位），并按品类给出合理默认；MUST NOT 对所有品类 / 账号写死同一组绝对值（例如固定 `likeCount>1000` **且** `collectCount>300`），以免系统性排除「高赞低藏」的情感 / 颜值类正当爆帖。**通用默认地板** SHALL 为：`likeCount > 300` **且**（`collectCount > 100` **或** `likeCount > 10000` 超高热豁免），边界均为严格大于。**无「收藏」概念的平台**（如 Facebook）SHALL **只放宽收藏合取项**、保留主门槛 `likeCount > 300`。普通评论任一不满足门槛 MUST 直接 `comment.skipped`，硬门槛之上继续叠加 LLM 精品判定与飞书人审；实际生效每日上限仍为运营配置与风控安全配额取小。

详情全文确认命中的结构化 `mandatory_interactions` 规则若含 `comment`，则是上述**普通评论策略的唯一显式例外**：`CommentAppraiser` MUST 跳过会话 comments 软预算、每日评论预闸、热度门槛、评论冷却与“要不要评”LLM，直接 emit `comment.appraised` 并携规则上下文。例外只取消普通策略二次否决；评论下发前仍 MUST 经过 `RiskController.canDo('comment')`，真实成功才计数。

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
- **THEN** `CommentAppraiser` 不检查软预算/每日预闸/冷却/热度、不调用评论判定 LLM，直接进入撰写

### Requirement: 循环内真人审批——暂停态 + 短超时 + 未授权不发

普通评论因必须在详情页打开时发出，审批 SHALL **循环内等待**：`CommentApprovalGate` 下发评论命令前 MUST 经飞书人审授权。等待期间系统 MUST 进入可识别的审批暂停态，并设硬性短超时；超时 / 拒绝 MUST 记审计并 `comment.skipped`。审批使用评论专属 requestId，未获授权 MUST NOT 下发评论命令。

唯一免逐条审批路径是：本篇携详情确认的结构化 mandatory context，规则 actions 含 comment，且规则显式 `comment_approval: auto_approve`。此时该规则保存本身构成账号级站立授权；`CommentApprovalGate` MUST 在提交前把账号、目标和清洗后的终稿发送到免审通知口，**通知成功后**才 emit `comment.approved`。通知口未接线或发送失败 MUST fail-closed 为 `comment.skipped{reason:'auto_approve_notice_failed'}`，MUST NOT 下发。未配置规则、规则为 `review`、或非规则命中评论继续逐条人审。

#### Scenario: 普通评论授权后下发、超时则跳过
- **WHEN** 普通评论的飞书人审在超时窗口内写入授权信号
- **THEN** gate 下发；若未授权 / 被拒则 skip、退出暂停态

#### Scenario: 强制规则免审先通知后授权
- **WHEN** mandatory comment 的规则显式 `auto_approve` 且免审通知成功
- **THEN** gate 不等待逐条点击，直接 emit approved；通知内容必须是即将提交的终稿

#### Scenario: 强制规则免审通知失败不裸发
- **WHEN** 免审通知口未接线或发送失败
- **THEN** MUST emit `comment.skipped{reason:'auto_approve_notice_failed'}`，不下发 edge 评论

#### Scenario: XHS 与普通 FB 评论仍需逐条审批
- **WHEN** 评论没有有效的 auto-approved mandatory context
- **THEN** 它仍走既有人审；MUST NOT 因本功能全局自动直发

### Requirement: Facebook comments require human review by default

All Facebook comments — whether or not they carry contact info — SHALL pass the Feishu human-review gate before edge submit by default. The only account-persona exception is a detail-confirmed structured mandatory rule whose actions include comment and whose `comment_approval` is explicitly `auto_approve`; that path MUST send a readable auto-approval notice successfully before submit and MUST fail closed when notification is unavailable. The existing `AIDCP_FB_COMMENT_REVIEW_ALL=false` escape hatch and contact-comment rules remain unchanged for scheduled comments. An unwired approval port, review timeout, rejection, or failed mandatory auto-approval notice MUST produce an honest non-submitting outcome with no success mark.

#### Scenario: Non-contact FB comment waits for review by default
- **WHEN** a Facebook comment has no valid auto-approved mandatory context and review is enabled
- **THEN** it MUST request Feishu approval and MUST NOT submit until approved

#### Scenario: Structured standing approval notifies then submits
- **WHEN** full-detail matching confirms an account rule with comment plus `comment_approval:auto_approve`
- **THEN** the system MUST send the final-comment notification first and MAY submit only after that send succeeds

#### Scenario: Review or auto-approval notification failure is honest no-submit
- **WHEN** review is unwired/timed out/rejected, or the mandatory auto-approval notice fails
- **THEN** the run MUST audit a non-success reason, MUST NOT call edge submit, and MUST NOT record the target as commented

#### Scenario: Shadow never reviews or submits
- **WHEN** Facebook comment shadow/dry-run mode is active
- **THEN** the run MUST short-circuit before review/notification and MUST NOT submit

#### Scenario: Red-line reversal — implicit auto-post is forbidden
- **WHEN** an implementation auto-posts because of free-form persona wording, account id, nickname, or a global heuristic rather than a validated structured rule
- **THEN** it MUST be treated as a violation and not merged

## ADDED Requirements

### Requirement: 强制评论必须生成贴题终稿并有界失败，禁止模板伪造“一定”

mandatory comment SHALL 继续经过 `CommentComposer`、`CommentDeAiFlavor` 与反照搬护栏。撰写 prompt MUST 注入规则的 `comment_guidance` 并明确本篇必须产出具体评论；模型返回弃权、空或超长时 MAY 有界重试一次。重试仍失败、清洗为空或仍与参考语料近似照搬 MUST 诚实 `comment.skipped`，MUST NOT 回退固定模板或占位话术来伪造“已满足必评”。mandatory context MUST 沿所有 `comment.*` payload 透传到审批终点。

#### Scenario: 强制评论按规则指引生成
- **WHEN** 越南招工规则命中且评论指引要求用越南语询问岗位细节
- **THEN** composer prompt 含该指引和必产要求，产出的终稿继续经过去 AI 味与反照搬检查

#### Scenario: 两次都无法生成则诚实不发
- **WHEN** mandatory composer 首次与一次重试均失败、弃权、为空或超长
- **THEN** 系统 emit 真实 skip 原因，不使用“还招吗/支持一下”等固定模板替代，不报告评论成功
