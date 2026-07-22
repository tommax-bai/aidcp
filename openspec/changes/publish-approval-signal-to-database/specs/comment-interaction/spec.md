## MODIFIED Requirements

### Requirement: 循环内真人审批——暂停态 + 短超时 + 未授权不发

普通评论因必须在详情页打开时发出，审批 SHALL **循环内等待**：`CommentApprovalGate` 下发评论命令前 MUST 经飞书人审授权。等待期间系统 MUST 进入可识别的审批暂停态，并设硬性短超时；超时 / 拒绝 MUST 记审计并 `comment.skipped`。审批使用评论专属 requestId，未获授权 MUST NOT 下发评论命令。

授权判据 SHALL 为持久授权记录的活跃行 `approved === true`，MUST NOT 读取本机文件、MUST NOT 依赖与写方共享文件系统。授权查询超时或不可达 MUST 计为「本轮未授权」并继续等待到超时，最终以 `approval_timeout` 收敛，MUST NOT 与 `approval_rejected` 混同、MUST NOT 因查询异常而放行。评论专属 requestId 仍 MUST 归一到受控字符集（作为记录主键与接口路径段），归一的唯一出口保持不变。

唯一免逐条审批路径是：本篇携详情确认的结构化 mandatory context，规则 actions 含 comment，且规则显式 `comment_approval: auto_approve`。此时该规则保存本身构成账号级站立授权；`CommentApprovalGate` MUST 在提交前把账号、目标和清洗后的终稿发送到免审通知口，**通知成功后**才 emit `comment.approved`。通知口未接线或发送失败 MUST fail-closed 为 `comment.skipped{reason:'auto_approve_notice_failed'}`，MUST NOT 下发。未配置规则、规则为 `review`、或非规则命中评论继续逐条人审。

#### Scenario: 普通评论授权后下发、超时则跳过
- **WHEN** 普通评论的飞书人审在超时窗口内写入活跃授权记录且 `approved === true`
- **THEN** gate 下发；若未授权 / 被拒则 skip、退出暂停态

#### Scenario: 授权查询不可达按未授权处理且拒因可区分
- **WHEN** 审批等待期内授权查询持续超时或不可达直到窗口期满
- **THEN** gate emit `comment.skipped{reason:'approval_timeout'}`，MUST NOT 报 `approval_rejected`、MUST NOT 下发评论

#### Scenario: 强制规则免审先通知后授权
- **WHEN** mandatory comment 的规则显式 `auto_approve` 且免审通知成功
- **THEN** gate 不等待逐条点击，直接 emit approved；通知内容必须是即将提交的终稿

#### Scenario: 强制规则免审通知失败不裸发
- **WHEN** 免审通知口未接线或发送失败
- **THEN** MUST emit `comment.skipped{reason:'auto_approve_notice_failed'}`，不下发 edge 评论

#### Scenario: XHS 与普通 FB 评论仍需逐条审批
- **WHEN** 评论没有有效的 auto-approved mandatory context
- **THEN** 它仍走既有人审；MUST NOT 因本功能全局自动直发
