# 组装根三等分 · 实测清单与执行方案

> 2026-07-25。目标＝把 `aidcp-cloud/src/server.ts` 的组合根三等分，让
> `aidcp-api` / `aidcp-automation` / `aidcp-content` 三个仓各有独立 `main()`。
> 上位背景见 `docs/cloud-decomposition-roadmap.md`；四个新仓的现状见控制仓 memory `cloud-four-repos-created`。
> **本文的数字全部是本机实测，不是估算。**

## 0. 已定的两条前提（用户 2026-07-25 拍板）

1. **一步到位，不留组装仓**：不走「同一份代码 + 三个进程」的中间形态。`aidcp-cloud` 在三个新仓
   能独立部署之前一直是线上唯一形态，之后**归档**（不删除——历史全在它那里）。
2. **批次 0 必须在 `aidcp-cloud` 上做，不在新仓里做**。新仓今天是逐字节副本、**没有 `test/` 也没有门禁**，
   在那里手工三等分等于放弃 375 个测试与三族边界闸，只能靠编译错误一条条撞。
   这与第 1 条不冲突：批次 0 是让新仓可行的前置，不是中间生产形态。

## 1. 实测家底

| 层 | 文件 | 行数 |
| --- | --- | --- |
| api | 104 | 30,138 |
| automation | 183 | 44,910 |
| content | 78 | 16,654 |
| kernel | 57 | 6,195 |
| **composition**（`server.ts` + `index.ts`） | 2 | **6,668** |

**跨边界 import 455 条断裂，但其中 352 条（77%）是组装根被复制三份的假象**——三等分后自动消失。
真业务耦合只有 103 条（api 56 / automation 26 / content 21，分布 48 个文件）。

## 2. `CompositionContext` 的赋值分布（实测）

`interface CompositionContext` 共 **122 个字段**（`src/server.ts:642-774`），段边界：

```
segAApiFoundation   932-2214
segBContent        2216-2550
segCAutomation     2552-5894
segDApiServing     5896-6650
```

**按「在哪一段被赋值」分布：基础段 74 / 内容段 3 / 自动化段 44 / 基础+自动化 1 / 面板段 0。**

面板段**一个字段都不赋值、只消费**。因此：

| 模式 | 跑的段 | 拿不到的字段 |
| --- | --- | --- |
| content | A+B | 44（自动化段专属） |
| automation | A+C | 3（内容段专属） |
| **api** | A+D | **47** ← 唯一真正跑不起来的模式 |

## 3. 关键手法：让类型系统说真话

上下文由 `const ctx = {} as CompositionContext`（`src/server.ts:788`）造出，而那些只在某一段赋值的
字段却声明成**非可选** ⇒ **`npm run typecheck` 对「本进程里这个字段根本没被赋值」完全失明**。
全仓也没有任何一条测试跑过 api 模式启动（`AIDCP_SERVICE` 在 `test/` 下零命中）。

**把非基础段赋值的字段改成可选，编译器会一次性把所有未守卫的使用点列全。** 这比 grep 和人工梳理
都可靠，且是唯一能机械证明「清单是全的」的手段。

**实测结果（41 个字段改可选）：`tsc` 报 33 处，全部在 `src/server.ts`，且全部落在面板段区间。**

| 错误类型 | 条数 |
| --- | --- |
| 调用可能为 undefined 的对象（TS2722） | 13 |
| 读可能为 undefined 的属性（TS18048） | 14 |
| 把可能 undefined 赋给非可选形参（TS2322） | 6 |

涉及的跨段依赖（按出现次数）：`riskRegistry` 4、`server`（边缘 WS 服务端）4、
`accountPersonaService` 3、`configMirrorRefresher` 1、`publishOrchestrator` 1、`publishDispatcher` 1，
其余 13 处为闭包内调用、由 TS2722 定位。

**逐条位置**（行号基于 `f3f6ed9`）：

```
5292  5914  5915  5916  5978  5980  5987  5997  6007  6008  6037
6038  6040  6077  6130  6148  6168  6183  6324  6400  6415  6452
6474  6492  6495  6497  6502  6561  6577  6580  6581  6582  6589
```

