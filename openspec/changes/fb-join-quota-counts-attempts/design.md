## Context

Facebook 加群的分/时/日配额今天由**两个闸**各自把守，而它们**读的是两个不同的数、对着同一个上限**：

| 闸 | 位置 | 分子 | 数据源 |
| --- | --- | --- | --- |
| 调度预筛 | `content-scheduler.ts:395` | `countJoinedToday` | **成员账本**：`status='joined' AND joined_at >= 今日`（`facebook-group-store.ts:912-918`） |
| 下发闸 | `server.ts:3198` `canJoin` | `canDo('join_group')` | **风控流水**：由 `handler.ts:558-560` 的记账闸喂 |

分母则是同一个：`effectiveQuotas().day.join_group`（`server.ts:3435-3438`）。

两个分子**都不认待审批**：

- 成员账本：待审批写的是 `status='pending'`（`facebook-group-join-scheduler.ts:436`），`joined_at` 保持 NULL ⇒ `countJoinedToday` 不数。
- 风控流水：记账闸（`handler.ts:558-560`）要求 `result.ok`；而边缘对「点了加入、FB 收到申请、管理员没批」**诚实回 `ok: false`**（`join-executor.ts:759`）⇒ 不记。

于是「日限 3」约束的是**今天批准了几个**，而不是**今天发出去几个申请**。后者不受任何约束、也不被任何计数器度量——**而 Facebook 恰恰是按后者观测这个账号的**。

### 决定性的既有事实：诚实信号早就在传

`join-executor.ts:758-759`：

```
if (post.reason === 'joined') return { ok: true,  ..., clicked: true, ... };
if (post.reason)              return { ok: false, ..., clicked: true, ... };   // pending 走这里
```

`clicked` 与 `ok` 是**两个正交的事实**，两个字段都已在协议里、都已如实上报：

- `clicked` = **边缘真的在页面上点了、FB 真的收到了**（既成事实）
- `ok` = **达成目的了吗**（平台对我们已做之事的回答）

**本 change 不需要边缘配合、不需要新字段、不需要动协议——只需要让配额闸读对那一个。**

### 更决定性的：记账闸里正确的判据**已经写好了**

`handler.ts:558-560` 现文：

```
if (
  result.ok &&
  (result.action === 'like' || ... || result.action === 'join_group') &&
  result.reason !== 'already_followed' &&
  (result.action !== 'join_group' || (result.clicked === true && result.reason !== 'already_member' && result.reason !== 'observation_only'))
)
```

最后那个 join_group 专属子句 **`clicked === true && !already_member && !observation_only`** —— **这就是「真的抵达了平台」的正确判据，一字不差**。它只是被压在 `result.ok` 的合取之下。**本 change 的核心改动 = 把它从 `ok` 底下解出来**，不是新写判据。

## Goals / Non-Goals

**Goals:**
- 加群配额计**真的抵达 Facebook 的入群动作**，而非「确认加入」。
- **一个分子**：调度预筛与下发闸读同一个数（顺带消灭「两个分子对一个分母」）。
- 成功账本口径**逐位不变**：只有确认加入才算成功。
- 零协议改动、零 DB 改动、零边缘改动、零 console 改动；纯云端单边，当天可部署。

**Non-Goals:**
- **不治「待审批 → 已加入 永不回查」**（用户 2026-07-17 明确 defer）。本 change **不依赖**它。
- 不改「只有确认加入才算成功」。
- 不碰 `interaction_feed` / `risk_counters` schema / `quota_config` / console / 边缘。
- **不重新评估日限的数值**（3 合不合适是另一个问题）。本 change 只让现有数字**名副其实**。

## Decisions

### D1：判据轴 = `clicked`，不是 `ok`

`ok` 问「达成目的了吗」，`clicked` 问「我们碰平台了吗」。**配额是风控预算 ⇒ 看后者。**

这条轴天然把边缘的各种返回分对了边，**无需任何额外分支**：

| 边缘返回 | `clicked` | 改后是否计 | 对不对 |
| --- | --- | --- | --- |
| 点后确认 pending（`:759`） | `true` | **计** | ✅ FB 收到了本次申请 |
| 点后确认 joined（`:758`） | `true` | 计 | ✅ 今天也不变 |
| 点前发现「之前就已待审批」（`:702`） | `false` | 不计 | ✅ 本次没对 FB 做任何动作 |
| `already_member`（`:699`） | `false` | 不计 | ✅ |
| shadow 模式 `observation_only` | `false` | 不计 | ✅ |
| 导航/登录在点击前就失败 | `false` | 不计 | ✅ 没抵达平台 |

