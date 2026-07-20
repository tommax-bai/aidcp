## MODIFIED Requirements

### Requirement: Facebook 昵称就地读取——id 锚定头像标签，绝不导航 /me

边缘读取 Facebook 登录账号昵称时 SHALL 从**当前 Facebook 页面 DOM**读取，MUST NOT 为取昵称导航到 `/me`、数字 profile URL 或任何作者主页。仅在**启动期身份首读显式允许导航**、且当前 tab 为 `about:blank` 或其他非 Facebook 上下文时，系统 MAY 一次性引导到 Facebook 消费端首页，再在该页就地采集；运行期身份校验、登录轮询与 `profile.open{direct}` 本人采集 MUST 禁止该引导并保持纯就地读取。

昵称来源 SHALL 为**本人 profile 锚点**：锚点 `href` 解析出的数字 id 等于该连接已确立的账号 id（或 `href` 为 `/me` 自链）方视为本人。系统 SHALL 优先从其 `aria-label` 去除已知本人自链后缀取得昵称；若本地化标签无法按后缀安全解析，系统 SHALL 可使用该同一 id 锚定锚点的可见文本并经通用名清洗后取得昵称。因 id 锚定，系统 MUST NOT 把非本人锚点（其他用户/主页）的标签或文本当作本账号昵称。数字账号 id 的确立逻辑（cookie `c_user` / profile 链接 / profile URL）SHALL 保持不变，显示文本 MUST NOT 用于确立账号 id。

#### Scenario: 就地从头像锚点读出昵称
- **WHEN** 当前 Facebook 页存在一个 `href` 数字 id 等于本账号 id 的头像锚点、其 `aria-label` 形如「<昵称>的头像」
- **THEN** 系统读出该昵称，且不发起任何页面导航

#### Scenario: 就地从时间线自链读出昵称（中文界面变体）
- **WHEN** 当前 Facebook 页存在一个 `href` 数字 id 等于本账号 id 的本人主页链接、其 `aria-label` 形如「<昵称>的时间线」（或繁体「<昵称>的時間線」/ 英文「<name>'s timeline」）
- **THEN** 系统剥离时间线后缀读出该昵称，且不发起任何页面导航

#### Scenario: 本地化 aria 不支持时读取本人锚点可见文本
- **WHEN** 当前 Facebook 页存在与本账号数字 id 匹配的本人锚点，其 `aria-label` 使用未覆盖的本地化语法而可见文本为非通用昵称
- **THEN** 系统从该 id 锚定锚点的可见文本读出昵称，MUST NOT 要求新增该语言的后缀正则

#### Scenario: 启动首读从空白 tab 引导到 Facebook 首页
- **WHEN** Facebook 启动期身份首读显式允许导航，当前 tab 为 `about:blank` 或非 Facebook 页面
- **THEN** 系统 MAY 导航一次到 Facebook 消费端首页并有界等待页面身份信号，MUST NOT 导航到 `/me`、数字 profile URL 或作者主页

#### Scenario: 运行期读不到昵称绝不导航
- **WHEN** 运行期身份校验、登录轮询或 `profile.open{direct}` 就地读不到本人昵称
- **THEN** 系统 MUST NOT 发起任何 `Page.navigate`，并按既有契约返回空昵称或诚实失败

#### Scenario: id 锚定拒绝他人名字
- **WHEN** 当前页存在多个 profile 锚点、仅其中一个 id 等于本账号 id
- **THEN** 系统只采本人锚点的标签或可见文本，MUST NOT 采用其他 id 的锚点名字

### Requirement: Facebook 启动期本人昵称采集经就地读取、由首个 feed 卡片触发

Facebook 账号的启动期昵称刷新 SHALL 优先由**启动身份首读**完成：当前 tab 尚非 Facebook 页面且首读显式允许导航时，边缘先一次性引导到 Facebook 消费端首页并有界等待，再从与稳定数字 id 绑定的本人锚点就地读取昵称；读到非空昵称后经 hello 附带，云端按既有平台校验与差异写规则持久化。该主路径 MUST NOT 依赖 `page.cards` 是否产生。

