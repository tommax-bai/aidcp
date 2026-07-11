# browse-loop-resilience Specification

## Purpose
TBD - created by archiving change fix-browse-loop-resilience. Update Purpose after archive.
## Requirements
### Requirement: 返回 feed 后浏览循环必须续刷而非死锁

返回 feed（`navigation.back`，`reason=back_to_feed`）之后，浏览循环 SHALL 继续评估并推进，MUST NOT 在「返回后首次扫描到 0 卡」时进入无限等待。无论 cloud 是否下发 `targetPage`，edge 的返回路径 MUST 优先前向导航到健康来源列表，并等待列表水合后再判定可见卡片，且 MUST 在仍为空时显式上报（而非静默吞掉），以保证 cloud 决策环始终能被触发。

#### Scenario: cloud 下发的 back 不带 targetPage
- **WHEN** edge 收到 `navigation.back{reason:'back_to_feed'}` 且 payload 无 `targetPage`
- **THEN** edge 按等同 `targetPage='feed'` 处理：优先 `Page.navigate(exploreUrl)` 返回 explore feed，并以 `waitForVisibleCards` 轮询（上限约 8s）等待卡片出现，而非依赖浏览器 `history.back()`

#### Scenario: 前向导航后仍未水合则重试健康校验
- **WHEN** 前向导航到来源列表后在轮询窗口内仍未出现可见卡片
- **THEN** edge 继续执行既有健康校验兜底：对 feed 重新确认 / 导航 `exploreUrl`，对 search 使用已记录搜索结果 URL或降级路径，并再次按 scroller 口径确认卡片出现

#### Scenario: 重轮询后仍为空不得静默
- **WHEN** 返回 feed 后重轮询仍扫到 0 张可见卡片
- **THEN** edge 显式上报一条空 `page.cards`（`cards: []`），MUST NOT 仅打日志后 `return` 而不发任何报文

### Requirement: cloud 在 back 成功后必须自驱动续刷

cloud orchestration SHALL 在收到 `action.completed{action:'back', ok:true}` 时主动发起一次 feed 续扫命令，而非仅依赖 edge 主动重报 `page.cards` 才能推进决策环。

#### Scenario: back 完成回执触发续刷
- **WHEN** cloud 收到 `action.completed{action:'back', ok:true}`
- **THEN** cloud 下发一次 `scroll`（`reason=rescan_after_back`），edge 据此重扫并重新上报 `page.cards`，决策环得以继续

### Requirement: 会话必须在有界 idle 内自愈或终止

cloud orchestration SHALL 运行一个 wall-clock 看门狗：当超过 idle-nudge 阈值无任何 edge 上报/命令活动时，MUST 发起一次恢复性 nudge；当超过更长的 idle-end 阈值仍无活动时，MUST 触发 `session.should_end` 结束会话。会话存活性 MUST NOT 依赖外部进程强杀（SIGTERM）来打破停滞。

看门狗的两段阈值 SHALL 可配置且热加载：**恢复轻推**（idle-nudge）默认保持较短（约 2min，且 MUST 大于详情页停留上限以免正常长停留中途误触），用于在**不结束会话**的前提下自愈瞬时卡顿；**放弃结束**（idle-end，MUST 大于 idle-nudge）默认 1 小时，仅当戳不活的真死局才回收。两段阈值 SHALL **为全局可配（取消账号维度——所有账号共用同一对阈值）**、运行时现读（改值下场即生效、无需重启），缺表/全局行缺失/非法值 MUST 逐位回落写死默认（**绝不 brick**）。看门狗的判活基线 MUST 由 edge 的真实上报/命令活动驱动，MUST NOT 把会话内 excursion（通知巡视）误判为停滞而过早结束（巡视上报本身即刷新判活基线）。

#### Scenario: 短 idle 触发恢复 nudge
- **WHEN** 距上一次 edge 上报/命令活动超过 idle-nudge 阈值且会话仍 active
- **THEN** cloud 下发一次 `scroll` nudge 以尝试重新驱动循环，且 MUST NOT 因此结束会话

#### Scenario: 长 idle 触发会话结束
- **WHEN** 距上一次活动超过 idle-end 阈值（默认 1h，> idle-nudge）仍无任何活动
- **THEN** cloud 触发 `session.should_end` 并下发 `session.end`，干净结束而非无限静默

