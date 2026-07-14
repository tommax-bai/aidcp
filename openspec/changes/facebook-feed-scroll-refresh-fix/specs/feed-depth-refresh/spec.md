## ADDED Requirements

### Requirement: Facebook 刷新经顶栏首页图标页内点击换批

在 Facebook 平台上执行「刷新 feed」命令时，边缘 SHALL 通过**页内 `element.click()` 点击顶栏首页图标**触发 SPA 换批（实机验证：此举换出新一批而**不触发整页重载**），而非小红书的右下「刷新」按钮。首页图标 SHALL 结构性定位（`[role="banner"]` 内 `a[href="/"]`），MUST NOT 依据「Home」/「首页」等本地化文案定位（跨语言不可靠）。点击换批后边缘 SHALL 显式滚动回顶（实机证实 Facebook 换批**不自动回顶**）。

该要求补充（而非取代）既有「刷新命令为独立协议消息且执行端诚实执行」要求中的小红书执行方式；协议消息 `feed.refresh` 复用现有、本 change MUST NOT 新增或改动协议消息。

#### Scenario: Facebook 页内点击首页图标换批不重载
- **WHEN** Facebook 会话在 explore 首页收到刷新命令，且顶栏首页图标可结构性定位、验证码/浮层复检通过
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
