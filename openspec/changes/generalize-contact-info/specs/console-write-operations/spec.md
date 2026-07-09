## RENAMED Requirements

- FROM: `### Requirement: 账号「关联群聊信息」编辑经账号存储单写、诚实非乐观、且 verbatim 存储`
- TO: `### Requirement: 账号「联系方式」编辑经账号存储单写、诚实非乐观、且 verbatim 存储`

- FROM: `### Requirement: 内容排期群评字段写入与开启硬校验（一码一号）`
- TO: `### Requirement: 内容排期带联系方式评论字段写入与开启校验（无联系方式硬拒、共用放行 + 提示）`

## MODIFIED Requirements

### Requirement: 账号「联系方式」编辑经账号存储单写、诚实非乐观、且 verbatim 存储

账号「联系方式」（`contact_info`）编辑 SHALL 经账号存储的一等单写方法完成（按 `account_id` upsert、写后回读真态），面板层受既有 JWT 保护、MUST NOT 用 raw SQL UPDATE 绕过、MUST NOT 报告乐观成功。写路由（`PUT /api/accounts/:id/contact-info`）SHALL 返回写后回读的真态；未注入该写依赖时 SHALL 503；未知账号 SHALL 404；坏类型（非 string/null）SHALL 400；退役保留账号 `default` SHALL 被拒且与成功可区分。空 / 空白输入 SHALL 归 NULL（清空）。与既有分组标签写入刻意相反：该值 MUST **verbatim 存储**——MUST NOT `trim`、MUST NOT 截断、MUST 保留 emoji 与换行。该 Requirement 与本 spec「写只经拥有者对象、绝不 raw UPDATE、绝不乐观假成功」的核心不变量同构。

#### Scenario: 写后回真态
- **WHEN** 面板保存某账号的联系方式
- **THEN** 接口经账号存储单写方法落库并返回从存储回读的真态，而非提交即返回的乐观「ok」

#### Scenario: verbatim 不 trim / 不截断
- **WHEN** 保存一串含 emoji、换行、首尾空白的联系方式
- **THEN** 回读值与输入字节一致，未被 trim、未被截断、emoji 完整

#### Scenario: 清空与拒绝可区分
- **WHEN** 分别对某账号提交空输入、对未知账号提交、对退役账号 `default` 提交、提交坏类型
- **THEN** 空输入归 NULL 清空并回真态；未知账号 404；退役账号被拒且与成功可区分；坏类型 400——各自诚实呈现，无一乐观假成功

### Requirement: 内容排期带联系方式评论字段写入与开启校验（无联系方式硬拒、共用放行 + 提示）

内容排期写通道（`PUT /api/content-schedule/:accountId`）SHALL 新增 `contactCommentEnabled`（布尔）与 `contactCommentDailyCap`（0..10 整数，硬上限与发帖 / 评论的 50 刻意分开）两字段，非法值整块拒、写后回读真态、默认 fail-closed（带联系方式评论不自动）。写入 `contactCommentEnabled=true` 时 SHALL 执行开启联系方式校验，含两支：

- **无联系方式硬拒**：该账号未配联系方式 → 具名拒 `no_contact_info`，整块不落库。该硬校验 MUST 在每次开启写入时重跑，MUST NOT 以警告放行、MUST NOT 静默降级、MUST NOT 部分落库。
- **共用放行 + 提示**（一码一号从硬阻断放松，change `loosen-group-comment-shared-code`）：该账号联系方式与任一其它账号 verbatim 相同时，MUST NOT 再具名拒绝——SHALL 照常放行落库，并在成功响应带 `sharedContactInfoWarning: true`。上层 MUST 据此如实提示防关联封号风险，MUST NOT 静默把「共用联系方式 = 最强跨账号关联指纹」的风险咽下去。放松为运营知情决策，靠小日上限 + 错峰 + 人审 + 明示提示压制、诚实声明非零风险。

#### Scenario: 无联系方式账号开启被拒
- **WHEN** 为一个未配联系方式的账号提交 `contactCommentEnabled=true`
- **THEN** 具名拒绝 `no_contact_info`、整块不落库，拒绝与成功可区分呈现

#### Scenario: 同联系方式账号开启放行并回带风险警告（一码一号放松）
- **WHEN** 该账号的联系方式与另一账号的联系方式逐字节相同、提交 `contactCommentEnabled=true`
- **THEN** 开关照常落库、成功响应带 `sharedContactInfoWarning: true`；上层 MUST 弹一条防关联封号风险提示，MUST NOT 静默放行

#### Scenario: 带联系方式评论上限越界整块拒
- **WHEN** 提交 `contactCommentDailyCap` 为 -1、0.5 或 11
- **THEN** 整块拒绝、绝不部分落库
