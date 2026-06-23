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

### Requirement: 返回列表页须按来源页型(sourcePageType)返回正确的列表

`back_to_feed` 返回 MUST 回到笔记**来源的列表页**：来自 explore feed 的会话回 explore，来自搜索结果的会话回**搜索结果**。云端 SHALL 把会话的 `sourcePageType` 经决策指令的 `targetPage` 透传到边缘；边缘据 `targetPage` 选择返回目标，MUST NOT 把搜索来源的会话一律拽回 explore。

#### Scenario: 搜索来源会话返回搜索结果
- **WHEN** 一条笔记经搜索结果打开、深读后云端决定 `back_to_feed`，且会话 `sourcePageType==='search'`
- **THEN** 云端下发的 `navigation.back` 携带 `targetPage='search'`，边缘返回到搜索结果列表（而非 explore feed）

#### Scenario: feed 来源会话返回 explore
- **WHEN** 会话 `sourcePageType==='feed'`（或缺省）时决定 `back_to_feed`
- **THEN** 边缘返回到 explore feed

### Requirement: 返回后须对 404/坏页健壮、健康校验通过再上报

边缘返回列表页时，若 `history.back()` 落到失效/过期/404 页面（如搜索来源笔记 `xsec_token` 过期导致"笔记不见了"），MUST 自动导航到已知良好的列表页兜底，并在**确认落在健康列表页（有可见卡片、非坏页）后**再上报 `page.cards`；MUST NOT 在坏页/0 卡时静默不上报而陷入边-云互等。

#### Scenario: history.back 落到过期笔记 404 → 兜底导航
- **WHEN** 返回时 `history.back()` 落到 token 过期的笔记详情页（404/坏页）
- **THEN** 边缘探测到非健康列表页（坏页标记或 0 卡）即 `Page.navigate` 到良好列表页（explore 或重新发起搜索），并轮询确认出现可见卡片后再上报 `page.cards`

#### Scenario: 坏页不静默
- **WHEN** 返回后页面无可见卡片且疑似坏页
- **THEN** 边缘不静默返回，而是导航兜底 + 健康校验；仍不可恢复时显式记录，避免循环停滞

### Requirement: CDP 连接丢失 MUST 有界自愈，不可恢复才诚实终止

边缘端与本机 Chrome 的 CDP（DevTools）WebSocket **意外关闭**时，边缘 MUST 在**有界重试**内尝试自愈：重新发现当前小红书页 target（MUST 按域名过滤、MUST NOT 落到无关 tab）→ 重建 CDP 连接 → 重新启用所需 CDP 域并**重注入反检测脚本** → 续跑浏览循环。重试 MUST 有次数上限，且重连总时长 MUST 由**运行时硬上限**约束并**短于云端 idle 看门狗阈值**，使重连必然在看门狗误判前完成或失败。

重试耗尽后边缘 MUST 干净终止：停止一切上报、退出浏览循环，由云端 idle 看门狗兜底结束会话；MUST NOT 静默假成功、MUST NOT 空转占着会话假装仍在浏览。

CDP 重连 MUST NOT 触碰边-云会话连接、MUST NOT 重发 `edge.hello`（即 MUST NOT 触发云端会话或互动预算重置）。重连续跑 MUST NOT 重放断连瞬间正在执行的命令（避免在已失效坐标上盲目重放造成静默假成功）。

边缘主动 `close()`（如会话正常结束）MUST 能抢占正在进行的重连退避循环，使其不再建立新连接。

#### Scenario: CDP WS 意外关闭 → 有界重连成功后对云端透明续跑
- **WHEN** 浏览过程中 CDP WS 被 Chrome 关闭（非边缘主动 close）
- **THEN** 边缘以指数退避在次数与总时长上限内重连：重新发现含小红书域名的 page target → 重建连接 → 重新启用 Runtime/Page/Input 并重注入反检测脚本 → 重报当前页 `page.cards` 或 `note.detail` 让云端重判
- **AND** 其间 MUST NOT 重发 `edge.hello`、`sessionId` 不变、云端透明续跑且互动预算与风控水位不被重置

#### Scenario: 重连成功但页面处于阻断态 → 先过浮层闸门再续跑
- **WHEN** 重连成功但当前页面被登录/验证码等阻断浮层盖住（域名过滤通过、但页面不可用）
- **THEN** 边缘在重报快照之前 MUST 先经过与冷启动同口径的浮层闸门（等待阻断解除或上报升级），MUST NOT 把「连接已活」误当「会话可用」而向被浮层盖住的页面盲发命令

#### Scenario: 重连耗尽上限 → 诚实终止、不静默假成功
- **WHEN** 有界重连的次数或总时长上限耗尽，仍无法重建 CDP 连接
- **THEN** 边缘保持 CDP「未连接」、后续 `cdp.send` 继续如实失败；浏览循环走干净终止路径（如本地终止理由 `cdp_unrecoverable`），停止一切上报并由云端 idle 看门狗兜底结束会话
- **AND** 边缘 MUST NOT 继续上报、MUST NOT 假装仍在浏览

#### Scenario: 重连不重放断连前的半截动作
- **WHEN** CDP 断连发生在某条命令执行中途，重连随后成功
- **THEN** 边缘丢弃该 in-flight 命令、MUST NOT 在重连后的页面上盲目重放它，而是按当前真实页面重报结构化快照交云端重新决策；断连时正在执行的动作如实回报 `ok=false`/`no_target`