### D2：这**不是**「凭下发即记」

`interaction-risk-gating` spec:27 明禁「MUST NOT 凭下发即记（下发未必成功）」。本 change **不违反**它，而且必须在 spec 里把这个区分写死：

- **下发（dispatch）= 意图**：云端发出命令，可能没到、可能没执行 ⇒ **MUST NOT 计**。
- **点击（clicked）= 既成事实**：边缘**事后回执**说它在真实页面上完成了点击 ⇒ **MUST 计**。

两者隔着一整个往返。把它们混为一谈，就会既失去这条 change 的收益，又保不住那条红线。

### D3：统一到风控流水这一个分子

> **【实装期证伪 2026-07-17 —— D3 不做，本节前提是错的】**
>
> D3 的整个论证压在一句话上：「改完 D1 后，风控流水的日计数**恰好就是**「今天真的抵达 FB 的入群动作数」」。**这句话是假的。**
>
> **根因**：记账函数 `RiskController.record()` 在写计数**之前会再过一次 `canDo()`**，不过就静默返 `false`、什么都不写（`risk-controller.ts:175-186`）。所以那个计数器的真实语义不是「抵达平台的动作数」，而是「**记账时policy恰好还允许**的动作数」——它是一个**下界**，不是那个量本身。**这正是本 change 要治的病，只不过在下一层**：拒绝把既成事实记下来，因为一条策略说这件事本不该发生。
>
> **它会具体怎么坏（已逐条坐实，非推演）**：加群的小时配额算出来是 **1**（`max(1, min(HOUR_BURST_CAP=2, ceil(3/4)=1))`，`quotas.ts:69`，normal 档 day=3 时无需任何覆盖即成立）。手动 `/comment --join` **按产品裁决刻意绕过配额闸**（`facebook-group-join-scheduler.ts:161`「手动命令跳过配额闸；自动巡回照旧受闸」），但回执照走记账闸——而 `skipRiskRecord`（`server.ts:1380`）**只豁免 `comment`、从不豁免 `join_group`**。于是：运营一小时内手动加 3 个群、全部真点、全部真加进去 ⇒ 第 1 次 record 通过（day=1），第 2、3 次撞小时窗（count 1 >= 1）被 `record()` 自己丢掉 ⇒ **计数器 = 1，真实点击 = 3**。
>
> 若照 D3 把调度预筛的分子换成这个计数器：预筛读到 1 < 3 ⇒ 放行 ⇒ 自动加群再打 2 次 ⇒ **当天真实点击 5 次，预算 3**。而**改之前**预筛读成员账本 = 3 ⇒ 挡住 ⇒ 总数 3 = 预算。**D3 会在本 change 存在的意义那一维上开倒车。**
>
> **认知反转**：「两个分子对一个分母」**不是缺陷**。那两个分子是**同一个量（今天抵达 FB 的入群动作数）的两个独立下界**——成员账本的每一个确认加入都必然抵达过平台；风控计数器记下的每一笔也必然抵达过平台。两个闸 AND 起来 = **取较紧的那个下界**，严格优于任何单个。D3 要求「统一」，实际是**把较紧的那个换成较松的那个**。
>
> **故本 change 只做 D1（记账闸），不做 D3**：调度预筛**逐字不动**，继续读 `countJoinedToday`。核心收益已经全在 D1 里——下发闸（`canJoin` → `canDo`）的分子从此认待审批，日限对「发出去几个申请」真正生效。D4 随之作废（`countJoinedToday` 仍是唯一生产调用点、仍然载荷）。
>
> **要真正统一，必须先治 `record()` 的丢数**（让 join_group 的「既成事实回执」不再被 policy 二次否决）。那是**另一个 change**，且要动风控子系统、须先对齐 `AC-RISK-*` 那条「被禁 record 返 false」红线的意图——已登记，见下方「不在本 change 范围」。

改完 D1 后，风控流水的日计数**恰好就是**「今天真的抵达 FB 的入群动作数」。故调度预筛（`content-scheduler.ts:395`）的分子改接同源（`server.ts:3434` 单点重接），**不再读成员账本**。

**备选（否决）**：让成员账本也数待审批（`status IN ('joined','pending') AND last_attempt_at >= 今日`）。**否决理由**：`markJoining`（`group-store.ts:741`）在**点击之前**就写 `last_attempt_at = now()`，因此「导航失败/登录失败/根本没点成」也会被数进去 ⇒ **过计**。过计与少计一样不诚实，而且会无故限死账号。风控流水的 `clicked` 判据没有这个问题——**这正是它该当分子的理由**。

