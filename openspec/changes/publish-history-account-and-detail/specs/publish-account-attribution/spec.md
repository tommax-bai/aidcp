## ADDED Requirements

### Requirement: 发帖触发携带真实账号并贯穿落库

发帖触发 SHALL 携带一个目标 `accountId`，并把它一路贯穿到人设解析、内容编排与记录落库：人设 MUST 经 `getSoul(accountId)`/`resolveSoul(accountId)` 按该账号解析；`publish_log` 写入时 MUST 把该 `accountId` 写入 `account_id` 列（不再恒为 `default`、不再依赖列默认值）。为保持现役单账号路径零回归，触发**省略**账号时 SHALL 回落到 `default`。

#### Scenario: 指定账号触发 → 该账号人设 + 落真实 account_id
- **WHEN** 以 `accountId = A`（A≠default）触发一次发布
- **THEN** 人设按 A 解析、内容据 A 的人设生成，且 `publish_log` 该行 `account_id = 'A'`

#### Scenario: 省略账号 → 回落 default、行为不变
- **WHEN** 触发未指定账号
- **THEN** 系统按 `default` 解析人设并落 `account_id = 'default'`，与现役单账号行为一致

#### Scenario: 记录账号等于真正发帖的账号
- **WHEN** 一次发布以账号 A 完成
- **THEN** `publish_log` 记录的 `account_id` 与实际发帖账号一致，MUST NOT 记成 `default` 或其他账号

### Requirement: 发布命令定向下发到绑定该账号的在线边缘节点

发布命令下发 SHALL 解析「目标账号 → 绑定该账号的在线边缘连接」并**定向**发送（凭连接 hello 期登记的账号绑定），MUST NOT 广播给所有边缘。当目标账号当前没有在线边缘节点时，系统 MUST 诚实判本次发布失败（带可定位原因，如 `no_edge_for_account`），MUST NOT 退回广播、MUST NOT 伪造成功。当同一账号存在多条在线连接时，系统 SHALL 取确定性的单一目标并记录日志（完整同账号多节点协调不在本能力范围）。

#### Scenario: 有在线节点 → 定向下发、不广播
- **WHEN** 账号 A 有一条在线边缘连接，触发以 A 发布
- **THEN** 发布命令只发往 A 的那条连接，其他账号的边缘不收到本次发布命令

#### Scenario: 目标账号无在线节点 → 诚实失败
- **WHEN** 触发以账号 B 发布，但当前没有任何在线边缘绑定 B
- **THEN** 本次发布判 `failed` 并带 `no_edge_for_account` 类原因，系统不广播、不下发到别的账号、不报成功

#### Scenario: 红线反例——无目标退回广播（禁止）
- **WHEN** 解析不到目标账号的在线节点，有实现想退回 `pushToEdges(env)` 广播以「至少发出去」
- **THEN** 这违反定向下发与诚实失败，MUST 被拒绝；正确行为是诚实判失败、不发送
