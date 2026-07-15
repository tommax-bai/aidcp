# facebook-feed-continuity Specification

## Purpose
TBD - created by archiving change facebook-feed-scroll-refresh-fix. Update Purpose after archive.
## Requirements
### Requirement: Facebook feed 滚动断言在页是幂等的、绝不重置滚动位置

边缘在执行 Facebook feed 滚动前对「是否在 feed」的断言 SHALL 是幂等的：先**探测一次**当前页面（当前 URL、由 URL 归类的 surface、是否存在 feed 容器、已水合文章数、是否有打开的 dialog），当页面**已在目标列表面**（explore 首页或搜索结果页）**且 feed 容器在场**时，MUST 直接放行、MUST NOT 发起整页 `Page.navigate`。仅当**不在目标列表面**（surface 不匹配）或**目标列表面上没有 feed 容器**时才导航到目标列表 URL。

**`[role="dialog"]` 的存在 MUST NOT 作为「需导航」的判据**（本 change 修正）：Facebook 首页会常驻**瞬时良性 dialog**（聊天弹窗、加载态、通知提示浮层，来了又走；单点探测常为 0、但恰在 scroll 命令那一刻常为 true），而 Facebook feed 就地读**不弹内容模态**——故 `dialogOpen` 对 Facebook 恒为良性。旧判据「存在任意 dialog 即判非目标→整页导航」会使**每条 scroll 命令开头都整页 `Page.navigate` 重载**（经 Facebook `maw_proxy_page` 重定向链回首页），真机表现为「页面一直刷新、feed 被反复钉回第一屏、永远下不去」（CDP 取证：`timeOrigin` 每约 8s 重置一次）。既已在正确列表面且 feed 容器在场，就是在目标，良性浮层绝不触发整页重载。`dialogOpen` 字段 MAY 继续被探测并写入边缘诊断日志（供观测），但 MUST NOT 参与 onTarget 判定。

surface 归类 SHALL 复用既有的 URL surface 归类器区分「首页」与「搜索页」，MUST NOT 写死为首页——该断言同时被搜索浏览支线调用，写死首页会把搜索页误判为需导航、把用户带离搜索结果。

红线（fail-closed 不得被省略）：不导航的放行路径 SHALL 仍执行与导航路径同等的登录态复检、验证码/阻断浮层复检、consent 预清理。真正的登录失效 / 验证码 / 阻断浮层 SHALL 由该 fail-closed 复检识别并诚实回报对应失败、MUST NOT 放行滚动——这条防线独立于 `dialogOpen`、不受本 change 影响。

#### Scenario: 已在首页则直接放行、不重新导航
- **WHEN** 收到 feed 滚动命令时页面已在 explore 首页且 feed 容器在场
- **THEN** 边缘不发起 `Page.navigate`，直接执行滚动手势；连续多次滚动命令下 `scrollY` 严格递增、整页 document-load / `timeOrigin` 保持不变

#### Scenario: 首页挂着瞬时良性 dialog 时仍不导航
- **WHEN** 页面已在 explore 首页、feed 容器在场，但存在瞬时良性 `[role="dialog"]`（聊天弹窗 / 加载态 / 通知提示）
- **THEN** 边缘 MUST NOT 因该 dialog 发起整页 `Page.navigate`，直接放行滚动；`timeOrigin` 保持不变

#### Scenario: 已在搜索结果页则按搜索页放行、不被带回首页
- **WHEN** 会话处于搜索结果页并收到 feed 滚动命令
- **THEN** 边缘按搜索页 surface 放行滚动，MUST NOT 导航回 explore 首页、MUST NOT 丢失搜索结果

#### Scenario: 不在目标列表面才导航
- **WHEN** 收到 feed 滚动命令时页面停在详情/通知/其它非列表面（surface 不匹配或无 feed 容器）
- **THEN** 边缘导航到目标列表 URL 后再滚动

#### Scenario: 放行路径仍 fail-closed 复检
- **WHEN** 页面虽在目标列表面、但登录已失效或存在验证码/阻断浮层
- **THEN** 边缘 MUST NOT 放行滚动，MUST 回报对应诚实失败（登录失效/验证码/阻断），与走导航路径时的复检等价（独立于 `dialogOpen`）

### Requirement: 详情返回落回发起浏览的列表面而非会话初始首页

