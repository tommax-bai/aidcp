## Context

云端每次推 `ui.snapshot` 用量时，在 `aidcp-cloud/src/server.ts` 里组装两样东西：**计数**（`totals`，:2064-2103 段）与**上限**（`quotas`，:2154-2193 段）。上限来自 `effectiveQuotas()`，其数据源 `quota_config` 的 PK 是 `(tier, action)`——**全局、跨平台、无 platform 维度**。组装时无人问「这个账号是什么平台」，于是档位里有什么就发什么。

同一个云端进程里另有一张 registry（`src/platform/registry.ts`）**早已声明** Facebook 无收藏概念（`:237`）、无关注执行器（`:307`），且已有两个现成的导出查询函数（`src/platform/surface.ts:40` `isNoteActionSupported` / `:62` `isOrchestrationCapabilitySupported`）。**两张表都在，从来没人让它们说过话。**

客户端那半契约**早已立好且实现正确**：`edge-companion-ui` spec:183/:234 规定上限缺失时不得编造上限 / 进度 / 完成态，`:208` 更明确写着「每个动作行显示其上限**当上限存在时**」。代码亦如实照做（`renderer.js:460` `hasCap`）。所以本 change 不需要客户端配合——**它只是第一次让云端别撒谎**。

### 关键的既有机制（本设计的全部杠杆）

`aidcp-edge/src/electron/main.cjs:1680-1681` 对计数与上限用**两套清洗规则**：

```
const totals = cleanRequiredCounts(input.totals);   // :1604 强制物化六键，undefined → 0
const quotas = cleanOptionalCounts(input.quotas);   // :1611 只抄存在的键，保留缺席
```

这条不对称**决定了整个方案的形状**：摘 `totals` 键是无效功（被补回 0）；摘 `quotas` 键则**旧客户端立刻生效**。

## Goals / Non-Goals

**Goals:**
- 云端不再供给它自己结构上不可能兑现的上限（FB 的 `collect` 与 `follow`）。
- 判据 100% 来自既有 registry 声明，**零新增 registry 字段**、零新增概念。
- **零客户端改动、零协议改动、零 DB 改动**——纯云端单边，当天可部署 dev，**绕开「需出安装包才到运营机」那堵墙**。
- 小红书载荷**逐位不变**（回归判据，不是善意期待）。
- 顺带解锁：FB 的「今日计划已完成」横幅**第一次成为可触发的**。

**Non-Goals:**
- 不换格子、不加「加群」计数、不删格子（详见 proposal 的 Non-Goals）。
- 不给 `quota_config` 加 platform 维度；不碰 `interaction_feed` / `risk_counters`。
- 不治「平台错标不可纠错」（本 change 的天花板，已在 proposal 登记）。
- 不改 console、不改边缘、不改 renderer。

## Decisions

### D1：只摘 `quotas`，绝不动 `totals`

**为什么**：`cleanRequiredCounts`（`main.cjs:1604`）强制物化六键、`undefined → 0`。云端摘 `totals` 键的改动会 **land、会全绿、会部署，而屏幕上一格都不会变**——且本地 `electron:dev` 看不出来。三份候选设计里有两份的核心机制栽在这里。

**备选（否决）**：改 `cleanRequiredCounts` 让它保留缺席。否决理由：那是**共享路径行为变更**（今天所有平台都靠它保证六键齐全），会牵出 `statsFromDailyUsage`（`:1724-1731`）的六字段 legacy 形状、`renderer.js:13-40` 的模块级静态节点绑定（节点 remove 后 `closest('.kpi')` 在游离子树上照样返回、写入静默进虚空）、以及 `styles.css:1121/2083-2087` 的 `nth-child` 边框逻辑（数的是 DOM 子节点、不是可见节点）——且必须出安装包才到运营机。**摘上限已达成全部诚实收益，摘计数只多一份审美收益、代价高一个量级。**

