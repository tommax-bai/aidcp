## Context

现状（业界模式分析 workflow 已坐实，带 file:line）：3 个监测体形状的东西各写各的契约（弹窗后台监测体 / 登录内联探测 / 云端 idle 看门狗），两套各自为政的暂停——边缘本地软闸（命令泵前读缓存态，自清除）+ 云端传输硬停 `pauseEdge`（`pushToEdges` 丢帧、只放行 `session.end`，阻塞到人工清除）。无"谁此刻拥有执行端"的单一约束。新增监测体要手工穿 ~6 文件。

关键结构事实（决定实现方式，评审纠正）：
- 云端**不是**"循环取下一条命令"，而是 ~14 个独立事件处理各自 `sendCommand`；唯一统一咽喉是 `sendCommand → server.pushToEdges` 出口。
- `sendCommand` 同步返回 void。
- `profile.open` 是复合命令范例：cloud 发 `profile.open` → edge `Page.navigate` + 抽取 + `reportProfileDetail`；`command-bridge` 映射 `profile_open → profile.open`。`notification.open` 照此办。
- 自动结束看门狗按"执行端回报"刷新活跃时刻，130s 发 nudge、240s 发 `session.end` 并拆会话（会绕过暂停）。

## Goals / Non-Goals

**Goals:** 通知监控端到端跑通（评论/@→飞书，忽略赞/藏/关注）；监测体统一基类 + 清单（可扩展）；引入"临时离开式"软中断且保证恢复；务实最小、留干净扩展缝；不破坏验证码阻塞式路径与红线。

**Non-Goals（YAGNI，留到第 3 个中断源 / 第 4-5 个监测体）：** 集中中断仲裁器类、多状态流程机 + 每步超时、引用计数暂停登记、流程状态持久化、合并轮询 tick、通用 `watcher.signal` 信封、把验证码改造进通用信封。

## Decisions

### D1 监测体统一基类（行为不变重构）
抽出后台监测体基类：自走时钟轮询、状态缓存、翻转 diff 后**只上报一次**、启停幂等；抽象点仅 `probe()`（每监测体的检测）+ 状态相等判定。容错策略两个旋钮：`onProbeError: 'sticky'|'reset'`（后台分类 sticky）+ 一个**始终抛出**的即时复检（动作前 fail-closed 用，仅验证码这类）。现有弹窗监测体改为子类，外部契约 `{state; probeNow(); start(onTransition); stop()}` 逐字不变。

### D2 健壮性两补
- **心跳/存活**：记录"上次成功检测时间"，超过 N×轮询间隔仍未成功 → 上报一个**独立的"看不见"态**（degraded），不并入"none/没事"。这是传感层的"绝不假成功"。
- **非对称去抖**：进入阻塞态快（验证码 fail-closed，拖延=重开封号窗）、退出慢（连续 2-3 次确认清除才算清除）。内联每类计数，不做通用去抖引擎。

### D3 监测体清单
小清单持 `Watcher[]`，`startAll/stopAll`；替掉 `main.ts` 手工接线块。新增监测体登记一行；停全部保证不漏定时器。

### D4 两个命名暂停原语，监测体二选一
- **阻塞式（已有 `pauseEdge`，保持）**：丢帧、阻塞到人工清除，用于验证码/登录。
- **临时离开式（新）**：**不**用 `pauseEdge`（它丢帧、会把巡视自己的命令也丢掉）。实现 = 云端逻辑挂起浏览：在 `sendCommand` 出口设抑制开关 + 给命令打来源标记（browse / excursion），抑制期间扣住 browse、放行 excursion。同步 `sendCommand` 故巡视由**带外 async 函数**驱动。

### D5 通知巡视的正确实现（务实最小）
通知协调器收到 `notification.detected`：
1. 一次 `isHardPaused(edgeId)` 读——被验证码硬停则不巡视（mask，待清除后由下一次 detected 重新触发）。
2. 置"正在巡视"布尔（防重入）+ 在出口挂 browse 抑制。
3. **等执行端当前动作报完成**再发第一条巡视命令（执行端一次一动作；深读是不可中断的较长单元，等它整段完成）。
4. 线性 async：发 `notification.open`（复合：导航通知页 → 「评论和@」tab → 抽原始 items → 上报 `notification.items`）→ 收 items → 评论/@ 去重后发飞书 → 发 `navigation.back`（复用）回 feed。
5. **`try/finally`**：finally 必跑"解除抑制 + 确保回 feed + 清正在巡视布尔"；外加一个**总超时**兜底。任何出口（成功/空/超时/被验证码抢占/断连）都回得来。
- 巡视命令仍走执行端正常通道 → 通知页若也弹验证码，本地软闸照样挡住巡视自己的点击。