## 4. 基础段的裁决：**各取所需**

不复制、不进 kernel、不抽成一个「segA 共享包」。

- **复制三份**与已完成的物理拆库直接冲突：基础段无条件建 4 个池、18 个存储横跨三个属主库
  一口气 `init()`，照抄等于把刚 DROP 的共享库在**连接层**复活。
- **进 kernel 走不通**：卡的不是那四条准入正则，是「kernel MUST NOT 导入任何业务层、无豁免通道」，
  而基础段用了 80+ 个业务层标识符。旁证：`boundaries/kernel-non-members.json` 已以「含 SQL」
  拒了精选库 / 客户用户 / 内容排期三个 store，而基础段正是它们的构造点。
- **可切的依据**：75 个字段里 40 个（53%）只有一个消费方，天然随该服务走；
  `src/server.ts:2139-2213` 那 75 行纯赋值块是现成的切割线。

### 4.1 单消费方句柄的实测分类（0d 的执行输入）

segA 赋值 **75 个**字段，按消费方分布实测：

| 消费方 | 个数 |
| --- | --- |
| 只 automation（C） | 30 |
| automation + api（CD） | 21 |
| 三家都要（BCD） | 9 |
| 只 api（D） | 5 |
| 只 content（B） | 5 |
| content + automation（BC） | 4 |
| 无人消费（死字段） | 1 → 已删（0a） |

**单消费方共 40 个**（30 C + 5 B + 5 D）。其中**属主与消费者反向的实测是 9 个**
（原估 17–20，实际更少），这 9 个不能跟着消费方走，必须逐个裁决：

| 字段 | 谁消费 | 却建在 | 性质 |
| --- | --- | --- | --- |
| `publishPipelineLogStore` | content | api 池 | 属主反转 |
| `roleLlm` | content | automation 池 | 属主反转 |
| `cache` | automation | api 池 | 属主反转 |
| `planner` | automation | api 池 | 属主反转 |
| `firstPostOnboardingStore` | automation | api 池 | 属主反转 |
| `personaAutoFillStore` | automation | api 池 | 属主反转 |
| `groupRouteStore` | api | automation 池 | 属主反转 |
| `configMirrorPool` | automation | **api 池的别名** | 池别名 |
| `mirrorVersionStore` | automation | api 池（经别名） | 池别名 |

其余 31 个单消费方**池与消费方一致或非存储**，可直接下沉。
另有 26 个双消费方 + 9 个三消费方 = **35 个必须逐个定「归谁 + 另一家怎么拿」**。

> 测法：字段消费方＝各段解构清单 ∪ 段内 `ctx.X` 读点；池＝构造块里的 `pool:` 实参。
> ⚠️ 这套按段扫描**看不见段函数体外的读点**（`main()` / `startApiInternalApi` 等），
> 判「无人消费」时必须改用全仓 grep —— 0a 就是这么差点删错的。

## 5. 还需要第二个共享包 `aidcp-transport`

`src/transport/`（14 个文件，全部跨进程胶水）**整目录只落进了 `aidcp-automation`**；
`aidcp-api` 与 `aidcp-content` 连这个目录都没有，而 api 的面板段今天就在调它们。

kernel 准入门实测：14 个文件里只有 6 个 CLEAN，**最承重的内部 HTTP 骨架同时命中「HTTP」与
「模块级活状态」两条，永远进不了 kernel**。

因此分两层：**kernel 装「零副作用的类型与契约」，`aidcp-transport` 装「有副作用但三家都要的运行时原语」**。
准入判据＝「三家都可能调用 + 不含任何属主表的 SQL」——比 kernel 宽，比「复制三份」严。

### 5.1 逐文件membership（2026-07-25 实测，14 个文件）

