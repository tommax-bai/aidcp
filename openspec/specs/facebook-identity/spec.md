# facebook-identity Specification

## Purpose
定义边缘读取 Facebook 登录账号身份（数字 id + 昵称）的契约：数字 id 由 cookie `c_user` / profile 锚点确立；昵称改为**就地、id 锚定**从顶栏头像锚点的 `aria-label` 读取——绝不为取昵称导航 `/me`、非本人主页页不把页面标题当昵称、清洗拒绝标签标题类垃圾、读不到诚实留空。红线：MUST NOT 静默假成功（不猜、不回落 default、不写垃圾名）。
## Requirements
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

### Requirement: 非本人主页页禁用页面标题类昵称来源

当**当前页不是本账号的个人主页**（即当前页 URL 的 profile id 不等于本账号 id）时，页面标题类信号（`document.title`、`og:title`、`h1`）MUST NOT 被用作昵称来源——这些在首页/信息流/群组页等一律是页面标题而非本人姓名。仅当**当前页就是本账号个人主页**（URL 的 profile id === 本账号 id）时，页面标题类信号方 SHALL 可作为昵称来源（本人主页标题即本人姓名）。

#### Scenario: 首页/群页面不拿标签标题当昵称
- **WHEN** 当前页是首页或群组页、`document.title` 为「(4) Facebook」或群名
- **THEN** 系统 MUST NOT 把该标题当作昵称（此时昵称只能来自 id 锚定的头像标签，否则留空）

#### Scenario: 本人主页页可用标题作昵称
- **WHEN** 当前页 URL 为 `profile.php?id=<本账号id>`、标题为「<昵称> | Facebook」
- **THEN** 系统 SHALL 可从标题解析出本人昵称

### Requirement: 昵称清洗拒绝标签标题类垃圾

昵称清洗 SHALL 剥离前导未读计数前缀 `(N) ` 后再判定，并 SHALL 把 `Facebook`、`(N) Facebook`、登录/注册页标题、账号菜单/「你的个人主页 / Your profile / 账户控制选项和设置」等通用外壳标签一律判为空。系统 MUST NOT 将上述任一垃圾字符串作为昵称写入或上报——**宁可留空，绝不写垃圾名**。

#### Scenario: 未读数标题被判空
- **WHEN** 候选昵称为「(4) Facebook」
- **THEN** 清洗结果为空（不作为昵称）

#### Scenario: 通用外壳标签被判空
- **WHEN** 候选昵称为「你的个人主页」「Your profile」「账户控制选项和设置」之一
- **THEN** 清洗结果为空（不作为昵称）

### Requirement: 就地读不到昵称诚实留空、有界重试、不阻断身份

昵称随顶栏异步渲染，系统 SHALL 按**次数上界**就地轮询等待昵称出现（不依赖注入时钟前进以免测试死循环），一旦读到即返回。若耗尽上界仍读不到昵称，系统 MUST 诚实以**空昵称**返回、且 MUST 仍返回已确立的账号 id（昵称缺失 MUST NOT 阻断身份确立），MUST NOT 猜测、MUST NOT 回落到页面标题、MUST NOT 导航。

#### Scenario: 有 id 无昵称——留空但不失败
- **WHEN** 就地能读出账号 id、但轮询耗尽仍无可用昵称
- **THEN** 系统返回 ok（带账号 id、昵称为空），不导航、不失败

#### Scenario: 昵称异步渲染——有界重试内读到
- **WHEN** 首次就地扫描时头像标签尚未渲染、在次数上界内的后续轮询中渲染出现
- **THEN** 系统在读到后即返回该昵称

### Requirement: Facebook 昵称经握手持久化——数字 id 已确立方附带、云端仅库内空时写

Facebook 身份确立 SHALL 始终以稳定的**数字账号 id** 为准；显示名 MUST NOT 用于确立身份。边缘 MAY 在**数字 id 身份已确立后**、于 hello 握手附带一个可选昵称——该昵称来源为本 capability 前述**就地、id 锚定**的读取（绝不为取昵称导航 `/me`）。云端 SHALL 仅在**握手平台校验通过**后，才处理该昵称；若昵称非空且与该账号当前库内昵称不同，云端 MUST 将其持久化为账号昵称。通用标题（如 `Facebook`）或未与匹配数字 id 绑定的显示名 MUST NOT 更新账号昵称。昵称更新 MUST 仅影响显示与人工选择，MUST NOT 改变账号主键、平台校验、路由或任务归因。

