# facebook-feed-continuity Specification

## Purpose
TBD - created by archiving change facebook-feed-scroll-refresh-fix. Update Purpose after archive.
## Requirements
### Requirement: Facebook feed 滚动断言在页是幂等的、绝不重置滚动位置

边缘在执行 Facebook feed 滚动前对「是否在 feed」的断言 SHALL 是幂等的：先**探测一次**当前页面（当前 URL、由 URL 归类的 surface、是否存在可识别 feed 结构、已水合真卡数、是否有打开的 dialog）。可识别 feed 结构 SHALL 同时支持：① 语义化 `[role="feed"]` + 顶层 `[role="article"]`；② 无 `[role="feed"]` / 真卡无 `[role="article"]`、但在主内容区域存在可见 story-message 与至少一个链接作者标题共同界定的轻量卡片布局。当页面**已在目标列表面**（explore 首页或搜索结果页）且任一受支持 feed 结构在场时，MUST 直接放行、MUST NOT 发起整页 `Page.navigate`。仅当**不在目标列表面**（surface 不匹配）或**目标列表面上没有任一受支持 feed 结构**时才导航到目标列表 URL。

**`[role="dialog"]` 的存在 MUST NOT 作为「需导航」的判据**：Facebook 首页会常驻瞬时良性 dialog，而 Facebook feed 就地读不弹内容模态。`dialogOpen` 字段 MAY 继续被探测并写入边缘诊断日志，但 MUST NOT 参与 onTarget 判定。

surface 归类 SHALL 复用既有的 URL surface 归类器区分「首页」与「搜索页」，MUST NOT 写死为首页。轻量布局识别 MUST 使用 locale-neutral 的 DOM 结构/属性，MUST NOT 依赖中文、英文、越南文等可见文案或账号专属标记。

红线（fail-closed 不得被省略）：不导航的放行路径 SHALL 仍执行与导航路径同等的登录态复检、验证码/阻断浮层复检、consent 预清理。真正的登录失效 / 验证码 / 阻断浮层 SHALL 由该 fail-closed 复检识别并诚实回报对应失败、MUST NOT 放行滚动。

#### Scenario: 已在语义化首页则直接放行、不重新导航
- **WHEN** 收到 feed 滚动命令时页面已在 explore 首页且语义化 feed 容器在场
- **THEN** 边缘不发起 `Page.navigate`，直接执行滚动手势；连续多次滚动命令下 `scrollY` 严格递增、整页 document-load / `timeOrigin` 保持不变

#### Scenario: 已在轻量布局首页也直接放行
- **WHEN** 页面已在 explore 首页、没有 `[role="feed"]` 且真卡没有 `[role="article"]`，但主内容区域存在受支持的轻量 story-message 卡片结构
- **THEN** 边缘判定 feed 在场并直接放行滚动，MUST NOT 因语义 role 缺失反复整页导航

#### Scenario: 首页挂着瞬时良性 dialog 时仍不导航
- **WHEN** 页面已在任一受支持首页 feed 布局，但存在瞬时良性 `[role="dialog"]`
- **THEN** 边缘 MUST NOT 因该 dialog 发起整页 `Page.navigate`，直接放行滚动；`timeOrigin` 保持不变

#### Scenario: 已在搜索结果页则按搜索页放行、不被带回首页
- **WHEN** 会话处于任一受支持布局的搜索结果页并收到 feed 滚动命令
- **THEN** 边缘按搜索页 surface 放行滚动，MUST NOT 导航回 explore 首页、MUST NOT 丢失搜索结果

#### Scenario: 不在目标列表面才导航
- **WHEN** 收到 feed 滚动命令时页面停在详情/通知/其它非列表面，或目标列表面不存在任一受支持 feed 结构
- **THEN** 边缘导航到目标列表 URL 后再滚动

#### Scenario: 放行路径仍 fail-closed 复检
- **WHEN** 页面虽在目标列表面、但登录已失效或存在验证码/阻断浮层
- **THEN** 边缘 MUST NOT 放行滚动，MUST 回报对应诚实失败，与走导航路径时的复检等价

### Requirement: 详情返回落回发起浏览的列表面而非会话初始首页

从某一列表面（首页或搜索结果页）打开帖子详情后返回，边缘 SHALL 返回**发起本次浏览的当前列表面**（当前 `activeFeedUrl`），MUST NOT 一律回到会话初始的首页 URL。这修复 split-brain：从搜索结果开帖后返回被带回首页、搜索结果丢失、下次滚动从头重搜。

