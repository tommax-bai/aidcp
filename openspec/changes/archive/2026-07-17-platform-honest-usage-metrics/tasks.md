# Tasks

> 按 sub-repo 分节。协议热点（两份 `protocol.ts`）**单写者串行**，见 CLAUDE.md §7。
> 顺序铁律：**cloud 先落**（老客户端立刻得到窗口明细行那一半，且会把未知的 `join_group` 键静默丢弃 —— 这是安全的丢弃）；edge 后落，**默认不出安装包**（用户 2026-07-17）。

## 1. aidcp-cloud — 协议与键清单单一来源

- [x] 1.1 `src/comm/protocol.ts`：把 `UiDailyUsageAction` 改为从 `as const` 数组派生 —— `export const UI_DAILY_USAGE_ACTIONS = ['view','like','collect','comment','follow','publish','join_group'] as const;` + `export type UiDailyUsageAction = (typeof UI_DAILY_USAGE_ACTIONS)[number];`（照 `src/risk/types.ts` 的 `RISK_ACTIONS` 同款 idiom）。键名与风控动作名**逐字同名**，绝不起 `join` 别名（design D4）。 <!-- cloud f127435 --> <!-- 2026-07-17 deployed dev -->
- [x] 1.2 `src/server.ts:335`：删掉手写的 `const UI_DAILY_USAGE_ACTIONS: UiDailyUsageAction[] = [...]`，改为 import 1.1 的数组。**这是本 change 唯一一处把手写清单变成 typecheck 可抓的地方**，别顺手又抄一份。 <!-- cloud f127435 --> <!-- 2026-07-17 deployed dev -->
- [x] 1.3 在 1.1 处留码内注释：本联集的漂移 **`Record<MessageType,true>` 那道穷举抓不到**（它不是消息类型）；两份 `protocol.ts` 仍靠 §2 的逐字一致纪律，edge 侧的 JS 清单靠 5.x 的测试钉。 <!-- cloud f127435 --> <!-- 2026-07-17 deployed dev -->

## 2. aidcp-cloud — 平台声明与投影

- [x] 2.1 `src/platform/registry.ts`：`OrchestrationCapability` 加 `group_join`；三个平台各表态 —— facebook `{supported:true}`、xiaohongshu `{supported:false, reason:'no_group_concept'}`、wechat_channels `{supported:false, reason:'interaction_inbox_only'}`。`Record<OrchestrationCapability, NoteSupport>` 会逼全部平台当场表态。 <!-- cloud f127435 --> <!-- 2026-07-17 deployed dev -->
- [x] 2.2 同文件：更新 facebook entry 上方那段注释 —— 它现在明写「capabilities 只登记有云端消费者的编排词，join 的编排接线在专属路径、不作零消费者声明」。`group_join` 现在**有**消费者（客户端指标投影，非闸），注释须改，否则下一个人会照旧注释把它删掉。 <!-- cloud f127435 --> <!-- 2026-07-17 deployed dev -->
- [x] 2.3 `src/platform/surface.ts`：`USAGE_CAP_SUPPORT_SOURCE` 加 `join_group: { matrix: 'capability', capability: 'group_join' }`（全覆盖 `Record` 会逼你表态）。 <!-- cloud f127435 --> <!-- 2026-07-17 deployed dev -->
- [x] 2.4 `src/platform/surface.ts`：把 `omitUnsupportedUsageCaps` 泛化为对**任意一份计数**生效的投影（上限与计数同一个函数，判据同一张表），并给新键实现**「显式 supported:true 才发」**的读法。**绝不复用 `isOrchestrationCapabilitySupported`**（它 fail-open 到 `true` ⇒ 平台未知的账号会凭空长出加群格，design D3）。保持同步 / 纯 / 内部自兜 try-catch 永不抛。 <!-- cloud f127435 泛化为 omitUnsupportedUsageMetrics；新键读法用显式 supported===true，不复用 fail-open 的 helper --> <!-- 2026-07-17 deployed dev -->
- [x] 2.5 `src/platform/surface.ts`：函数注释写清 fail-open 的**两个方向其实是一条**（只有显式声明才能改变现状），并保留既有的「必须在 `pickDailyUsageCounts` 之后调用」警告 —— 顺序颠倒会把摘掉的键补回 `0`，`quotaSaturation` 算 `0>=0` ⇒「0/0 今日计划已完成」，typecheck 全绿。 <!-- cloud f127435 --> <!-- 2026-07-17 deployed dev -->

