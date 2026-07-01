# edge-command-targeting Specification

## Purpose
保证定向边缘命令的目标寻址与投递安全：每个 edge 连接握手须携带可路由的节点身份（edgeId），出站命令只投递到唯一的目标节点，绝不因缺目标而隐式广播或误投到非目标节点。补齐「入站结构性隔离」之外、出站侧靠 edgeId 过滤的那道纪律（承 change edge-command-target-guard 归档）。
## Requirements
### Requirement: Edge handshake requires a routable node identity

云端 SHALL 在握手阶段要求每个 edge 连接携带非空的节点号（edgeId）。缺失或空白的节点号 MUST 与缺失账号号同等，被判为配置错误并拒绝握手；此类连接 MUST NOT 建立连接运行时（不创建私有事件通道、角色调度器或会话状态），因而永不进入可被下发命令的在线集合。

#### Scenario: 握手缺少节点号被拒

- **WHEN** 一个 edge 的握手帧携带有效账号号，但节点号缺失或为空白
- **THEN** 云端 SHALL 经既有配置错误出口拒绝该握手，返回配置错误结果
- **AND** SHALL NOT 为该连接建立任何连接运行时（无私有通道 / 调度器 / 会话）

#### Scenario: 握手携带合法节点号被接纳

- **WHEN** 一个 edge 的握手帧同时携带合法账号号与非空节点号
- **THEN** 云端 SHALL 建立与该节点号绑定的连接运行时，出站命令据此定向投递

### Requirement: Directed edge-command delivery must not implicitly broadcast

定向边缘命令的投递 MUST 只到达唯一的目标节点。当下发未提供目标节点号时，投递 MUST NOT 扇出到任意 edge——SHALL 命中 0 个连接、如实返回投递计数 0、并记录一条警告；缺少目标 SHALL 被当作诚实失败信号，而非广播触发条件。

#### Scenario: 空目标下发不广播

- **WHEN** 一条出站命令在未提供目标节点号（undefined / 空）的情况下被下发，且当前有多个在线 edge
- **THEN** 投递 SHALL NOT 向任何连接发送该命令
- **AND** SHALL 返回投递计数 0 并记录警告

#### Scenario: 带目标下发只命中目标节点

- **WHEN** 一条出站命令携带目标节点号被下发，且存在多个不同节点号的在线 edge
- **THEN** 投递 SHALL 只向节点号等于目标的连接发送
- **AND** 其余节点号的在线 edge SHALL NOT 收到该命令

### Requirement: All-edges broadcast must be explicit

若系统确需向全部在线 edge 广播，该行为 MUST 经一个语义明确、专用于广播的独立操作触发。任何定向投递路径 MUST NOT 通过省略目标节点号来隐式退化为广播。

#### Scenario: 全网广播需走显式操作

- **WHEN** 某功能需要把一条命令送达所有在线 edge
- **THEN** 它 SHALL 调用专用的显式广播操作
- **AND** SHALL NOT 依赖「对定向投递省略目标参数」来达成广播
