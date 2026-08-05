# 设计：巡视停滞兜底

## 1. 现状坐实（带文件:行）

巡视是「临时离开式打断」：准入 → 暂停浏览 → 开通知首页 → 分诊 → 按类浏览 → 分类 / 去重 / 发飞书 → 返回首页 → 再分诊，直到三栏清零或到尝试上限，最后由收敛角色一次性「解除暂停 + 回信息流」。

| 事实 | 位置 |
| --- | --- |
| 收敛角色只订阅三类显式终止，**无计时器**（文件头自陈） | `aidcp-cloud/src/agents/excursion-resumer.ts:1-14, 42-50` |
| 分诊唯一入口是 `notification.home.arrived`；非巡视期的杂散上报直接忽略 | `aidcp-cloud/src/agents/notification-triage.ts:56, 61` |
| 「清零收尾」与「到上限诚实放弃」都 emit 同一个 `notification.triage_done`（放弃只进日志） | `aidcp-cloud/src/agents/notification-triage.ts:78-82` |
| 一类处理完 → `notification.opening{reason:'back'}` → `notification_back_home` | `aidcp-cloud/src/agents/notification-return-home.ts:30-32`、`src/orchestrator/role-dispatcher.ts:4242-4249` |
| 巡视期软暂停丢弃 browse 命令，**这一条丢弃分支不打日志**（另外三条都打） | `aidcp-cloud/src/orchestrator/role-dispatcher.ts:2026-2031` vs `:2014-2026, 2032-2041, 2003-2012` |
| `pauseClock` 只 early-return `checkSession`，**不影响 `checkIdle`** | `aidcp-cloud/src/agents/session-monitor-role.ts:229-231, 249` |
| 任意边缘上报刷新判活基线，含 `notification.detected.arrived` | `aidcp-cloud/src/agents/session-monitor-role.ts:180-189` |
| idle-nudge 默认 240s / idle-end 默认 1h | `aidcp-cloud/src/risk/resume-limits.ts:28, 31` |
| 单次模型调用天花板 180s（无导出常量，两处字面量） | `aidcp-cloud/src/server.ts:2822`、`src/llm/qwen.ts:275` |
| `IDLE_NUDGE_MIN_MS = 200_000`，其注释已把「MUST ≥ 单次模型调用天花板 180s」立成 lockstep 不变量 | `aidcp-cloud/src/risk/resume-limits.ts:41` |

**失效模式**：任何一步「回执成功但走岔了」⇒ 下一个本该到达的巡视上报永不到达 ⇒ 三个显式入口一个不满足 ⇒ `excursionActive` 与 `browseSuspended` 永久为真。软暂停出口把此后一切浏览命令**无日志丢弃**，所以外观是「系统在跑、只是这个号很安静」。

## 2. 为什么这道兜底不是在替上游擦屁股

CLAUDE.md §2 的加闸准入要求先排除「这道闸在替上游没做的等待 / 没拆的分类擦屁股」。逐条自检：

1. **它不是在替一次等待擦屁股。** 缺的不是「多等一会儿」——第二次 `notification.home.arrived` 不是晚到，是**永不会到**：边缘已经完成并回执了，它认为自己做完了。再长的等待也等不来。
2. **它不是在替一次分类擦屁股。** 边缘的回执是 `ok:true`，云端没有把任何原因折进兜底桶；三态回报在这条路径上是完整的。缺的是「**没有回执**」这一态本身没有观测者。
3. **上游那条 bug 修好后本 case 不复现，但兜底仍然值得加。** 判据是它防的是**整类**而不是一个实例：巡视共有 5 条命令、每条都在边缘有独立实现，任何一条将来「成功地做了另一件事」（导航落到别的页、分类栏改版点到别处、平台把通知页并进别的入口），后果都一模一样。一个「靠订阅终止信号收敛」的设计，对「巡视没有结束」这一态**结构上不可观测**——补的是这个结构缺口，不是这个 bug。
4. **它是已上线要求，不是新增要求。** `notification-monitoring` 已写「巡视必须有一个总超时兜底」，本 change 只是把它实装并收紧成可验证判据。