| 文件 | SQL | 服务端 | 客户端 | 判定 |
| --- | :-: | :-: | :-: | --- |
| `internal-http.ts` | . | — | Y | **进包**（HTTP 骨架，三家都要；含 `createServer` ⇒ 永不入 kernel） |
| `config-mirror-bump-http.ts` | . | Y | Y | **进包** |
| `curated-content-http.ts` | . | Y | Y | **进包** |
| `delegated-task-http.ts` | . | Y | Y | **进包** |
| `interaction-store-reader-http.ts` | . | Y | Y | **进包** |
| `publish-generation-http.ts` | . | Y | Y | **进包** |
| `publish-status-http.ts` | . | Y | Y | **进包** |
| `risk-read-http.ts` | . | Y | Y | **进包** |
| `account-projection-store.ts` | **Y** | . | . | 随属主（automation） |
| `event-outbox.ts` | **Y** | . | . | 随属主（automation） |
| `risk-command-outbox.ts` | . | . | . | 随属主（automation）—— 见下前置 |
| `eventbus-outbox-bridge.ts` | . | . | . | 随属主（automation，依赖 outbox 本体） |
| `outbox-health.ts` | . | . | . | 随属主（automation，依赖 outbox 本体） |
| `outbox-notify-listener.ts` | . | . | . | 随属主（automation，**零 import**，但只有 automation 用） |

**进包的判据不是「没有 SQL」，是「同一份契约有两端、而两端会落在不同的仓」**。那 7 个文件各自同时导出
`registerXxxRoutes(server, impl)`（服务端）与 `XxxHttpClient`（客户端），**中间夹着一张 `XXX_ROUTES` 路径常量表**
—— 一个仓用服务端、另一个仓用客户端。**复制成两份 = 两端的路径会悄悄对不上**，而且**没有任何机械手段看得见**：
两侧各自编译通过、各自测试通过，只有真跑起来才 404。这与本仓「两份 `protocol.ts` 必须逐字一致」是同一个问题，
区别只在协议那边有 `Record<MessageType,true>` 穷举兜着，这边什么都没有。一个包 = 一份定义 = 不可能漂。

**⚠️ 一条真前置：`risk-command-outbox.ts` 现在 import `src/risk/types.ts`（automation）。**
Phase 2 的 P2-6 会把那个文件整体提进 kernel；**在那之前动传输层，这条会变成包 → 业务层的反向依赖**。
故 **`aidcp-transport` 必须排在 Phase 2 之后**。（这也是本文原先没写出来的一条顺序约束。）

## 6. 硬阻断：schema 契约门的判定范围 ✅ 已解（`aidcp-cloud` master `e4558de`，已部署 dev）

**原阻断**：启动期 schema 契约门恒判全部三个属主账本，而 `AIDCP_SCHEMA_GATE=enforce` 已在
dev 与 ol 两端开启 ⇒ 单服务进程连不上另外两个库会被直接拒绝启动。

**⚠️ 实装时纠正了本文最初的处方。** 原写「按本进程属主参数化」，隐含「按 `AIDCP_SERVICE` 收窄」——
**那是错的**：基础段 `server.ts:957-959` 的三行建池**无条件执行、零模式门控**，今天任何模式都连三个库。
按模式收窄会让门校验得比进程实际使用的少 —— 正好是这道门存在意义（enforce 假绿）的**反面**：
库里少一张表，门却说通过。

**正确判据＝「本进程开了哪些池」，不是「跑的是哪个模式」。** 实装：

- `runSchemaContractGate({ owners })`：传入集合外的属主**不读账本、不判定、不出现在结论里**
  —— 本进程既然不连那个库，就没有立场声称它的 schema 对或不对。
- `pgOwnersForProcess()`＝建池与契约门**共用的唯一事实源**，今天恒为全部三个。
- `assertOwnerPoolsMatchProcessOwners()`：启动期断言建池集合与它逐个吻合，对不上**拒绝启动**。
  批次 0d 收窄池时改一处即可，这条断言**两个方向都拦**（校验了没连的库 / 漏校验真在用的库）。
- `owners` 传空集合视为未指定、回落全部三个：「一个库都不判」永远不该是默认结果。