#### Scenario: 从搜索结果开帖后返回落回搜索结果
- **WHEN** 会话在搜索结果页打开一篇帖子详情后收到返回命令
- **THEN** 边缘返回该搜索结果页（`activeFeedUrl`），MUST NOT 回到 explore 首页

#### Scenario: 从首页开帖后返回落回首页
- **WHEN** 会话在 explore 首页打开详情后返回
- **THEN** 边缘返回 explore 首页

### Requirement: feed 卡片在 loading-aware 累积判稳后才上报

边缘上报 Facebook feed 卡片前 SHALL 执行一个 loading-aware 累积判稳循环（每轮约 450–600ms 复扫一次，直接对卡片抽取结果比对），并 SHALL 对语义化顶层 article 与轻量 story-message 卡片使用同一共享的顶层卡片发现口径。仅当**同时满足**下列三条件才算稳、才上报：① 至少 `minCards`（默认 1）张真卡（已水合、有作者且可抽出既有白名单接受的规范帖子 permalink；绝不把虚拟化空壳或只有歧义媒体 ID 的卡当真卡）；② 相邻两轮真卡集合相等（按 noteId 集合比较，非按数量）；③ feed 区域内无 loading 信号。loading 信号 SHALL 仅按可访问性语义识别（`role="progressbar"` / `aria-busy="true"`），MUST NOT 依据 Facebook 骨架屏的 CSS 类名判定。

该判稳循环 SHALL 合并替换既有的两道 existence gate，MUST NOT 与它们叠加串行。判稳 SHALL 直接对卡片抽取输出判稳，MUST NOT 另起一个抽取口径不同的探针。初始扫描与后续 feed 就地读/操作的卡片定位 SHALL 复用同一共享多布局口径，MUST NOT 出现“已上报但后续按另一布局无法定位”的分叉。

判稳循环 SHALL 有硬 wall-clock 上限（导航后约 6s、滚动后约 3.5s）。达上限时：有 ≥1 真卡则 SHALL 照实上报已抽到的真卡并在边缘诊断日志标记 degraded；0 真卡且仍有 loading 信号 SHALL 回报可重试的「仍在加载」；识别到 feed 结构但 0 张稳定身份真卡 SHALL 继续走既有有界滚动/no-target 逻辑，MUST NOT 因卡片身份不足反复重载页面；页面无任一受支持 feed 结构且无 loading 信号才 SHALL 回报「无 feed」作为升级候选。

#### Scenario: 两类布局集合连续两轮相等且无 loading 即上报
- **WHEN** 任一受支持布局中相邻两轮扫到的真卡 noteId 集合相等、feed 区域无 loading 信号、且真卡数 ≥ minCards
- **THEN** 边缘上报该批真卡

#### Scenario: 集合已稳但仍在 loading 则继续等
- **WHEN** 相邻两轮真卡集合相等，但 feed 区域仍存在 loading 信号
- **THEN** 边缘 MUST 继续等待，直到 loading 信号消失或触达 wall-clock 上限

#### Scenario: 触达上限有真卡则照实上报并标 degraded
- **WHEN** 判稳循环到达 wall-clock 上限且已抽到 ≥1 张真卡
- **THEN** 边缘照实上报已抽到的真卡，并仅在边缘诊断日志标记 degraded，MUST NOT 把 degraded 写进上报 payload

#### Scenario: 触达上限 0 卡且仍 loading 则可重试
- **WHEN** 判稳循环到达上限仍为 0 真卡、但仍有 loading 信号
- **THEN** 边缘回报可重试的「仍在加载」，MUST NOT 上报空批、MUST NOT 假成功

#### Scenario: 轻量 feed 存在但卡片身份不可靠时不重载不造卡
- **WHEN** 轻量布局结构在场，但当前卡片只暴露 photo/video 资源 ID、无法通过既有规范帖子身份白名单
- **THEN** 边缘保持在 feed 并继续有界滚动寻找真卡，MUST NOT 把媒体 ID 当 noteId 上报、MUST NOT 因 `[role="feed"]` 缺失重载页面

