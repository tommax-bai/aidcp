## MODIFIED Requirements

### Requirement: 内容排期写入经一等单写通道，UPSERT 前校验账号存在，默认 fail-closed

内容排期写入——每账号 `PUT /api/content-schedule/:accountId` 与全局拥有端点——SHALL 经 JWT 保护的一等单写通道，MUST NOT raw SQL UPDATE，MUST NOT 报告乐观成功。账号端点 SHALL 接受既有自动化字段及可选 `activeWeekMask`、`contentActiveMask`；两个掩码均只接受合法 168 位 '0'/'1' 或 NULL，NULL 表示清除该层覆盖并恢复继承。一次账号请求中的两个掩码 SHALL 在同一 UPSERT 中整体验证、原子落库并回读真态，任一非法则整块不落库。

账号 UPSERT 前 SHALL 校验 `accounts` 中存在真实非退役账号；未知或退役账号必须具名拒绝且不得产生幽灵行。只提交掩码不得改变未提交的总开关、动作模式或日上限。列表/回读 SHALL 可区分原始覆盖、继承来源和当前生效值，使 Console 不自行猜测服务端继承结果。

#### Scenario: 两个账号掩码原子写后回真态

- **WHEN** 运营为真实账号一次提交合法活跃掩码和内容掩码
- **THEN** 单写方法在同一 UPSERT 保存两者并返回回读真态，两个字段不得出现部分成功

#### Scenario: 清空覆盖恢复继承

- **WHEN** 账号请求对两个掩码提交 NULL
- **THEN** 服务端清空两个覆盖并回读来源为全局，未提交的自动化字段保持原值

#### Scenario: 未知账号拒、不造幽灵行

- **WHEN** 对不存在或退役账号提交账号排期
- **THEN** 接口具名拒绝并且不得 UPSERT 出孤儿排期行

#### Scenario: 任一非法值整块拒

- **WHEN** 同一请求中的任一掩码非法，或任一其它字段类型/范围非法
- **THEN** 整个请求拒绝、所有字段保持写前真态，拒绝与成功可区分呈现
