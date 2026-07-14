## ADDED Requirements

### Requirement: 冷待机期间云连接不可恢复不得触发浏览器重启

When an edge core is already in browser cold standby, exhaustion of the cloud WebSocket reconnect budget SHALL NOT be treated as an ordinary recoverable terminal failure that exits with recycle semantics and asks the supervisor to restart the browser. The edge MUST remain in the cold-standby lifecycle, keep the browser closed, and expose that cloud connectivity is recovering or degraded within standby. A scheduled wake, manual wake, explicit close, or non-standby terminal browser/CDP failure MAY still use the existing recycle/close paths.

#### Scenario: 冷待机云重连耗尽仍保持待机
- **WHEN** the core is in cold standby and cloud WebSocket reconnect attempts are exhausted
- **THEN** the core MUST NOT request recycle shutdown or exit solely because of that cloud reconnect exhaustion
- **AND** the Electron supervisor MUST NOT start a new browser for that environment as a result of this condition
- **AND** the environment remains represented as cold standby with cloud recovery pending

#### Scenario: 非冷待机云不可恢复沿用既有诚实下线
- **WHEN** the core is not in cold standby and cloud reconnect attempts are exhausted
- **THEN** the existing honest shutdown/recycle behavior remains available so the node does not silently pretend to be online

### Requirement: 冷待机子进程退出不得被分类为普通异常重启

The Electron supervisor SHALL classify a child-process close while `coldStandbyPending` or `coldStandbyActive` is set as a standby lifecycle event, not as a normal abnormal exit. It MUST NOT consume ordinary crash-respawn budget or immediately launch a browser unless a scheduled/manual wake explicitly asks it to leave standby.

#### Scenario: 冷待机中子进程退出不立即 respawn
- **WHEN** an edge child process closes while the shell marks the environment as cold-standby pending or active
- **THEN** the shell keeps the environment in standby/degraded-standby state and MUST NOT immediately call the normal environment start flow

#### Scenario: 非冷待机异常退出仍按重起策略处理
- **WHEN** an edge child process closes abnormally outside cold standby
- **THEN** the existing bounded respawn and honest give-up policy continues to apply
