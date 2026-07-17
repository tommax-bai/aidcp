## Why

配额表是**全局的**（PK `(tier, action)`，按保守/正常/激进分档），不含平台维度；云端组装 `ui.snapshot` 用量载荷时（`aidcp-cloud/src/server.ts:2154-2193`）**完全平台盲**，把档位里的每一项上限照单全发。于是 Facebook 账号收到「收藏 25/天」「关注 15/天」——而 Facebook **结构上没有收藏概念、也没有关注执行器**，registry 早已如此声明（`src/platform/registry.ts:237` `collect: { supported:false, reason:'no_collect_concept' }`、`:307` `follow: { supported:false, reason:'no_follow_actuator' }`）。两张表都在，只是**从来没人让它们说过话**。

后果是客户端「今日进展」为 FB 渲染出「收藏 0/25」+ `has-limit` 卡片样式 + 一根**永远 0% 的进度条**（`aidcp-edge/src/electron/renderer/renderer.js:460/468/469/473`），关注格逐位同构（0/15）。这不是「格子空着」——是**在展示一个不存在的计划**，即 `edge-companion-ui` spec:234 明禁的「MUST NOT fabricate caps, percentages, or plan-completed states」。

**客户端那半契约早就立好、也早就实现对了**：spec:183 已规定「上限缺失时，渲染计数但不编造上限 / 进度 / 完成态」，代码亦如实照做。缺的只是**云端那半**——没有任何要求禁止云端供给它自己不可能兑现的上限。本 change 补的就是这一条。

**附带收益（非次要）**：`aidcp-edge/src/electron/renderer/ui-logic.js:87` 的 `QUOTA_ACTION_PRIORITY` 循环里，一条永远完不成的「收藏 25」使 FB 上的「今天先到这里，明天继续」完成态横幅（archive `2026-07-13-client-goal-completion-ui`）**永久无法触发**。上限摘掉后该条自动掉出 `capped`（:139 `if (cap === null) continue`），完成态在 FB 上**第一次成为可触发的**。

## What Changes

- **云端按平台过滤用量上限**：`effectiveQuotas()` 之后、下发之前，把「该平台结构上不支持的动作」的上限从 minute / hour / day 三份 quotas 里摘掉。判据 100% 来自既有 registry 声明，**零新增 registry 字段**。
- **范围 = Facebook 的 `collect` 与 `follow` 两项**。只摘收藏则 FB 会带着一个逐位同构的谎上线、且说不出为什么它不算谎。注意 `follow` 的不支持声明在 `capabilities` 而非 `noteActions`——只查 `noteActions` 会**结构性看不见 follow**，故两个既有查询函数（`surface.ts:40` `isNoteActionSupported` / `:62` `isOrchestrationCapabilitySupported`）都要用。
- **只摘 `quotas`，绝不动 `totals`**。客户端对两者用两套清洗规则（`aidcp-edge/src/electron/main.cjs:1680-1681`）：`totals` 走 `cleanRequiredCounts`（`:1604` 强制物化六键、`undefined→0`），`quotas` 走 `cleanOptionalCounts`（`:1611` 只抄存在的键、保留缺席）。因此摘 `totals` 键是**无效功**（会 land、会全绿、会部署，屏幕一格不变）；摘 `quotas` 键则**旧客户端立刻生效**——零客户端改动、**无需出安装包**。
- **fail-open 是硬要求**：平台查询失败/抛异常 ⇒ 照发全部上限（回落今天行为），MUST NOT 因此让整行用量消失。
- **小红书逐位不变**（两个查询函数对 XHS 全 `true`）——这是回归判据，不是善意期待。
- **非 BREAKING**：`UiDailyUsageCounts` 本就是 `Partial<Record<…>>`（edge `protocol.ts:533` / cloud `:243`），缺键早在契约内；本 change 是**第一次真正行使该契约**。

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `edge-companion-ui`（**ADDED**，不改既有要求）: 新增「云端 MUST NOT 为平台结构上不支持的动作供给上限」——补齐 spec:183/:234 **客户端半边契约所缺的云端半边**（客户端「上限缺失时不得编造上限/进度/完成态」早已立法且实现正确，缺的只是没人禁止云端**发**这种上限）。**不动** `:96/:159/:201/:208` 的「六项指标」措辞——既有 spec 已写明「每个动作行显示其上限**当上限存在时**」（`:208`），本 change 与之逐字兼容、不改格数，故与三个 active `wechat-channels-*` change 的争用面仅为「同文件不同要求」。**不动** `:921-934`（FB 写动作分档呈现 / 加群 MUST NOT 贡献计数）——见下「已知 nit（本 change 不治）」。
- `platform-browse-surface`（**MODIFIED**，承重）: 既有要求「Note-scoped action support is declared per platform and gated at one point」写的是 **A single dispatch wrapper MUST be the only place that *reads* this support**——本 change 的 UI 上限投影是**第二个读者**，**按字面直接违反该 MUST**。按其真实意图（registry 注释自陈「唯一**拒绝点** + 审计」）把「唯一读者」收紧为「唯一**下发闸**」，并明确：只读消费者 MAY 读、但 MUST NOT 下发/拒绝/取消、MUST NOT 被当作执行点、MUST NOT 使任何拒绝逃过审计、且 MUST fail-open。这条**必须改、不能绕**——留着按字面就是违规实装。`capabilities` 侧无需改（其要求「each MUST have a wired consumer」是**下限不是上限**，未声明排他）。

## Impact

