## ADDED Requirements

### Requirement: Manual override 不得扩散到批量或异步委托

manual override SHALL 只适用于既有单次、操作员在线等待的人工命令。DelegatedTask 的批量评论、跨账号动作、定时/下一安全空档执行和任何异步剩余部分 MUST 使用自动化风险额度并向下游传 `manualOverride=false`；系统 MUST NOT 把一个 N 条任务拆成 N 次人工 override 来绕过配额。

#### Scenario: 五条评论任务遇到日配额
- **WHEN** 自动化额度只允许再完成 2 条评论而委托目标为 5 条
- **THEN** 最多执行额度允许的部分并等待/部分完成
- **AND** MUST NOT 通过五次 manual override 达成表面 5/5