**后果侧的正当性**（CLAUDE.md 要求「概率低 × 后果可恢复 = 不加闸；只有后果不可逆且对外可见的才配用低概率当加闸理由」）：这里两个条件都不靠「低概率」——它**已经发生**，且后果是账号浏览无限期停摆、运营侧无任何信号。与项自身失败率的量级估计：新增的是一个进程内 `setTimeout` + 一次已有命令的重发，无网络、无库、无模型调用，自身失败率相对被防护的失效模式可忽略（不构成连乘风险）。

## 3. 判据：计什么、什么算「前进」

**不计「巡视总时长」，计「距上一次前进的间隔」。** 理由是总时限这个形状在本系统里必然错：巡视的结构上限是 3 类 × 3 次尝试 = 9 轮，每轮含一次边缘往返，其中评论类还含一次分类模型调用（天花板 180s）。要不误杀健康巡视，总时限得设到 9×180s ≈ 27min 以上——那个数字大到对停滞毫无兜底价值。**停滞判据没有这个矛盾**：健康巡视每轮都在前进，时限永不到点；一挂死就立刻开始累积。

「前进」= 巡视这条链上任何一个「还在动」的证据：

| 信号 | 为什么算前进 |
| --- | --- |
| `notification.opening` | 一次去通知页的导航意图发出（含自愈重发本身） |
| `notification.home.arrived` | 边缘真的重报了三栏计数（新一轮分诊的唯一入口） |
| `notification.category_selected` | 分诊真的选出了一类 |
| `notification.items.arrived` | 边缘真的回了条目 |
| 巡视命令 `action.completed{ok:true}` | 一条巡视命令真的被边缘执行完 |

**刻意不算前进的**：`page.cards.arrived` 等非巡视上报。事故里边缘正是靠它「看起来还活着」——把它算作前进，这道兜底就在它本该抓住的那一类上恒不触发。

## 4. 超时值 300s 及其量级依据

`EXCURSION_STALL_TIMEOUT_MS = 300_000`（5 min），自愈预算 1 次。

**下界（不可低于）**：健康巡视里存在一段**不可压缩的、期间零边缘上报**的间隔——评论类的分类模型调用，天花板 180s（`server.ts:2822`）。时限低于它 ⇒ 在合法的模型判定中途注入自愈导航。这与 `IDLE_NUDGE_MIN_MS` 注释里已经立过的 lockstep 不变量是同一条；本 change 把该关系写成断言（见 §7）。加上模型返回后的尾巴（飞书推送 + 一次边缘导航）约 20s ⇒ 下界约 200s，取 300s 留裕量。

**上界（不可高于）**：
- 最坏停滞窗口 = (1 次自愈 + 1) × 300s = **10 min**，必须远小于 idle-end（默认 1h）——否则巡视的兜底会被「杀掉整场会话」抢先，那是更粗的恢复手段。10 min ≪ 60 min ✓。
- 也应小于自动续场的一个休息周期，避免与续场路径互相踩。

**参考量级**：健康巡视全程实测 5–20s（用户实测），300s 是它的 15–60 倍，健康轮次上**不可能**触发；边缘通知任务租约 `leaseMs: 2*60_000`（`role-dispatcher.ts:1832`，实测约 200s 后 `released reason=expired`）——租约到期只释放任务、不碰巡视状态，所以它不是兜底，只是一个同量级的旁证。

**明确不做的精化**：可以做「相位感知」的时限（平时 60s，仅在分类模型在途时放宽到 300s），把常见情形的检出从 5min 压到 1min。不做的理由：它要引入一个额外的在途相位状态机，而 5 min 与「永久」之间的差距才是本 change 的价值所在；1 min 与 5 min 的差距是优化。留作后续，判据是「5 min 是否被实测证明太慢」。