今天行为逐字节不变（三池 ⇒ 三属主全判，仍是一条连接读一次账本）。
验证：typecheck 0 / acceptance 115·0 / 全量 3318 pass 0 fail 10 skip（+2 条收窄回归）；
dev 部署后三个契约门结论全过、零 error、断言未触发。

## 7. 执行批次与机械验收判据

| 批次 | 内容 | 人日 |
| --- | --- | --- |
| 0 ✅ | cloud master 上的逐字节等价重构（见下，**五步已全部完成并部署 dev**） | 4–6 |
| 1 | `aidcp-transport` 包 + 三仓 `test/` 与门禁地基 | 3–4 |
| 2 | content `main()` | 5–7 |
| 3 | api `main()` | 7–10 |
| 4 | automation `main()` | 8–12 |
| 5 | dev 三服务部署 + soak + ol | 3–4 |
| **合计** | | **30–43 人日**（约 6–9 人周） |

批次 2/3/4 落在三个独立仓、可并行，墙钟能压到 4–5 周。**批次 0 是单文件热点（`server.ts`），
必须串行独占**（CLAUDE.md §7）。

**批次 0 的五步 —— 五步全部完成（2026-07-25），逐条见下**。

- **0a** ✅ **已完成并合入 `aidcp-cloud` master `1d5ac18`**。死字段只有一个：`postProcessor`
  （有声明有赋值、**全仓零读点**；segB 内那处用的是同名局部常量，与 ctx 无关）。
  **同批曾误判 `configMirrorBumpSink` 为死字段** —— 它在 `startApiInternalApi`（`server.ts:811`）
  有读点，只是那行不在四个段函数体内、按段扫描看不见。**判死字段必须全仓 grep，不能只扫段内。**
- **0b** ✅ **已完成并合入 `aidcp-cloud` master `0f4cb46`，已部署 dev**（2026-07-25）。

  **前向引用不是一类，是三类，只有第三类要改**（段边界 / 赋值段 / 读点全部从源码现算，不靠人工清单）。
  实测 11 个字段存在前向引用：

  | 类别 | 个数 | 处置 |
  | --- | --- | --- |
  | 段内前向（自动化段读自己后面赋的值） | 2 | 三等分后仍同段，**无事** |
  | 段函数体外（`main()` / `start*Api` 里读） | 4 | 四处**本来就诚实**（如实告警 + 不注册路由），不动 |
  | **基础段 / 内容段 → 自动化段** | **5 字段 7 读点** | ← 本次目标 |

  第三类的形状：装配期构造回调、回调体读一个由**自动化段**赋值的句柄。单体里自动化段恒跑、
  回调只在请求期触发 ⇒ 永远读得到，前向引用毫无代价；三等分后 api / content 进程不跑自动化段，
  同一行变成读 `undefined`，而写法是裸 `ctx.X?.doSomething()` ⇒ **缺席被静默吞掉、调用方拿到「成功」**。
  **这一类没有任何现成机械手段看得见**：类型系统对 `?.` 短路无话可说，日志里一个字都不留。

  处置＝新增取用闸 `crossSegment(句柄, 丢了什么动作, 归哪段, 后果由谁承接)`：有实现原样返回
  （**单体逐字节等价**），没有则记一条带 `cross_segment_drop:` 前缀的 error 并点名后果。
  **有意不抛错**——一次界面推送失败不该让发布事务回滚；与「构造期就必须有、缺了拒绝启动」的
  `requireSegment` 分工明确。收口的三种后果（此前全部静默）：

  - **稿件审批通过后的下发触发**——丢了 = 已记「已批准」却永远不会被发出去（本组最重）。
  - **绑定人设后的会话唤醒**——丢了 = 「绑了人设却一直不动」。
  - **三处界面推送**（首作进度 / 人设绑定态 / 候审展开）——丢了 = 客户端停在旧值。

  **两处有意保留裸 `?.` 并写明理由**（同时进白名单）：SIGTERM 停排期对账器（停一个本进程没起过的
  东西，没有动作被丢弃，记 error 只会每次正常退出喊狼）；参照创作调度器（已有显式
  `throw publish_unready` 前置守卫，缺席拿到的是失败而非假成功）。

  **新增机械闸 `test/acceptance/composition-cross-segment.test.ts`（AC-SPLIT-CROSSSEG，2 条）**：
  从源码现算段边界与赋值段，任何「基础段 / 内容段裸解引用后段字段」当场失败到行，白名单须写明理由。
  **反向验证过**——把其中一处退回 `ctx.runtimes?.…`，闸立即指名到行。（一条从没红过的闸不算闸。）

  验证：typecheck 0 / acceptance 117·0（+2）/ 全量 3320 pass 0 fail 10 skip（+2）；
  dev 部署后三个契约门全过、零 error、`cross_segment_drop` 零次（单体下正确）、47 项子系统就绪。
