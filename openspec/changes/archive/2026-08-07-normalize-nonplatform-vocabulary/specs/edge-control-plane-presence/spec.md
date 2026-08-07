## MODIFIED Requirements

### Requirement: Cloud 控制面在线 SHALL 与浏览器槽位解耦

已归属且可解析权威账号绑定的环境 SHALL 能在没有浏览器槽位时启动 Edge 核心、建立 Cloud 会话并声明浏览器缺席。浏览器并发上限 SHALL 只限制浏览器执行实例，MUST NOT 限制 Cloud 控制面会话数。

#### Scenario: 槽位外环境仍连接 Cloud
- **WHEN** 客户启动的环境已归属且有无冲突的账号绑定，但当前浏览器槽位已满
- **THEN** 该环境核心以 browser-absent standby 状态启动并完成 Cloud 握手
- **AND** Cloud 可向其发送 `ui.push_snapshot`、人设真态与唤醒信号

#### Scenario: 不能可信解析时绝不猜账号
- **WHEN** 环境未归属、未绑定、绑定冲突或绑定存储不可用
- **THEN** Edge MUST NOT 从环境名、profile id、本地日志或旧 UI 状态猜测账号并连接 Cloud
- **AND** 客户端 SHALL 如实保留浏览器排队状态并显示可区分原因
