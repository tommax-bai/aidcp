## ADDED Requirements

### Requirement: 关闭浏览器前必须先把浏览循环排空

Edge SHALL drain the browse loop out of its atomic section **before** closing the browser, on every path that closes it (cold standby, pause-to-close, exit, recycle). A stop *request* (`close()`) is not sufficient: the loop may be suspended in an `await` and will resume and touch the page afterwards. The drain MUST be bounded — an operation that hangs MUST NOT be able to hang the standby/shutdown itself — and a drain that exceeds its budget MUST be reported honestly rather than silently proceeding.

#### Scenario: 冷待机关浏览器前等循环退出原子区
- **WHEN** cold standby is entered while the browse loop is running
- **THEN** edge requests the loop to stop, waits (bounded) until its in-flight atomic operation has drained, and only then closes the browser
- **AND** no CDP call is issued after the browser has been closed

#### Scenario: 排空超时如实告警，绝不把待机挂死
- **WHEN** an in-flight operation does not drain within the budget
- **THEN** edge logs an honest warning naming the reason, closes the browser as planned, and reports any aborted in-flight action as `ok:false` (never as success)

### Requirement: 浏览循环启动段必须遵守停止请求并纳入断连处理域

The browse loop's startup segment (initial scan and first snapshot report) SHALL re-check the stop/closing flags after every `await`, and SHALL be covered by the same `CdpDisconnectedError` handling as the command loop. A disconnect that occurs while a stop has been requested is an expected terminal state (the browser was closed on purpose) and MUST result in a clean exit — never in an unhandled "session error".

#### Scenario: 停止请求期间浏览器被关 → 干净退出
- **WHEN** the browser is closed while the loop is in its startup segment and a stop/close has been requested
- **THEN** the loop exits cleanly, reports nothing, and raises no session-level exception

#### Scenario: 非预期断连 → 有界重连，不静默
- **WHEN** CDP disconnects during the startup segment and no stop was requested
- **THEN** edge attempts a bounded reconnect and, on exhaustion, terminates honestly

### Requirement: 页面轮询辅助不得把断连吞成「内容还没来」

Polling helpers that wait for page content SHALL rethrow `CdpDisconnectedError` immediately instead of swallowing it and continuing to poll. Swallowing a disconnect reads "the device is gone" as "the content is slow", burns the entire wall-clock budget in silence, and defers the real failure.

#### Scenario: 浏览器已死时轮询立刻上抛
- **WHEN** the browser is gone and a content-wait helper polls the page
- **THEN** the helper rethrows the disconnect on the first attempt rather than polling until its timeout expires

#### Scenario: 瞬态异常仍保持宽容
- **WHEN** a poll attempt fails for a transient reason (e.g. execution context lost during navigation)
- **THEN** the helper keeps polling as before
