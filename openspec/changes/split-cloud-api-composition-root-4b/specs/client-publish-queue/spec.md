## MODIFIED Requirements

### Requirement: Customer progress SHALL use truthful four-stage semantics

客户端 SHALL 以“开始创作、正文与配图、发布确认、发布结果”四阶段展示客户进度，但每一阶段状态
MUST 只由 Cloud 显式生命周期投影映射。当前阶段有可证实数量时 SHALL 展示，例如配图 `2/4`；
“发布确认”处于 `waiting_human` 时 SHALL 显示“待你确认”，完成时 SHALL 显示“已确认”；
“发布结果”有可靠未开始证据时 SHALL 显示“等待发布”。

Cloud 明确返回 `inFlightEvidence.state=unknown|stale|invalid` 且没有 durable dispatch 证明时，
客户端 SHALL 将发布确认/结果中受影响的阶段显示为“下发状态暂不可用”，MUST NOT 根据空集合推断
“等待发布”“正在发布”或“未下发”。缺少其它状态证据时 SHALL 显示未知或未开始，不得根据等待时长、
字段存在或页面顺序推断完成。

#### Scenario: 等待人工确认

- **WHEN** lifecycle 以 durable/fresh 证据明确显示审批阶段为 `waiting_human` 且下发阶段为 `pending`
- **THEN** 客户端显示“发布确认”为当前阶段及“待你确认”
- **AND** 显示“发布结果”为“等待发布”并提供现有稿件审核入口

#### Scenario: 下发证据暂不可用

- **WHEN** lifecycle 缺少 durable dispatch 证明且 `inFlightEvidence.state` 为 unknown、stale 或 invalid
- **THEN** 客户端显示“下发状态暂不可用”
- **AND** MUST NOT 显示“等待发布”“正在发布”“未下发”或零在途结论
