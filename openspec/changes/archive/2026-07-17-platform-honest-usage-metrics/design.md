## Context

前一个 change `platform-honest-usage-caps`（cloud `6122083`，已部署 dev、已归档 `2026-07-17`）做了半步：云端不再给 FB 供「收藏 25/天」「关注 15/天」这种它永远兑现不了的上限。它**刻意**把「计数照发、客户端行数不变」写进了法条：

> Withholding a cap MUST NOT withhold the corresponding total: ... This requirement changes which caps the cloud supplies; it does not change how many action rows the client renders.

结果就是今天屏幕上的样子：FB 的收藏格没有了 `/25`、没有了进度条，**但「收藏 0」还在**。用户 2026-07-17 的裁决直接推翻这一段：**不支持就不要展示**。

同时缺的另一半：FB 每天真在做、真受日限约束的**加群**，客户端一格都没有。数据一直在（风控计数器 `join_group`，均衡档 3/天；`fb-join-quota-counts-attempts` 刚把「待审批也记账」修好），后台用量表也一直在按「加群 用了/上限」渲染 —— 只有面向客户的那块屏幕看不见。

### 现状里几处必须先知道的事实

1. **上限面已被前一个 change 收口，计数面还没有**。云端 `pickDailyUsageCounts()` 把六个键**无条件物化**（缺失 → `0`），客户端 `main.cjs` 的 `cleanRequiredCounts()`（`:1604`）再物化一遍。两道物化叠在一起 ⇒ 只在云端摘 totals 是**无效功**（老客户端照样补回 0）。
2. **展开的窗口明细行已经是数据驱动的**：`renderer.js` 的 `quotaWindowView()`（`:590-593`）已经写着 `if (!hasTotal && !hasCap) continue`，且窗口 totals 走的是保留缺席的 `cleanOptionalCounts`（`main.cjs:1648`）。**云端一摘，窗口行立刻消失，客户端零改动。** 需要改的只有顶部那排 KPI 格。
3. **同一份「客户端指标键清单」在四个地方各手写了一遍**：cloud `protocol.ts:242` 联集 / cloud `server.ts:335` 数组 / edge `protocol.ts:533` 联集 / edge `main.cjs:1593` 数组（+ `renderer.js:429` 的 `USAGE_ITEMS`）。**没有任何一处漂移会被 typecheck 抓到** —— `Record<MessageType,true>` 那道穷举只护消息类型，护不到载荷字段的联集；而 `main.cjs` / `renderer.js` 是纯 JS。这正是 CLAUDE.md §2 第 4/5 处「静默丢弃」的同一个模子。

## Goals / Non-Goals

**Goals:**

- 平台结构上做不到的动作，客户端**整格不渲染**（不是「渲染一个诚实的 0」）。
- FB 客户端出现「加群」格，口径与后台用量表逐位同源。
- 判据 100% 来自 registry 既有声明，**不新建第二张「展示表」**。
- 投影失败时**保持现状**，绝不因查表失败让某个平台丢格子或凭空长格子。

**Non-Goals:**

- 不治「平台错标不可纠错」（backlog 90.8）—— 那是本 change 的天花板，见 Risks。
- 不给加群做边缘乐观 bump（客户端本地事件即时 +1）：加群不由浏览闭环在边缘产生可观测事件，靠 ≤60s 的云端快照足够。
- 不动 console 后台用量表（内部运维面，非客户信任边界；前一个 change 已把它明写为 Non-Goal）。
- 不碰 `dm_reply` / `comment_like` 两个风控动作。前者三档配额全是 0 ⇒ 一旦展示立刻是「0/0 今日计划已完成」= 新造一个谎；后者在 `AIDCP_COMMENT_LIKE` 旗标后。两者都等各自的线自己决定。
- 不出安装包（用户 2026-07-17 明确）。

## Decisions

### D1. 投影的对象从「上限」扩到「整个指标」，并显式推翻前一条法条