## 3. aidcp-cloud — 每一个计数面接线

- [x] 3.1 `src/server.ts` `buildTodayUsageForAccount`：`dayTotals` / `minuteTotals` / `hourTotals` 三面在 `pickDailyUsageCounts` **之后**接投影。 <!-- cloud f127435 --> <!-- 2026-07-17 deployed dev -->
- [x] 3.2 `src/server.ts` `completeSessionUsageCounts` 的产出（session 面）同样接投影 —— **这一面最容易漏**：它内部也调 `pickDailyUsageCounts(riskTotals)`，不投影则小红书「本轮计划」会冒出「加群 N」（风控计数器里真有这个数）、FB 会冒出「收藏 0」。 <!-- cloud f127435 --> <!-- 2026-07-17 deployed dev -->
- [x] 3.3 核对上限侧四个面（day / minute / hour / session + 慢启动开关回执 `dayQuotas`）在泛化后仍逐位如前：本 change **不得**改变任何一个已被摘掉或已被保留的**上限**。 <!-- cloud f127435 上限四面逐位不变，dev 实测坐实 --> <!-- 2026-07-17 deployed dev -->
- [x] 3.4 `src/server.ts:4178` 那处 `pickDailyUsageCounts(controller.effectiveQuotas().day)`（慢启动开关回执）：确认它拿到 `join_group` 后仍按平台投影，不会给小红书回一个加群上限。 <!-- cloud f127435 该处本就用 platformFor + 同一函数，天然正确、零改动 --> <!-- 2026-07-17 deployed dev -->

## 4. aidcp-cloud — 测试

- [x] 4.1 纯函数层：FB 投影后摘 `[collect, follow]`、含 `join_group`；XHS 摘 `[]`、**不含** `join_group`（**首要回归判据：XHS 逐位不变**）；视频号只剩 `publish`；平台 `undefined` / 抛异常 ⇒ 原样返回入参且**不含** `join_group`。 <!-- cloud f127435 --> <!-- 2026-07-17 deployed dev -->
- [x] 4.2 断言 `join_group` 的读法不是 fail-open-to-supported：构造一个查表抛异常的平台，断言**没有**加群键。 <!-- cloud f127435 --> <!-- 2026-07-17 deployed dev -->
- [x] 4.3 反向 tripwire：断言把投影推进 `effectiveQuotas()` 会让 `test/risk-slow-start.test.ts` 的 FB `deepEqual` 变红 —— 那是把投影钉在展示边界的机制（`platform-honest-usage-caps` 已建，勿破）。 <!-- cloud f127435 tripwire 仍在（risk-slow-start.test.ts 的 FB deepEqual 未动） --> <!-- 2026-07-17 deployed dev -->
- [x] 4.4 `npm run test:acceptance` → 全量 `npm test` → `npm run typecheck`（**直接跑、看退出码，绝不 `| tail`** —— 管道会让退出码变成 `tail` 的，假绿已中过两次）。 <!-- cloud f127435 acceptance 55/55、全量 2436 pass 0 fail、typecheck 干净（直接跑取退出码，未用管道） --> <!-- 2026-07-17 deployed dev -->

## 5. aidcp-edge — 协议与清洗

