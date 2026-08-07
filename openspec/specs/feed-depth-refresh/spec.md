# feed-depth-refresh Specification

## Purpose
TBD - created by archiving change feed-refresh-on-depth. Update Purpose after archive.
## Requirements
### Requirement: 会话内 feed 浏览深度达阈值须改为刷新回顶而非继续下滚

系统 SHALL 在每个浏览会话内累计统计「已浏览的不重复 explore feed 卡片数」，并在该数达到阈值时，于 feed 滚动决策点改为下发一次「刷新 feed」命令（点击右下角「刷新」按钮回到顶部换出新一批），MUST NOT 在到达阈值时继续向下滚动。计数 SHALL 只统计 explore feed 的卡片（`sourcePageType==='feed'`），搜索结果页的卡片 MUST NOT 计入。

计数 SHALL 复用每批结构化上报时已算出的「本批新卡数」增量累加（天然去重），MUST NOT 因同一张卡重复出现而重复计数。阈值 SHALL 可经环境变量配置（默认约 60），功能 SHALL 默认开启并提供环境变量总开关兜底（仅当显式置为关闭时停用）。

#### Scenario: 累计达阈值改发刷新
- **WHEN** 某会话内已浏览的不重复 feed 卡累计达到阈值，且下一次 feed 滚动决策触发（`content.no_valuable` 等）
- **THEN** 系统在滚动决策点改为发起一次「刷新 feed」意图（而非 `feed.scrolled` / `search.needed`），指示边缘点击 feed 右下「刷新」按钮

#### Scenario: 未达阈值维持原有滚动/转搜索
- **WHEN** 已浏览 feed 卡累计**未**达阈值
- **THEN** feed 滚动决策照旧（滚动，或连续空滚达 5 次转搜索），MUST NOT 触发刷新

#### Scenario: 功能关闭时永不刷新
- **WHEN** 总开关被显式关闭
- **THEN** 无论累计浏览多少 feed 卡，系统 MUST NOT 触发刷新，浏览行为与本 change 前一致

#### Scenario: 搜索结果卡不计入 feed 深度
- **WHEN** 会话处于搜索结果页（`sourcePageType==='search'`）并上报卡片
- **THEN** 这些卡 MUST NOT 计入 feed 浏览深度计数

### Requirement: 刷新计数复位与 per-session 语义

达阈值触发刷新时，系统 SHALL 在滚动决策点即刻（乐观）复位 feed 浏览深度计数与连续滚动计数，使刷新后从新一批重新累计、每累计阈值张周期性重复；计数 SHALL 为 per-session（会话重置 / 边缘重连即归零），MUST NOT 跨逻辑会话残留。乐观复位 MUST NOT 被解读为刷新成功的声明——动作真实成败仍以边缘回执为准（见能力 `browse-loop-resilience`）。

#### Scenario: 刷新后计数归零并可再次触发
- **WHEN** 一次刷新意图在滚动决策点被触发
- **THEN** feed 浏览深度计数与连续滚动计数即刻归零；随后新顶批重新累计，再次达阈值时再次触发刷新

#### Scenario: 会话重置归零深度计数
- **WHEN** 会话被重置（新的 `edge.hello` / 重连 / 会话拆除）
- **THEN** feed 浏览深度计数归零（per-session），下一场从满额深度预算重新开始

### Requirement: 刷新命令为独立协议消息且执行端诚实执行

「刷新 feed」SHALL 表达为一个**独立的** cloud→edge 协议消息（非复用滚动消息的魔法参数），并按协议同步纪律在两端消息类型定义、动作↔消息映射、协议文档、以及**执行端主动命令白名单**四处同步接线（白名单遗漏会导致命令静默丢弃）。

