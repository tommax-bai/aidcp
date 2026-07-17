## Why

**一个数字被拿去回答两个不同的问题。**

| 问题 | 正确的分子 | 谁在问 | 今天 |
| --- | --- | --- | --- |
| 今天成功加进了几个群？ | 只数确认加入的 | 成功账本 | ✅ 对 |
| 今天 Facebook 看见这个号做了几次加群动作？ | 数真的点出去的 | **配额闸** | ❌ **没人回答** |

加群的分/时/日配额是**风控预算**——它约束的是「平台观察到多少动静」。但它读的是「我们办成了几件事」：

- `content-scheduler.ts:395` 的调度闸读**成员账本**：`countJoinedToday`（`facebook-group-store.ts:912-918`）只数 `status='joined' AND joined_at >= 今日`。
- `server.ts:3198` 的 `canJoin` 读**风控流水**：`canDo('join_group')`，而流水只在 `handler.ts:558-560` 的记账闸放行时才 +1，该闸要求 `result.ok`。

而边缘对「点了加入、Facebook 收到申请、但管理员还没批」**诚实回 `ok: false`**（`join-executor.ts:758-759`）：

```
if (post.reason === 'joined') return { ok: true,  ..., clicked: true, ... };
if (post.reason)              return { ok: false, ..., clicked: true, ... };   // ← pending 走这里
```

于是：**我们点了加入、Facebook 那边记了一笔申请、我们的风控记 0**。「日限 3」约束的是「今天批准了几个」，而**不是**「今天发出去几个申请」——后者不受任何约束、也不被任何计数器度量。从平台风控视角，**申请本身就是被观测、被计频的行为**。

**关键**：诚实的信号**早就在传了**——`clicked: true` 表示「边缘真的在页面上点了、FB 真的收到了」，与 `ok`（「达成目的了吗」）是**两个正交的事实**，且两个字段都已在协议里、都已如实上报。缺的只是让配额闸读对那一个。

**这不是「凭下发即记」**（`interaction-risk-gating` spec:27 明禁的那条）：**下发 ≠ 点击**。下发是云端发出命令（未必到达、未必执行）；`clicked: true` 是边缘**已在真实页面上完成点击**的事后回执。前者是意图，后者是既成事实。

## What Changes

- **重述加群配额的语义**：加群的分/时/日配额计的是**「真的抵达 Facebook 的入群动作」**，不是「确认加入」。**BREAKING（行为）**：日限第一次真正生效——今天超发的部分会被挡住。
- **记账闸按 `clicked` 而非 `ok` 放行 join_group**：`handler.ts:558-560` 的条件里，join_group 专属子句**已经**要求 `clicked === true && reason !== 'already_member' && reason !== 'observation_only'`——**该子句本身就已经是正确的判据**，只需把它从 `result.ok` 的合取下解出来。`ok` 继续管其余动作，逐位不变。
- **统一分子（顺带消灭「两个分子对一个分母」）**：`content-scheduler.ts:395` 的调度闸不再读成员账本，改读与 `canJoin` **同一个**风控流水日计数。`countJoinedToday` 本身**保留不动**（它回答的「今天成功加进几个群」是个正确且有用的问题，只是不该被当配额分子）。
- **明确不做**：**不动**「只有确认加入才算成功」——成功账本只认确认加入，这条是对的、原样保留。展示账本（`interaction_feed`）不受影响：join_group 的 `targetId` 早被刻意置 `undefined`（`handler.ts:571-576`）+ 入表要求 targetId 为真（`server.ts:1422-1427`），**双重挡在外、无需任何改动**。

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `interaction-risk-gating`: **MODIFIED**「Facebook group join is a first-class rate-limited action」——该要求现文明写 **a join MUST count against the quota only after a verified join**，且带 scenario「Only verified join counts」。本 change 正是**推翻这一条**（其余部分原样保留）：改为「配额计真的抵达平台的入群动作」，并显式区分**下发（意图，MUST NOT 计）** / **点击（既成事实，MUST 计）** / **确认加入（成功，另一个问题）** 三者。新增「配额闸与调度闸 MUST 读同一个分子」约束。

## Impact

