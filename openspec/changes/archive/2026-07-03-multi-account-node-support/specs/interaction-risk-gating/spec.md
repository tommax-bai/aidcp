## ADDED Requirements

### Requirement: 限频闸与计数按连接真实账号解析，绝不钉死 default

云端的互动前限频闸与互动后计数 SHALL 按**发起该决策的连接的真实账号**解析其 `RiskController`（经 per-account 控制器注册表），MUST NOT 钉死在 `default` 控制器上。当连接带有真实 `accountId` 时，闸判定与记账 MUST 同落到该真实账号；MUST NOT 出现「闸看 `default` 而记账看真实账号」的分叉，致真实账号限频形同失效。握手缺失 `accountId` 的连接 MUST NOT 被静默映射成 `default` 账号计入其配额。

#### Scenario: 闸与记账落在同一真实账号
- **WHEN** 账号 A 的连接产生一次点赞意图
- **THEN** 限频判定读 A 的控制器、成功后计数也累加到 A，两者一致，不读 `default` 控制器

#### Scenario: 多账号在线时限频各按其账号
- **WHEN** 账号 A、账号 B 各有连接在线并各自互动
- **THEN** A 的互动只计入 A 的配额、B 的只计入 B 的，互不串算，任一账号超限只拦它自己
