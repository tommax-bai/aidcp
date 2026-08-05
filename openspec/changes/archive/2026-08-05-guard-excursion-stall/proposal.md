## Why

已上线规格 `notification-monitoring` 的要求「通知巡视保证恢复，且不被自动结束看门狗误伤」里写着一句 **「巡视必须有一个总超时兜底」**，配套 Scenario「巡视任意出口都恢复浏览」把「因**超时** / 通知页打不开 / 被验证码抢占而未正常完成」并列为必须恢复的出口。

**这条要求从来没有被实装。** 收敛巡视终止的角色 `excursion_resumer` 只订阅三类**显式**信号（分诊完成 / 分类异常 / 巡视命令回执 `ok:false`），它自己的文件头注释就写着「收敛所有终止，**无计时器**」。

**它是怎么被漏掉的**：那三个入口覆盖了巡视**所有已声明的结束方式**，看上去是穷举的——每一种「巡视结束了」都有对应事件。漏的是另一类：巡视**没有结束、也不会再结束**。「什么都没发生」不产生事件，所以一个「靠订阅终止信号来收敛」的设计，结构上就看不见它。少的那条腿只有计时器能补。

2026-08-05 14:17 OL 上把这个缺口跑成了真事故（账号 `63e2ff0500000000260049ce`）：巡视处理完评论类后，云端下发 `notification_back_home` 期望边缘重报通知首页三栏计数；边缘把这条命令实现成了「回信息流首页」，回报 `page.cards` 且**回执是成功的**。于是第二次 `notification.home.arrived` 永不到达 → 分诊不再触发 → 三个显式终止入口一个都不满足 → `ctx.excursion` 永远 active、`browseSuspended` 永远为真 → 该账号此后收不到任何浏览命令。**全链每一层的回执都是诚实的，所以无人报警。**

边缘那条语义 bug 由另一条工作流修。本 change 补的是云端这条已上线但缺席的保证——它防的是**整类**「回执成功但走岔了」，不是这一个 bug：任何一次巡视步骤「成功地做了另一件事」，今天都会让账号浏览无限期挂起。

### 一处必须先纠正的现状认知

事故分析里流传的「巡视期 `pauseClock` 让空闲看门狗也停了，所以会话也不会被收掉」**是错的**。`pauseClock` 只 early-return `checkSession`（时长 / 动作数 / 配额），`checkIdle` 明确不受它影响（`session-monitor-role.ts` 注释：「空闲看门狗**不受 clockPaused 影响**」）。真实情况是：

- **idle-nudge（默认 240s）确实发了，但完全无效且完全静默**——它被翻译成一次 `scroll`，而 `scroll` 在 `browseSuspended` 期被发命令统一出口丢弃，那条丢弃分支是**四个丢弃分支里唯一不打日志的**（配额休眠、评论在途、镜像陈旧三条都有日志）。
- **idle-end（默认 1h）确实会结束会话**，所以存在一条 1 小时的外层兜底。但它①太慢；②靠**杀掉整场会话**而不是救回巡视；③**并不保证到达**——判活基线由任意边缘上报刷新，而 `notification.detected.arrived` 也在刷新名单里，所以只要账号还在收新通知，这 1 小时可以被无限推后。挂死在活跃账号上就是真的永久。

同时这条要求的后半句「巡视期间看门狗 MUST NOT 发出恢复 nudge 或结束会话」与另一份已上线规格 `browse-loop-resilience`（「excursion 期间 MUST NOT 冻结空闲看门狗，卡死巡视由看门狗有界兜底」）**直接矛盾**，代码实装的是后者。本 change 顺带把这处矛盾按「实装 + 本次新增的巡视自有兜底」的口径收敛掉：巡视的兜底责任 MUST 由巡视自己的停滞判据承担，会话级空闲看门狗既 MUST NOT 被冻结、也 MUST NOT 被当作巡视的兜底。

## What Changes

- **给巡视装上停滞判据与有界自愈通道**（落在 `excursion_resumer`——巡视终止的唯一收敛点）：
  - 巡视开启时起算一条**停滞时限**；任何一条「巡视仍在前进」的信号到达即重新起算。
  - 时限到而巡视仍 active ⇒ **先走一次有界自愈**：重发一次「打开通知首页」重新对齐（只读，只重读三栏计数，不点分类栏、不消费未读）。
  - 自愈后仍在时限内毫无进展 ⇒ **诚实收尾**：解除浏览暂停、回信息流，`excursion.ended` 带**与正常收尾可区分**的原因值。MUST NOT 落终态说「巡视失败」，MUST NOT 静默什么都不做。
- **把巡视收尾的三态拆开**（今天「清零收尾」与「到尝试上限诚实放弃」压成同一个 `triage_done`）：分诊完成事件带上「哪些类被放弃」，收尾原因值随之三分——正常清零 / 诚实放弃 / 停滞兜底。
- **补上软暂停丢弃命令的日志**：`browseSuspended` 丢弃分支加节流日志，与既有三条丢弃分支对齐。这半个缺口正是「无人报警」的直接原因。
- **规格侧**：把「巡视必须有一个总超时兜底」这句概括收紧成可机械验证的判据（谁计时、从哪一刻起算、什么算前进、超时先做什么再做什么、原因值必须可区分），并收敛与 `browse-loop-resilience` 的看门狗矛盾。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `notification-monitoring`: 修改「通知巡视保证恢复，且不被自动结束看门狗误伤」——把已有的「必须有一个总超时兜底」从一句概括收紧为可验证判据（停滞判据 + 有界自愈 + 诚实收尾 + 三态可区分原因值），并把与 `browse-loop-resilience` 矛盾的看门狗条款按实装口径收敛。原有的「任意出口都恢复浏览」「巡视不因看门狗被误杀」两条保证不变、只增强。

## Impact

- `aidcp-cloud/src/agents/excursion-resumer.ts`：新增停滞计时 + 有界自愈 + 可区分原因值。
- `aidcp-cloud/src/agents/notification-triage.ts`：分诊完成事件带上被放弃的分类。
- `aidcp-cloud/src/event-bus/types.ts`：`notification.triage_done` 载荷加一个可选字段（additive）。
- `aidcp-cloud/src/risk/resume-limits.ts`：新增停滞时限常量与其 lockstep 不变量说明。
- `aidcp-cloud/src/orchestrator/role-dispatcher.ts`：软暂停丢弃分支补节流日志。
- `aidcp-cloud/test/integration/notification-excursion.test.ts`：补停滞兜底用例（含喂违规输入看闸真拦住）。
- `aidcp-cloud/test/acceptance/`：常量关系 tripwire。
- 不改协议 v2、不改数据库 schema、不改风控状态机、不改角色注册表（不新增 `RoleName`）、不改边缘。
- 拆仓（§8）：全部改动文件属主均为 `automation`，须同步到 `aidcp-automation` 后部署。
- 部署：默认 `dev`（现跑派生三服务，本改动落 `aidcp-automation.service`）。**ol 不动**。
