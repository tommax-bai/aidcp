## ADDED Requirements

### Requirement: 云端 WebSocket 意外关闭后边缘必须有界重连或诚实终止

边缘端与云端会话 WebSocket **意外关闭**时，边缘 SHALL 在进程内以有界退避自动重连云端，重连成功后 MUST 重新执行 `edge.hello` 以恢复云端路由注册和云端下发的会话/节奏状态。重连期间边缘 MUST 将云端连接状态标记为 reconnecting/disconnected，MUST NOT 继续把自身表现为可正常收发云端命令。

重连成功后，边缘 MUST 清理旧连接上的瞬态命令状态，MUST NOT 重放旧连接断开前未完成或未确认的云端命令，并 MUST 基于当前真实浏览器页面重新上报结构化快照（如 `page.cards` 或 `note.detail`）交由云端重新决策。断线期间的 in-flight 请求或发布动作 MUST 如实失败、取消或丢弃，MUST NOT 编造成功。

重试耗尽或判定不可达时，边缘 MUST 进入诚实失败路径：停止继续上报、关闭云端连接状态、通过日志/Electron 状态暴露失败原因，并以可重起语义退出或交给看护层处理；MUST NOT 长时间空转占着本地运行态而让云端继续无边缘可路由。

#### Scenario: 云端服务重启后自动重连并重新注册
- **WHEN** 浏览过程中云端 WebSocket 因 `aidcp-cloud.service` 重启而关闭，且网络随后恢复
- **THEN** 边缘进入 reconnecting 状态并按有界退避重连云端
- **AND** 重连成功后重新发送 `edge.hello`，云端恢复该 edge/account 的在线路由注册
- **AND** 边缘应用新的 pacing/session 快照后重新上报当前真实页面快照，使浏览决策环继续推进

#### Scenario: 重连不重放旧连接命令
- **WHEN** 云端 WebSocket 关闭时边缘正在等待旧连接上的请求回包或执行旧连接下发的浏览/发布命令
- **THEN** 边缘将旧连接 pending 请求按连接关闭失败处理，清理旧命令队列或旧 in-flight 状态
- **AND** 重连成功后 MUST NOT 自动重放这些旧命令，而是上报当前页面快照交云端重新下发新命令

#### Scenario: 重连耗尽后诚实失败
- **WHEN** 云端 WebSocket 在配置的次数或时间上限内始终无法重连
- **THEN** 边缘记录并暴露云端重连耗尽状态，停止声称云端已连接
- **AND** 边缘以可重起失败语义退出或移交看护层，MUST NOT 保持一个本地 alive 但云端不可路由的僵尸浏览进程

#### Scenario: 主动关闭不触发自动重连
- **WHEN** 用户停止、会话正常结束或边缘主动下线而关闭云端 WebSocket
- **THEN** 边缘不启动自动重连退避循环，不重新发送 `edge.hello`，并按正常关闭语义退出或待命
