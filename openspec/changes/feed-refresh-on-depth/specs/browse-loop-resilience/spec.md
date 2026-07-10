## ADDED Requirements

### Requirement: 刷新分支须保证浏览闭环续跑不死锁

feed 深度到阈值触发的「刷新 feed」分支 MUST 在成功与失败两条出口都让浏览决策环继续推进、各恰好一次驱动，MUST NOT 因刷新分支使闭环死锁或双重驱动：

- **刷新成功**（边缘确认回顶 + 换出具体新首卡）→ 边缘 SHALL 以新一批 `page.cards` 单次驱动决策环；云端 MUST NOT 在收到该新批之外再对同一次刷新成功另发一次续刷命令（避免双驱动）。
- **刷新失败**（任一诚实失败回执 `action.completed{action:'refresh', ok:false}`）→ 命中云端既有「失败动作兜底」发一次恢复性滚动使闭环续跑；刷新动作 MUST NOT 被加入「不做兜底滚动」的豁免集，否则失败即死等 idle 看门狗兜底。

刷新计数在滚动决策点的乐观复位属去抖记账，MUST NOT 被当作刷新成功；会话存活性 MUST NOT 依赖刷新成功。

#### Scenario: 刷新成功以新批单次续驱、不双驱动
- **WHEN** 一次刷新被边缘确认成功（回顶 + 具体新首卡）
- **THEN** 边缘上报的新一批 `page.cards` 单独驱动决策环继续评估；云端 MUST NOT 对这次成功再额外补发一次续刷命令

#### Scenario: 刷新失败走既有兜底滚动、闭环不死锁
- **WHEN** 边缘回报 `action.completed{action:'refresh', ok:false}`（任一原因：wrong_context / no_floating_btn / no_reload_btn / not_reloaded / blocked_by_captcha / 异常）
- **THEN** 云端既有失败动作兜底下发一次恢复性滚动（如 `reason=recover_after_refresh_failed`），浏览闭环继续，MUST NOT 因刷新失败陷入停滞直到 idle 看门狗才 nudge

#### Scenario: 软暂停抑制刷新时闭环由暂停解除后续驱
- **WHEN** 刷新命令在软暂停期间被统一出口抑制而未下发（无回执产生）
- **THEN** 闭环存活性不依赖这次刷新：暂停解除后既有续刷/重扫路径照常驱动决策环，MUST NOT 因刷新被抑制而永久挂起