边缘执行刷新 MUST 诚实：仅当确认页面在 explore feed、定位到右下「刷新」按钮、验证码/浮层复检通过后才点击；点击后 MUST 以后置校验确认「刷新真的发生」——**滚动位置回到顶部 且 出现一张具体的、非空的、与点击前不同的首卡 noteId**——才回报成功并上报新一批卡片。任一前置不满足或后置校验不通过，MUST 回报诚实失败原因，MUST NOT 静默假成功、MUST NOT 把仅「回到顶部而内容未换」当作刷新成功、MUST NOT 把可能陈旧/空的卡片当新批上报。

红线：绝不伪造刷新成功回执。

#### Scenario: 刷新成功
- **WHEN** 边缘在 explore feed 定位到「刷新」按钮并点击，点击后滚动回到顶部且首卡 noteId 换成一张具体非空的新 id
- **THEN** 边缘回报 `action.completed{action:'refresh', ok:true}` 并上报新一批 `page.cards`

#### Scenario: 不在 feed 页则诚实失败
- **WHEN** 收到刷新命令时页面不在 explore feed（如停在详情/搜索/通知页）
- **THEN** 边缘回报 `action.completed{action:'refresh', ok:false, reason:'wrong_context'}`，MUST NOT 假装刷新

#### Scenario: 找不到刷新按钮则诚实失败
- **WHEN** 页面上不存在右下悬浮容器或其中的「刷新」按钮（如尚未滚动出、或平台改版）
- **THEN** 边缘回报 `ok:false` 且原因指明按钮缺失（如 `no_floating_btn` / `no_reload_btn`），MUST NOT 假成功

#### Scenario: 点了但没真换新批则诚实失败、不报陈旧卡
- **WHEN** 点击刷新后后置校验窗口内**未**出现具体非空的新首卡（仅滚动归零、或首卡为空/无 noteId、或首卡未变）
- **THEN** 边缘回报 `action.completed{action:'refresh', ok:false, reason:'not_reloaded'}` 且 MUST NOT 上报卡片（不得把陈旧/空卡当新批）

#### Scenario: 验证码/浮层复检不过则不点击
- **WHEN** 点击前的验证码/阻断浮层复检发现存在阻断
- **THEN** 边缘 fail-closed：不点击并回报 `ok:false, reason:'blocked_by_captcha'`

### Requirement: 刷新是导航类动作，不消耗互动风控配额

刷新命令 SHALL 经统一命令下发出口下发，从而在软暂停（阻塞式验证码暂停 / 临时离开式巡视）期间被自动抑制；刷新 SHALL 计入会话动作数，但 MUST NOT 作为互动风控动作消耗点赞/收藏/关注/评论等互动配额，MUST NOT 触发互动风控闸。

#### Scenario: 软暂停期间刷新被抑制
- **WHEN** 会话处于软暂停（验证码阻塞 / 通知巡视离开）期间到达刷新触发条件
- **THEN** 刷新命令被统一出口抑制、本轮不下发（不在暂停中刷新）；乐观复位下本轮刷新即跳过、需再累计阈值后重试（不重试、不锤击）

#### Scenario: 刷新不烧互动配额
- **WHEN** 一次刷新命令被下发并执行
- **THEN** 该动作 MUST NOT 扣减任何互动配额（点赞/收藏/关注/评论/评论点赞），MUST NOT 被计为互动风控动作

### Requirement: Facebook 刷新经顶栏首页图标页内点击换批

在 Facebook 平台上执行「刷新 feed」命令时，边缘 SHALL 通过**页内 `element.click()` 点击顶栏首页图标**触发 SPA 换批（实机验证：此举换出新一批而**不触发整页重载**），而非小红书的右下「刷新」按钮。首页图标 SHALL 结构性定位（`[role="banner"]` 内 `a[href="/"]`），MUST NOT 依据「Home」/「首页」等本地化文案定位（跨语言不可靠）。点击换批后边缘 SHALL 显式滚动回顶（实机证实 Facebook 换批**不自动回顶**）。