- **0c** ✅ **已完成并合入 `aidcp-cloud` master `00d30a3`，已部署 dev**。
  **原方案「整簇上提」的前提不成立**：segC 赋值的 45 个字段里有 35 个「只被 segD 消费」，但那 ≠ 能搬——
  边缘服务端 / 评论调度器 / 下发器本来就是 automation 域的东西，面板只是**读**它，搬过去是错的。
  真判据＝**构造只依赖 segA**。逐条查实后**只有 9 个满足**：模型配置视图、模型探活、
  角色 / 品类 / 限额 / 节奏 / 单场 / 热帖 / 续场七个配置面板外观（各自只依赖 segA 的一个 store）。
  已整段上提、不再进 `CompositionContext`（少 9 个字段）、不再经 ctx 往返。
  **明确不搬**：`rolePromptProvider`（依赖 segC 预览调度器）、`listAccountAutomationCatalog`
  （依赖风控控制器）、`botChatsProvider`（依赖边缘服务端）—— 这些要走端口，不是搬家。
  **成效（机械口径）：segD 对 segC 的依赖 36 → 27。**

  **⚠️ 但这一刀有 4 个搬错了边，必须在批次 3 用端口纠正（已登记，勿当已完成）**。
  上提后面板改为**直接读配置 store**，而那 7 个 store 的表分属两家：

  | 面板 | 表 | 表属主 | 判定 |
  | --- | --- | --- | --- |
  | 角色配置 | `role_config` | api | ✅ |
  | 品类配置 | `category_config` | api | ✅ |
  | 热帖阈值 | `hot_lead_config_global` | api | ✅ |
  | 模型配置视图 / 探活 | 无表 | — | ✅ |
  | 安全限额 | `quota_config` | **automation** | ❌ api 进程会直连自动化库 |
  | 节奏兜底 | `pacing_floor_config` | **automation** | ❌ 同上 |
  | 单场上限 | `session_config` | **automation** | ❌ 同上 |
  | 续场配置 | `resume_config` | **automation** | ❌ 同上 |

  **不是线上回归**（monolith 逐字节等价，api 模式未部署），但方向错：这 4 个应由 automation 域
  暴露接口、api 侧只依赖接口，而不是自己去读别人的表。**批次 3 必须补这条端口**，否则
  「一个域绝不直连另一个域的数据库」这条铁律在 api 进程上守不住。

  **顺带查实**：`boundaries/table-ownership.json` **无缺口**（98 张表全覆盖）。中途出现的
  「两张表未登记」是我把表名猜错了（真名是 `pacing_floor_config` / `category_config`）——
  **查属主必须用代码里的真表名，不能按 store 名反推。**

  **另一条必须知道的连带效应**：这一刀把 7 个配置 store 从「只被 segC 消费」变成「segC+segD 都要」，
  于是它们**不能再下沉进 segC**（0d 的可下沉集合因此从 40 降到 34）。段间搬家会改变消费方分布，
  **0d 之前必须重测，不能沿用 0c 之前的清单。**
  过程踩坑：首版用「含某字段名的解构行」定位面板段，撞上更早的同名解构、把整块插进了内容段，
  typecheck 17 错当场暴露。**定位段落必须用段函数边界，不能用内容特征串。**