前一个 change 的分界线（摘上限、留计数）当时的理由是「计数是事实、上限是承诺，只有承诺会撒谎」。**这条理由在结构不支持的动作上不成立**：FB 的「收藏 0」不是一个事实观测，它是 `pickDailyUsageCounts` 对一个不存在的动作**物化**出来的常量。它读起来是「今天还没收藏」（暗示明天会有数字），而真相是「这个平台没有收藏」。**它和那条永远 0% 的进度条是同一个谎的两半，只是一半带分母、一半不带。**

所以 spec delta 必须**显式改写**那一段，而不是在别处加一条新规则绕开它 —— 两条互相矛盾的法条留在同一个 capability 里，下一个人照哪条都有理。

**备选（弃）**：客户端自己按平台隐藏。弃因：把 registry 的知识复制进渲染层 = 第二张表，且客户端拿不到权威平台值（本地 AdsPower 标签会错标，正是 90.8 那个坑）。

### D2. 判据只来自 registry 既有声明，两张矩阵都查

沿用前一个 change 已建好的 `USAGE_CAP_SUPPORT_SOURCE` 全覆盖 `Record<UiDailyUsageAction, …>`：`collect` 的不支持声明在逐帖动作矩阵、`follow` 的在编排能力矩阵、`publish` 两张都没有（显式 `'none'` = 永不摘）。新键 `join_group` 加进这张表 ⇒ **typecheck 逼下一个加第八个指标的人当场表态**它的支持性从哪读。这张表存在的全部理由就是这个（载荷类型是宽松的 `Partial<Record<…>>`，漏键 typecheck 一声不吭）。

### D3. fail-open 的方向是「保持现状」，不是「一律发」也不是「一律不发」

看起来是两条相反的规则，实为同一条：

| 键 | 现状 | 改变现状需要 | 查表失败 / 平台未知 |
| --- | --- | --- | --- |
| 既有六键 | 发 | 显式 `supported: false` | 照发（= 今天） |
| 新键 `join_group` | **根本没有** | 显式 `supported: true` | **不发**（= 今天） |

**统一表述：只有显式声明才能改变现状。**

这条不是洁癖。`isOrchestrationCapabilitySupported()` 的 fail-open 是 `true` —— 如果拿它来决定加群格是否出现，那么**平台未知的账号（90.8 那个永久错标坑）会凭空长出一个「加群」格**，而小红书没有群。新造一个谎来治一个谎。所以 `join_group` 的读法必须是「显式 `supported === true` 才算」，**绝不能复用那个 fail-open 到 true 的 helper**。

### D4. UI 键名直接叫 `join_group`，不起 `join` 别名

风控计数器、配额表（三档 1/3/5）、后台用量表全叫 `join_group`。UI 侧起个短别名就要一张 UI↔风控的**裸 string 对裸 string** 映射表 —— 本仓已经在 `action.completed.action` 上吃过一模一样的亏（CLAUDE.md §2 第 5 处：两侧各 21 条映射、typecheck 抓不到、回错名的后果不是报错而是角色永远等不到回执）。同名 ⇒ `pickDailyUsageCounts(riskTotals)` 直读，零映射、零漂移面。

代价：UI 键清单里六个短名 + 一个带下划线的长名，不齐整。**换 typecheck 抓得到的漂移面，值。**

### D5. 联集从 `as const` 数组派生，杀掉 cloud 侧那张手写清单

```ts
export const UI_DAILY_USAGE_ACTIONS = ['view','like','collect','comment','follow','publish','join_group'] as const;
export type UiDailyUsageAction = (typeof UI_DAILY_USAGE_ACTIONS)[number];
```

单一来源，`server.ts` 直接 import，那张手写数组消失。这是 `src/risk/types.ts` 的 `RISK_ACTIONS` 已在用的既有 idiom（同仓同款）。