该要求补充（而非取代）既有「刷新命令为独立协议消息且执行端诚实执行」要求中的小红书执行方式；刷新协议消息按词汇批 4 平台段化为 `xiaohongshu.feed.refresh` / `facebook.feed.refresh`，两平台各自的执行方式与诚实回执要求随名字直接对应、语义不变。

#### Scenario: Facebook 页内点击首页图标换批不重载
- **WHEN** Facebook 会话在 explore 首页收到 `facebook.feed.refresh`，且顶栏首页图标可结构性定位、验证码/浮层复检通过
- **THEN** 边缘对首页图标做页内 `element.click()`、随后显式滚动回顶，MUST NOT 发起整页 `Page.navigate`/`Page.reload`（除非落入受频率下限约束的兜底档）

#### Scenario: 定位不到首页图标则诚实失败
- **WHEN** 顶栏 `[role="banner"] a[href="/"]` 不存在（平台改版或 DOM 未就绪）
- **THEN** 边缘回报 `ok:false, reason:'no_home_link'`，MUST NOT 假成功、MUST NOT 凭文案盲点

### Requirement: Facebook 刷新后置校验以首卡 permalink 变更为判据

Facebook 刷新的后置校验判据 SHALL 是「首卡 permalink 变更且非空」，MUST NOT 采用「滚动位置回到顶部」作为判据（实机证实 Facebook 换批后 `scrollY` 不可靠、不归零，以回顶为判据会误判）。仅当刷新后重新判稳扫出的首卡 permalink **非空且不同于**点击前首卡时，才算刷新成功。

刷新成功 SHALL 以**单一终态报文**回报：直接回 `type=cards`（刷新后新判稳扫出的一批）作为唯一终态——既推进云端浏览循环、又即成功信号，MUST NOT 另外再发一个 `ok` 终态。刷新失败 SHALL 回 `type=action, ok:false` 并带诚实原因（`no_home_link` / `not_refreshed` / `wrong_context` / `blocked_by_consent` / `blocked_by_captcha`），MUST NOT 把陈旧/空/未变的首卡当新批上报。

#### Scenario: 首卡 permalink 变更即刷新成功回 cards
- **WHEN** Facebook 刷新点击后重新判稳，扫出的首卡 permalink 非空且不同于点击前
- **THEN** 边缘以 `type=cards` 单一终态上报该新批，MUST NOT 再另发 `ok` 终态

#### Scenario: 首卡未变或为空则诚实失败不报陈旧卡
- **WHEN** 刷新点击后后置校验窗口内首卡 permalink 为空、或仍等于点击前首卡
- **THEN** 边缘回报 `type=action, ok:false, reason:'not_refreshed'`，MUST NOT 上报卡片

### Requirement: Facebook 刷新的整页重载兜底受频率下限约束且仅刷新路径可达

Facebook 刷新 SHALL 优先走页内点击换批；仅当页内换批不可用时，MAY 退到 `Page.reload` 兜底档，且该兜底 SHALL 受频率下限约束（同一会话内两次 `Page.reload` 兜底至少间隔约 3 分钟）。`Page.reload` 兜底 SHALL 仅在 `reason==='feed_refresh'` 的刷新路径可达，MUST NOT 从其它恢复/滚动路径可达（避免恢复路径又退化成整页重载）。

#### Scenario: 页内换批不可用时受限退到 reload 兜底
- **WHEN** 顶栏首页图标点击换批失败或不可用，且距上次 reload 兜底已超过频率下限
- **THEN** 边缘 MAY 执行一次 `Page.reload` 兜底并按同样的首卡-permalink 判据后置校验

#### Scenario: 频率下限内不重复 reload
- **WHEN** 距上次 `Page.reload` 兜底未超过频率下限
- **THEN** 边缘 MUST NOT 再次 `Page.reload`，按诚实失败回报

#### Scenario: 恢复/滚动路径不可触发 reload 兜底
- **WHEN** 当前处于恢复滚动或普通滚动路径（`reason!=='feed_refresh'`）
- **THEN** MUST NOT 触发 `Page.reload` 兜底

