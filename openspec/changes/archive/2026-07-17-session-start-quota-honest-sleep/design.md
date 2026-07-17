# Design — session-start-quota-honest-sleep

> 本设计经一轮 43-agent 对抗性压测（`wf_497a58b2-823`，0 error）。压测**推翻了提案人的两条核心断言**，本文按推翻后的结论写。被推翻的两条各自留了一节（§3、§5），因为它们都很反直觉、下一个人极可能重新踩。

## 1. 修法只有一个形状：现问一次

配额账本（`RiskController`）**按账号存、跨连接共用**（`connection-runtime.ts:169-170`）。派生标记（`viewQuotaSleeping`）**每连接归零**（`:194` 重造）。

于是有两条路：

| 路 | 判决 |
|---|---|
| 把休眠标记**持久化 / 上提到账号级** | ✗ 过度设计。它是个纯派生量——权威事实已经跨连接活着了，再存一份副本＝多一处会漂移的状态 |
| 新会话**向权威事实现问一次**，无状态重算 | ✓ 无新状态、无新漂移面、无迁移 |

**现问一次是唯一可行形状**，因为它同时是 A 的可行部分（见 proposal Why ①：「别取消」没有靶子）。

## 2. 插入点：必须在 `feed.entered` 派发之前 🔴

`restartSession()`（`role-dispatcher.ts:1543-1591`）结尾是：

```ts
this.sessionActive = true;
this.sessionStartedAt = this.clock();
this.eventBus.emit('feed.entered', { pageType: 'feed', trigger: 'session_start', ts: this.clock() });
```

`EventBus` 是**进程内同步派发**。`feed.entered` 的下游角色链有可能在这一行内就同步走到 `sendCommand`。

⇒ **刹车必须踩在 `emit` 之前**，否则第一批命令从刹车底下漏出去，而且是**间歇性**的——测试可能全绿、生产偶发。

> 仓内已有同族判例：memory `fb-like-gate-sync-emit-race`（「点赞闸集合同步 emit 顺序竞态」）——闸装好了，但装在 emit 之后，于是首发漏过。**同一个坑，第二次。**

**选定插入点**：`this.sessionStartedAt = this.clock();` 之后、`this.eventBus.emit('feed.entered', ...)` 之前。

为什么不放在函数开头（`:1547` 可活跃时间闸旁边）：
- 那里是**拒签位**（`return` 掉、不开会话）。放这里等于把它写成会话级配额闸 ⇒ **破坏既有规格反向不变量**（`spec.md:483-486`：配额满 MUST 休眠、MUST NOT `session.end`）。
- 且 `sleepForViewQuota()` 要调 `sessionMonitor?.pauseClock()`，而 `SessionMonitor` 的 `startedAt` 在 `:1581` 的 `roles.forEach(r => r.subscribe())` 才重置。踩早了会 pause 一个还没开始计时的时钟。

**会话照开、刹车踩死** —— 这是本 change 的姿势，也是既有规格要的姿势。

## 3. 为什么保留 `:1556` 那行取消（被推翻的断言 #1）

提案人原先向用户陈述过两遍：「休眠被 `restartSession()` 里那行 `cancelViewQuotaSleep(false)` **主动取消**了」。

**这是错的。** `connection-runtime.ts:194` 每条连接重造 dispatcher ⇒ 事故路径（重连）上那行作用在一个**刚出生、`viewQuotaSleeping === false`** 的对象上，**什么都没取消**。观察对（重连后确实没刹车），因果反了（不是被取消，是从没被带过来）。

**但那行不是死代码。** `restartSession()` 是**四个入口的统一收口**（`:1544-1545` 注释逐字：「边缘 hello / 绑人设自启 / 续场 / 面板手动」）。后三个是**同连接内**重启 ⇒ 对象没重造 ⇒ 标记可能真的是 `true` ⇒ 那行是真取消。

⇒ **保留。** 而 §2 的「现问一次」紧跟其后，会把该睡的重新装回去。净效果：

```
cancelViewQuotaSleep(false)   // 清掉旧场的陈旧刹车（同连接重启时有意义）
   ... 重置会话态 ...
现问一次 → 被拒 → sleepForViewQuota()   // 按最新事实重新装
```

**先清后问**，不是「别清」。四个入口一视同仁，无分支。

## 4. 为什么看门狗一行不用改（B 被否）

用户的诊断对：不该对一个没活干的账号发滚动。但**位置错**。

刹车装上后，那条 240s nudge 走的是 `sendScrollCommand('idle_recover_nudge')` → `sendCommand()` → **`:765-767` 当场扣住**。它发不出去，边缘收不到，浏览器不被唤醒。**目的达成，看门狗零改动。**

三条不该动它的理由：

1. **它是唯一的存活探针**，且「不受 `clockPaused` 影响」是 spec 级 MUST（`browse-loop-resilience/spec.md:32/106/116-118`）——巡视期靠它兜底。
2. 边缘的重连预算按它的阈值立过约。
3. B 只管得到 `session.idle_nudge` 那一条，管不到另外两条重驱滚动：`:1457`（`resume_after_view_quota`）与 `:1781`（`resume_redrive`）。**C 三条全管**，因为它们全部经过 `sendCommand`。

