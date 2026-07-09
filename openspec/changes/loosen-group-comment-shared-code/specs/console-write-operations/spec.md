## MODIFIED Requirements

### Requirement: 内容排期群评字段写入与开启硬校验（一码一号）

内容排期写通道（`PUT /api/content-schedule/:accountId`）SHALL 新增 `groupCommentEnabled`（布尔）与 `groupCommentDailyCap`（0..10 整数，硬上限与发帖 / 评论的 50 刻意分开）两字段，非法值整块拒、写后回读真态、默认 fail-closed（群评不自动）。写入 `groupCommentEnabled=true` 时 SHALL 执行开启群码校验，含两支：

- **无码硬拒**：该账号未配群码 → 具名拒 `no_group_code`，整块不落库。该硬校验 MUST 在每次开启写入时重跑，MUST NOT 以警告放行、MUST NOT 静默降级、MUST NOT 部分落库。
- **共用放行 + 提示**（一码一号从硬阻断放松）：该账号群码与任一其它账号 verbatim 相同时，MUST NOT 再具名拒绝——SHALL 照常放行落库，并在成功响应带 `sharedGroupCodeWarning: true`。上层 MUST 据此如实提示防关联封号风险，MUST NOT 静默把「共用群码 = 最强跨账号关联指纹」的风险咽下去。放松为运营知情决策，靠小日上限 + 错峰 + 人审 + 明示提示压制、诚实声明非零风险。

#### Scenario: 无码账号开启被拒
- **WHEN** 为一个未配群码的账号提交 `groupCommentEnabled=true`
- **THEN** 具名拒绝 `no_group_code`、整块不落库，拒绝与成功可区分呈现

#### Scenario: 同码账号开启放行并回带风险警告（一码一号放松）
- **WHEN** 该账号的群码与另一账号的群码逐字节相同、提交 `groupCommentEnabled=true`
- **THEN** 开关照常落库、成功响应带 `sharedGroupCodeWarning: true`；上层 MUST 弹一条防关联封号风险提示，MUST NOT 静默放行

#### Scenario: 群评上限越界整块拒
- **WHEN** 提交 `groupCommentDailyCap` 为 -1、0.5 或 11
- **THEN** 整块拒绝、绝不部分落库
