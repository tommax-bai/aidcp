## ADDED Requirements

### Requirement: 程序化 Facebook 环境归属与默认慢启动原子完成

customer-auth 的程序化环境归属完成接口 SHALL 接受可选布尔字段 `slowStartEnabled`，并保持省略该字段的旧客户端请求兼容。`slowStartEnabled=true` MUST 仅在同一请求的规范平台为 `facebook` 时接受；小红书、视频号、未知平台或非布尔值 MUST fail-closed，且不得部分注册环境或写入归属。

首次成功完成 Facebook 创建 intent 时，Cloud SHALL 在同一数据库事务中插入环境、写入唯一客户归属、完成 intent，并把 `client_environments.slow_start_since` 写为服务端当前时刻所属上海自然日的 00:00，同时显式标记初始化完成。慢启动起点 MUST NOT 取 Edge 时钟、账号入库时间、Cookie 时间或 `accounts.slow_start_since`。

已完成 intent 的幂等重试 MUST 只返回既成归属，不得再次写入或重置慢启动起点；若运营在首次完成后手动关闭慢启动，陈旧重试 MUST NOT 重新开启。接口不得修改风控档位、风险状态、账号旧慢启动列或其它环境配置。

#### Scenario: Facebook 创建原子写入 D1 起点

- **WHEN** 有效客户使用待完成 intent 注册一个全新 Facebook 环境并提交 `slowStartEnabled=true`
- **THEN** 环境、归属、intent 完成态与上海当日 00:00 慢启动起点在同一事务中提交

#### Scenario: 旧客户端省略字段保持兼容

- **WHEN** 有效旧客户端完成环境归属但未提交 `slowStartEnabled`
- **THEN** 请求继续按既有规则成功，环境慢启动字段保持 NULL

#### Scenario: 非 Facebook 开启意图原子拒绝

- **WHEN** 请求以小红书、视频号或未知平台提交 `slowStartEnabled=true`
- **THEN** Cloud 在注册环境前拒绝整个请求，环境、归属和 intent 均不发生部分写入

#### Scenario: 完成重试不重置或复活慢启动

- **WHEN** Facebook intent 已成功完成，随后同一 intent/环境被再次提交
- **THEN** Cloud 返回幂等成功但不更新 `slow_start_since`
- **AND** 即使该环境已被运营手动关闭，也不得重新开启