**统一出口只有一个 ⇒ 刹车只装一处 ⇒ 三条源自动被管。** 这正是那个统一出口存在的意义。

## 5. D 不是 C 的前置（被推翻的断言 #2）

提案人原先向用户陈述过：「D 是 C 的必要前置，C 单独上 = 制造新事故」，还给了失败剧本（发布任务唤醒浏览器 → `main.ts:1463` 无条件 `browse.start()` → 在刹车下空转）。

**压测推翻了。** 理由：**配额耗尽期浏览器本来就是关的**（18:24:24 日志已证），任务唤醒一个停放的浏览器**今天就在发生**。C 不开新洞，只把暴露率从「大部分时候」抬到「总是」。

且已坐实边缘不会自己开：`browse.start()` 全仓 4 处——`main.ts:941` 在**身份重立**路径、`:1120` / `:1190` 是**启动期一次性装配**、`:1463` 是**唤醒后**。**WS 重连不经过任何一处** ⇒ 云端不发命令，浏览器就真停着。C 的前提成立。

**D 仍是真缺口，另起 change**（边缘侧、要出包，故不与止血捆绑）：

- `main.ts:1412` `wakeFromStandby` **不带唤醒原因** ⇒ 分不清「发布任务叫的」还是「浏览命令叫的」。
- `:1456-1463` 唤醒后**无条件** `browse.start()`，而 `:1114` / `:1184` 两处装配点**都有** `taskCoordinator.blocksBrowse` 守卫——`:1463` 是唯一漏的。
- 🔴 **D 的陷阱（务必写进 D 的 tasks）**：**不要直接复用 `blocksBrowse`**。`edge-task-coordinator.ts:324-326` 与 `:275-277` 的取值口径不同，它**不覆盖「正在唤醒」这个中间态** ⇒ 守卫会**静默失效，且测试全绿**。
- D 另带两项：FB 首屏 feed 上报未计入写者记账（违反 `facebook-session.ts:357` 自己的注释）；`session.end` 打到一个停放的浏览器上应为 no-op。

## 6. 日志：不补就是把红线扶正

`:765-767` 现在是裸 `return false`，**无日志**。同函数下方 `:778-782`（`comment_inflight` 支）就打：

```
[RoleDispatcher] command.suppressed reason=comment_inflight action=... note=... account=...
```

照抄格式，`reason=view_quota_sleep`。

**必须节流**：睡到明天 ≈ 8h，看门狗每 240s 一条 ⇒ 约 120 条/夜/账号，乘以车队规模。节流键取 `(account, reason)`，同一轮休眠只打首条 + 定期汇总，或按固定间隔降频。**宁可少打，不可不打**——不打日志的丢弃就是静默丢弃。

## 7. 明确不做（YAGNI）

| 不做 | 为什么 |
|---|---|
| 休眠标记持久化 / 上提账号级 | §1：纯派生量，权威事实已跨连接共用 |
| 会话级配额闸（配额满不开会话） | 破坏 `spec.md:483-486` 反向不变量 |
| 改看门狗 | §4 |
| 边缘加配额预检 | 违背「边轻云重 + 状态单写」铁律；边缘全仓无一处读用量，本来就不该有 |
| 修 `sliding-window-counter.ts:38` 的 `quota <= 0 → retryAfterMs undefined` | 真雷，但**本 change 打不到**：FB 慢启动第 1 天 view 上界 `[10,20]`、非 0。且刹车在，回落 60s 重判也只是空转日志、不唤醒浏览器。**单独记 backlog** |
| 修「frozen 账号被贴成 view 配额休眠」 | 同上：`explain()` 对 `state:frozen` 不返回 `retryAfterMs` ⇒ 回落 60s 重判、日志标签不诚实。**是既有行为**（`:2269` 那道闸今天就这样），非本 change 引入。可选顺手，见 tasks 4.1 |

## 8. 代价与验收

**代价**（三项，按大小）：约 67 轮/夜 × 40s 浏览器冷启动（≈13% 占空比）+ 700MB 内存翻搅 + **约 83k tokens（最小项，不作为立论）**。

**验收未知项**：边缘约每 5 分钟重连一次会重置空闲时钟 ⇒ 看门狗 1h 结束会话这条尾巴**今天可能从未触发过**。C 上线后：

- 若重连 churn 仍在 → 每次重连重新现问 → 再睡，行为收敛，1h 尾巴仍不现形。
- 若 churn 停了 → 1h 尾巴首次现形 → `endSession` → `:1604` 取消休眠 → 休息 → 续场闸（`:1804-1843`，六道判据无配额）放行 → `restartSession` → **本 change 重新现问 → 再睡**。闭环安全，每小时一次空转会话（不开浏览器）。

⇒ **两条路都安全**，但真机需观测一夜确认。**那个 5 分钟重连 churn 本身是否是独立缺口，根因未查** —— 单独记 backlog。