### D6 看门狗感知巡视
看门狗在"正在巡视"期间视为"有意暂停、不算空闲"：巡视期不发 nudge、不发 `session.end`；巡视结束恢复计时。**正确性阻断项**——否则巡视一卡，240s 看门狗会拆会话、绕过一切。

### D7 去重与不丢
- `notification.detected` 去重键 = `(edgeId, epoch)`，`epoch` 是**每次"无→有"翻转单调 +1**（不随未读数量变，数量会反复跳）。
- 飞书"已通知"水位/已见集合**只在确认收到 `notification.items` 后推进**；超时/失败不推进 → 失败的巡视能干净重来、真评论不被悄悄漏（红线）。

### D8 协议（+3，三处同步）
`notification.detected` / `notification.open` / `notification.items`，两份 `protocol.ts` 逐字一致 + `Record<MessageType,true>` + AC-PROTO-02 44→47 + `command-bridge` 加 `open_notifications → notification.open` + `docs/protocol.md` 头计数与表。强类型 per-type（不做通用信封）；payload 形状预留一个极薄共有壳便于将来合并。

### D9 边/云职责（边轻云重 / 状态单写）
检测在边缘（只读、只上报、不动手、不写风控态）；响应在云端（协调器决定是否飞书、驱动巡视命令走既有串行通道）。抽取在边缘产**原始** items（同 `page.cards`/`profile.detail`），**云端判要不要通知**——分类决策不下沉边缘。通知巡视是瞬时操作，**不**迁移 normal→warned→restricted（仅验证码迁移，风控终态仍云端单写）。

## Risks / Trade-offs

- [抑制开关漏放行巡视命令 / 漏标来源 → 巡视卡死] → 来源标记 + finally 解除 + 总超时三重兜底；测试钉"巡视后浏览必恢复"。
- [看门狗未感知 → 巡视半路拆会话] → D6 必须先于通知特性上线（correctness blocker）。
- [epoch 用数量 → 去重失效、并发巡视] → D7 epoch 单调每翻转一次。
- [抽取选择器对不上真实通知页] → best-effort 选择器 + 真机校准（同既有抽取器做法）；抽不到=上报空、不发飞书、正常恢复。
- [协议三处漂移] → 严格三处同步 + 两仓 typecheck + AC-PROTO 47。
- [重构碰到刚落地的验证码代码] → 外部契约逐字不变 + 现有测试护栏；不碰 `chrome-launcher`（edge 残留他人 WIP）。

## Migration Plan（分阶段，每步可独立验证）

1. **edge 重构**：抽监测体基类，弹窗监测体子类化（行为字节级不变）+ 去抖 + 心跳字段；现有 edge 测试 + AC-PROTO 不变护栏。
2. **edge 清单**：小清单替手工接线块（仅弹窗），行为保持。
3. **协议**：3 消息加两份 `protocol.ts` + Record + AC-PROTO 44→47 + bridge + docs；纯增量、typecheck 护栏。
4. **通知端到端**：通知监测体（清单登记）+ `notification.open` handler；云端通知协调器（线性巡视 + 出口抑制 + 来源标记 + `isHardPaused` + 看门狗感知 + 去重 + 复用飞书告警）。
5. 两仓全量回归 → §5 批量部署 → 真机校准选择器与去抖阈值。

## Open Questions

- 「开消息页 / 切评论@ tab」是否需要细分命令，还是 `notification.open` 一个复合命令内部做完（倾向后者，仿 `profile.open`）——已按"一个复合命令 +3 消息"定。
- login 是否借此也上报云端、成为阻塞式源 + 飞书告警（目前只本地停不上报）——本次不做，记为后续。
- 深读进行中能否被巡视打断——本次定为"等深读整段完成"（不可中断单元）。
