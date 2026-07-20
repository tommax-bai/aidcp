## MODIFIED Requirements

### Requirement: Facebook feed 滚动断言在页是幂等的、绝不重置滚动位置

边缘在执行 Facebook feed 滚动前对「是否在 feed」的断言 SHALL 是幂等的，并 SHALL 将“已在目标列表面”与“已有可读卡片”分开探测。对于 explore 首页，顶层 URL 属于允许的 Facebook 首页、认证态和主区域已在场且无登录/checkpoint/consent/captcha 阻断，即可判定已在首页，MUST NOT 仅因 feed 容器或卡片为 0 而重复 `Page.navigate`；对于搜索结果页和群组 feed，仍 SHALL 复用既有 URL surface 与列表容器判据。仅当 surface 不匹配或页面不满足对应列表面的 readiness 时才导航到目标列表 URL。

**`[role="dialog"]` 的存在 MUST NOT 作为「需导航」的判据**：Facebook 首页会常驻瞬时良性 dialog，故 `dialogOpen` MAY 写入诊断日志但 MUST NOT 参与 onTarget 判定。不导航和导航路径 SHALL 执行同等的登录态、验证码/阻断和 consent 复检。

首页 0 卡 SHALL 被分类为 `empty_feed_confirmed`、`feed_still_loading` 或 `feed_unknown`。只有在同一 URL 与同一 `performance.timeOrigin` generation 下，document age 至少 8 秒、无真卡和 loading 信号、同一紧凑容器内的显式空态标题/说明语义以约 600ms 间隔连续命中 3 次，并通过动作前最终完整复检，才可返回 `empty_feed_confirmed`。卡片或 loading 出现、URL/generation 改变、认证/阻断态变化 SHALL 立即清零证据；约 15 秒窗口结束仍证据不足 SHALL 返回 `feed_unknown`，MUST NOT 推断为空态。

#### Scenario: 已在无卡首页仍不重新导航
- **WHEN** 页面已稳定落在通过认证且无阻断的 Facebook explore 首页，但尚无 feed 容器或可读卡片
- **THEN** 边缘不因 0 卡重复导航，并进入 loading-aware 内容状态确认

#### Scenario: 页面加载完成后出现卡片则取消空态
- **WHEN** 首页加载早期曾出现空态文字，但在连续确认或最终复检期间出现真卡或 loading 信号
- **THEN** 空态证据立即清零，边缘按正常 feed 上报或继续等待，MUST NOT 切换 Reels

#### Scenario: 三次显式空态且最终复检稳定
- **WHEN** 同一首页 generation 已超过最短水合时间，显式空态成对语义连续命中 3 次且最终复检仍无卡、无 loading、无阻断
- **THEN** 边缘诚实返回 `empty_feed_confirmed`

#### Scenario: about blank 与安全页绝不算空态
- **WHEN** 浏览器尚在 `about:blank`、AdsPower 启动页、Facebook 登录/checkpoint/consent/captcha 或其它非首页页面
- **THEN** 边缘返回对应未就绪/阻断状态，MUST NOT 累积首页空态样本

#### Scenario: URL 或 document generation 变化会重置样本
- **WHEN** 连续确认期间 URL 或 `performance.timeOrigin` 发生变化
- **THEN** 先前样本全部作废，新页面从零开始满足最短水合与连续确认条件

#### Scenario: 首页挂着瞬时良性 dialog 时仍不导航
- **WHEN** 页面已在 explore 首页但存在聊天、加载提示或通知类良性 `[role="dialog"]`
- **THEN** 边缘 MUST NOT 因该 dialog 重新导航，但仍按独立 loading/阻断探针判断内容状态

#### Scenario: 已在搜索结果页则按搜索页放行
- **WHEN** 会话处于搜索结果页并收到 feed 滚动命令
- **THEN** 边缘按搜索页 surface 和列表容器放行，MUST NOT 导航回 explore 首页或套用首页空态 fallback

#### Scenario: 放行路径仍 fail-closed 复检
- **WHEN** 页面 URL 看似目标列表面但登录已失效或存在验证码/阻断浮层
- **THEN** 边缘 MUST NOT 放行滚动或确认空态，MUST 回报对应诚实失败