- [x] 5.1 `src/comm/protocol.ts`：与 cloud 1.1 **逐字一致**（含 `as const` 数组与派生联集）。 <!-- edge 8976637 -->
- [x] 5.2 `src/electron/main.cjs:1593`：`DAILY_USAGE_ACTIONS` 加 `'join_group'`。**这张是纯 JS 清单、派生不了、typecheck 抓不到**：漏了的症状是「云端发了、界面不显示、没有任何报错」（与 `cleanSlowStart` 白名单同款，`main.cjs:1711` 的注释已预警过这个模子）。 <!-- edge 8976637 -->
- [x] 5.3 `src/electron/main.cjs`：删掉 `cleanRequiredCounts`（`:1604`），两个调用点（`normalizeDailyUsage:1680` 的 totals、`bumpDailyUsage:1753`）改为**保留缺席**；顶层 totals 缺全部键时回落 `{}` 而非 `null`（类型上 totals 必填）。 <!-- edge 8976637 cleanRequiredCounts 整个删除，改 cleanSuppliedCounts（恒返回对象、保留缺席） -->
- [x] 5.4 `src/electron/main.cjs` `bumpDailyUsage`：只给**已存在**的键 +1，**绝不新建键**（design D8）。不改的后果不是报错，是**收藏格在下一个本地事件到达时当场闪回**、≤60s 后又消失。 <!-- edge 8976637 -->
- [x] 5.5 `src/electron/main.cjs` `statsFromDailyUsage`：确认缺席键映射到 legacy `stats` 时不炸（`cleanCount(undefined) → 0`），且 legacy 六键 stats 面**不新增** join（它没有本机来源）。 <!-- edge 8976637 -->

## 6. aidcp-edge — 渲染

- [x] 6.1 `src/electron/renderer/index.html`：加群 KPI **静态节点**（`data-action="join_group"`，`#joins` / `#joins-cap` / `#joins-bar`，标签「加群」），插在发帖之后。**绝不动态建元素** —— `usage-grid` 不在任何 `innerHTML` 重建范围内。 <!-- edge 8976637 -->
- [x] 6.2 `src/electron/renderer/renderer.js`：`fields.usageCaps` / `fields.usageBars` 补 `join_group` 项；`USAGE_ITEMS`（`:429`）补 `{ action:'join_group', stat:null, value:fields.joins, label:'加群' }`（`stat:null` = 无本机回落来源 ⇒ 无云端载荷时不显）。 <!-- edge 8976637 -->
- [x] 6.3 `src/electron/renderer/renderer.js` `usageView`（`:485`）：产出「云端真实给了哪些键」的集合（用 `hasOwnProperty`，**不是 `值 > 0`** —— 0 是真实的「今天还没做」，必须照显）；无云端载荷 ⇒ 回落 legacy 六格（= 今天）。 <!-- edge 8976637 -->
- [x] 6.4 `src/electron/renderer/renderer.js` `renderUsageItem`（`:505`）：键不在集合内 ⇒ 整格 `hidden`。 <!-- edge 8976637 -->
- [x] 6.5 `renderUsageItem` 顺带核对 `usageProgressLabel`（`:546`）与 `quotaCompletionSummary`（`:527`）的完成态文案只数**存在的**计划（spec：「4 项今日计划已完成」而非把不存在的动作算进去）。 <!-- edge 8976637 已核：完成态计数来自 rows.filter(complete)，rows 只含供给键 ⇒ 自动只数存在的计划，无写死项数 -->
- [x] 6.6 **零改动确认**：`quotaWindowView`（`:590-593`）已有 `if (!hasTotal && !hasCap) continue` + 窗口 totals 走保留缺席的 `cleanOptionalCounts` ⇒ 窗口明细行**云端一摘就自动消失**。跑一遍确认，别顺手重写它。 <!-- edge 8976637 已核零改动：quotaWindowView 的 !hasTotal && !hasCap 判断本就在 -->

## 7. aidcp-edge — 布局

- [x] 7.1 `src/electron/renderer/styles.css`：`.usage-grid`（`:1139`）不再写死 `repeat(6, …)`；格间分隔线改由**间隙透出容器底色**产生（`gap:1px` + 容器底色 = 发丝色 + 格子自身不带 `border-left`）。 <!-- edge 8976637 flex + 1px 间隙透出容器底色；末行自动拉伸、永不留空格位 -->
- [x] 7.2 同文件：删掉 `.kpi:first-child { border-left: 0 }`（`:1162`）与窄窗 `:nth-child(4)` 那两条（`:2155-2156`）—— **`:nth-child` 数的是 DOM 位置、不管 `display:none`**，隐藏两格后边框必错位。 <!-- edge 8976637 -->
- [x] 7.3 目视核对三种形状：FB 5 格（浏览/点赞/评论/发帖/加群）、XHS 6 格、视频号 1 格（发帖）；窄窗折行后**无空格位、无错位分隔线**。 <!-- edge 8976637 三种形状由 companion-ui.test.ts 断言（jsdom 真 HTML+CSS），窄窗折行改由 flex-basis:30% 控 -->

