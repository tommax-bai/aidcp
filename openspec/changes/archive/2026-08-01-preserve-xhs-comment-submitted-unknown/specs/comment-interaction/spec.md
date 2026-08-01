## ADDED Requirements

### Requirement: 小红书评论提交后不确定回执必须去重且不得自动重投

Cloud MUST 将小红书评论回执 `submitted_unconfirmed`、`submitted_editor_not_cleared` 与 `submitted_ack_unreadable` 统一归为“提交已派发但结果未确认”。该状态 MUST 写入笔记级评论去重账并终止自动重试，MUST NOT 计作平台确认成功。只有执行端 `ok:true` 才能归为确认成功；提交前抢占和未派发失败 MUST 保持既有的不去重语义。

#### Scenario: 评论出现但编辑器未清空

- **WHEN** 小红书评论返回 `ok:false reason=submitted_editor_not_cleared`
- **THEN** Cloud MUST 归为 `submitted_unconfirmed`、写评论去重账并停止自动重试，且 MUST NOT 计作确认成功

#### Scenario: 提交后确认状态不可读

- **WHEN** 小红书评论返回 `ok:false reason=submitted_ack_unreadable`
- **THEN** Cloud MUST 归为 `submitted_unconfirmed`、写评论去重账并停止自动重试，且 MUST NOT 计作确认成功

#### Scenario: 既有提交未确认原因保持兼容

- **WHEN** 小红书评论返回 `ok:false reason=submitted_unconfirmed`
- **THEN** Cloud MUST 继续写评论去重账并停止自动重试，且 MUST NOT 计作确认成功

#### Scenario: 提交前结果不得升级成已提交

- **WHEN** 小红书评论在提交前被抢占，或返回不属于上述闭集的失败原因
- **THEN** Cloud MUST NOT 将其归为 `submitted_unconfirmed`，MUST NOT 因本要求写评论去重账
