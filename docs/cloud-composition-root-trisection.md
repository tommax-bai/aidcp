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
带 SQL 的（事件 outbox、账号投影存储、风控命令 outbox 写侧）**不进包，随属主走**；发送函数的**签名**可进。

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
| 0 | cloud master 上的逐字节等价重构（见下） | 4–6 |
| 1 | `aidcp-transport` 包 + 三仓 `test/` 与门禁地基 | 3–4 |
| 2 | content `main()` | 5–7 |
| 3 | api `main()` | 7–10 |
| 4 | automation `main()` | 8–12 |
| 5 | dev 三服务部署 + soak + ol | 3–4 |
| **合计** | | **30–43 人日**（约 6–9 人周） |

批次 2/3/4 落在三个独立仓、可并行，墙钟能压到 4–5 周。**批次 0 是单文件热点（`server.ts`），
必须串行独占**（CLAUDE.md §7）。

**批次 0 的五步**：

- **0a** ✅ **已完成并合入 `aidcp-cloud` master `1d5ac18`**。死字段只有一个：`postProcessor`
  （有声明有赋值、**全仓零读点**；segB 内那处用的是同名局部常量，与 ctx 无关）。
  **同批曾误判 `configMirrorBumpSink` 为死字段** —— 它在 `startApiInternalApi`（`server.ts:811`）
  有读点，只是那行不在四个段函数体内、按段扫描看不见。**判死字段必须全仓 grep，不能只扫段内。**
- **0b** 前向引用改显式端口 + 诚实不可用实现（不是空值）。
- **0c** 面板段资产从自动化段上提（`server.ts:5757-5845` 那一簇；数据全在基础段，是**搬家不是造接口**）。
- **0d** 基础段 40 个单消费方句柄下沉到消费段；沉不了的三类（属主反转 / 池别名 / 闭包捕获）原地登记。
- **0e** ✅ **已完成并合入 `aidcp-cloud` master `f18ba96`**（2026-07-25）。41 个字段改可选、33 处
  逐处收口，新增两个取用闸 `requireSegment`（构造期必须有 → 带字段名与来源段响亮抛错）与
  `unavailableInMode`（请求期才用 → 那条路由诚实失败、其余照常）。
  顺带修掉一处真缺陷（`server.ts:5292`）：发布生成端口的 local 分支在 automation 模式下拿到
  `undefined` 并**静默落穿**成端口本体 ⇒ 排期发帖每次炸 TypeError、被归一成「失败」，
  而小时格幂等票在触发前已认领 —— 失败一次就烧掉那一小时。
  验证：monolith 逐字节等价 / typecheck 0 / acceptance 115·0 / 全量 3316 pass 0 fail 10 skip。
  **schema 门按本进程属主参数化仍未做**（见 §6），留给 0e 的后半或批次 1。

**批次 0 完成判据（全部可机械验证）**：`typecheck` 0；`test:acceptance` 与全量 `test` 全绿
（安全红线 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 必须全过）；monolith 启动日志与改前逐行 diff 无差异。

**批次 1 必须加的一条断言**：**本进程只对本属主库开过连接池**。它能兜住整类「字段表看不见」的漏网
（属主反转、池别名、闭包捕获）。

## 8. 风险（历史踩过的，别重蹈）

- 跳段开机崩（segB 曾构造 ~34 个共享地基对象）。
- 看着接线其实回落 local（配了网关地址 ≠ 边界已收口）。
- 共享池被某个 store 的 `close()` 整个关掉（只有互动域那三个加了拥有权守卫）。
- advisory lock 按库——写者锁留旧库、写落新库＝静默双写。
- 跨库事务不能跨库，必须最终一致。
- **`AIDCP_SERVICE` 绝不能写进共享 `.env`**：一份文件表达不了三个值，且会污染单体回滚路径。
