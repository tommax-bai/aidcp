## MODIFIED Requirements

### Requirement: 循环内真人审批——暂停态 + 短超时 + 未授权不发

普通评论默认因必须在详情页打开时发出而**循环内等待**：`CommentApprovalGate` 下发评论命令前 MUST 经人审授权。等待期间系统 MUST 进入可识别的审批暂停态，并设硬性短超时；超时 / 拒绝 MUST 记审计并 `comment.skipped`。审批使用评论专属 requestId，未获有效授权 MUST NOT 下发评论命令。

免逐条审批路径有两类：① 本篇携详情确认的结构化 mandatory context，规则 actions 含 comment，且规则显式 `comment_approval: auto_approve`；② 当前账号显式配置全局评论 `auto_approve_all`，后者 MUST 覆盖普通浏览、排期、联系、mandatory、飞书 `/comment` 和结构化委托来源的局部模式。任一免审路径下，`CommentApprovalGate` MUST 直接 emit `comment.approved`，并把账号、目标和清洗后的终稿旁路发送到免审通知口。提交链 MUST NOT 等待通知；通知口未接线或发送失败只记日志，MUST NOT emit `comment.skipped`、MUST NOT 阻止下发、MUST NOT 回退为按钮审批。账号为 `source_rules` 时，未配置规则、规则为 `review`、或非规则命中评论继续逐条人审。

#### Scenario: 普通评论授权后下发、超时则跳过
- **WHEN** `source_rules` 账号的普通评论人审在超时窗口内写入授权信号
- **THEN** gate 下发；若未授权 / 被拒则 skip、退出暂停态

#### Scenario: 强制规则免审直接授权并旁路通知
- **WHEN** `source_rules` 账号的 mandatory comment 规则显式 `auto_approve`
- **THEN** gate 不等待逐条点击，直接 emit approved；旁路通知内容必须是即将提交的终稿

#### Scenario: 账号全局免审覆盖普通评论
- **WHEN** 普通浏览评论所属账号显式配置 `auto_approve_all`
- **THEN** gate 不发送按钮审批卡、不等待点击，直接 emit approved 并继续既有目标复核与提交链

#### Scenario: 免审通知失败不影响全局免审
- **WHEN** 任一免审路径的通知口未接线或发送失败
- **THEN** MUST 只记录日志并继续既有提交链，MUST NOT 回退按钮审批或产生 `auto_approve_notice_failed`

#### Scenario: 来源规则账号的 XHS 与普通 FB 评论仍需逐条审批
- **WHEN** 账号为 `source_rules` 且评论没有有效的 auto-approved mandatory context
- **THEN** 它仍走既有人审，MUST NOT 被隐式全局自动直发

### Requirement: Facebook comments require human review by default

All Facebook comments — whether or not they carry contact info — SHALL pass the human-review gate before edge submit by default. The exceptions are a detail-confirmed structured mandatory rule whose actions include comment and whose `comment_approval` is explicitly `auto_approve`, or an explicit account policy of `auto_approve_all`. Either exception MUST authorize without waiting for a button and SHOULD send a readable best-effort auto-approval notice; notice delivery MUST NOT gate or delay submit. The account-wide exception MUST apply to every comment source, including Feishu `/comment`; a source-specific schedule mode MUST NOT override it back to review. The existing `AIDCP_FB_COMMENT_REVIEW_ALL=false` escape hatch and contact-comment rules remain unchanged for `source_rules` accounts. An unwired approval port, review timeout, or rejection on a `review` path MUST produce an honest non-submitting outcome with no success mark.

#### Scenario: Non-contact FB comment waits for review by default
- **WHEN** a `source_rules` account comment has no valid auto-approved mandatory context and review is enabled
- **THEN** it MUST request approval and MUST NOT submit until approved

#### Scenario: Structured standing approval submits independently of notice delivery
- **WHEN** full-detail matching confirms a `source_rules` account rule with comment plus `comment_approval:auto_approve`
- **THEN** the system MUST authorize immediately and SHOULD send the final-comment notification best-effort

#### Scenario: Account-wide standing approval covers manual comments
- **WHEN** an `auto_approve_all` account receives an exact Feishu `/comment` command
- **THEN** the system MUST authorize without waiting for a second button approval; notice failure MUST NOT change that decision

#### Scenario: Review failure blocks but auto-approval notice failure does not
- **WHEN** review is unwired/timed out/rejected, or an auto-approval notice fails
- **THEN** only the `review` failure MUST block edge submit; an auto-approval notice failure MUST be logged and MUST NOT create an approval fallback

#### Scenario: Shadow never reviews or submits
- **WHEN** Facebook comment shadow/dry-run mode is active
- **THEN** the run MUST short-circuit before review/notification and MUST NOT submit

#### Scenario: Red-line reversal — implicit auto-post is forbidden
- **WHEN** an implementation auto-posts because of free-form persona wording, account id, nickname, or a global heuristic rather than a validated structured rule or explicit persisted account policy
- **THEN** it MUST be treated as a violation and not merged