## 8. aidcp-edge — 测试

- [x] 8.1 穿透测试（钉 5.2 那张 JS 清单）：一份带 `join_group` 的 `dailyUsage` 载荷穿过 `normalizeDailyUsage` 后该键仍在。 <!-- edge 8976637 偏离：main.cjs 无任何 export、全仓无 test import ⇒ 先把清洗块抽成 src/electron/daily-usage.cjs（纯函数、零 Electron 依赖）才谈得上落测。抽出的唯一理由就是这两条静默不变量此前零覆盖 -->
- [x] 8.2 缺席保持测试（钉 5.3 / 5.4）：一份**不含** `collect` 的载荷穿过 `normalizeDailyUsage` 后 `collect` 仍缺席；随后对它 `bumpDailyUsage('like', 1)`，断言 `collect` **仍然缺席**。 <!-- edge 8976637 已验真：stash 掉产品改动单跑新测试 → 7 条恰好 6 条红（剩 1 条是本就存在的行为）⇒ 非假绿 -->
- [x] 8.3 `test/electron/renderer-smoke.test.ts`：FB 形状（无 collect/follow、有 join_group）渲染后收藏格与关注格 `hidden`、加群格可见；XHS 形状六格全可见且**逐位如常**。 <!-- edge 8976637 -->
- [x] 8.4 `npm run test:acceptance` → 全量 `npm test` → `npm run typecheck`（同 4.4，**别用管道**）。 <!-- edge 8976637 acceptance 23/23、全量 1680 pass 0 fail、typecheck 干净（直接跑取退出码） -->

## 9. 集成与部署

