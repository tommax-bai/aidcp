## ADDED Requirements

### Requirement: 握手时自动登记新账号

云端 SHALL 在 edge 以一个未登记的 `accountId` 握手时，对 `accounts` 主表做一次**幂等 upsert**，使该账号以一个**显式状态**出现在主表（从而在后台账号列表即时可见、等待配置人设）。该 upsert MUST NOT 覆盖一个已被运营配置过的同名账号行（不抹掉既有 `status`/标签/绑定），MUST NOT 把无显式状态的行默认成 `active`（与既有「去掉默认 active 回退」一致）。

#### Scenario: 新账号握手后出现在主表
- **WHEN** 一个此前不存在于 `accounts` 的 `accountId` 首次握手接入
- **THEN** 该账号以显式状态被登记进主表，后台账号列表可见，且不被默认成 `active`

#### Scenario: 已配置账号不被握手 upsert 覆盖
- **WHEN** 一个已被运营配置（如已暂停、已绑人设）的账号再次握手
- **THEN** 其既有行不被 upsert 抹掉或重置，配置保持

### Requirement: 账号人设绑定状态为派生字段

账号是否已绑人设 SHALL 作为一个**派生字段**对外暴露，以**人设存储中是否存在该账号的人设行**为唯一判据。死列 `accounts.persona_ref` MUST NOT 被用作绑定指针（保留不用）。

#### Scenario: 绑定状态以人设行存在为准
- **WHEN** 计算某账号的人设绑定状态
- **THEN** 有人设行 → 已绑，无人设行 → 未绑；不读取/不依赖 `persona_ref` 列