### D4：`countJoinedToday` 保留不动

> **【实装期作废 2026-07-17】D4 随 D3 一起作废，但结论比它想要的更强**：`countJoinedToday` 不只是「保留」——它**仍是调度预筛的分子、仍在生产路径上载荷**，而且按上面的反转，它承担的是「较紧的那个下界」这个真实职责。**一个调用点都没摘。** 原文下面那段「若因此失去全部调用点」的处置**不适用**（实装期确曾摘掉并坐实归零，随 D3 一并撤回）。

它回答的「今天成功加进几个群」是个**正确且有用**的问题，只是不该被当配额分子。本 change 只摘掉它作为闸门分子的那**一个**调用点（`server.ts:3434`）。

**若因此失去全部调用点**：**显式登记、不顺手删**——它是成功度量的现成实现，将来做 pending 回查、后台展示、真机验收都要用。

### D5：`joinDailyCap` 一个字不动

`server.ts:3435-3438` 的 `joinDailyCap` **兼作启用闸**：`if (!facebookGroupJoinAutoEnabled() && !facebookGroupJoinShadow()) return 0;`。它不是纯粹的「日限数字」——**改它会顺手关掉/打开自动加群**。本 change 只换分子、绝不碰分母。

### D6：展示账本零改动，无需任何防护

记账闸放行后会 `emit('interaction.occurred')`。join_group 的 `targetId` 早被**刻意**置 `undefined`（`handler.ts:571-576`），而入 `interaction_feed` 要求 targetId 为真且动作在四类白名单内（`server.ts:1422-1427`）⇒ **双重挡在外**。待审批的加群**不会**污染展示账本，**不需要新增任何防护**。

同理：`curated-content-store` 的 `markBotAction` 只认 `like`/`collect`（`:781`）⇒ 不受影响。

**实装时仍须逐点复核 `interaction.occurred` 的其余订阅者**（`server.ts:1391/:1412/:1424` 等），确认没有第四个消费者会把「计了配额的待审批加群」误当成功——**这是本 change 唯一需要审慎排查的面**。

> **【实装期修正 2026-07-17】D6 的前提对、结论错——审计轴选错了。**
>
> 前提两半均已逐字坐实：join_group 的 `targetId` 确为刻意 `undefined`（`handler.ts:572-577`），入 `interaction_feed` 确实同时要求 targetId 为真 + 四类动作白名单（`server.ts:1438-1442`）⇒ 展示账本双重挡在外，属实。`markBotAction` 只认 `like`/`collect`（实际在 `src/cache/curated-content-store.ts:784`，**不是** `src/comment-agent/`）⇒ 不受影响，属实。
>
> **但「无需任何防护」是错的**：真正会被操作员看见的那一处**根本不走 `interaction.occurred`**。后台仪表盘按账号的用量表直接读 `risk_counters`（`panel-store.ts:389` `todayTotalsByAccount` → `/api/dashboard/summary` → console `AccountTotalsTable.tsx:35-53` 按 `RISK_ACTIONS` 铺列，`join_group` 标签「加群」，渲染成 `用了 / 上限`）。改完之后那一格从「加了几个群」变成「点了几次加群」，而同后台的 FB 群页面同时诚实显示「已加入 0 / 待审批 1」。**沿着「订阅者」这条轴审计，永远审不到它**——它是那张表本身被展示，不是事件被消费。
>
> **裁决（用户 2026-07-17）**：**不改前端标签**。「在不同 tab 下，代表的含义就是不一样」——那张表的主语是**配额用量**，「加群 2/3」读作「加群配额用了 2 格」，在新语义下是**真话**；主语是**成员关系**的页面继续只认确认加入。据此在 spec 里补了一段与一个 scenario 把这个区分写死，防止下一个人照着 D6 的误读去「修」前端。
>
> **另一个被漏掉的订阅者（仍属良性）**：`panel/panel-ws.ts:135` 用 `onAny()` 通配订阅**全部**事件、无动作过滤、无 targetId 要求，序列化后广播给已认证的后台浏览器客户端。全文 grep `interaction.occurred` 永远找不到它。它是原始事件中继（console 侧无 join_group 专属渲染），**不构成「报成已加入」**，故不改；但「grep 事件名 = 审计完毕」这条直觉在本仓是错的，记在这里。

## Risks / Trade-offs