- [x] 9.1 cloud：rebase 到最新 `master` → `test:acceptance` + `typecheck` → ff 合并 → push。 <!-- cloud f127435 --> <!-- 2026-07-17 deployed dev -->
- [x] 9.2 cloud 部署 dev（安全序列：`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck）。**先探 ECS 真实现状**（并发 session 也在改同机）。 <!-- cloud f127435 backup cloud.bak.20260717-172200.tar.gz；healthcheck: active + 8787 + panel 8090 + 飞书长连接已建立 --> <!-- 2026-07-17 deployed dev -->
- [x] 9.3 dev 实测：FB 账号的 `ui.snapshot.dailyUsage` 载荷里 totals 摘 `[collect, follow]`、含 `join_group`；XHS 账号载荷**逐位不变**。 <!-- cloud f127435 dev 实测（真部署代码 + 真配额档）：fb={view,like,comment,publish,join_group:3}、xhs 六键逐位不变且无 join_group、视频号只剩 publish、平台未知回落六键且无 join_group。另核 dev 库 platform 列：xhs 9 / fb 7 / wechat 2，无 null --> <!-- 2026-07-17 deployed dev -->
- [x] 9.4 edge：rebase → 测试 → ff 合并 `master` → push。**不打包**（用户 2026-07-17：先不出包）。 <!-- edge 8976637 已合 master + push。**未打安装包**（用户 2026-07-17 裁定：先不出包） -->
- [x] 9.5 主 checkout ff 到最新 `master`（用户在那跑 `electron:dev`）。 <!-- edge 8976637 land-change 已自动 ff 同步主 checkout -->

## 10. 收尾

- [x] 10.1 真机验收项登记 `docs/real-machine-acceptance-backlog.md` 簇 90，**分「有新包 / 无新包」两组判据**（无新包时只有窗口明细行那一半可验）。 <!-- 2026-07-17 已登记 backlog 簇 90：A 组 90.14-90.16 无需新包、B 组 90.17-90.20 需含 edge 8976637 的包 -->
- [x] 10.2 订正 backlog 90.7 的第 ③ 条：它写着完成态文案应读「4 项今日计划已完成」，本 change 后 FB 的带上限指标变为 5 项（含加群）。 <!-- 2026-07-17 已改写 90.7 第 ③ 条并标注「按原文验收会把正确行为当 bug 报回来」 -->
- [x] 10.3 登记不治的两项：慢启动 day1-2 把加群上限压到 0 ⇒「加群 0/0 今日计划已完成」（**预先存在**，FB 冷启动曲线的 comment/publish 今天就这样）；平台错标（90.8）现在多一个后果 —— 错标的 FB 环境连加群格也不会出现。 <!-- 2026-07-17 登记为 backlog 90.21 / 90.22 -->
- [x] 10.4 `openspec validate platform-honest-usage-metrics --strict` → archive。 <!-- 2026-07-17 validate 通过 → archive -->

## 11. 归档后修（真机首跑暴露：加群格根本不出现）

> **归档时全绿是真的，但它证明不了这条链是通的。** 云端投影正确（dev 实测坐实）、两份 protocol.ts 逐字一致、
> `main.cjs` 与 `renderer.js` 的清单都加好了、typecheck 全绿、cloud 2436 + edge 1680 全过 —— 屏幕上依然只有
> 4 格、加群怎么也不出现、**全链路零报错**。

- [x] 11.1 根因＝**第四张手写键清单**：`aidcp-edge/src/flows/ui-event-lines.ts:22` 的 `DAILY_USAGE_ACTIONS`（六键），`sanitizeCounts` 拿它**过滤** totals ⇒ `join_group` 在到达 Electron 主进程**之前**就被这道白名单吃掉。收藏/关注的缺席被它正确保留（它只拷贝存在的键），所以症状只表现为「加群不出现」，看起来像投影没生效。<!-- edge 3939049 -->
- [x] 11.2 设计文档与 tasks 第 1 节数清单时数漏了它：只数了两份 `protocol.ts`、cloud `server.ts`、edge `main.cjs`、`renderer.js` 五张，**没有对边缘仓做全局扫描**。已改为从 `UI_DAILY_USAGE_ACTIONS` 派生，该表不复存在。<!-- edge 3939049 -->
- [x] 11.3 顺带修同类漏：`src/electron/renderer/ui-logic.js:87` 的 `QUOTA_ACTION_PRIORITY` 也是六键手写 ⇒ 加群的上限对「配额休息 / 计划完成」逻辑完全不可见（加群满了不会被算作在等配额）。本文件是纯 JS、import 不了，只能手工对齐 + 注释。<!-- edge 3939049 -->
- [x] 11.4 补穿透测试 `test/flows/ui-event-lines.test.ts`：FB 投影后的真实载荷形状穿过 `uiSnapshotToLines` 后 `join_group` 仍在、collect/follow 仍缺席。**已验真**：把手写清单写回去 → 该条恰好红（`undefined !== 2`）。<!-- edge 3939049 -->
- [x] 11.5 `dist` 必须 `npm run build:dist`：`npm run build`（`tsconfig.json`，`rootDir:"."`）写到 `dist/src/…`，而应用读的是 `dist/flows/…`（来自 `tsconfig.build.json`，`rootDir:"src"`）⇒ `build` 退出码 0 但产物纹丝不动。已对编译产物直接做穿透验证（非只看测试）。<!-- edge 3939049 -->

**教训（值得带走的那条）**：本 change 的设计文档专门用一节讲「同一份键清单在几个地方各手写了一遍、typecheck 一张都抓不到」，并逐张点名 —— 然后还是漏了一张，而漏的那张正是唯一真正破坏功能的。**点名清单靠回忆是不够的，必须对两个仓做一次全局扫描**（`grep -rn "'view'.*'like'.*'collect'"`）。edge 全局扫描现存结果：`daily-usage.cjs`（已含）、`ui-logic.js`（已修）、`ui-event-lines.ts`（已派生）、`protocol.ts`。另发现一处**既有**协议漂移（非本 change 引入、不治）：`RiskCanDoPayload.action` 云端有 `join_group`、边缘没有 —— `risk.canDo` 是 CLAUDE.md §2 明列的「保留通道、边缘尚未接线」，故当前无害。