## 5. 自愈通道的形状（红线逐条对照）

### 结构性可恢复 ⇒ 必须有带上限的自愈通道

判据是「同一步在**重新加载后的页面上**原样重来，有没有可能得到不同结果」。有：页面没渲染完、分类栏没出来、导航走岔到了别的页——**重开一次通知首页完全可能拿到三栏计数**。所以 MUST NOT 直接落终态、MUST NOT 记成「巡视失败」。

自愈动作 = 重发一次 `open_notifications`（经 `notification.opening{reason:'open'}`）。它有三条性质正好合适：

1. **只读**：只让边缘导航到通知首页并重报三栏计数，不点任何分类栏。
2. **重新对齐**：不假设浏览器现在在哪——事故里它已经跑到信息流了，`open_notifications` 从任何页都能把它拽回通知页。
3. **能穿过软暂停**：它属巡视命令集，`isQuotaSleepBypass` 放行（`role-dispatcher.ts:1930-1935`），不会被自己设的暂停开关扣住。

**恢复预算 MUST 只由失败消费**：预算只在停滞时限**到点**时扣（每次扣 1），健康巡视里的导航 / 返回一次都不占。

### 提交点：不得重复触发已按下的消费

巡视里**分类栏点击是消费未读、无回滚的提交动作**。自愈通道 MUST NOT 重复触发它：

- 自愈只发 `open_notifications`（首页），**不发** `browse_notification_*`（分类栏）。分类栏点击的唯一发起者仍是分诊角色，且只由 `notification.home.arrived` 驱动。
- 残余风险与它的既有边界：自愈带回的 `home.arrived` 会让分诊多跑一轮，可能多点一次分类栏。这不是「重投一条可能已上墙的内容」（读通知列表不对外可见、飞书侧另有 `itemKey` 去重水位），且**已被既有机制封顶**——`maxAttemptsPerCategory = 3` 是 per-excursion 单调计数器，无论自愈发生几次，一趟巡视对每类的点击数恒 ≤ 3（`notification-triage.ts:70-76`、`session-context.ts:incrementCategoryAttempts`）。本 change 不放宽这个上限。

### 回报三态不得压成一态

`excursion.ended.reason` 的取值域改为端到端可区分：

| 情形 | reason | 今天 |
| --- | --- | --- |
| 三栏真清零，正常收尾 | `triage_done` | `triage_done` |
| 到尝试上限**诚实放弃**某些类 | `triage_incomplete:<类名逗号分隔>` | ← 与上一行同为 `triage_done`（压成一态，本次拆开） |
| **因停滞被兜底强制收尾** | `stalled_no_progress:<phase>` | 不存在（永不收尾） |
| 分类异常 | `classify_failed:<原因>` | 不变 |
| 巡视命令诚实失败 | `cmd_failed:<动作>` | 不变 |

「被自愈救回、随后正常收尾」不单列原因值（它的终局**就是**正常收尾），但自愈发生本身 MUST 留一条响亮日志——否则「一次成功的抢救」与「从来没出过事」不可区分。

### 停手必须是结构性的

兜底收尾**不是**判巡视「做不到」：它解除浏览暂停、回信息流，让浏览闭环继续；未读水位不推进（`notifiedItemKeys` 只在确认收到条目时推进，本路径不碰），所以下一次「无→有」翻转仍会重新巡视这些通知，真消息不被静默吞掉。收尾日志 MUST 写清「已到停滞时限且自愈预算耗尽」，而不是伪装成一次正常结束。

## 6. 落点：为什么装进 `excursion_resumer` 而不新起一个角色