#### Scenario: 看门狗阈值全局配置热加载
- **WHEN** 运营把**全局** idle-end 阈值由默认 1h 改为更短值
- **THEN** **所有账号**下一次判活即按新阈值（无需重启）；配置缺失/非法时回落写死默认、云端照常运行

### Requirement: 返回列表页须按来源页型(sourcePageType)返回正确的列表

`back_to_feed` 返回 MUST 回到笔记**来源的列表页**：来自 explore feed 的会话回 explore，来自搜索结果的会话回**搜索结果**。云端 SHALL 把会话的 `sourcePageType` 经决策指令的 `targetPage` 透传到边缘；边缘 SHALL 在打开笔记前记录当前来源列表 URL，并据 `targetPage` 选择返回目标，MUST NOT 把搜索来源的会话一律拽回 explore。

#### Scenario: 搜索来源会话返回搜索结果
- **WHEN** 一条笔记经搜索结果打开、深读后云端决定 `back_to_feed`，且会话 `sourcePageType==='search'`
- **THEN** 云端下发的 `navigation.back` 携带 `targetPage='search'`，边缘优先 `Page.navigate` 到打开笔记前记录的搜索结果 URL（而非 explore feed）

#### Scenario: feed 来源会话返回 explore
- **WHEN** 会话 `sourcePageType==='feed'`（或缺省）时决定 `back_to_feed`
- **THEN** 边缘通过前向导航返回到 explore feed

#### Scenario: 搜索来源 URL 缺失时诚实降级
- **WHEN** `targetPage='search'` 但边缘没有可用的已记录搜索结果 URL（如 edge 重启、直接停在详情页启动）
- **THEN** 边缘 MUST NOT 编造搜索 URL；它可以使用既有健康校验降级路径恢复到 explore feed，并显式上报真实卡片状态

### Requirement: 返回后须对 404/坏页健壮、健康校验通过再上报

边缘返回列表页时，若前向导航或必要的历史兜底落到失效/过期/404 页面（如搜索来源笔记 `xsec_token` 过期导致"笔记不见了"），MUST 自动导航到已知良好的列表页兜底，并在**确认落在健康列表页（有可见卡片、非坏页）后**再上报 `page.cards`；MUST NOT 在坏页/0 卡时静默不上报而陷入边-云互等。

#### Scenario: 返回落到过期笔记 404 → 兜底导航
- **WHEN** 返回路径落到 token 过期的笔记详情页（404/坏页）
- **THEN** 边缘探测到非健康列表页（坏页标记或 0 卡）即 `Page.navigate` 到良好列表页（explore 或已记录搜索结果 URL），并轮询确认出现可见卡片后再上报 `page.cards`

#### Scenario: 坏页不静默
- **WHEN** 返回后页面无可见卡片且疑似坏页
- **THEN** 边缘不静默返回，而是导航兜底 + 健康校验；仍不可恢复时显式记录，避免循环停滞

### Requirement: CDP 连接丢失 MUST 有界自愈，不可恢复才诚实终止

边缘端与本机 Chrome 的 CDP（DevTools）WebSocket **意外关闭**时，边缘 MUST 在**有界重试**内尝试自愈：重新发现当前小红书页 target（MUST 按域名过滤、MUST NOT 落到无关 tab）→ 重建 CDP 连接 → 重新启用所需 CDP 域并**重注入反检测脚本** → 续跑浏览循环。重试 MUST 有次数上限，且重连总时长 MUST 由**运行时硬上限**约束并**短于云端 idle 看门狗阈值**，使重连必然在看门狗误判前完成或失败。

重试耗尽（或快判判定浏览器进程已死 / 页面 target 归零）后边缘 MUST 走**主动诚实终止**：停止一切上报、退出浏览循环，并 MUST **主动诚实下线**——干净关闭边-云会话连接、使云端经其现成掉线清理**立即停止把该节点当作账号→节点路由目标**——随后以**可重起**语义退出进程，把恢复移交看护层（见能力 `edge-node-supervised-recycle`）。边缘 MUST NOT 静默假成功、MUST NOT 空转占着会话假装仍在浏览；MUST NOT 以「仅停止上报、保持边-云连接开着、被动等云端 idle 看门狗兜底结束会话」替代主动下线（那会在云端在线判据窗口内留下「在线但无浏览器能力」的可被路由僵尸）。诚实下线 MUST 等边-云连接真正关闭后再退出进程（带有界等待上限），MUST NOT 发起关闭后同步立即退出。