**剩下抓不到的**：edge `main.cjs:1593` 的 `DAILY_USAGE_ACTIONS` 是纯 JS 数组，派生不了 ⇒ 只能靠测试钉住（一条断言：带 `join_group` 的载荷穿过清洗后该键仍在）。这个缺口必须写进注释，因为它的症状是**云端发了、界面不显示、没有任何报错** —— 与 `cleanSlowStart` 那道白名单同款（`main.cjs:1711` 的注释已经预警过这个模子）。

### D6. 每一个计数面都要投影，且**必须在 `pickDailyUsageCounts` 之后**

前一个 change 实装期数出来的上限面是 4 个（day / minute / hour / **session** + 慢启动开关回执）。计数面同理：`dayTotals` / `minuteTotals` / `hourTotals` / **`sessionTotals`**。

- **session 面尤其要盯**：`completeSessionUsageCounts()` 内部也调 `pickDailyUsageCounts(riskTotals)` ⇒ 不投影的话，小红书的「本轮计划」会冒出一个「加群 N」（风控计数器里真有这个数），FB 的会冒出「收藏 0」。
- **顺序法条继承**：投影必须是最后一步。`pickDailyUsageCounts` 六键（现七键）无条件物化，先摘再 pick 会把摘掉的键补回 `0`，而 `quotaSaturation` 会算出 `totals(0) >= cap(0)` ⇒ 标 saturated ⇒ 「收藏 **0/0** 今日计划已完成」——**同一个谎早一行重新引入，typecheck 全绿**。前一个 change 已在 `surface.ts` 函数注释 + 调用点各留了码内警告，本 change 扩到计数面时照抄。

### D7. 客户端：静态格 + 切 `hidden`，绝不动态建元素

`usage-grid` 不在任何 `innerHTML` 重建范围内（`slow-start-row` 的注释已经把这条纪律写在码里）。加群格作为**静态节点**进 `index.html`，JS 只切 `hidden`。

渲染规则：
- 有云端用量载荷 ⇒ 可见格集合 = **云端 totals 里真实存在的键**（`hasOwnProperty`，不是「值 > 0」—— 值为 0 是真实的「今天还没做」，必须照显）。
- 无云端载荷 ⇒ 回落今天的行为：本机六格（加群没有本机来源 ⇒ 不显）。

### D8. 乐观 bump **绝不能复活缺席键**（本 change 最容易静默回归的一处）

`bumpDailyUsage()`（`main.cjs:1750`）在边缘本地事件到达时给计数 +1，它内部调 `cleanRequiredCounts(usage.totals)`。**如果不改**：云端摘掉 collect ⇒ 格子隐藏 ⇒ 边缘来一个 `like` 事件 ⇒ bump 把 `collect: 0` 补回去 ⇒ **收藏格当场复活**，直到 ≤60s 后下一个云端快照才再消失。屏幕上就是「格子自己闪回来」。

⇒ `cleanRequiredCounts` 整个删掉，两个调用点（`normalizeDailyUsage` / `bumpDailyUsage`）都改成保留缺席；bump 只能给**已存在**的键 +1，绝不新建键。纯 JS，typecheck 一声不吭，**必须有测试**。

### D9. 布局不得假设恒为 6 格

`styles.css:1141` 写死 `repeat(6, minmax(58px, 1fr))`，窄窗 `:2153` 改 `repeat(3, …)` 并靠 `:nth-child(4)` 画行首边框。**`:nth-child` 数的是 DOM 位置、不管 `display:none`** ⇒ 隐藏两格后边框会错位。

改法：格子间的分隔线改由**网格间隙透出容器底色**产生（`gap: 1px` + 容器底色 = 发丝色 + 格子自己不带 border），彻底消灭 `:first-child` / `:nth-child(4)` 这类**位置依赖**；列数用 flex-wrap 或 `--kpi-count` 变量跟随实际可见格数。具体形态实装时定，法条只要求「不得假设固定格数」。

### D10. 加群格的口径 = 用量面

数字 = 今天发出去几次加群申请（**点了就算，含待审批**），分母 = 风控日配额（均衡档 3）。**不是**「今天成功进了几个群」。

