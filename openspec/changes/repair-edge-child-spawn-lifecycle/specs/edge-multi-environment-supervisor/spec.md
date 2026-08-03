## ADDED Requirements

### Requirement: The supervisor SHALL observe a spawned child before fallible post-spawn setup

Immediately after `spawn()` returns, the desktop supervisor SHALL assume ownership of that child, create its launch-readiness waiter, and register IPC message, `error`, `exit`, and `close` observers plus any available stdout and stderr observers before proxy-authority pipe delivery, queue release, or status publication. A synchronous exception during later setup MUST settle that launch as failed, release its waiting reservation, expose a stable lifecycle-scoped failure, and best-effort terminate the child while retaining ownership until a terminal observer reaps it. A setup failure MUST remain retryable under the bounded respawn policy even when the cleanup signal produces a graceful `code=0` exit.

#### Scenario: Initial status projection throws after spawn

- **WHEN** the child exists but initial post-spawn status construction or publication throws synchronously
- **THEN** launch readiness settles as failed, the child is asked to terminate, and its observed terminal event clears the handle and advances waiting work
- **AND** the environment MUST NOT remain indefinitely `starting` without a live child, queue position, or scheduled retry

#### Scenario: Spawn fails without stdio streams

- **WHEN** `spawn()` returns a child that has no stdout or stderr stream and then emits a pre-spawn `error`
- **THEN** the already-installed spawn-error observer handles the terminal failure exactly once and releases the environment through the existing bounded failure or respawn path

#### Scenario: Already-spawned child reports a kill or send error

- **WHEN** a child with confirmed process ownership emits `error` because a kill or IPC send could not be delivered
- **THEN** the supervisor records that delivery failure but MUST retain child ownership and MUST NOT start a replacement until `exit` or `close` confirms process termination

#### Scenario: Known proxy setup terminal is reaped

- **WHEN** the proxy-authority pipe is unavailable after spawn and the cleanup signal later terminates the child
- **THEN** the supervisor preserves the actionable proxy failure, clears the child through the common finalizer, and MUST NOT reinterpret cleanup `SIGTERM` as a retryable crash

#### Scenario: Exit arrives but stdio close is delayed

- **WHEN** the child OS process exits and inherited stdout or stderr delays `close`
- **THEN** launch readiness and execution capacity are released immediately, while terminal log classification remains bounded by the existing close-drain grace period
