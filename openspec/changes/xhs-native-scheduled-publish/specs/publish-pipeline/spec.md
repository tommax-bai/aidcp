## ADDED Requirements

### Requirement: 小红书原生定时模式覆盖通用元数据 best-effort 语义

当 `publishMetadata.mode === 'scheduled'` 时，发布管线 SHALL 应用 `xhs-native-scheduled-publish` 能力定义的关键步骤与终局状态：`set_schedule` MUST fail-fast，定时提交后 MUST 产出 `scheduled` 结果而非强求同页 `capture_postId`。该窄化规则对定时模式优先于 `publish-trigger-and-apply` 中“元数据步骤可 best-effort 跳过”和“提交后统一 capture_postId”的通用描述；立即发布与其它元数据步骤保持既有行为。

#### Scenario: set_schedule 失败停止发布
- **WHEN** 定时序列的 `set_schedule` 回报失败
- **THEN** `CommandSequencer` 返回提交前失败且不下发 `submit_publish`，不得按元数据 best-effort 继续

#### Scenario: 定时提交产生独立终局
- **WHEN** 定时设置成功且平台接受提交
- **THEN** sequencer 返回 `scheduled_pending`（可带内部定时 id），dispatcher 落 `scheduled` 且不调用发布记账

