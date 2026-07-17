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

改完 D1 后，风控流水的日计数**恰好就是**「今天真的抵达 FB 的入群动作数」。故调度预筛（`content-scheduler.ts:395`）的分子改接同源（`server.ts:3434` 单点重接），**不再读成员账本**。

**备选（否决）**：让成员账本也数待审批（`status IN ('joined','pending') AND last_attempt_at >= 今日`）。**否决理由**：`markJoining`（`group-store.ts:741`）在**点击之前**就写 `last_attempt_at = now()`，因此「导航失败/登录失败/根本没点成」也会被数进去 ⇒ **过计**。过计与少计一样不诚实，而且会无故限死账号。风控流水的 `clicked` 判据没有这个问题——**这正是它该当分子的理由**。

### D4：`countJoinedToday` 保留不动

它回答的「今天成功加进几个群」是个**正确且有用**的问题，只是不该被当配额分子。本 change 只摘掉它作为闸门分子的那**一个**调用点（`server.ts:3434`）。

**若因此失去全部调用点**：**显式登记、不顺手删**——它是成功度量的现成实现，将来做 pending 回查、后台展示、真机验收都要用。

### D5：`joinDailyCap` 一个字不动

`server.ts:3435-3438` 的 `joinDailyCap` **兼作启用闸**：`if (!facebookGroupJoinAutoEnabled() && !facebookGroupJoinShadow()) return 0;`。它不是纯粹的「日限数字」——**改它会顺手关掉/打开自动加群**。本 change 只换分子、绝不碰分母。

### D6：展示账本零改动，无需任何防护

记账闸放行后会 `emit('interaction.occurred')`。join_group 的 `targetId` 早被**刻意**置 `undefined`（`handler.ts:571-576`），而入 `interaction_feed` 要求 targetId 为真且动作在四类白名单内（`server.ts:1422-1427`）⇒ **双重挡在外**。待审批的加群**不会**污染展示账本，**不需要新增任何防护**。

同理：`curated-content-store` 的 `markBotAction` 只认 `like`/`collect`（`:781`）⇒ 不受影响。

**实装时仍须逐点复核 `interaction.occurred` 的其余订阅者**（`server.ts:1391/:1412/:1424` 等），确认没有第四个消费者会把「计了配额的待审批加群」误当成功——**这是本 change 唯一需要审慎排查的面**。

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

1. **`countJoinedToday` 摘掉闸门用途后是否还有调用点？** 若归零 → 按 D4 显式登记保留（加 `@deprecated`? **倾向不加**——它没被弃用，只是暂无消费者，且 pending 回查一旦开工立刻会用）。实装时确认并写回。
2. **shadow 模式（`AIDCP_FB_GROUP_JOIN_SHADOW`）是否真的恒 `observation_only`？** D1 表格假设如此。**实装时坐实**——若 shadow 下也存在 `clicked: true` 的路径，那是个独立 bug（影子模式点了真按钮），须当场上报而非绕过。
3. **日限 3 在新口径下够不够用？** 明确**不在本 change 范围**。先让数字名副其实，再据真实数据评估数值。
