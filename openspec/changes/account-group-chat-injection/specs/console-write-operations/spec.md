## ADDED Requirements

### Requirement: 账号「关联群聊信息」编辑经账号存储单写、诚实非乐观、且 verbatim 存储

账号「关联群聊信息」（`group_chat_info`）编辑 SHALL 经账号存储的一等单写方法完成（按 `account_id` upsert、写后回读真态），面板层受既有 JWT 保护、MUST NOT 用 raw SQL UPDATE 绕过、MUST NOT 报告乐观成功。写路由（`PUT /api/accounts/:id/group-chat-info`）SHALL 返回写后回读的真态；未注入该写依赖时 SHALL 503；未知账号 SHALL 404；坏类型（非 string/null）SHALL 400；退役保留账号 `default` SHALL 被拒且与成功可区分。空 / 空白输入 SHALL 归 NULL（清空）。与既有分组标签写入刻意相反：该值 MUST **verbatim 存储**——MUST NOT `trim`、MUST NOT 截断、MUST 保留 emoji 与换行。该 Requirement 与本 spec「写只经拥有者对象、绝不 raw UPDATE、绝不乐观假成功」的核心不变量同构。

#### Scenario: 写后回真态
- **WHEN** 面板保存某账号的关联群聊信息
- **THEN** 接口经账号存储单写方法落库并返回从存储回读的真态，而非提交即返回的乐观「ok」

#### Scenario: verbatim 不 trim / 不截断
- **WHEN** 保存一串含 emoji、换行、首尾空白的群聊码
- **THEN** 回读值与输入字节一致，未被 trim、未被截断、emoji 完整

#### Scenario: 清空与拒绝可区分
- **WHEN** 分别对某账号提交空输入、对未知账号提交、对退役账号 `default` 提交、提交坏类型
- **THEN** 空输入归 NULL 清空并回真态；未知账号 404；退役账号被拒且与成功可区分；坏类型 400——各自诚实呈现，无一乐观假成功