这不是本 change 的发明：用户 2026-07-17 已就后台用量表裁决过 —— 「**在不同 tab 下，代表的含义就是不一样**」，用量面主语是配额、成员面才认确认加入。客户端 KPI 格与后台用量表**读同一个计数器**，所以必须是同一个口径；两块屏幕对同一个账号说不同的数，本身就是那个谎。而且这与旁边五格一致（它们也全是风控计数器）。

### D11. 视频号会只剩「发帖」一格 —— 这是规则统一的必然结果，用户已确认

视频号注册表声明 `read_content` / `like` / `collect` / `comment` 全 `interaction_inbox_only` 不支持，`follow` 同；`publish` 是 `'none'`（永不摘）⇒ 投影后只剩发帖。它今天显示的那六个 0 与 FB 的「收藏 0」是同一个谎，只是没人在看。**不为平台开白名单特例**（那要在投影里塞一张平台名单 = 第二张表 = D2 明禁）。

## Risks / Trade-offs

- **[出包前只有一半可见]** → 客户端改动落 master 但不打包（用户裁决）。运营机在出包前：窗口明细行已诚实（云端一摘就生效）、顶部 KPI 格仍是老样子、加群格不出现。**这不是 bug**，验收时必须按客户端版本分别核；本机 `electron:dev` 可立刻看全貌。
- **[平台错标不可纠错，backlog 90.8]** → 本 change 不治，且它现在多一个后果：错标成小红书的 FB 环境不但拿不到摘除，**加群格也不会出现**，症状与病灶依旧一模一样、无信号可辨（`account-store.ts:238` 的 `ON CONFLICT DO NOTHING RETURNING platform` 既有行永不覆盖 + 平台缓存无 `delete` + 缺失值静默回落小红书）。建议的最小治法仍是「载荷回带云端按哪个平台投影的」作诊断字段。
- **[慢启动 day1-2 会把加群上限压到 0 ⇒ 「加群 0/0 今日计划已完成」]** → **预先存在、非本 change 引入**：FB 冷启动曲线 day1 的 `comment` / `publish` 也是 `[0,0]`，今天就已经这么显示。本 change 只是让加群加入这个既有形状。登记，不治。
- **[四张手写键清单杀掉一张，剩三张]** → cloud 侧派生消灭一张；edge 两处（`protocol.ts` 联集靠 §2 的逐字一致纪律、`main.cjs` 数组靠测试）+ `renderer.js` 的 `USAGE_ITEMS`（漏了就是格子不显、无报错）。缺口写进码内注释 + 一条穿透测试。
- **[协议热点并行冲突]** → 两份 `protocol.ts` 是 §7 明列的单写者文件。本 change 只动 `UiDailyUsageAction` 一个联集（不动 `MessageType`），与在跑的 `facebook-join-actuation-decouple`（动 `GroupJoinPayload`）冲突面不重叠，但集成时仍按 rebase 纪律、不 force。

## Migration Plan

1. cloud 先落：registry 能力词 + 投影泛化 + 各 totals 面接线 + 派生联集。此时**老客户端立刻受益一半**（窗口明细行里 FB 的收藏 / 关注行消失），KPI 格不变、加群键被老客户端的键清单静默丢弃（**这是安全的丢弃，不是事故**）。
2. edge 落 master：协议联集 + 清洗保留缺席 + 乐观 bump 不复活 + 加群静态格 + 布局。**不打包。**
3. cloud 部署 dev（安全序列：`test:acceptance` → 全量 `test` → `typecheck` → 备份 → rsync → restart → healthcheck）。
4. 真机验收登记 backlog 簇 90（FB 环境），**分「有新包 / 无新包」两组判据**。

**回滚**：cloud 单侧回滚即可恢复今天的全部形状（把 `join_group` 从 UI 键清单摘掉 + 投影退回只作用于上限）—— 客户端不需要回滚，因为它只渲染云端给的键；老包本来就看不见加群格。

## Open Questions

- 无。范围（一律按平台声明 vs 只动 FB）与出包时机（先不出）已由用户 2026-07-17 裁定。
