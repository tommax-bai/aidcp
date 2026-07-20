## ADDED Requirements

### Requirement: 监督器 SHALL 分别监督每环境核心与浏览器执行器

桌面监督器 SHALL 为每个环境维护独立的核心句柄和浏览器执行器句柄。核心退出只触发核心的有界退避重启，不得顺带启动浏览器；浏览器退出只更新执行器和受影响页面任务，不得终止核心。两类资源 MUST 使用独立并发预算，浏览器槽位不得限制核心数。

#### Scenario: 核心重启保持浏览器关闭

- **WHEN** 浏览器关闭的环境 core 意外退出且仍满足客户归属条件
- **THEN** 监督器按核心退避预算恢复 core，整个恢复过程不得调用 provider 或进入浏览器槽位队列

#### Scenario: 浏览器故障不重启核心

- **WHEN** 环境 core 正常而浏览器执行器崩溃
- **THEN** 监督器只回收执行器并诚实更新页面任务，核心 PID/会话不因该故障被普通 restart 流程替换

### Requirement: 批量核心 bootstrap MUST 有界且不复用浏览器启动队列

客户登录后的多环境核心 bootstrap SHALL 使用专用的有界并发、指数退避、抖动与每环境熔断；MUST NOT 通过 AdsPower 串行队列、浏览器槽位或 `queueStartEnv` 实现。一个环境失败 MUST NOT 阻塞其他环境，达到熔断阈值时该环境 SHALL 停在具名 `core=error` 直至显式恢复或条件变化。

#### Scenario: 十六环境登录不造成同时重连风暴

- **WHEN** roster 一次返回十六个可信环境
- **THEN** 监督器按核心专用并发上限分批 bootstrap 并对失败使用抖动退避，MUST NOT 同时启动十六个浏览器或让一个失败环境卡住队列

### Requirement: offboard 恢复 MUST 使用无浏览器的受限清理会话

未完成的 offboard 清理 SHALL 使用 Cloud 签发并绑定 `offboardId/envKey/accountId/edgeId` 的短期单用途凭证启动受限核心会话。该会话仅可领取和回报对应清理命令，MUST NOT 注册普通任务能力、恢复通用客户会话、调用 `queueStartEnv` 或启动浏览器。凭证过期、已使用或绑定不匹配时 MUST 诚实失败并进入人工处理。

#### Scenario: 客户端重启后恢复 offboard 清理

- **WHEN** 客户端重启时发现一个持久化的未完成 offboard 清理且凭证仍有效
- **THEN** 监督器启动受限浏览器无关会话完成清理和回执，浏览器状态全程保持 `closed`

#### Scenario: 清理凭证与环境不匹配

- **WHEN** 受限会话携带的凭证绑定到另一个环境或已经过期
- **THEN** Cloud 拒绝清理命令，客户端不得降级为普通环境启动或打开浏览器重试
