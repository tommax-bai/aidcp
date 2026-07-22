## MODIFIED Requirements

### Requirement: 循环内真人审批——暂停态 + 短超时 + 未授权不发

普通评论默认因必须在详情页打开时发出而**循环内等待**：`CommentApprovalGate` 下发评论命令前 MUST 经人审授权。等待期间系统 MUST 进入可识别的审批暂停态，并设硬性短超时；超时 / 拒绝 MUST 记审计并 `comment.skipped`。审批使用评论专属 requestId，未获有效授权 MUST NOT 下发评论命令。

免逐条审批路径有两类：① 本篇携详情确认的结构化 mandatory context，规则 actions 含 comment，且规则显式 `comment_approval: auto_approve`；② 当前账号显式配置全局评论 `auto_approve_all`，后者 MUST 覆盖普通浏览、排期、联系、mandatory、飞书 `/comment` 和结构化委托来源的局部模式。任一免审路径下，`CommentApprovalGate` MUST 在提交前把账号、目标和清洗后的终稿发送到免审通知口，**通知成功后**才 emit `comment.approved`。通知口未接线或发送失败 MUST fail-closed 为 `comment.skipped{reason:'auto_approve_notice_failed'}`，MUST NOT 下发。账号为 `source_rules` 时，未配置规则、规则为 `review`、或非规则命中评论继续逐条人审。

#### Scenario: 普通评论授权后下发、超时则跳过
- **WHEN** `source_rules` 账号的普通评论人审在超时窗口内写入授权信号
- **THEN** gate 下发；若未授权 / 被拒则 skip、退出暂停态

#### Scenario: 强制规则免审先通知后授权
- **WHEN** `source_rules` 账号的 mandatory comment 规则显式 `auto_approve` 且免审通知成功
- **THEN** gate 不等待逐条点击，直接 emit approved；通知内容必须是即将提交的终稿

#### Scenario: 账号全局免审覆盖普通评论
- **WHEN** 普通浏览评论所属账号显式配置 `auto_approve_all` 且免审通知成功
- **THEN** gate 不发送按钮审批卡、不等待点击，直接 emit approved 并继续既有目标复核与提交链

#### Scenario: 免审通知失败不裸发
- **WHEN** 任一免审路径的通知口未接线或发送失败
- **THEN** MUST emit `comment.skipped{reason:'auto_approve_notice_failed'}`，不下发 edge 评论

#### Scenario: 来源规则账号的 XHS 与普通 FB 评论仍需逐条审批
- **WHEN** 账号为 `source_rules` 且评论没有有效的 auto-approved mandatory context
- **THEN** 它仍走既有人审，MUST NOT 被隐式全局自动直发

### Requirement: Facebook comments require human review by default

All Facebook comments — whether or not they carry contact info — SHALL pass the human-review gate before edge submit by default. The exceptions are a detail-confirmed structured mandatory rule whose actions include comment and whose `comment_approval` is explicitly `auto_approve`, or an explicit account policy of `auto_approve_all`. Either exception MUST send a readable auto-approval notice successfully before submit and MUST fail closed when notification is unavailable. The account-wide exception MUST apply to every comment source, including Feishu `/comment`; a source-specific schedule mode MUST NOT override it back to review. The existing `AIDCP_FB_COMMENT_REVIEW_ALL=false` escape hatch and contact-comment rules remain unchanged for `source_rules` accounts. An unwired approval port, review timeout, rejection, or failed auto-approval notice MUST produce an honest non-submitting outcome with no success mark.

#### Scenario: Non-contact FB comment waits for review by default
- **WHEN** a `source_rules` account comment has no valid auto-approved mandatory context and review is enabled
- **THEN** it MUST request approval and MUST NOT submit until approved

#### Scenario: Structured standing approval notifies then submits
- **WHEN** full-detail matching confirms a `source_rules` account rule with comment plus `comment_approval:auto_approve`
- **THEN** the system MUST send the final-comment notification first and MAY submit only after that send succeeds

#### Scenario: Account-wide standing approval covers manual comments
- **WHEN** an `auto_approve_all` account receives an exact Feishu `/comment` command
- **THEN** the system MUST send the final-comment notification first and MUST NOT wait for a second button approval

#### Scenario: Review or auto-approval notification failure is honest no-submit
- **WHEN** review is unwired/timed out/rejected, or any auto-approval notice fails
- **THEN** the run MUST audit a non-success reason, MUST NOT call edge submit, and MUST NOT record the target as commented

#### Scenario: Shadow never reviews or submits
- **WHEN** Facebook comment shadow/dry-run mode is active
- **THEN** the run MUST short-circuit before review/notification and MUST NOT submit

#### Scenario: Red-line reversal — implicit auto-post is forbidden
- **WHEN** an implementation auto-posts because of free-form persona wording, account id, nickname, or a global heuristic rather than a validated structured rule or explicit persisted account policy
- **THEN** it MUST be treated as a violation and not merged