- **0d** ✅ **第一批已完成并合入 `aidcp-cloud` master `18a33b7`，已部署 dev**（14 个：automation 8 / content 3 / api 3）。
  **净效果：segA 赋出字段 75 → 61，`CompositionContext` 112 → 98，segA 1293 → 1108 行。**
  dev 实测被搬走的三个存储（点赞库 / 优质评论库 / 互动流）均正常初始化，三个契约门全过、零 error。

  **判据三条全中才搬**：① segA 赋值 ② 只有本段读 ③ **segA 自己不再引用它**。
  第三条最易漏：`delegatedTaskStore` 等在**声明之前**就被惰性回调捕获（**前向引用**），
  只查「声明之后的引用」会漏掉、搬走即编译报错。整段扫描后 27 个候选里 11 个因此留下；
  另 2 个依赖 segA 的**局部变量**（非 ctx 字段）一并退回。

  **剩余未下沉 20 个，分三类原地登记**：
  - **segA 自己仍引用（11）**：`facebookCommentAuditStore` / `accountDisplayNameCandidates` /
    `accountState` / `delegatedTaskStore` / `getSoul` / `manualCommentAccounts` / `resolvePersona` /
    `dashscopeApiKey` / `credentialStore` / `approvalPolicyStore` / `groupRouteStore`。
  - **依赖 segA 局部变量（2）**：`anyImageKeyPresent`（依赖 `arkRuntime`）、
    `publishApprovalClient`（依赖 `publishApprovalApi`）。
  - **属主反转 / 池别名（6，见 §4.1 表）**：`cache` / `planner` / `firstPostOnboardingStore` /
    `personaAutoFillStore` / `configMirrorPool` / `mirrorVersionStore` —— 搬位置解决不了跨库，须走端口。

  **两条工程教训（编译器打回三次换来的）**：
  1. 块尾判据「括号配平」不够 —— `new Map<…>` 的多行泛型里花括号先配平，会把结尾的 `>();` 落在块外、
     切出语法错误。判据须是「配平**且**该行以分号结尾」。
  2. 段内定位不能靠「函数起始 N 行内」或内容特征串：内容段的 ctx 解构既**不靠前**又是**多行写法**，
     两者分别导致「块插到解构之前」和「同名重复声明」。须整段搜索 + 按行处理多行解构。
- **0e** ✅ **已完成并合入 `aidcp-cloud` master `f18ba96`**（2026-07-25）。41 个字段改可选、33 处
  逐处收口，新增两个取用闸 `requireSegment`（构造期必须有 → 带字段名与来源段响亮抛错）与
  `unavailableInMode`（请求期才用 → 那条路由诚实失败、其余照常）。
  顺带修掉一处真缺陷（`server.ts:5292`）：发布生成端口的 local 分支在 automation 模式下拿到
  `undefined` 并**静默落穿**成端口本体 ⇒ 排期发帖每次炸 TypeError、被归一成「失败」，
  而小时格幂等票在触发前已认领 —— 失败一次就烧掉那一小时。
  验证：monolith 逐字节等价 / typecheck 0 / acceptance 115·0 / 全量 3316 pass 0 fail 10 skip。
  ~~**schema 门按本进程属主参数化仍未做**，留给 0e 的后半或批次 1。~~
  **已于 `e4558de` 补齐并部署 dev**（见 §6），此行为写作当时的状态、现已过期。

**批次 0 完成判据（全部可机械验证）**：`typecheck` 0；`test:acceptance` 与全量 `test` 全绿
（安全红线 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 必须全过）；monolith 启动日志与改前逐行 diff 无差异。

### 批次 0 结项（2026-07-25，五步全落 `aidcp-cloud` master 并部署 dev）