- **aidcp-cloud（唯一动代码的仓）**：
  - `src/comm/handler.ts:558-576`：join_group 的记账放行条件从 `ok && <join子句>` 改为 `<join子句>`；其余动作的 `ok` 要求**逐位不变**。
  - `src/server.ts:3434`：调度闸分子从 `facebookGroupMembershipStore.countJoinedToday` 改接风控流水日计数（与 `canJoin` 同源）。`joinDailyCap`（`:3435-3438`）**不动**——注意它兼作「自动加群未开则返回 0」的启用闸，勿破坏。
  - `src/comment-agent/facebook-group-store.ts:912`：`countJoinedToday` **保留不动**（不再作配额分子，但仍是正确的成功度量；若失去全部调用点则显式登记而非顺手删）。
- **协议五处同步点一处不碰**：`clicked` / `ok` 均为既有字段、既有语义、既有上报；两份 `protocol.ts` **零 diff** ⇒ **不是热点单写者改动**。
- **aidcp-edge / aidcp-console**：**零改动**（边缘早已如实回 `clicked: true` + `ok: false`）。
- **DB**：**零改动**、无迁移（`risk_counters` 的 CHECK 早已含 `join_group`，`pg-risk-store.ts:32` + `:63-78` 幂等自愈 ALTER。**注意 `migrations/0002` 里那份仍是旧的六项——迁移文件会骗你说不支持，以 `pg-risk-store.ts` 为准**）。
- **部署**：纯云端单边，dev 当天可部署，无需出安装包。
- **真机验收**：挂 backlog 簇 90——发出 N 个入群申请（含待审批）后，日计数 = N 而非「批准数」；额度耗尽后调度闸不再起加群。

### 运营预期（必须提前打招呼，否则会被当 bug 报回来）

本 change 会让「日限 3」**第一次真正生效**。运营大概率会觉得「加群怎么变少了」——**其实是之前一直在超发，只是没人看得见**。这是本 change 的**目的**，不是回归。

### 前置事实（已核实，供实装者省一遍功）

- 边缘对 pending 的两个返回点语义**不同**，且已经天然正确，**无需区分处理**：
  - `join-executor.ts:702`（点击**前**观测到「之前就已在待审批」）→ `clicked: false` ⇒ 本次没对 FB 做任何动作 ⇒ **本来就不该计，改后仍不计**。
  - `join-executor.ts:758-759`（点击**后**确认为 pending）→ `clicked: true` ⇒ **FB 收到了本次申请** ⇒ **改后开始计**。
  - `already_member`（`:699`）同为 `clicked: false`；shadow 模式（`AIDCP_FB_GROUP_JOIN_SHADOW`）为 `observation_only` ⇒ 两者改后仍不计。
- `countJoinedToday` 作为闸门分子**只有一个调用点**（`server.ts:3434` → `content-scheduler.ts:395`）⇒ 换分子是单点改动。

### 关联与串行

- 与 `platform-honest-usage-caps`（已 propose）**无重叠**：那个改 UI 上限投影（`edge-companion-ui` / `platform-browse-surface`），本 change 改配额闸语义（`interaction-risk-gating`）。可并行。
- 与 `account-level-slow-start` 在 `interaction-risk-gating` spec 上**同文件不同要求**（它改「冷启动爬坡」要求，本 change 改「FB 加群一等限频动作」要求）⇒ 争用面小，archive 时按依赖序合并即可。
- 与 `facebook-join-actuation-decouple`（deferred）**无重叠**：那个治点击定位的语言相关缝，本 change 不碰 `join-executor` 与 `GroupJoinPayload`。

### Non-Goals

- **不治「待审批 → 已加入 永不回查」**（用户 2026-07-17 明确 defer：「待审批就记录待审批好了，后面再处理」）。数据已全在库（成员账本 `status='pending'`、加群审计 `outcome='pending'`、后台 FB 群页已有「待审批」列与筛选，`FacebookGroupsPage.tsx:249`）；缺的只是把它们捞回来复查的路径。本 change **不依赖**它。
- **不改「只有确认加入才算成功」**（成功账本口径正确，原样保留）。
- **不碰** `interaction_feed`（join_group 早被双重刻意挡在外，无约束违反可修）、不碰 `risk_counters` schema、不碰 `quota_config`、不改 console、不改边缘。
- **不重新评估日限的数值**（3 是否合适是另一个问题）。本 change 只让现有数字**名副其实**。