完整浏览器启动后首批 `page.cards{startupId}` 触发的 Cloud 本人采集 SHALL 保留为**二次就地机会**。Cloud 在该时机下发 `profile.open{direct}` 时，边缘 MUST 仅就地读取本人身份与昵称，MUST NOT 导航到 `profile.php`、`/me` 或任何其他页面。边缘 SHALL 按就地读到的数字 id 与昵称上报本人 `profile.detail`；读到不匹配 id 时云端 SHALL 按非本人安全忽略。就地读空 SHALL 上报空昵称并保留原系统昵称，MUST NOT 猜测或用页面标题覆盖。

#### Scenario: 页面就绪后的 hello 昵称不依赖 feed 卡片
- **WHEN** Facebook 启动首读在消费端页面读到与稳定 id 绑定的昵称，但当前 feed 布局没有产出 `page.cards`
- **THEN** 边缘仍在 hello 附带该昵称，云端按既有差异写路径更新显示名

#### Scenario: 云端本人采集命令仍严格就地读
- **WHEN** 云端在首批 `page.cards` 时机对某 Facebook 连接下发 `profile.open{direct}` 本人采集命令
- **THEN** 边缘就地读取本人 id + 昵称并上报 `profile.detail`，MUST NOT 发起任何 `Page.navigate`

#### Scenario: 就地读到非空昵称后差异写库
- **WHEN** 启动 hello 或二次就地采集读到与本账号数字 id 绑定的非空昵称、且与系统库内昵称不同
- **THEN** 云端将账号昵称更新为该已验证昵称，账号 id 与任务归因不变

#### Scenario: 就地读空诚实保留原昵称
- **WHEN** 有界预算内仍读不到与本人 id 绑定的昵称
- **THEN** 系统保留原昵称，MUST NOT 写页面标题类垃圾、MUST NOT 猜测或为昵称跳转个人主页

#### Scenario: 二次采集完回 feed 不重载
- **WHEN** `profile.open{direct}` 就地采集完成后云端派发回 feed 的 `back`
- **THEN** 边缘经幂等 feed 校准处理，因就地读从未离开 feed 而不触发整页重载

## ADDED Requirements

### Requirement: Facebook 启动昵称等待业务页面就绪而非空白文档 load 完成

当启动身份首读从 `about:blank` 或非 Facebook 页面开始时，系统 SHALL 将“已进入允许的 Facebook 页面上下文并出现可与稳定 id 绑定的本人信号”作为昵称可采集成功条件，MUST NOT 将 `about:blank` 的 `document.readyState=complete` 当作 Facebook 页面已经就绪。等待 SHALL 有次数或时长上界；上界耗尽但 `c_user` 已确立稳定 id 时 SHALL 返回该 id 与空昵称，不阻断身份握手。

#### Scenario: about blank 自身 complete 不算 Facebook 就绪
- **WHEN** CDP 附着页为 `about:blank` 且该空白文档报告 `document.readyState=complete`
- **THEN** 系统不在该空白 DOM 上判定昵称采集完成，而是按显式启动权限引导并等待 Facebook 业务上下文

#### Scenario: React 顶栏延迟水合后读到昵称
- **WHEN** 已进入 Facebook 消费端 URL，但本人锚点在有界等待内稍后才渲染
- **THEN** 系统继续重扫并在本人锚点出现后返回与稳定 id 绑定的昵称

#### Scenario: 等待耗尽仍保留稳定 id
- **WHEN** 页面就绪等待耗尽、`c_user` 已给出唯一稳定数字 id，但本人昵称信号仍未出现
- **THEN** 系统返回该稳定 id 与空昵称，MUST NOT 猜测、MUST NOT 阻断握手