从某一列表面（首页或搜索结果页）打开帖子详情后返回，边缘 SHALL 返回**发起本次浏览的当前列表面**（当前 `activeFeedUrl`），MUST NOT 一律回到会话初始的首页 URL。这修复 split-brain：从搜索结果开帖后返回被带回首页、搜索结果丢失、下次滚动从头重搜。

#### Scenario: 从搜索结果开帖后返回落回搜索结果
- **WHEN** 会话在搜索结果页打开一篇帖子详情后收到返回命令
- **THEN** 边缘返回该搜索结果页（`activeFeedUrl`），MUST NOT 回到 explore 首页

#### Scenario: 从首页开帖后返回落回首页
- **WHEN** 会话在 explore 首页打开详情后返回
- **THEN** 边缘返回 explore 首页

### Requirement: feed 卡片在 loading-aware 累积判稳后才上报

边缘上报 Facebook feed 卡片前 SHALL 执行一个 loading-aware 累积判稳循环（每轮约 450–600ms 复扫一次，直接对卡片抽取结果比对），仅当**同时满足**下列三条件才算稳、才上报：① 至少 `minCards`（默认 1）张真卡（已水合、可抽出作者/permalink，绝不把虚拟化空壳当卡）；② 相邻两轮真卡集合相等（按 noteId 集合比较，非按数量）；③ feed 区域内无 loading 信号。loading 信号 SHALL 仅按可访问性语义识别（`role="progressbar"` / `aria-busy="true"`），MUST NOT 依据 Facebook 骨架屏的 CSS 类名判定；loading 信号是单向的「继续等」否决票——即使集合已连续两轮相等，只要仍有 loading 信号就 MUST 继续等。

该判稳循环 SHALL **合并替换**既有的两道 existence gate（feed 就绪判据只要 1 篇水合即就绪、扫卡第一次 ≥1 张即返回），MUST NOT 与它们叠加串行（叠加会累加逼近命令超时）。判稳 SHALL 直接对卡片抽取输出判稳（复用同一抽取比对 noteId 集合），MUST NOT 另起一个抽取口径不同的探针。

判稳循环 SHALL 有硬 wall-clock 上限（导航后约 6s、滚动后约 3.5s）。达上限时：有 ≥1 真卡则 SHALL 照实上报已抽到的真卡并在**边缘诊断日志**标记 degraded（非假成功——卡是真抽的；`degraded` MUST NOT 进入上报 payload 契约）；0 真卡且仍有 loading 信号 SHALL 回报可重试的「仍在加载」；0 真卡且无 loading 信号 SHALL 回报「无 feed」作为升级候选。

#### Scenario: 集合连续两轮相等且无 loading 即上报
- **WHEN** 相邻两轮扫到的真卡 noteId 集合相等、且 feed 区域无 `role=progressbar`/`aria-busy` 信号、且真卡数 ≥ minCards
- **THEN** 边缘上报该批真卡

#### Scenario: 集合已稳但仍在 loading 则继续等
- **WHEN** 相邻两轮真卡集合相等，但 feed 区域仍存在 loading 信号
- **THEN** 边缘 MUST 继续等待（不提前上报），直到 loading 信号消失或触达 wall-clock 上限

#### Scenario: 触达上限有真卡则照实上报并标 degraded
- **WHEN** 判稳循环到达 wall-clock 上限且已抽到 ≥1 张真卡（集合可能仍未完全稳定）
- **THEN** 边缘照实上报已抽到的真卡，并仅在边缘诊断日志标记 degraded，MUST NOT 因未完全稳定而回报假失败、MUST NOT 把 degraded 写进上报 payload

#### Scenario: 触达上限 0 卡且仍 loading 则可重试
- **WHEN** 判稳循环到达上限仍为 0 真卡、但仍有 loading 信号
- **THEN** 边缘回报可重试的「仍在加载」，MUST NOT 上报空批、MUST NOT 假成功

#### Scenario: 触达上限 0 卡且无 loading 则升级候选
- **WHEN** 判稳循环到达上限仍为 0 真卡、且无 loading 信号
- **THEN** 边缘回报「无 feed」作为升级候选，MUST NOT 静默当作已上报

#### Scenario: 虚拟化空壳绝不被当卡上报
- **WHEN** feed 中除顶部若干张真卡外存在大量未水合的虚拟化空壳文章
- **THEN** 边缘 MUST NOT 把空壳计入真卡集合或上报，只上报可抽出作者/permalink 的真卡

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