- **aidcp-cloud（唯一动代码的仓）**：`src/server.ts:2154-2193`（**必须在 try 块内**）——`effectiveQuotas()` 之后、`pickDailyUsageCounts` 之前按平台摘键。可新增一个纯函数收口（宜落 `src/platform/surface.ts`，与既有两个查询函数同处）。
- **协议五处同步点一处不碰**：两份 `protocol.ts` **零 diff** ⇒ **不是热点单写者改动** ⇒ 可与 `account-level-slow-start` 及三个 `wechat-channels-*` change 并行；`command-bridge.ts` 动作映射不动；`edge-client.ts` 主动命令白名单不动；`action.completed` 动作名口径不动；`docs/protocol.md` 的 `MessageType` 计数不变，仅需在 `:267-341` 样例处补一句语义说明（**某动作缺上限 = 该平台结构上无此动作**）。
- **aidcp-edge / aidcp-console**：**零改动**。
- **DB**：**零改动**、无迁移。
- **部署**：纯云端单边，dev 当天可部署，**无需出安装包**（本 change 的核心价值即在于绕开簇 90/92 那堵「已 land 但未到运营机」的墙）。
- **真机验收**：挂 backlog 簇 90，一条即可——FB 环境的收藏格与关注格不再显示 `/N` 与进度条，且「今日计划已完成」横幅在 FB 上第一次成为可触发的。

### 串行 / 协作声明

与 `account-level-slow-start`（今日新提、尚无 tasks）在 `edge-companion-ui` spec 与 `server.ts` 配额组装段重叠。本 change 体量小一个量级（云端一处、半天、零风险、不碰协议），**建议先落**，`account-level-slow-start` 在其上 rebase。**组合顺序**：先算完 `effectiveQuotas`（含慢启动 `min(曲线, 档位)` 压低），**最后**再按平台摘掉不支持动作的上限——本 change 的过滤**永远是最后一步**。

### 已知天花板（如实登记，不在本 change 治）

**平台错标不可纠错**：`aidcp-cloud/src/account-store.ts:238` `ON CONFLICT (account_id) DO NOTHING RETURNING platform` 使既有行 `platform` **永不被覆盖**；平台缓存全仓无 `delete`/`clear` 路径；`normalizePlatformId`（`registry.ts:345-351`）对**缺失**值静默回落小红书（`raw ?? 'xiaohongshu'`），只对未知字符串才抛。合起来：AdsPower remark 缺 `plat` 的 FB 环境（memory `adspower-env-platform-label` 记的真实场景）**首次登记即永久是小红书**。此类账号**拿不到本 change 的摘除**，且症状（收藏 0/25）与病灶**一模一样、无信号可辨**。`account-level-slow-start` 已在冷启动曲线侧治同一个根（「平台未知 MUST NOT 静默回落小红书曲线」），可参照其 fail-honest 形态另立 change。

### Non-Goals（显式防范围蔓延）

- **绝不给 `quota_config` 加 platform 维度**。把「不支持」编码成「限额=0」正是 `platform-browse-surface` 明禁的「靠数值巧合推断支持性」的变体——FB 收藏上限消失**必须**是因为 registry **声明**该平台无此概念。
- **绝不放宽 `interaction_feed` 的 CHECK**（加群已被 `handler.ts:571-576` 与 `server.ts:1422-1427` 双重刻意挡在外，该 CHECK 从未被挑战、无约束违反可修）。不碰 `risk_counters`。
- **不换格子、不加「加群」计数**（spec:934 已明禁；加群与收藏不是同一类量：结果由第三方决定、有「待批准」中间态，标量计数器表达不了「申请 3 个批了 0 个」）。
- **不删格子**（第二层：需改共享路径的六键补全器 `main.cjs:1604` + 静态节点绑定 `renderer.js:13-40` + CSS `nth-child` 边框逻辑 `styles.css:1121/2083-2087`，且需出安装包才到运营机）。摘上限后 FB 显示「收藏 0」——**仍占位，但不再撒谎**。
- **微信视频号排除在规则外**：其 `noteActions` 七项全 false、`capabilities` 六项全 false（`registry.ts:242-250/330-337`），套上规则只剩发布一格；而 `wechat-channels-interaction-management`（45/47，即将成法）已立法该平台整行不渲染、走独立 workspace。
- **不改 console**；**不动评论评估器的收藏哨兵**（它问的是「平台有无收藏概念」，与 `noteActions` 的「发不发命令」是不同问题；`comment_like: v1_unimplemented` 即反例形状）。

### 已知 nit（本 change 不治，登记备查）

`edge-companion-ui` spec:934「加群与搜索 MUST NOT 贡献任何计数」所附的理由是**falsifiable-by-work** 的：「（二者在云端权威计数投影中均不存在对应字段）」——这是一句关于**今日实现**的事实，不是原则。字段哪天被加上，这条要求的自陈理由就蒸发了，而它**真正的依据**是其上方的四档模型（待第三方批准 MUST 自成一档、MUST NOT 贡献计数）——一个标量计数器没有第四档，表达不了「申请 3 个、批了 0 个」。理由应改为引用该模型。

**本 change 放弃修它**，理由是成本收益不成立：该句被包在 `:921` 起的大要求块「Facebook 写动作必须在客户端如实分档呈现」内，MODIFIED 须整块复制（含全部 scenario），为一句括号措辞与已排队的 4 个 change 抢同一 spec 文件不划算，且与本 change 的云端上限投影无因果关系。留作后续独立 nit。
