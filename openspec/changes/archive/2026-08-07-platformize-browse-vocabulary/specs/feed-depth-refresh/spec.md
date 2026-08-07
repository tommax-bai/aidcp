## MODIFIED Requirements

### Requirement: Facebook 刷新经顶栏首页图标页内点击换批

在 Facebook 平台上执行「刷新 feed」命令时，边缘 SHALL 通过**页内 `element.click()` 点击顶栏首页图标**触发 SPA 换批（实机验证：此举换出新一批而**不触发整页重载**），而非小红书的右下「刷新」按钮。首页图标 SHALL 结构性定位（`[role="banner"]` 内 `a[href="/"]`），MUST NOT 依据「Home」/「首页」等本地化文案定位（跨语言不可靠）。点击换批后边缘 SHALL 显式滚动回顶（实机证实 Facebook 换批**不自动回顶**）。

该要求补充（而非取代）既有「刷新命令为独立协议消息且执行端诚实执行」要求中的小红书执行方式；刷新协议消息按词汇批 4 平台段化为 `xiaohongshu.feed.refresh` / `facebook.feed.refresh`，两平台各自的执行方式与诚实回执要求随名字直接对应、语义不变。

#### Scenario: Facebook 页内点击首页图标换批不重载
- **WHEN** Facebook 会话在 explore 首页收到 `facebook.feed.refresh`，且顶栏首页图标可结构性定位、验证码/浮层复检通过
- **THEN** 边缘对首页图标做页内 `element.click()`、随后显式滚动回顶，MUST NOT 发起整页 `Page.navigate`/`Page.reload`（除非落入受频率下限约束的兜底档）

#### Scenario: 定位不到首页图标则诚实失败
- **WHEN** 顶栏 `[role="banner"] a[href="/"]` 不存在（平台改版或 DOM 未就绪）
- **THEN** 边缘回报 `ok:false, reason:'no_home_link'`，MUST NOT 假成功、MUST NOT 凭文案盲点