### D2：两张矩阵都要查，只查一张是缺陷

`collect` 的不支持声明在 `noteActions`（`registry.ts:237`），`follow` 的在 `capabilities`（`:307`）。**只查 `noteActions` 会结构性看不见 `follow`**——FB 会带着一个与收藏逐位同构的谎（「关注 0/15」+ 假进度条）上线，且**说不出为什么它不算谎**。一轮对抗评审正是在候选设计的产出里当场抓到这一点。

### D3：过滤点必须在 `server.ts:2154` 起的 try 块**内**，且是**最后一步**

**try 块内**：该 try 的 catch 只 warn（`:2189-2192`）⇒ 平台查询抛异常 = 无上限 = 客户端降级成「有数无上限」= **天然 fail-open**。反例：放进 `totals` 段（`:2064-2103`，**不在** try 内）之前会 **fail-closed**——`ui-snapshot.ts:130-133` 对整个 promise `.catch(() => null)`，整行 KPI 消失、退回本机实时数。候选设计里有两份踩了这个坑。

**最后一步**：过滤必须在 `effectiveQuotas()` **之后**。这样与 `account-level-slow-start` 的 `min(曲线, 档位)` 压低天然可组合——先算完该发多少，最后再把发不了的摘掉。顺序颠倒则慢启动曲线会对一个不存在的动作做 clamp 运算。

### D4：宜落一个纯函数、收在 `surface.ts`

与既有两个查询函数同处（`isNoteActionSupported` / `isOrchestrationCapabilitySupported`），入参 `(platform, quotas)`、出参过滤后的 quotas，**同步、纯、永不抛**（内部 try/catch 兜住 registry 查询）。这样 D3 的 fail-open 不依赖调用点记得包 try，而是函数自证。

### D5：`capabilities` 侧的 spec 无需改，`noteActions` 侧**必须**改

`platform-browse-surface` 既有要求写的是 **A single dispatch wrapper MUST be the only place that _reads_ this support**。本 change 的 UI 上限投影是第二个读者，**按字面直接违反该 MUST**。按其真实意图（registry 注释自陈「唯一**拒绝点** + 审计」）改为「唯一**下发闸**」，并明确只读消费者的三条纪律（不得下发/拒绝/取消、不得被当执行点、必须 fail-open）。

`capabilities` 侧无需改：其要求「each MUST have a wired consumer」「No capability word may remain declared without a consumer」是**下限不是上限**，未声明排他。

### D6：不给 `quota_config` 加 platform 维度

把「不支持」编码成「限额=0」正是 `platform-browse-surface` 明禁的「靠数值巧合推断支持性」的变体（其既有 scenario「Facebook collect is refused explicitly, not by coincidence」即为此立）。FB 收藏上限消失**必须**是因为 registry **声明**该平台无此概念。

### D7：微信视频号排除在规则外

其 `noteActions` 七项全 false、`capabilities` 六项全 false（`registry.ts:242-250/330-337`）⇒ 规则机械套上去只剩发布一格。而 `wechat-channels-interaction-management`（45/47，即将成法）已立法该平台**整行不渲染、走独立 workspace**。故本 change 的过滤**只对已声明部分支持的平台生效**；对「全不支持」的平台不接管其渲染决策。

**实装形态**：过滤规则只摘**显式声明为不支持**的动作。视频号因全 false 会被摘到只剩发布——这与「整行不渲染」不冲突（整行不渲染由那个 change 决定，优先级更高），但**本 change 的验收 MUST NOT 依赖视频号的载荷形状**，且 Non-Goals 须写清不为其负责。

## Risks / Trade-offs

