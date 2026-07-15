## MODIFIED Requirements

### Requirement: Facebook 昵称就地读取——id 锚定头像标签，绝不导航 /me

边缘读取 Facebook 登录账号昵称时 SHALL **仅就地**从当前页 DOM 读取，MUST NOT 为取昵称而 `Page.navigate` 到 `/me` 或任何其他页面。昵称来源 SHALL 为**本人 profile 锚点的 `aria-label`**：锚点 `href` 解析出的数字 id 等于该连接已确立的账号 id（或 `href` 为 `/me` 自链）方视为本人；取其 `aria-label` 去除**本人自链后缀**——包括头像后缀（`…的头像` / `…的大头像` / `…的大頭貼` / `…'s profile picture/photo/avatar`）与**时间线后缀**（`…的时间线` / `…的時間線` / `…'s timeline`）——后得到昵称（中文界面下个人主页链接常用「<名>的时间线」而非「<名>的头像」）。因 id 锚定，系统 MUST NOT 把非本人锚点（其他用户/主页）的名字当作本账号昵称。数字账号 id 的确立逻辑（cookie `c_user` / profile 链接 / profile URL）SHALL 保持不变，本要求只改昵称这一路来源。

#### Scenario: 就地从头像锚点读出昵称
- **WHEN** 当前页存在一个 `href` 数字 id 等于本账号 id 的头像锚点、其 `aria-label` 形如「<昵称>的头像」
- **THEN** 系统读出该昵称，且**不**发起任何到 `/me` 的导航

#### Scenario: 就地从时间线自链读出昵称（中文界面变体）
- **WHEN** 当前页存在一个 `href` 数字 id 等于本账号 id 的本人主页链接、其 `aria-label` 形如「<昵称>的时间线」（或繁体「<昵称>的時間線」/ 英文「<name>'s timeline」）
- **THEN** 系统剥离时间线后缀读出该昵称，且**不**发起任何到 `/me` 的导航

#### Scenario: 绝不导航取昵称
- **WHEN** 当前页就地读不到本人昵称
- **THEN** 系统 MUST NOT 为取昵称发起 `Page.navigate`（对 `/me` 或其他任何页）

#### Scenario: id 锚定拒绝他人名字
- **WHEN** 当前页存在多个 profile 锚点、仅其中 id 等于本账号 id 的那个带本人自链后缀标签
- **THEN** 系统只采该锚点的名字，MUST NOT 采用其他 id 的锚点名字
