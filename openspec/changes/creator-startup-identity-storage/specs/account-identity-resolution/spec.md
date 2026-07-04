# account-identity-resolution Specification (delta)

## MODIFIED Requirements

### Requirement: 账号身份来自登录态读出的稳定 id，读不出即诚实失败

节点 SHALL 在登录完成后从登录态**读出该账号的稳定标识（如平台 userid）**作为账号身份，MUST NOT 以昵称作为身份主键（昵称仅作显示名）。读不出稳定 id 时 MUST **诚实失败、停手**，MUST NOT 猜测、MUST NOT 回落 `default`（否则等于借默认账号/默认人设静默开跑，违反「绝不静默假成功」）。

当启动期浏览器当前停在 `creator.xiaohongshu.com` 的真实创作平台页面（非 `/login`）时，该页面的登录门禁只证明"登录在场"；节点 MAY 进一步只读同源登录态存储中的平台 userid 字段来确立稳定账号 id。该路径 MUST 只接受形态合规且候选一致的稳定 id，MUST NOT 用右上角昵称、展示名、手机号、cookie/session token、畸形值或冲突值作为账号身份。若当前页是 `creator.xiaohongshu.com/login`，或创作平台同源存储无法给出可信稳定 id，节点 MUST 诚实失败或继续既有可证明安全的身份读取兜底，MUST NOT 猜测。

#### Scenario: 登录后读出稳定 id 作为身份
- **WHEN** 操作者在某节点的浏览器里登录了一个真实账号
- **THEN** 节点从登录态读出该账号的稳定 id，并以它作为该节点的账号身份（而非启动器外部指派的标签）

#### Scenario: 启动期停在创作平台真实页
- **WHEN** 节点启动后附着的浏览器页是 `creator.xiaohongshu.com` 的非 `/login` 页面，且同源登录态存储包含一致的形态合规 userid
- **THEN** 节点 MAY 用该 userid 确立账号身份并继续握手，MUST NOT 因消费端「我」锚点缺失而直接停手

#### Scenario: 创作平台只显示昵称但无可信稳定 id
- **WHEN** 创作平台页面右上角显示昵称，但同源登录态存储没有形态合规且一致的稳定 userid
- **THEN** 节点 MUST NOT 用昵称当主键，MUST 继续既有安全兜底或诚实失败停手

#### Scenario: 读不出稳定 id → 诚实失败，不回落 default
- **WHEN** 登录已完成但节点无法读出稳定账号 id
- **THEN** 节点诚实失败、停手并告警，绝不猜一个 id、绝不以 `default` 或任何默认身份开跑

#### Scenario: 昵称仅作显示名、不作主键
- **WHEN** 系统需要标识/区分账号
- **THEN** 用稳定 id 作主键，昵称只用于展示；昵称变化 MUST NOT 改变账号主键

