## MODIFIED Requirements

### Requirement: 返回 feed 后浏览循环必须续刷而非死锁

返回 feed（`{platform}.navigation.back`，`reason=back_to_feed`）之后，浏览循环 SHALL 继续评估并推进，MUST NOT 在「返回后首次扫描到 0 卡」时进入无限等待。`xiaohongshu.navigation.back` 的 `targetPage` MUST 必填（`'feed' | 'search'`）：目标列表是发令方意图的一部分，边缘 MUST NOT 替云端补空；云端在会话来源页型未知时 MUST 显式下发 `targetPage='feed'`。缺 `targetPage` 的 `xiaohongshu.navigation.back` MUST 按格式错误 fail-closed 拒收（与未登记命令同族），MUST NOT 以任何缺省执行。`facebook.navigation.back` 不携带 `targetPage`——FB 的来源列表（home / search / group）是引擎记录的会话事实而非云端选择项。edge 的返回路径 MUST 优先前向导航到健康来源列表，并等待列表水合后再判定可见卡片，且 MUST 在仍为空时显式上报（而非静默吞掉），以保证 cloud 决策环始终能被触发。

#### Scenario: 缺 targetPage 的 XHS back 拒收
- **WHEN** edge 收到 `xiaohongshu.navigation.back{reason:'back_to_feed'}` 且 payload 无 `targetPage`
- **THEN** edge 按格式错误 fail-closed 拒收并如实回报，MUST NOT 按任何缺省列表执行；云端侧发送点在 `pageType` 缺席时已显式补 `targetPage='feed'`，正常运行不触发本路径

#### Scenario: 前向导航后仍未水合则重试健康校验
- **WHEN** 前向导航到来源列表后在轮询窗口内仍未出现可见卡片
- **THEN** edge 继续执行既有健康校验兜底：对 feed 重新确认 / 导航 `exploreUrl`，对 search 使用已记录搜索结果 URL或降级路径，并再次按 scroller 口径确认卡片出现

#### Scenario: 重轮询后仍为空不得静默
- **WHEN** 返回 feed 后重轮询仍扫到 0 张可见卡片
- **THEN** edge 显式上报一条空 `page.cards`（`cards: []`），MUST NOT 仅打日志后 `return` 而不发任何报文

### Requirement: 返回列表页须按来源页型(sourcePageType)返回正确的列表

`back_to_feed` 返回 MUST 回到笔记**来源的列表页**：来自 explore feed 的会话回 explore，来自搜索结果的会话回**搜索结果**。云端 SHALL 把会话的 `sourcePageType` 经决策指令的必填 `targetPage` 透传到边缘（来源页型未知时显式下发 `'feed'`）；边缘 SHALL 在打开笔记前记录当前来源列表 URL，并据 `targetPage` 选择返回目标，MUST NOT 把搜索来源的会话一律拽回 explore。

#### Scenario: 搜索来源会话返回搜索结果
- **WHEN** 一条笔记经搜索结果打开、深读后云端决定 `back_to_feed`，且会话 `sourcePageType==='search'`
- **THEN** 云端下发的 `xiaohongshu.navigation.back` 携带 `targetPage='search'`，边缘优先 `Page.navigate` 到打开笔记前记录的搜索结果 URL（而非 explore feed）

#### Scenario: feed 来源会话返回 explore
- **WHEN** 会话 `sourcePageType==='feed'`（或来源页型未知、云端显式补 `'feed'`）时决定 `back_to_feed`
- **THEN** 边缘通过前向导航返回到 explore feed

#### Scenario: 搜索来源 URL 缺失时诚实降级
- **WHEN** `targetPage='search'` 但边缘没有可用的已记录搜索结果 URL（如 edge 重启、直接停在详情页启动）
- **THEN** 边缘 MUST NOT 编造搜索 URL；它可以使用既有健康校验降级路径恢复到 explore feed，并显式上报真实卡片状态

### Requirement: 无浮层的整页离页返回必须直连来源列表、不得回踩失效笔记详情

边缘返回列表页时 MUST 以「直接来源列表导航」作为默认策略，而非优先依赖浏览器历史：

- **已在目标列表**（feed 匹配 explore feed、search 匹配搜索结果）→ MUST NOT 触发浏览器后退或整页重载（关浮层后列表即露出、滚动位由 SPA 保住）。
- **feed 来源** → MUST 直接前向导航（`Page.navigate(exploreUrl)`）回 explore feed，MUST NOT 为保滚动位而优先 `history.back()`。
- **search 来源且已记录搜索结果 URL** → MUST 直接前向导航到记录的搜索结果 URL，MUST NOT 回踩失效详情。
- **缺少可用来源列表 URL的边界情形** → MAY 使用健康校验包裹的历史兜底，但落地后仍 MUST 通过列表健康检查；一旦落坏页 MUST 立即前向导航到已知良好列表。

本要求是**预防**（不落到坏页），与既有「返回后须对 404/坏页健壮、健康校验通过再上报」互补而非替代：既有要求作为**落地后的安全网**原样保留；本要求消除会渲染出失效详情并被旁路监测误报的触发路径。返回完成的 `action.completed{action:'back', ok:true}` 回执契约不变。

#### Scenario: 看笔记→开通知→返回，直连 feed 不闪坏页

- **WHEN** 会话在 explore feed 打开笔记（真实点击、URL 带 `xsec_token`）后离页进入通知巡视，随后收到 `xiaohongshu.navigation.back{reason:'back_to_feed'}`，当前在 `/notification`
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

### Requirement: 浏览循环因结束命令停止后须可被云端浏览类命令唤醒重启

边端浏览循环在收到会话结束命令（`session.end`）停止后（循环退出、不再上报），若随后收到云端**浏览类推进命令**（如 `xiaohongshu.feed.scroll` / `facebook.feed.scroll`、`{platform}.navigation.back` 等），MUST 能**重启浏览循环**并重新上报 `page.cards`，使云端决策环得以继续；MUST NOT 把这类命令静默堆进**无人消费**的命令队列致其永久堆积（既有缺陷：循环停止后命令被入队但无消费者）。重启 MUST 幂等（循环已在跑时为安全空操作），且重启语义 MUST 与自动续场配套——云端续场重开会话后下发的引导命令必须能让已停的边端循环复活。重启 MUST NOT 在边端**主动诚实下线/关闭**流程中误触（关闭中收到的迟到命令不得复活循环）。

#### Scenario: 结束后收到浏览类命令重启已停循环

- **WHEN** 边端浏览循环已因 `session.end` 停止，随后收到云端一条浏览类推进命令（如续场引导的 `xiaohongshu.feed.scroll` / `facebook.feed.scroll`）
- **THEN** 边端重启浏览循环、重新评估当前页并上报 `page.cards`，云端据此续驱决策环

#### Scenario: 浏览类命令 MUST NOT 静默堆积无人消费

- **WHEN** 浏览循环未在运行时收到云端浏览类命令
- **THEN** 命令 MUST 触发循环重启被消费，MUST NOT 仅入队后无任何消费者而永久静默堆积

#### Scenario: 关闭流程中迟到命令不复活循环

- **WHEN** 边端正在主动诚实下线/关闭，期间收到一条迟到的云端浏览类命令
- **THEN** 边端 MUST NOT 因该命令重启浏览循环（关闭语义优先），干净退出
