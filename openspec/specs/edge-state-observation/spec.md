# edge-state-observation Specification

## Purpose
TBD - created by archiving change add-state-observation-command. Update Purpose after archive.
## Requirements
### Requirement: 云端 MUST 能主动询问边缘浏览器现场

系统 SHALL 提供一条云端→边缘的观察命令，应答一次带回：当前执行面（结构化枚举）、当前登录身份观察、采集时刻。该命令属观察族，命令名 MUST NOT 携带平台段；面的取值 MUST 为穷举类型，MUST NOT 以自由字符串表达。

#### Scenario: 恢复链主动问真相

- **WHEN** 云端对某会话的当前页推定存疑（如收到「确认到不在期望面」的报错后）并下发问现状命令
- **THEN** 边缘 MUST 回带当前面与身份观察的应答，云端可据此重新规划
- **AND** 应答 MUST 经信封关联回到请求方，MUST NOT 靠事后回执顺带

### Requirement: 问现状 MUST 纯读且两态诚实

问现状的执行 MUST NOT 触发任何导航、点击或滚动；仅读取。页面状态无法读出时 MUST 回「没能确认」，与「确认到在某面」使用不同的结构化取值，MUST NOT 把读不出来伪装成任何具体面，也 MUST NOT 静默超时。

#### Scenario: 页面读不出来

- **WHEN** 问现状执行时页面卡死或连接不健康，无法完成读取
- **THEN** 应答 MUST 明确表达「没能确认」及原因
- **AND** MUST NOT 回落到任何默认面取值

#### Scenario: 观察不改变现场

- **WHEN** 问现状在任意页面执行
- **THEN** 执行前后页面 MUST 无导航、无输入事件、无滚动位移