| 步 | commit | 净效果 |
| --- | --- | --- |
| 0a | `1d5ac18` | 删 1 个死字段 |
| 0e | `f18ba96` | 41 字段改可选、33 处逐处收口，**顺带修掉一处真缺陷**（排期发帖每小时烧掉一格） |
| — | `e4558de` | schema 契约门按**本进程开了哪些池**参数化 + 双向断言 |
| 0c | `00d30a3` | 9 个面板外观上提；segD→segC 依赖 36 → 27（**但 4 个搬错边，欠批次 3 一条端口**） |
| 0d | `18a33b7` | 下沉 14 个单消费方句柄；segA 赋出 75 → 61、上下文 112 → 98、segA 1293 → 1108 行 |
| 0b | `0f4cb46` | 5 个跨段前向引用改响亮取用 + 新增 AC-SPLIT-CROSSSEG 机械闸 |

**机械口径**：typecheck 0；acceptance 115 → **117**；全量 3316 → **3320** pass 0 fail 10 skip；
dev 三个契约门全过、零 error。**新增两族闸**：owner 池范围双向断言（启动期拒绝）、
AC-SPLIT-CROSSSEG（源码级、反向验证过）。

**批次 0 留下的两笔明账，不得当作已完成**：
① 0c 误把 4 个 automation 属主的配置面板上提到 api 段（安全限额 / 节奏兜底 / 单场上限 / 续场），
**批次 3 必须补端口**，否则 api 进程会直连自动化库；
② 0d 还剩 20 个句柄未下沉（11 个 segA 自己仍引用 / 2 个依赖 segA 局部变量 / 6 个属主反转），
后 6 个**搬位置解决不了**，须与 §4.1 一起在批次 2/3/4 走端口。

**批次 1 必须加的一条断言**：**本进程只对本属主库开过连接池**。它能兜住整类「字段表看不见」的漏网
（属主反转、池别名、闭包捕获）。

## 7.5 批次 1 已落的两件地基（2026-07-25）

**① 拆仓可复现：控制仓 `scripts/sync-split-repos`。**
四个属主仓当初是**手工切**的——切得对（按属主清单重放，424 个 src 文件里 416 个逐字节一致、
文件数逐仓吻合），但**不可复现**：没有任何东西记得「哪个文件该在哪个仓」，而 master 天天在走。
首跑即抓到三仓落后 12 个文件。现在每批做完自动对账 + 同步，另含一条**尤其阴**的检查：
三仓靠一条固定 sha 引用 kernel 包，**那条 sha 过期时 npm 不报错、编译照过，跑的却是过期契约**。
三条纪律：只管 `src/` + 那条 kernel pin；组装根**只报不改**（批次 2/3/4 的主交付物，自动覆盖等于悄悄删掉）；
删文件要单独开口。反向验证过（把 pin 改回旧 sha，闸立即报）。

**② 三仓依赖集按真实 import 重算（含动态 import）。**
此前三份 `package.json` 是 cloud 的逐字复制、三份完全相同。按属主重算后：
api = 飞书 SDK + pg + ws；automation = pg + ws；content = 对象存储 + pg + 两个渲染库。

> **动态 import 这条必须记住**：文字卡渲染的两个依赖是 `await import(...)` 懒加载的，
> 只匹配 `from` 说明符的静态扫描**完全看不见**。而那条链路**工厂返回 null 即降级**——
> 依赖装漏了不崩不报，只是封面悄悄退回生成式。这与本清单开头「103 vs 实测 104」是同一类漏检
> （那条也是内联动态 import）。**凡是「扫 import 得出的结论」，都要问一句动态 import 算没算。**

---

## 8. 风险（历史踩过的，别重蹈）

- 跳段开机崩（segB 曾构造 ~34 个共享地基对象）。
- 看着接线其实回落 local（配了网关地址 ≠ 边界已收口）。
- 共享池被某个 store 的 `close()` 整个关掉（只有互动域那三个加了拥有权守卫）。
- advisory lock 按库——写者锁留旧库、写落新库＝静默双写。
- 跨库事务不能跨库，必须最终一致。
- **`AIDCP_SERVICE` 绝不能写进共享 `.env`**：一份文件表达不了三个值，且会污染单体回滚路径。