#### Scenario: 已验证昵称经握手持久化

- **WHEN** 某 Facebook 边缘已确立账号 id `A`、就地读到一个与 id `A` 绑定的非通用昵称，且该账号当前库内无昵称
- **THEN** 边缘在 hello 附带该昵称，云端在平台校验通过后将其持久化为账号昵称

#### Scenario: 已验证昵称变化经握手更新

- **WHEN** 某 Facebook 边缘已确立账号 id `A`、就地读到一个与 id `A` 绑定的非通用昵称，且该账号当前库内已有不同昵称
- **THEN** 云端在平台校验通过后将账号昵称更新为该已验证昵称

#### Scenario: 通用名或未绑定名被忽略

- **WHEN** 页面只暴露通用标题（如 `Facebook`），或昵称未与匹配的数字 id 绑定
- **THEN** 该昵称被忽略：不确立身份、不更新账号昵称

#### Scenario: 相同昵称不重复写

- **WHEN** 账号库内已有昵称与边缘握手附带的已验证昵称相同
- **THEN** 云端保留既有昵称，不产生不必要的更新

### Requirement: Facebook 启动期本人昵称采集经就地读取、由首个 feed 卡片触发

Facebook 账号的**启动期本人昵称采集** SHALL 复用平台统一的采集时机（完整浏览器启动后首批 `page.cards{startupId}` 触发、同代号只采一次、采空有界重试、超时兜底——见 `account-identity-resolution`）。当云端在该时机对某 Facebook 连接下发本人采集命令（`profile.open{direct}`）时，边缘 MUST **仅就地**读取本人身份与昵称（id 锚定头像标签，与本 capability「就地、绝不为取昵称导航」的既有要求一致），MUST NOT 为本人采集导航到 `profile.php` / `/me` 或任何其他页面。

边缘 SHALL 按**就地读到的**数字 id 与昵称上报本人 `profile.detail`（`authorId` 用就地读到的 id，自校验——读到不匹配的 id 时云端按「非本人」安全忽略、绝不写错账号）。就地读到非空昵称且与库内不同 → 云端差异持久化；就地读空 → 上报空昵称，计一次采空、进有界重试，MUST NOT 猜测、MUST NOT 回落页面标题、MUST NOT 导航。采集完成后的回 feed（`back`）SHALL 经幂等 feed 校准实现——已在 feed 时不重新导航、不整页重载。

hello 握手附带昵称的既有路径（见「Facebook 昵称经握手持久化」）保持不变，作为幸运时更早写入的机会主义路径；可靠且与 XHS 统一的采集时机由本要求的「首个 feed 卡片」触发承担。

#### Scenario: 云端本人采集命令 → 边缘就地读、绝不导航
- **WHEN** 云端在首批 `page.cards` 时机对某 Facebook 连接下发 `profile.open{direct}` 本人采集命令
- **THEN** 边缘就地读取本人 id + 昵称并上报 `profile.detail`，MUST NOT 发起任何 `Page.navigate`（对 `profile.php` / `/me` 或任何页）

#### Scenario: 就地读到非空昵称 → 差异写库
- **WHEN** 边缘就地读到与本账号数字 id 绑定的非空昵称、且与系统库内昵称不同
- **THEN** 云端将账号昵称更新为该已验证昵称，账号 id 与任务归因不变

#### Scenario: 就地读空 → 诚实空、有界重试、不导航
- **WHEN** 首批 feed 时机就地读不到本人昵称（顶栏未水合 / 语言未覆盖等）
- **THEN** 边缘上报空昵称、云端计一次采空并保留原昵称，MUST NOT 写页面标题类垃圾、MUST NOT 为取昵称导航；留待下一个浏览器启动代号在有界预算内重试

#### Scenario: 采集完回 feed 不重载
- **WHEN** 本人就地采集完成后云端派发回 feed 的 `back`
- **THEN** 边缘经幂等 feed 校准处理——因就地读从未离开 feed，`back` 不触发整页重载