CDP 重连 MUST NOT 触碰边-云会话连接、MUST NOT 重发 `edge.hello`（即 MUST NOT 触发云端会话或互动预算重置）。重连续跑 MUST NOT 重放断连瞬间正在执行的命令（避免在已失效坐标上盲目重放造成静默假成功）。

边缘主动 `close()`（如会话正常结束）MUST 能抢占正在进行的重连退避循环，使其不再建立新连接。

#### Scenario: CDP WS 意外关闭 → 有界重连成功后对云端透明续跑
- **WHEN** 浏览过程中 CDP WS 被 Chrome 关闭（非边缘主动 close）且浏览器进程仍在、页面 target 可复现
- **THEN** 边缘以指数退避在次数与总时长上限内重连：重新发现含小红书域名的 page target → 重建连接 → 重新启用 Runtime/Page/Input 并重注入反检测脚本 → 重报当前页 `page.cards` 或 `note.detail` 让云端重判
- **AND** 其间 MUST NOT 重发 `edge.hello`、`sessionId` 不变、云端透明续跑且互动预算与风控水位不被重置

#### Scenario: 重连成功但页面处于阻断态 → 先过浮层闸门再续跑
- **WHEN** 重连成功但当前页面被登录/验证码等阻断浮层盖住（域名过滤通过、但页面不可用）
- **THEN** 边缘在重报快照之前 MUST 先经过与冷启动同口径的浮层闸门（等待阻断解除或上报升级），MUST NOT 把「连接已活」误当「会话可用」而向被浮层盖住的页面盲发命令

#### Scenario: 重连耗尽上限 → 主动诚实下线并以可重起语义退出
- **WHEN** 有界重连的次数或总时长上限耗尽（或快判判定浏览器进程已死 / 页面 target 归零），仍无法重建可用 CDP 连接
- **THEN** 边缘保持 CDP「未连接」、后续 `cdp.send` 继续如实失败；停止一切上报，**关闭边-云会话连接使云端立即停止路由**，等连接真正关闭（有界上限内）后以可重起退出码退出，恢复移交看护层
- **AND** 边缘 MUST NOT 继续上报、MUST NOT 假装仍在浏览、MUST NOT 保持边-云连接开着空转等云端看门狗兜底

#### Scenario: 重连不重放断连前的半截动作
- **WHEN** CDP 断连发生在某条命令执行中途，重连随后成功
- **THEN** 边缘丢弃该 in-flight 命令、MUST NOT 在重连后的页面上盲目重放它，而是按当前真实页面重报结构化快照交云端重新决策；断连时正在执行的动作如实回报 `ok=false`/`no_target`

### Requirement: 单场计时须排除会话内 excursion 耗时且不被时限中途打断

会话监测体的单场时长判定 MUST 排除会话内 excursion（通知巡视）所耗时间：excursion 开始时 MUST 暂停时限判定，excursion 结束时 MUST 把该段从单场已用时长扣除（恢复后再判）。时限 MUST NOT 在 excursion 进行中触发 `session.should_end` 把 excursion 中途打断——该结束须**延期**到 excursion 结束、扣除其耗时后，若真实浏览时长仍超限再判结束。暂停态 MUST 用多原因引用计数（而非布尔）以正确处理嵌套/并发暂停，且 MUST 在会话重启/拆除时清空、绝不跨场残留。excursion 期间 MUST NOT 冻结空闲看门狗（巡视上报持续刷新判活基线，卡死巡视由看门狗有界兜底）。

#### Scenario: 巡视期到点不中途结束、延期到巡视结束
- **WHEN** 单场时限在通知巡视进行中到达
- **THEN** 云端 MUST NOT 当场结束会话/打断巡视；待巡视结束、扣除巡视耗时后，若真实浏览时长仍超限再触发 `session.should_end`

