# browse-loop-resilience Specification

## Purpose
TBD - created by archiving change fix-browse-loop-resilience. Update Purpose after archive.
## Requirements
### Requirement: 返回 feed 后浏览循环必须续刷而非死锁

返回 feed（`navigation.back`，`reason=back_to_feed`）之后，浏览循环 SHALL 继续评估并推进，MUST NOT 在「返回后首次扫描到 0 卡」时进入无限等待。无论 cloud 是否下发 `targetPage`，edge 的返回路径 MUST 等待 feed 水合后再判定可见卡片，且 MUST 在仍为空时显式上报（而非静默吞掉），以保证 cloud 决策环始终能被触发。

#### Scenario: cloud 下发的 back 不带 targetPage
- **WHEN** edge 收到 `navigation.back{reason:'back_to_feed'}` 且 payload 无 `targetPage`
- **THEN** edge 按等同 `targetPage='feed'` 处理：`history.back()` 后以 `waitForVisibleCards` 轮询（上限 ~8s）等待卡片出现，而非固定 `sleep(2000)` 后瞬时判断

#### Scenario: 轮询超时则整页重载兜底
- **WHEN** `history.back()` 后在轮询窗口内仍未出现可见卡片
- **THEN** edge `Page.navigate(exploreUrl)` 重载 feed 并再次按 scroller 口径确认卡片出现

#### Scenario: 重轮询后仍为空不得静默
- **WHEN** 返回 feed 后重轮询仍扫到 0 张可见卡片
- **THEN** edge 显式上报一条空 `page.cards`（`cards: []`），MUST NOT 仅打日志后 `return` 而不发任何报文

### Requirement: cloud 在 back 成功后必须自驱动续刷

cloud orchestration SHALL 在收到 `action.completed{action:'back', ok:true}` 时主动发起一次 feed 续扫命令，而非仅依赖 edge 主动重报 `page.cards` 才能推进决策环。

#### Scenario: back 完成回执触发续刷
- **WHEN** cloud 收到 `action.completed{action:'back', ok:true}`
- **THEN** cloud 下发一次 `scroll`（`reason=rescan_after_back`），edge 据此重扫并重新上报 `page.cards`，决策环得以继续

### Requirement: 会话必须在有界 idle 内自愈或终止

cloud orchestration SHALL 运行一个 wall-clock 看门狗：当超过 idle 阈值无任何 edge 上报/命令活动时，MUST 发起一次恢复性 nudge；当超过更长的 idle 阈值仍无活动时，MUST 触发 `session.should_end` 结束会话。会话存活性 MUST NOT 依赖外部进程强杀（SIGTERM）来打破停滞。

#### Scenario: 短 idle 触发恢复 nudge
- **WHEN** 距上一次 edge 上报/命令活动超过 idle-nudge 阈值（N 秒）且会话仍 active
- **THEN** cloud 下发一次 `scroll` nudge 以尝试重新驱动循环

#### Scenario: 长 idle 触发会话结束
- **WHEN** 距上一次活动超过 idle-end 阈值（M 秒，M>N）仍无任何活动
- **THEN** cloud 触发 `session.should_end` 并下发 `session.end`，干净结束而非无限静默