- **[日限第一次真正生效 —— 这是目的，不是回归]** 运营大概率反馈「加群怎么变少了」。**其实是之前一直在超发**。→ **缓解**：部署前**必须**向运营打招呼；tasks 列为独立勾选项。若真的因此不够用，正确动作是**评估日限数值**（另一个问题），**而不是**把分子改回去。
- **[存量待审批不会被追溯]** 本 change 只影响改动后新发生的动作；历史上已发出、当时没记数的申请不会补记。→ **权衡**：接受。补记需要回溯审计流水，收益不抵复杂度；滑动窗自然在一天内收敛到正确。
- **[`interaction.occurred` 可能有未预料的第四个消费者]** 见 D6。→ **缓解**：tasks 列为强制排查项，逐个订阅者确认；**这是本 change 最可能出事的地方**。
- **[两个 pending 返回点语义不同]** `:702`（点前，`clicked:false`）与 `:759`（点后，`clicked:true`）**都叫 pending**，reason 字符串相同。若实装者按 `reason === 'pending'` 判据而非 `clicked` 判据，会把「之前就已待审批」也计进去 ⇒ 过计。→ **缓解**：D1 明确判据轴是 `clicked`、**绝不是** `reason`；测试须同时覆盖这两个点。

## Migration Plan

1. `handler.ts:558-576`：把 join_group 从 `result.ok` 的合取下解出来（其余动作的 `ok` 要求逐位不变）。
2. 排查 `interaction.occurred` 的全部订阅者（D6）。
3. `server.ts:3434`：调度预筛分子重接风控流水日计数（与 `canJoin` 同源）。
4. 单测 + 载荷级测试（见 tasks §3）。
5. `test:acceptance` → `test` → `typecheck`。**`AC-RISK-*` 必须全过**（安全红线：绝不自残、被禁 `record` 返 false）。
6. **向运营打招呼**（日限将真正生效）。
7. 部署 dev（安全序列照 §5）。**无需出安装包**、无 DB 迁移。
8. **回滚**：纯云端单边、无迁移 ⇒ 还原上一版本 tar。滑动窗计数会残留改动期间记入的 attempt 计数，一天内自然收敛，**无需数据修复**。

## Open Questions

1. **`countJoinedToday` 摘掉闸门用途后是否还有调用点？** ✅ **已结（2026-07-17）：问题本身作废——它根本没被摘掉**。实装期确曾摘掉并坐实「全仓归零」（唯一生产调用点就是 `server.ts` 那一处闸；`test/content-scheduler.test.ts:401/:434` 只注入自己的桩、从不碰 store 方法），随后因 D3 被证伪而**整个撤回**。它**仍在生产路径上、仍是调度预筛的分子**，且按 D3 的反转，它承担的是两个下界里**较紧的那个**——不是遗留物，是保险。
   （备查：若将来 D3 的后继 change 真的摘掉它，届时 TypeScript **不报未使用的公开方法** ⇒ typecheck / 测试 / lint 都不会告诉你它死了，必须靠注释显式登记，否则下一次清理会顺手删掉。）
2. **shadow 模式（`AIDCP_FB_GROUP_JOIN_SHADOW`）是否真的恒 `observation_only`？** ✅ **已结：是，但问题本身问错了地方**。`AIDCP_FB_GROUP_JOIN_SHADOW` **在边缘仓根本不存在**——影子模式纯粹是**云端调度器**的旗标，边缘对它一无所知。故这不是边缘问题；边缘只是在收到「只观测」指令时于点击代码之前就返回 `observation_only` / `clicked:false`。**不是独立 bug、无停手条件**。
   **但由此暴露一个真的隐患，值得记下**：正因为边缘不知道影子模式开着，它**没有能力拒绝点击**——整个「影子模式不点真按钮」的不变量，只靠云端点击调用点上游那两处 `if (shadow)` 守着。将来任何一条云端路径绕过那两处守卫到达点击，影子模式就会点真按钮，而**边缘测试、边缘 typecheck、两份 protocol.ts 全都抓不到**。已在 `test/handler-join-quota.test.ts` 补了一条防御性断言：即便回执谎称 `observation_only + clicked:true`，排除表仍不计——那是最后一道兜底，不是根治。
3. **日限 3 在新口径下够不够用？** 明确**不在本 change 范围**。先让数字名副其实，再据真实数据评估数值。

## 实装期坐实：几处与提案不符的事实（2026-07-17）

提案与 design 的行号 / 路径成文于改动前，实装时逐条重新定位，修正如下——**后来者以本节为准**：