#### Scenario: 巡视耗时不计入单场时长
- **WHEN** 一场会话内发生了一次耗时 T 的通知巡视
- **THEN** 该 T 不计入单场已用时长（巡视结束时从计时扣除），单场剩余浏览时长不被巡视吃掉

#### Scenario: 卡死巡视仍被看门狗兜底
- **WHEN** 巡视异常卡住、长时间无任何 edge 上报
- **THEN** 空闲看门狗（未被冻结）在 idle-end 阈值内照常触发 `session.should_end`，会话自愈终止而非永久冻结

### Requirement: 无浮层的整页离页返回必须直连来源列表、不得回踩失效笔记详情

边缘返回列表页时 MUST 以「直接来源列表导航」作为默认策略，而非优先依赖浏览器历史：

- **已在目标列表**（feed 匹配 explore feed、search 匹配搜索结果）→ MUST NOT 触发浏览器后退或整页重载（关浮层后列表即露出、滚动位由 SPA 保住）。
- **feed 来源** → MUST 直接前向导航（`Page.navigate(exploreUrl)`）回 explore feed，MUST NOT 为保滚动位而优先 `history.back()`。
- **search 来源且已记录搜索结果 URL** → MUST 直接前向导航到记录的搜索结果 URL，MUST NOT 回踩失效详情。
- **缺少可用来源列表 URL的边界情形** → MAY 使用健康校验包裹的历史兜底，但落地后仍 MUST 通过列表健康检查；一旦落坏页 MUST 立即前向导航到已知良好列表。

本要求是**预防**（不落到坏页），与既有「返回后须对 404/坏页健壮、健康校验通过再上报」互补而非替代：既有要求作为**落地后的安全网**原样保留；本要求消除会渲染出失效详情并被旁路监测误报的触发路径。返回完成的 `action.completed{action:'back', ok:true}` 回执契约不变。

#### Scenario: 看笔记→开通知→返回，直连 feed 不闪坏页

- **WHEN** 会话在 explore feed 打开笔记（真实点击、URL 带 `xsec_token`）后离页进入通知巡视，随后收到 `navigation.back{reason:'back_to_feed'}`，当前在 `/notification`
- **THEN** 边缘直接 `Page.navigate` 回 explore feed，MUST NOT `history.back()` 回踩那条 token 已失效的笔记详情；返回过程中 `error_code=300031` 坏页 MUST NOT 被经过 / 闪现，地址栏直接落在 explore feed

#### Scenario: 搜索来源的返回回到搜索结果

- **WHEN** 会话 `sourcePageType==='search'`、离页动作后返回，且边缘记录了打开笔记前的搜索结果 URL
- **THEN** 边缘前向导航回该搜索结果列表（而非 explore feed），同样不经浏览器后退回踩失效详情

#### Scenario: 笔记浮层盖在列表上的普通返回也优先直连

- **WHEN** 返回瞬间笔记浮层仍盖在来源列表之上（未发生整页离页）
- **THEN** feed 来源边缘仍优先 `Page.navigate(exploreUrl)` 直连列表；只有缺少可用来源列表 URL的边界情形才可使用健康校验包裹的 `history.back()`

#### Scenario: 万一仍落坏页，既有兜底照旧生效

- **WHEN** 因边界情形（如嵌套历史栈残留）前向导航或后退后仍落在非健康列表页（坏页 / 0 卡）
- **THEN** 既有「落坏页→`Page.navigate` 良好列表 + 健康校验后再上报 `page.cards`」兜底照常触发，MUST NOT 静默不上报而陷入边-云互等

### Requirement: 临时离开式软中断须在安全点暂停并保证恢复

除"阻塞式暂停"（出现后停到外部清除，用于验证码/登录）外，系统 SHALL 支持一种"临时离开式"软中断：暂停浏览闭环、跑一段有界的离开流程（如去通知页查看）、然后恢复。该软中断 MUST 在**统一的命令下发出口**处以抑制开关实现——暂停期间扣住浏览类命令、放行该离开流程自身的命令（命令须带来源标记区分）——MUST NOT 复用"阻塞式"的丢帧暂停（那会把离开流程自己的命令一并丢弃）。离开流程 MUST 在执行端**当前动作报完成之后**才插入第一条命令（执行端一次只执行一个动作，深读为不可中断单元），MUST NOT 与在途动作并发交错。离开流程 MUST 有总超时，且在任何出口（成功 / 空 / 超时 / 被阻塞式抢占 / 断连）都执行"恢复浏览闭环"补偿，使闭环 MUST NOT 被永久挂起。