#### Scenario: 触达上限 0 卡且无任何 feed 结构则升级候选
- **WHEN** 判稳循环到达上限仍为 0 真卡、无 loading 信号、且不存在任一受支持 feed 结构
- **THEN** 边缘回报「无 feed」作为升级候选，MUST NOT 静默当作已上报

#### Scenario: 虚拟化空壳绝不被当卡上报
- **WHEN** feed 中除顶部若干张真卡外存在大量未水合的虚拟化空壳文章
- **THEN** 边缘 MUST NOT 把空壳计入真卡集合或上报，只上报有作者与规范 permalink 的真卡

### Requirement: feed「到底」判据是懒加载感知的、绝不在还有内容时误判换批

边缘在一条 feed 滚动命令内 SHALL 有界续滚寻找**未见过的新卡**；判定「feed 到底」（回执 `feed_exhausted`，云端据此换批）SHALL 是懒加载感知的：本轮 0 新卡时，仅当**同时满足**下列三条件才可诚实判到底——① 本轮滚动后内容总高 `scrollHeight` **不再增长**（Facebook 懒加载没有在追加内容）；② 已**接近底部**（`scrollHeight − scrollY − innerHeight` 小于约一屏余量——Facebook 通常在触底前就懒加载，故留余量提前判定）；③ 上述状态**连续确认 ≥2 轮**。只要页面仍在增长（懒加载进行中）或尚未接近底部，边缘 MUST 继续下滚、MUST NOT 判到底。

续滚 SHALL 有硬上限（`FEED_SCROLL_MAX_ROUNDS`，默认 8，配合单命令兜底超时约束在预算内）。轮次耗尽时：从**未扫到任何卡**（loading/no_feed）SHALL 回报可重试的 `no_target`（区分「没内容」与「没新内容」）；扫到过卡但一直无新卡 SHALL 兜底回 `feed_exhausted`。红线：只上报**真抽的未见过新卡**，MUST NOT 把回收重现的旧卡当新内容重复上报，MUST NOT 在页面仍在懒加载 / 尚未接近底部时假判到底。

此判据使**浏览深度阈值**（云端按已浏览不重复卡数换批，默认 60）成为换批主路，`feed_exhausted → refresh` 仅在**真·刷到底**时兜底（正常应罕见），消除「一滚不出新卡就刷新回顶」的换批抖动。

#### Scenario: 懒加载还在长内容 / 未到底 → 续滚不判到底
- **WHEN** 本轮 0 新卡，但滚动后 `scrollHeight` 增长（懒加载在追加）或尚未接近底部
- **THEN** 边缘继续下滚寻找下沉的新卡，MUST NOT 回 `feed_exhausted`；后续轮次出现新卡即上报

#### Scenario: 高度稳定且接近底部、连续无新卡 → 诚实 feed_exhausted
- **WHEN** 连续 ≥2 轮「`scrollHeight` 不再增长 + 接近底部 + 0 新卡」
- **THEN** 边缘诚实回 `feed_exhausted`（云端据此换批），MUST NOT 上报陈旧卡

#### Scenario: 全程未扫到任何卡 → no_target 而非 feed_exhausted
- **WHEN** 有界续滚全程 settle 都为空（loading / 无 feed 容器）
- **THEN** 边缘回可重试的 `no_target`，MUST NOT 误报 `feed_exhausted`

### Requirement: Facebook initial feed continues past visible unreportable cards

When initial Facebook feed settling finds zero reportable cards, the Edge SHALL distinguish a genuinely empty, loading, blocked, or unknown homepage from a homepage that contains visible structural cards without trustworthy post identities. If the empty-state probe returns `cards_ready`, the Edge MUST treat the current cards as skipped and immediately run the existing bounded, humanized, lazy-load-aware feed continuation until it finds at least one reportable card or reaches an honest bounded terminal result. It MUST NOT remain idle on the same viewport waiting only for a later Cloud watchdog nudge.

The initial continuation MUST emit `page.cards` only for cards with canonical identities. Because no Cloud command initiated this bootstrap recovery, a bounded failure MUST remain an Edge diagnostic and MUST NOT emit an unsolicited `action.completed` receipt. Confirmed empty, loading, login, captcha, and unknown states SHALL preserve their existing fail-closed behavior.

#### Scenario: Unreportable first card is skipped and a later card starts the loop
- **WHEN** the homepage first viewport contains a visible lightweight media or video card with no accepted post identity, and a bounded downward scroll reveals a card with a canonical permalink
- **THEN** the Edge skips the first card, scrolls downward without reloading the page, and emits `page.cards` for the later canonical card

