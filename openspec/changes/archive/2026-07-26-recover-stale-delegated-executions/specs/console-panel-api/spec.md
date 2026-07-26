## ADDED Requirements

### Requirement: 排队任务必须解释有证据的暂缓原因

管理后台内容页显示 `deferred` 发布任务时，除状态与下一次检查时刻外，SHALL 根据 Cloud 已返回的稳定 `currentStep` 展示可读等待原因。页面 MUST NOT 把重试轮询时刻描述为届时一定开始；未知步骤码 MUST NOT 被猜测成具体原因。

#### Scenario: 同源 ownership 占用可见

- **WHEN** 一条发布任务为 `deferred` 且 `currentStep=waiting_ownership`
- **THEN** 排队卡 SHALL 说明正在等待同一参照稿任务释放
- **AND** SHALL 把 `nextEligibleAt` 描述为预计再次检查时刻，而非承诺起跑时刻

#### Scenario: 生成槽位暂满可见

- **WHEN** 一条发布任务为 `deferred` 且 `currentStep=waiting_safe_slot`
- **THEN** 排队卡 SHALL 说明生成槽位暂满、任务仍在排队

#### Scenario: 未知步骤不猜测

- **WHEN** 一条暂缓任务带有 Console 不认识的 `currentStep`
- **THEN** 页面 SHALL 保留“暂缓”状态与时间事实
- **AND** MUST NOT 补写未经 Cloud 证实的原因
