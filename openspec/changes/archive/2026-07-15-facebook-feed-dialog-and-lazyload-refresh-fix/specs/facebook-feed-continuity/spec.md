## MODIFIED Requirements

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

## ADDED Requirements

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
