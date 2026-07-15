## MODIFIED Requirements

### Requirement: Facebook identity reader returns stable platform id or fails honestly

The Facebook platform driver SHALL implement identity reading that returns a stable Facebook account identifier suitable for `accounts.account_id` registration/routing, plus an optional display name. Identity candidates MUST come from logged-in page/session signals that are stable enough for routing; raw session tokens or display names alone MUST NOT be used as the account primary key.

**The logged-in `c_user` cookie provides the authoritative numeric self id**：当读到唯一且形态合规的 `c_user` 数字值时，该值 SHALL 作为本连接的自我账号 id。此时页面上出现的**其他用户** `profile.php?id=` 链接（信息流帖子作者、评论者、群成员等）与「自我 id 确立」无关，MUST NOT 被当作自我 id 候选、MUST NOT 触发「候选冲突」失败；本人昵称 SHALL 由 **id 锚定**读取（只认 `href` 数字 id 等于该权威自我 id 的本人锚点），故绝不会把他人名字当作本账号昵称。

「候选冲突 → 诚实失败」SHALL 仅在**自我 id 信号真歧义**时适用——即无权威 `c_user` cookie、需靠页面 profile 链接确立 id 却出现多个互异候选；或本人主页 URL 的 id 与 `c_user` 明确不一致。若无任何稳定 id 可读，edge MUST 诚实失败、MUST NOT 回落 `default`。

#### Scenario: Stable Facebook id read succeeds
- **WHEN** a logged-in Facebook AdsPower profile exposes a consistent stable account id through approved identity signals
- **THEN** edge uses that stable id in hello/account routing and may expose display name separately

#### Scenario: Display name alone is insufficient
- **WHEN** Facebook UI shows a name but no stable id candidate can be verified
- **THEN** edge does not use the name as account id, fails identity resolution honestly, and does not start account-scoped actions

#### Scenario: 权威 c_user 在场时，feed 上的他人 profile 链接不算冲突
- **WHEN** 就地读到唯一合规 `c_user`（=本账号数字 id），当前页为信息流/详情等、页面上同时存在多个**其他用户**的 `profile.php?id=` 链接
- **THEN** edge 以 `c_user` 为自我 id、按 id 锚定读本人昵称（读到即带、读不到留空），MUST NOT 因他人链接判「候选冲突」而失败

#### Scenario: Conflicting identity candidates fail
- **WHEN** 无权威 `c_user` cookie，仅靠页面 profile 链接确立 id 却出现两个互异候选，或本人主页 URL 的 id 与 `c_user` 明确不一致
- **THEN** edge treats identity as inconclusive, reports failure, and does not guess or fall back to `default`
