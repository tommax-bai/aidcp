## ADDED Requirements

### Requirement: 内容排期必须尊重委托任务 ownership 并避免双重执行

`ContentScheduler` 在触发发帖、评论或联系评论前 SHALL 查询同账号动作族的 DelegatedTask ownership。存在 queued/planning/waiting_approval/executing 的冲突委托时，本 tick MUST 诚实跳过且不得启动第二个 scheduler；委托 worker 同样必须尊重已在途排期/scheduler ownership。busy 跳过不得被计为平台尝试或成功。

#### Scenario: 委托发布等待人审时排期不再生成第二稿
- **WHEN** 同账号已有一个用户委托发布处于 `waiting_approval`
- **THEN** 该账号排期发帖 tick 跳过并记录 ownership 原因
- **AND** MUST NOT 生成另一份自动候选来争用同一发布槽