#### Scenario: 软中断在安全点插入、不交错
- **WHEN** 软中断在执行端正执行某动作时触发
- **THEN** 系统等该动作报完成后才下发离开流程的第一条命令，不在动作执行中途插入

#### Scenario: 离开流程任意出口都恢复
- **WHEN** 离开流程超时或失败
- **THEN** 抑制开关被解除、浏览闭环恢复，不残留永久暂停

### Requirement: 自动结束看门狗在有意暂停期间不得开火

"长时间无动静自动结束会话"的看门狗 SHALL 区分"真空闲"与"有意暂停"（验证码阻塞式暂停、临时离开式巡视）。在有意暂停期间，看门狗 MUST NOT 发出恢复 nudge，MUST NOT 触发结束会话；有意暂停解除后才恢复正常空闲计时。

#### Scenario: 有意暂停不被误判空闲
- **WHEN** 边缘因验证码或通知巡视被有意暂停，期间无常规浏览回报
- **THEN** 看门狗不发 nudge、不结束会话，待暂停解除后恢复计时

### Requirement: 浏览循环因结束命令停止后须可被云端浏览类命令唤醒重启

边端浏览循环在收到会话结束命令（`session.end`）停止后（循环退出、不再上报），若随后收到云端**浏览类推进命令**（如 `page.scroll`、`navigation.back` 等），MUST 能**重启浏览循环**并重新上报 `page.cards`，使云端决策环得以继续；MUST NOT 把这类命令静默堆进**无人消费**的命令队列致其永久堆积（既有缺陷：循环停止后命令被入队但无消费者）。重启 MUST 幂等（循环已在跑时为安全空操作），且重启语义 MUST 与自动续场配套——云端续场重开会话后下发的引导命令必须能让已停的边端循环复活。重启 MUST NOT 在边端**主动诚实下线/关闭**流程中误触（关闭中收到的迟到命令不得复活循环）。

#### Scenario: 结束后收到浏览类命令重启已停循环

- **WHEN** 边端浏览循环已因 `session.end` 停止，随后收到云端一条浏览类推进命令（如续场引导的 `page.scroll`）
- **THEN** 边端重启浏览循环、重新评估当前页并上报 `page.cards`，云端据此续驱决策环

#### Scenario: 浏览类命令 MUST NOT 静默堆积无人消费

- **WHEN** 浏览循环未在运行时收到云端浏览类命令
- **THEN** 命令 MUST 触发循环重启被消费，MUST NOT 仅入队后无任何消费者而永久静默堆积

#### Scenario: 关闭流程中迟到命令不复活循环

- **WHEN** 边端正在主动诚实下线/关闭，期间收到一条迟到的云端浏览类命令
- **THEN** 边端 MUST NOT 因该命令重启浏览循环（关闭语义优先），干净退出

### Requirement: 作者主页关注被拦截后仍必须返回信息流，返回不得死等关注回执

进作者主页后的返回信息流 MUST NOT 依赖「关注的执行回执」作为触发器。云端 SHALL 在「主页关注评估完成」这一**单一决策点**上顺序处理：当且仅当决定关注且风控放行时先下发关注命令，随后**无条件**触发一次返回信息流。关注命令与返回命令 MUST 在该单一决策点按序下发（关注在前、返回在后），由边缘 FIFO 串行命令队列保证「关注先执行、返回后执行」，云端 MUST NOT 依赖回执来排序。

主页子链的所有分支——决定关注且放行、关注被风控/限频拦截、决定不关注——MUST 收敛到**恰好一次**返回信息流；返回触发器 MUST 唯一，MUST NOT 出现重复返回或零返回（卡死）。关注回执 SHALL 保留用于关注配额按真实回执扣减与诚实成败记录，但 MUST NOT 再作为返回信息流的触发器。返回命令 SHALL 携带主页停留时长（`dwellMs`）以保持关注后停留再离开的拟人节奏。