- 它是**巡视终止的唯一收敛点**，`if (!ctx.excursionActive) return` 这条幂等闸已经在那里；把第四个入口（计时器）接到同一个 `resume()` 上，天然与其余三个入口互斥，不会出现「兜底和显式终止同时收尾两次」。
- 新起角色要动 `event-bus/types.ts` 的 `RoleName` 穷举 + `src/config/role-catalog.ts` + 调度器注册 + 角色计数——CLAUDE.md §7 把角色注册列为**热点文件、单写者**，并行车队期不值得为一个计时器去占它。
- 代价：该角色的职责从「收敛终止」扩成「收敛终止 + 看住巡视别停滞」，文件头那句「无计时器」要改。这是诚实的职责扩张，不是耦合——两件事都以「巡视必须结束」为唯一目标。

计时器注入 `setTimeoutFn` / `clearTimeoutFn` / `clock`（照 `SessionMonitorRole` 的 `setIntervalFn` 先例）以便单测不靠真实墙钟；生产用真 `setTimeout` 并 `.unref()`。**生命周期**：`excursion.requested` 起算；每个前进信号重排；`resume()` 与 `unsubscribe()` 必清（角色实例跨会话复用，`endSession` 会 `unsubscribe` 全部角色 —— `role-dispatcher.ts:3073, 3201, 3278`），杜绝计时器跨场残留误触已结束的会话。回调里再查一次 `excursionActive` 作二道闸。

## 7. 测试策略（含「喂违规输入看闸真拦住」）

CLAUDE.md 与项目记忆都要求：恒真的闸等于没有闸；变异要问「哪条用例抓住的」。

1. **兜底真触发**（承重用例，直接复刻事故）：巡视开着 → 只喂一次 `home.arrived` 与一轮正常处理 → 之后**只喂 `page.cards.arrived`**（模拟边缘走岔到信息流、且回执成功）→ 推进假时钟过一次时限 ⇒ 断言发出了自愈的 `open_notifications`；再推进一次 ⇒ 断言 `browseSuspended === false`、`excursionActive === false`、`feed.entered{back_to_feed}` 发出、`excursion.ended.reason` 以 `stalled_no_progress` 开头。
   - 这条同时是**违规输入**用例：`page.cards.arrived` 就是那个「看起来像活着」的干扰项；若实现误把它算作前进，本用例必红。
2. **健康巡视不被误杀**（反向闸）：在时限内持续喂前进信号 ⇒ 断言零自愈命令、巡视不被强制收尾。守的是「兜底不误伤」。
3. **自愈预算只由失败消费 + 有上限**：断言自愈命令恰好 1 条（不是 0、不是 2），即「先自愈再收尾」的顺序真的存在，且不会无限重发。
4. **三态原因值可区分**：分诊到上限诚实放弃 ⇒ `excursion.ended.reason` 以 `triage_incomplete` 开头，与清零收尾的 `triage_done` 不相等。守的是「三态不得压成一态」。
5. **计时器不跨场残留**：`unsubscribe()` 后推进时钟 ⇒ 零事件。守的是「瞬时态绝不跨场」。
6. **常量关系 tripwire**（acceptance）：断言 `EXCURSION_STALL_TIMEOUT_MS >= IDLE_NUDGE_MIN_MS`（后者已锚定单次模型调用天花板）且 `× (预算+1) < DEFAULT_IDLE_END_MS`。守的是 §4 那两条边界不被后人随手改坏。

## 8. 明确不做

- **不改边缘**（`notification_back_home` 的语义 bug 由另一条工作流修）。
- **不加飞书告警**：本 change 只保证「不挂死」并留下可区分的原因值与响亮日志。把停滞升级成运营告警需要接告警存储与路由，属独立一件事；先让日志里有得查。
- **不做后台可配**：停滞时限走写死常量 + 构造注入（测试用），不进 `ResumeConfigProvider` / 面板 / schema。运营目前没有调它的诉求，而那条链路要动存储 + 面板 + 契约三层。
- **不给巡视加总时长上限**：理由见 §4（在本系统的结构下，它要么误杀健康巡视，要么松到没有兜底价值）。
- **不动 `maxAttemptsPerCategory`**、不动风控、不动协议、不新增角色。
