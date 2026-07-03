## ADDED Requirements

### Requirement: 账号分组标签编辑经账号存储单写、写后回真态、诚实可区分

来自管理后台的账号分组标签（`accounts.group_label`）编辑 SHALL 只经账号存储（`accounts` 表行属性的拥有者）的一等单写方法 `setGroupLabel(accountId, label)` 完成，与既有 `setNickname` 同构。面板层 MUST NOT 持有或使用对 `accounts` 表的 raw SQL UPDATE 能力，MUST NOT 报告乐观成功。

分组写 SHALL 经受既有 JWT 保护的写路由（`PUT /api/accounts/:id/group-label`，body `{ groupLabel }`）触发，且：

- 写方法 SHALL 用 UPDATE-only 语义（`WHERE account_id`），MUST NOT 在账号行不存在时 seed 造行；行不存在 SHALL 作为「未找到」**与成功可区分地**返回，绝不静默成功。
- 写方法 SHALL 对入参做 `trim`：trim 后为空（空串 / 纯空白 / 缺省）SHALL 写入 NULL（即**清空分组**），MUST NOT 存入纯空白脏值。
- 写方法 SHALL 拒绝退役保留账号 `default`（`RETIRED_ACCOUNT_ID`），不写、不静默成功。
- 接口 SHALL 返回从存储回读的写后真实分组值（`RETURNING`），而非提交即返回的乐观「ok」。

该编辑 MUST NOT 触碰风控最终状态单写路径、MUST NOT 走边-云协议、MUST NOT 涉及边缘端——是纯账号属性编辑。前端「分组」列编辑 SHALL 非乐观：round-trip 成功后重新拉取账号列表以显示真态，只读账号视图（不传保存回调）SHALL 保持纯文本、不受影响。

#### Scenario: 写后回读真态而非乐观 ok
- **WHEN** 运营在账号列表点击「分组」单元格、输入一个分组名并保存
- **THEN** 接口经账号存储 `setGroupLabel` 落库并返回 `RETURNING` 回读的分组值，前端 round-trip 后重新拉取账号列表显示该真态，绝不提交即报成功

#### Scenario: 空输入清空分组
- **WHEN** 运营把某账号的「分组」输入清空（空串 / 纯空白）并保存
- **THEN** 账号存储把 `group_label` 写为 NULL（分组被清除），MUST NOT 存入纯空白脏值

#### Scenario: 不存在的账号可区分为未找到
- **WHEN** 分组写请求的 `account_id` 在 `accounts` 表无对应行
- **THEN** UPDATE-only 影响 0 行，接口把结果作为「未找到」返回、与成功可区分，MUST NOT seed 造出幽灵账号行、MUST NOT 静默成功

#### Scenario: 拒绝退役保留账号
- **WHEN** 分组写请求针对退役保留账号 `default`
- **THEN** `setGroupLabel` 拒绝该写、不落库、不静默成功

#### Scenario: 面板层绝不 raw UPDATE 绕过所有者
- **WHEN** 面板需要写账号分组标签
- **THEN** 改动经账号存储的 `setGroupLabel` 单写方法进行，面板层不持有也不使用对 `accounts` 表的 raw SQL UPDATE 能力