红线：MUST NOT 伪造关注回执来触发返回；关注真实成败 MUST 如实回报。

#### Scenario: 关注被风控拦截 → 仍返回信息流

- **WHEN** 决策端决定关注、但该次关注被风控/限频拦截（关注命令未下发、因而永不产生关注回执）
- **THEN** 云端仍在同一决策点触发一次返回信息流，边缘干净回到来源列表页（explore/搜索结果），MUST NOT 停留在作者主页死等关注回执

#### Scenario: 关注放行 → 关注先于返回执行（FIFO 时序）

- **WHEN** 决策端决定关注且风控放行
- **THEN** 云端先下发关注命令、随后下发返回命令；边缘按 FIFO 先执行关注（点击+校验+回报）、再执行返回；返回 MUST NOT 抢在关注点击之前导致关注落空

#### Scenario: 决定不关注 → 仍返回信息流

- **WHEN** 决策端看完主页决定不关注
- **THEN** 云端经同一决策点触发返回信息流，边缘回到来源列表页

#### Scenario: 关注回执只记账不触发返回

- **WHEN** 关注命令已下发并产生执行回执（真实新关注 / 已关注 no-op / 失败任一）
- **THEN** 该回执用于关注配额扣减（仅真实新关注扣）与诚实成败记录，但 MUST NOT 被用作返回信息流的触发器（返回已由单一决策点触发）

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

### Requirement: 云端 WebSocket 意外关闭后边缘必须有界重连或诚实终止

边缘端与云端会话 WebSocket **意外关闭**时，边缘 SHALL 在进程内以有界退避自动重连云端，重连成功后 MUST 重新执行 `edge.hello` 以恢复云端路由注册和云端下发的会话/节奏状态。重连期间边缘 MUST 将云端连接状态标记为 reconnecting/disconnected，MUST NOT 继续把自身表现为可正常收发云端命令。

重连成功后，边缘 MUST 清理旧连接上的瞬态命令状态，MUST NOT 重放旧连接断开前未完成或未确认的云端命令，并 MUST 基于当前真实浏览器页面重新上报结构化快照（如 `page.cards` 或 `note.detail`）交由云端重新决策。断线期间的 in-flight 请求或发布动作 MUST 如实失败、取消或丢弃，MUST NOT 编造成功。

重试耗尽或判定不可达时，边缘 MUST 进入诚实失败路径：停止继续上报、关闭云端连接状态、通过日志/Electron 状态暴露失败原因，并以可重起语义退出或交给看护层处理；MUST NOT 长时间空转占着本地运行态而让云端继续无边缘可路由。

#### Scenario: 云端服务重启后自动重连并重新注册
- **WHEN** 浏览过程中云端 WebSocket 因 `aidcp-cloud.service` 重启而关闭，且网络随后恢复
- **THEN** 边缘进入 reconnecting 状态并按有界退避重连云端
- **AND** 重连成功后重新发送 `edge.hello`，云端恢复该 edge/account 的在线路由注册
- **AND** 边缘应用新的 pacing/session 快照后重新上报当前真实页面快照，使浏览决策环继续推进

#### Scenario: 重连不重放旧连接命令
- **WHEN** 云端 WebSocket 关闭时边缘正在等待旧连接上的请求回包或执行旧连接下发的浏览/发布命令
- **THEN** 边缘将旧连接 pending 请求按连接关闭失败处理，清理旧命令队列或旧 in-flight 状态
- **AND** 重连成功后 MUST NOT 自动重放这些旧命令，而是上报当前页面快照交云端重新下发新命令

#### Scenario: 重连耗尽后诚实失败
- **WHEN** 云端 WebSocket 在配置的次数或时间上限内始终无法重连
- **THEN** 边缘记录并暴露云端重连耗尽状态，停止声称云端已连接
- **AND** 边缘以可重起失败语义退出或移交看护层，MUST NOT 保持一个本地 alive 但云端不可路由的僵尸浏览进程

#### Scenario: 主动关闭不触发自动重连
- **WHEN** 用户停止、会话正常结束或边缘主动下线而关闭云端 WebSocket
- **THEN** 边缘不启动自动重连退避循环，不重新发送 `edge.hello`，并按正常关闭语义退出或待命