| 提案写的 | 实际 | 影响 |
| --- | --- | --- |
| `clicked` 判据需新增 / 「把 `ok` 换成 `clicked`」 | **`clicked` 判据 2026-07-09 就在闸里了**（`handler.ts:561`），今天是 `ok` **且** `clicked` 两个都要 | 真正的改动只是**让 `ok` 不再管 join_group**。照字面「换成 clicked」去改，要么是 no-op、要么把 `ok` 整条删掉——而 `ok` 是**六个动作共用**的第一个合取项，删了 = 失败的点赞 / 评论被记成真互动，**直接踩「绝不静默假成功」红线**。已按动作收窄：`(result.ok \|\| result.action === 'join_group')`，并补零回归绊线测试钉住其余五个动作 |
| 「记账闸调用 `RiskController.record`」 | **闸里没有任何 record**。闸只决定 `emit('interaction.occurred')`；record 在 `server.ts:1369` 的订阅者里 | 「emit ≠ +1」：`record()` 内部**还会再过一次 `canDo`**，账号被限 / 配额已耗尽时静默返 false。故单测只能断言 emit 决策，**「日计数真的 +1」必须真机坐实**（tasks 6.4） |
| `content-scheduler.ts` 在 `src/comment-agent/` | 在 **`src/orchestrator/`**（`:395` 行号正确） | 照路径找会扑空 |
| `curated-content-store` 在 `src/comment-agent/:781` | 在 **`src/cache/:784`** | 同上 |
| `server.ts:3198` canJoin / `:3434` 分子 / `:3435-3438` cap | 实际 **`:3234` / `:3470` / `:3471-3474`**（整体漂移约 +36） | 仅定位 |
| D1 表格列了边缘 4 个返回点 | **还有第 5 个 `clicked:true` 返回点**（边缘 `join-executor.ts:763`）：`join_failed` / `post_not_confirmed_slow` | 两者改后**都开始计**。在「尝试」这条轴上是**对的**（真的点了 = FB 真的收到了）。但 `post_not_confirmed_slow` 是**刻意设计的可重试瞬态**，云端会短退避**重新下发、重新真点** ⇒ **一个群可能烧掉 N 格配额**。这在 D1 里完全没建模——FB 群页渲染慢时配额消耗会比预期快，属**预期内的诚实**，但运营看到「加群变少」时这是原因之一 |

### 本次撞见、但**不在本 change 范围**的洞（只登记、不动）

0. **【最重要，是 D3 的前置】`record()` 拒绝记录既成事实**（`risk-controller.ts:175-186`）。它在写计数前再过一次 `canDo()`，不过就静默丢弃——**而它丢掉的是一次已经真实发生、无法回滚的动作**。这与本 change 治的病**同构**（拒绝把既成事实记下来，因为策略说这件事不该发生），只是低一层。后果：那个计数器**永远只是下界**，「统一分子」（D3）在它被治好之前**做不得**。
   治法方向：让 join_group 的既成事实回执走一条**不二次否决**的记账路径（下发前的 `canJoin` 才是「该不该做」的闸；对事后回执再判一次「该不该做」，丢掉的只有事实本身）。**动手前必须先对齐 `AC-RISK-*` 那条「被禁 `record` 返 false」红线的意图**——它防的是「做」，不是「记」；但那是既有红线，不能单方面推翻。
   注：多记只会让 `canDo` 更早拒绝 ⇒ 方向上**只会更保守，不会更激进**，不构成「自残」风险。
1. **每会话加群预算同样只认「确认加入」**（`facebook-group-join-scheduler.ts:416`：`verdict === 'joined' && edgeOk` 才 `recordSessionJoin`）。**同一个 bug 的另一个计数器**：待审批的加群不消耗会话预算。今天被收紧后的日限盖住（日限先撞顶），故不构成越界，但两个计数器语义不一致。
2. **边缘在「点完之后被任务抢占」时回执不带 `clicked`**（边缘 `comment-handler.ts:107` 经 `TaskTakeoverError` 路径发 `{ok:false, reason:'preempted_by_task'}`，无 `clicked`）。点击**已经真实发生且不回滚**（边缘自己的注释就这么写），但云端按 `clicked === true` 判 ⇒ **漏计一次真实申请**。今天被 `ok:false` 挡着看不出来；本 change 之后它变成一个真实的少计。修它要动边缘 + 重打客户端。
3. **加群事件携带一个无关的 `noteId`**（`handler.ts:567-570` 对非 like/collect 回落 `session.currentNoteId`）。今天无害——三个 noteId 消费者各自**又**按动作过滤了；`noteId?` 是可选字段，无任何类型级保护。将来任何一个不按动作过滤的 noteId 消费者，会把一次 FB 加群误归到一篇不相干的小红书笔记上。