#### Scenario: Consecutive unreportable cards do not create fake observations
- **WHEN** every card found within the bounded continuation exposes only media resource ids or non-post links
- **THEN** the Edge emits no `page.cards` and no unsolicited `action.completed`, records an honest bounded diagnostic, and never fabricates a target

#### Scenario: Explicit empty feed remains Cloud-authorized Reels fallback
- **WHEN** the homepage contains no structural cards and satisfies the existing stable explicit-empty evidence
- **THEN** the Edge reports the confirmed empty observation and waits for Cloud authorization instead of scrolling as though an unreportable card existed

### Requirement: Facebook automatic browse establishes Feed before its initial scan

Every new or resumed Native-only Facebook automatic browse session SHALL navigate to the canonical Facebook home Feed before reading or reporting its first card batch. The Edge MUST NOT treat the fingerprint browser's persisted last page as the session baseline, even when that page is a valid Facebook Reel, profile, group, search, notification, publish, or content-detail surface. Only a later explicit Cloud command may move the session away from Feed. Failure to establish or inspect the canonical Feed MUST surface honestly and MUST NOT fall back to reporting cards from the persisted page.

#### Scenario: Persisted Reel is reset to Feed

- **WHEN** a Facebook automatic browse session starts while the attached browser is on `/reel/<id>`
- **THEN** the Native adapter navigates to `https://www.facebook.com/` before its initial scan and reports only the resulting Feed state

#### Scenario: Persisted excursion page is reset to Feed

- **WHEN** a Facebook automatic browse session starts or resumes on a profile, group, search, notification, publish, or content-detail page
- **THEN** the Native adapter establishes the canonical home Feed before reporting the first card batch

#### Scenario: Failed Feed reset does not reuse the old page

- **WHEN** the canonical home navigation or its post-navigation readiness check fails
- **THEN** the startup command returns an honest failure and emits no card batch derived from the persisted page

#### Scenario: Other platforms keep their startup behavior

- **WHEN** a Xiaohongshu or WeChat Channels runtime starts
- **THEN** it does not execute the Facebook home-baseline branch and retains its existing platform startup behavior

### Requirement: Native Feed probe timing is decodable across the browser-to-Rust boundary

The Facebook browser router SHALL emit `documentAgeMs` as a finite, non-negative integer that the strict Rust Native Feed probe model can decode. A real browser's fractional high-resolution time origin MUST NOT terminate initial or resumed automatic browsing before the existing bounded Feed settle flow begins. Rust SHALL continue to reject malformed or undeclared probe fields rather than coercing arbitrary values or bypassing the Native-only boundary.

#### Scenario: Fractional Chrome time origin starts the bounded Feed flow

- **WHEN** the Facebook Feed probe computes document age from a Chrome `performance.timeOrigin` containing a fractional millisecond component
- **THEN** the router emits a non-negative integer `documentAgeMs`, Rust decodes the bounded probe, and the session proceeds into the existing Feed settle and continuation flow

#### Scenario: Strict bounded-result validation remains fail-closed

- **WHEN** a Facebook Feed probe contains an undeclared field or a value that does not satisfy the declared bounded shape
- **THEN** Rust rejects the probe and reports an honest Native failure without fabricating cards or activating a JavaScript fallback

### Requirement: Confirmed Reels navigation SHALL retain Reels surface ownership while the first card is late
After the browser confirms a Facebook Reels route, Edge MUST NOT continue to treat the page as Feed solely because the first active Reel card is not readable within the initial settle budget.

#### Scenario: Reels route is ready before its semantic card
- **WHEN** the fallback navigation reaches a canonical Reels route but no trustworthy active card is readable before the initial deadline
- **THEN** Edge SHALL retain pending Reels ownership, report an honest non-success terminal, and count no view

#### Scenario: Pending Reels recovery reports the current card before advancing
- **WHEN** a subsequent recovery command arrives while Reels ownership is pending and the current active card becomes readable
- **THEN** Edge SHALL report that current card, confirm Reels ownership, and MUST NOT advance past it first

#### Scenario: Pending Reels recovery never navigates to Feed
- **WHEN** a recovery scroll arrives while the browser is on a confirmed pending Reels route
- **THEN** Edge SHALL use the Reels reader and MUST NOT call Feed navigation recovery