- **[平台错标不可纠错 —— 本 change 的天花板]** `account-store.ts:238` `ON CONFLICT DO NOTHING RETURNING platform` 使既有行 platform 永不被覆盖；平台缓存全仓无 `delete`/`clear`；`normalizePlatformId`（`registry.ts:345-351`）对缺失值静默回落小红书（`raw ?? 'xiaohongshu'`）。AdsPower remark 缺 `plat` 的 FB 环境**首次登记即永久是小红书** → **拿不到摘除，症状（收藏 0/25）与病灶一模一样、无信号可辨**。→ **缓解**：本 change 不治，如实登记；`account-level-slow-start` 已在冷启动曲线侧治同一个根（「平台未知 MUST NOT 静默回落小红书曲线」），建议参照其 fail-honest 形态另立 change（最小治法：载荷回带「云端按哪个平台做的投影」作**诊断字段、不作决策依据**，客户端发现与本地环境平台不符即旁白告警——把静默错标变成可见事故）。
- **[`pickDailyUsageCounts` 有 4 个调用点，typecheck 不会提醒]** `:2157/:2158/:2159` 为 quotas 侧、`:2099-2103` 为 totals 侧，另 `completeSessionUsageCounts:422` 内部一个。四者入参均为宽松 `Partial<Record<string, number>>`。→ **缓解**：实装时逐点分类、**只动 quotas 侧**；tasks 里列为独立勾选项，不与主改动合并。
- **[fail-open 与 fail-closed 只差一个位置]** 见 D3。→ **缓解**：D4 的纯函数内部自兜 try/catch；验收含「平台查询抛异常时 payload 仍带完整六项上限」的显式断言。
- **[与 `account-level-slow-start` 的 spec 争用]** 两者同改 `edge-companion-ui`；另有三个 `wechat-channels-*` 也在该 spec 上排队。→ **缓解**：本 change 全部落 **ADDED**、不动任何既有要求措辞（含不动「六项指标」与 `:921-934`），争用面降为「同文件不同要求」；archive 时按依赖序合并。建议本 change **先落**（体量小一个量级），`account-level-slow-start` 在其上 rebase。
- **[「收藏 0」仍占位]** 摘上限后 FB 仍显示「收藏 0」「关注 0」——诚实但占位。→ **权衡**：接受。彻底删格子是纯审美收益，代价见 D1 备选（共享路径 + 静态绑定 + CSS + 必须出包）。

## Migration Plan

1. cloud 实装 D4 的纯函数 + D3 的接入点（try 块内、`effectiveQuotas()` 之后、`pickDailyUsageCounts` 之前）。
2. 单测：小红书逐位不变 / FB 恰好少 `collect` 与 `follow` / 查询抛异常时六项齐全（fail-open）。
3. `npm run test:acceptance` → `npm test` → `npm run typecheck`（顺序照 CLAUDE.md §4；本 change 不碰协议，`AC-PROTO-*` 应无变化——若变化即说明改错了地方）。
4. 部署 dev（安全序列照 §5：`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck）。**无需出安装包**、无需运营侧动作。
5. **回滚**：纯云端单边、无 DB 迁移 ⇒ 回滚 = 还原上一版本 tar。无数据面残留。

## Open Questions

1. **视频号的载荷形状**（D7）：本 change 的过滤对其生效会把它摘到只剩发布一格。`wechat-channels-interaction-management` 已立法整行不渲染 ⇒ 实际不可见。是否需要在过滤函数里对「全不支持平台」显式短路（早返回原 quotas），以免两条规则将来解耦时产生意外形状？**倾向：不短路**（摘掉本就诚实），但验收 MUST NOT 依赖其形状。
2. **`follow` 的历史计数**：是否存在 FB 账号在风控流水里留有历史 `follow` 记录？若有，摘上限不影响数字本身（`totals` 不动），只是没了上限 ⇒ 仍安全。**待实装时用一条 dev 库查询确认，不阻塞设计。**
3. **是否顺带把 `browse_images` / `scroll_comments` 等也纳入投影**：它们不在今天的六格里 ⇒ 无载荷、无问题。**倾向：不纳入**（YAGNI，六格之外没有消费者）。
