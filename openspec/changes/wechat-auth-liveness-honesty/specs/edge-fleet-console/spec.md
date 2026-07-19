## ADDED Requirements

### Requirement: 环境栏鲜活度必须由独立于业务成功的真实控制面往返维持

对于已完成 Cloud 握手且核心仍在运行的视频号环境，Edge SHALL 使用不依赖浏览器、平台鉴权或业务同步成功的 Cloud 请求/响应往返作为控制面鲜活度证据。只有收到与请求匹配的成功响应后才 SHALL 刷新桌面环境栏的鲜活度；本地定时器触发、请求发出、请求失败或超时本身 MUST NOT 被当作在线证据。

控制面鲜活度只证明引擎与 Cloud 在线，MUST NOT 提升视频号鉴权、只读探针或写能力状态。持续没有真实往返证据时，既有 stale 阈值 SHALL 继续把环境收敛为“失联”。

#### Scenario: 鉴权未完成但控制面往返正常时不误报失联

- **WHEN** 视频号核心已与 Cloud 握手，鉴权处于 `login_required`、`reauth_required` 或浏览器启动失败后的可恢复状态，且周期性 `ping` 收到匹配 `pong`
- **THEN** 环境栏鲜活度持续更新，MUST NOT 仅因没有业务同步日志而显示“失联”
- **AND** 互动工作区仍如实显示原授权状态，MUST NOT 显示“鉴权通过”

#### Scenario: 心跳请求失败不得冒充在线

- **WHEN** 控制面心跳请求失败、超时或收到非匹配响应
- **THEN** Edge MUST NOT 输出成功心跳或刷新环境栏鲜活度
- **AND** 持续超过既有 stale 阈值后，环境栏 SHALL 如实显示“失联”

#### Scenario: 心跳不得并发堆积

- **WHEN** 上一个控制面心跳仍在等待响应而下一个周期到达
- **THEN** Edge MUST NOT 再发起并行心跳
- **AND** 后续周期在前一请求结束后 SHALL 恢复正常探测
