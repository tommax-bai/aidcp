# edge-control-plane-presence Specification

## Purpose
TBD - created by archiving change browser-slot-cloud-presence. Update Purpose after archive.
## Requirements
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

### Requirement: Cloud welcome SHALL 是连接成功的唯一判据

Edge SHALL 仅在 hello 请求收到 `type='welcome'` 且 payload 包含非空 `sessionId` 与 `serverVersion` 时宣告 Cloud 已连接。WebSocket transport 已打开、任意同 id 响应或畸形 payload MUST NOT 被视为成功。

#### Scenario: Cloud error envelope 握手失败
- **WHEN** hello 收到相同 request id 的 `error` envelope
- **THEN** Edge 以 Cloud 错误码和消息结束本次握手
- **AND** MUST NOT 设置 connected、启动心跳或显示“已连接云端”

#### Scenario: 畸形 welcome fail-closed
- **WHEN** hello 收到 `welcome` 但缺少有效 sessionId 或 serverVersion
- **THEN** Edge 以协议错误结束握手并保持离线
- **AND** MUST NOT 出现 `sessionId=?` 的成功状态

### Requirement: 浏览器唤醒后 SHALL 复核真实身份

以控制面绑定身份启动的 Edge 在取得浏览器并附着页面后 SHALL 重新读取真实平台账号身份。身份复核与必要的 Cloud 重连成功之前，任何页面读取或写入任务 MUST NOT 开始。

#### Scenario: 页面身份与引导一致
- **WHEN** browser-absent 环境被唤醒且页面解析出的账号等于控制面引导账号
- **THEN** Edge 保持当前 Cloud 会话、标记浏览器就绪并开始被授权的运行时

#### Scenario: 页面已经换号
- **WHEN** 页面解析出的真实账号 B 不等于控制面引导账号 A
- **THEN** Edge 先以账号 B 重建 Cloud 会话并取得有效 welcome，再回报浏览器唤醒成功
- **AND** MUST NOT 在账号 A 的 Cloud 会话下对账号 B 页面执行动作

#### Scenario: 页面未登录或身份不可读
- **WHEN** 浏览器已启动但平台身份缺失、登录失效或身份复核失败
- **THEN** Edge MUST NOT 执行页面任务，并以可诊断失败回报唤醒请求

### Requirement: 引擎在线与浏览器就绪 SHALL 独立上报

协议和客户端状态 SHALL 将 Cloud engine presence 与 browser readiness 作为两个正交事实。需要浏览器的命令在 engine 在线但 browser absent 时 SHALL 走既有有界唤醒/槽位流程。

#### Scenario: 引擎在线浏览器待机
- **WHEN** Edge 持有有效 Cloud session 但没有浏览器实例
- **THEN** Cloud 将该 edge 视为控制面在线且浏览器缺席
- **AND** 客户端 MUST NOT 将其显示为浏览器运行中

#### Scenario: 唤醒未在死线内完成
- **WHEN** browser-absent edge 收到需要浏览器的任务但未在死线内取得槽位并完成身份复核
- **THEN** 调用方收到明确、可恢复的 browser wake failure
- **AND** MUST NOT 将其误报为 edge offline 或静默等待到超时

