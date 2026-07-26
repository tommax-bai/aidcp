# 组装根三等分 · 实测清单与执行方案

> 2026-07-25。目标＝把 `aidcp-cloud/src/server.ts` 的组合根三等分，让
> `aidcp-api` / `aidcp-automation` / `aidcp-content` 三个仓各有独立 `main()`。
> 上位背景见 `docs/cloud-decomposition-roadmap.md`；四个新仓的现状见控制仓 memory `cloud-four-repos-created`。
> **本文的数字全部是本机实测，不是估算。**

## 0.0 进度卡（2026-07-26 更新，接手先看这里）

| 项 | 状态 |
| --- | --- |
| **批次 0** 组装根等价重构（0a–0e） | ✅ 五步全完，已部署 dev |
| **耦合处置 Phase 0** 收口三份重复契约 | ✅ −10 条 |
| **耦合处置 Phase 1** 归属再裁决 | ◐ −5 条；P1-1（三个限频配置门面翻转）**有意延后到 Phase 2 批** |
| **耦合处置 Phase 3** 共享层析出 | ✅ 八条全完，−13 条 |
| **耦合处置 Phase 2** 面板契约析出 | ✅ 八簇 + 延后的那条全完，68 → 39 |
| **耦合处置 Phase 4** 端口注入 | ✅ 全 29 条一次落，39 → 10；三个方向整体归零 |
| **耦合处置 Phase 5** 三个大件 | ✅ 三件全完 + 三条「永久豁免」边一并消掉，10 → **0** |
| **`aidcp-transport`** 共享传输包 | ✅ 已建仓、**17 个成员**（批次 2 新增 9 条契约三件套）、typecheck 0、已纳入对账 |
| **三仓 + kernel 的 `test/`** | ✅ 286 个已按派生归属就位（99 个跨属主留守，随耦合消除自动减少） |
| **批次 2** content `main()` | ◐ **10 条前置契约全部落地并部署 dev**；内容段跨域依赖归零（含传递性复核）。剩 `main()` 本体，见 §9 |
| **批次 3/4** api / automation `main()` | ⏸ 未开始 |
| **批次 5** dev 三服务部署 + soak + ol | ⏸ 未开始 |

**跨边界豁免轨迹：96 → 86 → 81 → 79 → 69 → 68 → 39 → 10 → 0（2026-07-26 达成）。** 共享层成员 57 → **82**。
**「一端是 content」的边 29 → 9 → 0。** 门禁实测 `crossBoundaryEdges: 0, exemptionEntries: 0, frozenTotal: 0`。

> **Phase 5 顺带推翻了一条旧裁决，理由必须记住**：那三条边原判「不做、维持豁免」，
> 是在**单体语境**下做的——豁免是「治理上允许它继续存在」的记账，三域同进程时边挂着不影响任何东西。
> 拆仓后不成立：content 的 `src` 里根本没有 `event-bus/types.ts` / `agents/base-role.ts`，
> 那几行 import 解析不了、仓编译不过。**豁免管得住门禁，管不住模块解析。**
> 判「某条边可否留着」时，MUST 分清「门禁允不允许」与「拆完还能不能解析」——它们不是一回事。

**批次 2/3/4 的真实距离（2026-07-26 实测，按「该仓 src 里指向本仓没有的文件」计）**：

| 仓 | 断裂引用合计 | 其中组装根副本贡献 | **业务代码断裂** |
| --- | ---: | ---: | ---: |
| api | 128 | 113 | **15** |
| automation | 123 | 109 | **14** |
| content | 158 | 143 | **15** |

也就是说：**每个仓写完自己的 `main()`，一次消掉 109–143 条**；真正要逐条处置的业务耦合**各只剩 14–15 条**
（＝ Phase 4/5 的余额）。这是「组装根被复制三份是假象」那句话的最终量化形态。

> 三个仓各有 1 条指向共享层的断裂，**全在 `src/server.ts` 里**——组装根按设计从不同步，
> 保留着原始相对引用，各仓写 `main()` 时自然消失。**不是改写漏了。**
**七个仓/包的对账一律用 `scripts/sync-split-repos`**（六个目标 + 测试；`--check` / `--apply` / `--prune` / `--tests`）。
**不变量已固化成 CLAUDE.md §8（OVERRIDE 级）**，任何触碰 `aidcp-cloud/src` 或 `boundaries` 的改动都受其约束。

### 0.0.1 下一步做什么（接手直接照做）

> **接手请直接读 `docs/cloud-split-next-session-handoff.md`** —— 那份是可粘贴执行的完整交接
> （现状核对命令 / 待拍板缺陷 / 主交付物的量化距离 / 固定收尾 / 踩过的坑）。本节是它的摘要。
>
> 耦合处置**已全部完成**（Phase 0–5，96 → 0）。下面是余下的事，按优先级排。

1. ~~**⚠️ 先看 §0.0.2：风控状态机在 dev 与 ol 上都持久化不了。**~~ **已修并部署 dev**
   （`aidcp-cloud@8d903dd`，2026-07-26）。同批抓到并修掉第二处同形缺陷，
   并加了门禁 `AC-OWN-06` 防第三次。**ol 仍未部署**，需用户明确要求 + 走发布分支。
2. **批次 2/3/4 三个 `main()`** —— 主交付物。**批次 2（content）的逐条执行清单见 §9**
   （2026-07-26 用真编译器实测：断裂 100% 只在两个组装根文件里；content 对基础段的依赖恰好 20 个字段，
   已逐个分好「本地建 / 走端口 / 无需处理」；另揪出两条**同步读**不能包 HTTP、须走本地镜像）。
   **距离已量化**（见上表）：各仓业务代码断裂只剩 14–15 条，
   写完 `main()` 一次消掉 109–143 条。三仓可并行，但组装根改动期间彼此不冲突（各写各的仓）。
   **注：上表是 Phase 4 时点的旧数。Phase 5 之后 2026-07-26 重测：三个仓的业务代码断裂**
   **已全部归零（0 / 0 / 0），剩余断裂 107 / 107 / 138 全部来自组装根副本**——
   也就是说每个仓写完 `main()` 就一次全消。复现命令见交接文档 §2.1。
3. **批次 5** —— dev 三服务部署 + soak，再按用户明确要求上 ol。
4. **补上迁移的同步机制**（见 §0.0.3）——现在 `sync-split-repos` 只管 `src/`，迁移文件靠手工放。

### 0.0.2 ✅ 已修并全环境上线：风控状态机写不进库（dev + ol 均已部署）

> **2026-07-26 结案**。用户在两条候选里选了 ①「走已有的窄读口」。
> 修于 `aidcp-cloud@8d903dd`，dev 已部署验证：`risk_state` 在 07:55:48 写入成功
> （上一次成功是 07-23），那条卡了 2352 次重试的面板命令回读到 `state=applied`
> ——**这同时补上了本批一直缺的那条真机证据：`applied` 成功路径此前从未在真机上跑通过。**
> **ol 已部署**（2026-07-26 11:24，用户明确要求后执行）：发布分支 `release/20260726-cloud-risk-ownership`
> 自 `origin/master@ae8eb06` 切出、**在 linked worktree 里切**（canonical checkout 全程停 master）。
> 该分支自 master 切出后**零额外提交**，故无回流主干义务（§6 铁律的例外形态：分支内容 ≡ 主干）。
> 部署前实测 typecheck 0 / 验收 123·0 / 全量 3390·0；ECS 先备份（含 .env），rsync 后哈希逐字校验通过。
> 部署后：服务 active、8787 与面板端口在听、三个契约门全过、飞书长连接已建立、**零 error**。
> 缺陷确认消失：属主谓词已不再 join `accounts`（`WITH owner AS` 命中 0），`AC-OWN-06` 门禁随之上线。
>
> **顺带查清一条与文档不符的现状**：ol 的 `.env` 里那几个属主库 URL 我第一次用正则没匹配上，
> 一度误以为 ol 还回落在旧的共享库。实测 `pg_stat_activity`：ol 的连接确实分布在
> `aidcp_api` / `aidcp_automation` / `aidcp_content` 三个库上，旧库 `aidcp` 已不可连（确已退役）。
> **查「连的是哪个库」要看 `pg_stat_activity` 的真实连接，别看 env 文本**——后者一个正则写歪就会得出反的结论。
>
> **同一形态在扫描中又抓到第二处**：互动运行控制行的播种守卫也内联 `SELECT 1 FROM accounts`
> （automation 池上跑 api 属主表），同批修掉，改经既有的账号平台读端口。
>
> **已固化成门禁 `AC-OWN-06`（无跨属主表读）**：`AC-OWN-02/03` 只看 DML/DDL，
> 两处缺陷都是**读**、都被全绿放过去。新门禁**无豁免通道**——跨层写在拆库前至少还能跑、
> 可以记账慢慢消；跨层读在拆库后连跑都跑不起来，「以后再消」不成立。已注入违规验证它会红。
> 当前实测 `crossLayerReads: 0`。
>
> 下面保留原始诊断，供追溯。

**症状**：`risk_state` 的任何持久化都失败，报 `relation "accounts" does not exist`。
dev 上 `risk_state` 最近一次更新停在 **2026-07-23**；ol 的日志 2026-07-25 19:53 有同一条错。

**根因**：`aidcp-cloud/src/risk/pg-risk-store.ts` 的 `saveState` 用**归属条件写**——
SQL 里 `WITH owner AS (SELECT 1 FROM accounts WHERE account_id=$1 AND execution_target=$8)`。
`accounts` 是 **api 属主表**，而 `PgRiskStore` 绑的是 **automation 池**。
物理拆库前三域同库、这条 join 成立；拆完 automation 库里没有 `accounts`，整条写必炸。
同一文件 `:382` 还有第二处 `SELECT execution_target FROM accounts`。

**这不是 Phase 5 引入的**：旧的同步面板路由调的是同一个 `controller.setQuotaLevel()`，
一样会炸、只是回一个没有原因的 500。P5-1 改成异步后，失败原因第一次变得可见可归因
（回读到 `state:'failed', reason:'relation "accounts" does not exist'`）——这正是那个四态设计要的效果。

**影响面**：`applySignal` 先改内存态、再 `persistState()`，所以**进程活着时行为是对的，一重启全丢**，
回落到 07-23 的陈旧表。受影响的是全部状态迁移来源：验证码协助信号、FB 限流信号、面板人工信号。
配额计数（`risk_counters`）是另一条路，不受影响。

**为什么没有当场修**：条件写是**一条语句里同时做谓词与写**，拆成「先经端口读归属、再写」会引入
TOCTOU 窗口——而这是风控**单写者**路径，CLAUDE §7 明列的热点串行文件。两条候选：
① 走已有的 `AccountOwnershipPort`（`src/kernel/account-ownership-port.ts`，其文档本就写明
「automation 侧只持本接口、绝不自己拼 accounts 的 SQL」，即本就该这么改，但要接受 TOCTOU）；
② 把属主 target 落到 `risk_state` 自己这张表上，让谓词回到 automation 本域内（无 TOCTOU，但要加列 + 回填）。
**选哪条是设计决定，且改的是线上风控单写路径，留给用户拍板。**
注：`automation_account_projection`（0077）**帮不上忙**——它有意不带 `execution_target`（见该迁移注释）。

**用户 2026-07-26 选定 ①。** 落地时把 TOCTOU 这笔账写在代码里、没有藏：读与写不再是一条原子语句，
接管若恰落在这个窗口里，先写方仍会落一次自己的状态。**MUST NOT 用重试或写后回读去糊它**
——那只会把一次陈旧覆盖变成多次；兜底仍是既有那条（下一次写被拒 → 驱逐本地 controller → 从库重读）。
另外 `getExecutionTarget` 把「账号不存在」和「归属为空」压成同一个 null，直接改会让告警原因静默失真，
故给端口补了一个**三态读**（`resolveExecutionTarget`），由属主域回答。
enforce 但没注入读口时**降级为无谓词 upsert 并在组装根与 store 两处响亮告警**，绝不假装还在 enforce。

### 0.0.3 已知机制缺口：迁移文件不在同步脚本范围内

`scripts/sync-split-repos` 明确「只管 `src/` + package.json 的 kernel pin」，
所以每加一条迁移，都要**按表属主手工放进对应的 sub-repo**（本次 `0079` 手工放进了 `aidcp-automation/migrations/`）。

已实测这条规则**是可机械化的**：以 `boundaries/table-ownership.json` + 迁移头部
`-- aidcp:objects=` 声明推导「该迁移进哪几个仓」，68 个带头声明的迁移里 **63 个严格符合**；
另 5 个是共享基础设施（账本表 `schema_migrations`、跨属主索引批）——它们进全部三个仓，是对的。
补这个机制时要显式建模「共享基础设施」这一类，别把它当异常。
在补上之前：**加迁移 = 记得手工放一份**，否则拆仓后那个仓的库永远缺这张表且没有任何提示。

**每批的固定收尾**（顺序不可换）：
`typecheck` → `test:acceptance` → `test` → `boundaries:refresh` → 逐条对账 `git diff boundaries/`
→ commit/land → 部署 dev + 哈希校验 + 健康检查 → `scripts/sync-split-repos --apply --tests` 同步七个目标
→ 回写本文与耦合清单 → 真机项登记 `docs/real-machine-acceptance-backlog.md` 簇 60。

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

**~~⚠️ 一条真前置：`risk-command-outbox.ts` import `src/risk/types.ts`，故传输层必须排在 Phase 2 之后。~~
更正（同日）：这条约束是我推错的** —— 那个文件的判定是**随属主留在 automation**，压根不进包，
它的出边自然也就与包无关。**判顺序约束要看「进包那几个的出边」，不是「整目录里谁 import 了什么」。**

**实测：8 个进包候选的出边只有三种** —— 彼此（`internal-http.ts`）、kernel 文件、node 内置。
**对 api / automation / content 的业务层出边为 0。** 因此 `aidcp-transport` **完全不被 Phase 2 阻塞、随时可建**。
（`internal-http.ts` 今天标 automation 只是因为整个 `src/transport/` 目录规则如此；它进包后那条边变成包内边。）

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

---

## 9. 批次 2（content `main()`）执行清单 —— 2026-07-26 **用真编译器**实测

> 此前所有「距离」数字都来自静态扫描（相对 import 说明符能否解析到本仓文件）。
> 本节第一次在 `aidcp-content` 里**真的装了依赖、真的跑了 `tsc`**，结论比扫描更强。

### 9.1 先解一个会拦住所有人的环境坑：三个新仓 `npm install` 装不上

`~/.npmrc` 把 **`@types` 整个 scope** 指向公司内网 registry（`npm.zhaopin.com`），本机连不上、
`ECONNRESET`。`aidcp-cloud` 不受影响是因为它有 `package-lock.json`、resolved URL 全指 npmjs；
四个新仓**没有 lockfile** ⇒ 每次都去解析 `@types/*` ⇒ 必失败。

**绕法（不动用户全局配置）**：`npm install --userconfig /dev/null`。
命令行 `--@types:registry=…` 试过**无效**（scope registry 在 userconfig 里优先级更高）。
content 已按此装好并生成 lockfile 一并提交，另三个仓照做即可。

### 9.2 实测结论：剩余断裂 **100% 只在两个组装根文件里**（三仓都是）

三仓各自 `npm install` + `tsc` 全跑一遍：

| 仓 | 总错误 | `src/server.ts` | `src/index.ts` | **业务代码** | 其他 |
| --- | ---: | ---: | ---: | ---: | --- |
| `aidcp-content` | 578 | 573 | 5 | **0** | — |
| `aidcp-api` | 391 | 385 | 6 | **0** | — |
| `aidcp-automation` | 372 | 361 | 5 | **0** | 6（见下） |
| `aidcp-transport` | **0** | — | — | — | 已可独立编译 |

交接文档 §2.1 的静态扫描结论（业务代码断裂 0）由此**被真编译器坐实**，三仓皆然。
**批次 2/3/4 的交付物各自就是重写那两个文件，没有别的。**

automation 那 6 个在两个 test helper 里（`role-factories.ts` 5 条指向 content 属主模块、
`interaction-store-test-deps.ts` 1 条指向 api 属主模块），**是既存的跨属主留守项、与本次无关**——
`sync-split-repos` 的「跨属主·留守 cloud 96 个」统计的就是这类，随耦合消除自动减少。

### 9.3 content 对基础段的全部依赖 = 20 个字段（机械算出，非人工清点）

口径：`segBContent` 的 ctx 解构 ∪ 段内 `ctx.X` 读点，减去它自己赋值的两个
（`imageProvider` / `publishOrchestrator`）。逐个查了构造点与所绑的池：

**A. 本地建，零跨库（8 个）** —— content 池或压根没有池：

`curatedContentStore`（content 池）· `facebookPublishMediaStore`（content 池）·
`tokenUsageStore`（content 专用小池 max:4）· `llm`（QwenClient，无池）·
`providerRuntime` · `ossUploader` · `dashscopeApiKey` · `anyImageKeyPresent`（后四者无池）

> `curatedContentStore` 已有一条 automation 出边（`triggeredRefsReader: () => delegatedTaskStore`），
> `facebookPublishMediaStore` 已有一条 api 出边（`accountPlatformReader`）——两者**都已是端口形态**，
> 批次 2 只需把实参换成远程实现，不需要改结构。

**B. 必须新开跨进程契约（api 域，7 个）** —— 它们全绑 `apiPool`：

| 字段 | 表 / 属主 | content 实际用到的面 |
| --- | --- | --- |
| `publishLogStore` | `publish_log` / api | `init` `insert` `updateStatus` `recordMetadata` `markImagesAttached` |
| `publishPipelineLogStore` | `publish_pipeline_logs` / api | 一个 best-effort 写 sink（§4.1 已登记的属主反转，就在 segB 里建、绑 apiPool） |
| `clientUserStore` | api | **只一个方法** `hasEnabledClientApprovalReachability` |
| `approvalPolicyStore` | api（实为 `PgAccountStore`） | **只一个方法** `getGroupPublishPolicyForAccount` |
| `botChatStore` | api | 整个对象被交给审批卡接线，**面待收窄**（批次 2 先量它到底调了哪几个方法） |
| `modelConfigStore` | api 池 | `getCached().imageModel` / `.imageProvider` —— ⚠️ 见 9.4 |
| `accountDisplayName` | 依赖 api 的账号存储 | `getAccountName` —— ⚠️ 见 9.4 |

**C. 飞书出口（3 个）** —— `messenger` 的三个方法 + `resolveCardChatId` + `writeApprovalDecision`。
**这条最容易被漏判**：批次 1 重算依赖集时把飞书 SDK 判给了 api，
`aidcp-content/package.json` 里**确实没有** `@larksuiteoapi/node-sdk`——而 segB 现在直接在用它。
两者只有一个能成立。**正解是后者：content 绝不装飞书 SDK，卡片出口走端口到 api 进程。**
（§4.6.2 的「飞书契约缝」已经把 automation 侧改成只交结构化数据、由组装根构卡并发送，
content 侧照同一形态收口即可。）

**D. 无需处理（2 个）** —— `uiSnapshot` / `triggerPublishDispatchOnApprove` 由自动化段赋值，
**已经在 `crossSegment` 响亮闸后面**（批次 0b）。content 进程里它们恒缺席，闸会如实记一条
`cross_segment_drop:` 并点名后果，正是设计意图。**别把它们当成待补的端口。**

### 9.4 ⚠️ 两条是**同步读**，不能包成 HTTP —— 这条会在实装中途炸

- `modelConfigStore.getCached(): ModelConfigValue` —— 同步返回进程内镜像。
- `accountDisplayName(accountId): string | undefined` —— 同步，底下是账号存储的进程内显示名缓存。

两者都在**热闭包里**被调用（每次取图模型 / 每张卡取账号名）。把它们改成 `await 一次 HTTP`
不是加个包装，而是**改掉每一个调用点的签名**，且给热路径加了一跳网络。
**正解是本地镜像 + 刷新器**，与已有的两条判例同形：配置镜像失效通道（`config_mirror_version`
版本号 + 有界轮询比对）、账号投影表（`automation_account_projection` + `fresh_until` 陈旧即拒）。
**批次 2 排期时必须把这两条当独立工作项，别混在「包个 HTTP 客户端」里估。**

### 9.5 因此批次 2 的真实形状

不是「裁掉两段就完事」，是**先定义 6 条新的跨进程契约**，再写 `main()`。
（**这 6 条已于 2026-07-26 全部落地并部署 dev**，逐条见 §9.6。）
它们要按 §5 的判据进 `aidcp-transport`（一份定义、两端共用），
**MUST NOT 在两个仓各写一份**——那正是「两端路径悄悄对不上、两边都编译通过、只有真跑才 404」。

**顺序建议**：先在 `aidcp-transport` 落这 6 条三件套 + 在 `aidcp-cloud` 的组装根注册服务端
（单体下服务端与客户端同进程、逐字节等价、可立刻部署验证），**再**写 content 的 `main()`。
这样每一条契约在被 content 依赖之前，已经在单体上真跑过一遍。

### 9.5.1 ⚠️ 写 `main()` 时才发现的第 11 项：schema 基础设施整族不在内容仓

十条契约做完、准备动手写 `main()` 时，按内容段的 import 逐条核对可用性，发现**只差一样东西**：
`schemaEnsurer`（三个内容属主存储都把它当**必填注入口**）与启动期的迁移契约门。
它们在单体里住在 `src/schema/`，按目录规则判 automation ⇒ **content 仓的 `src` 里根本没有**。

**实测这一族是通用件，不是 automation 的业务**（八个文件，逐个数过）：

| 文件 | 属主表 SQL | 行数 |
| --- | ---: | ---: |
| `schema-capability.ts` | 0（唯一一条 SQL 查的是 `pg_indexes`，PG 目录表） | — |
| `schema-gate.ts` / `schema-contract.ts` | 0 / 0 | 375 / 277 |
| `migration-files/-order/-owners/-plan` | 全 0 | 48 / 100 / 298 / 209 |
| `pg-catalog.ts` | 0 | 59 |

它们只做两件事：**读本仓 `migrations/` 目录** + **查 PG 系统目录**。三个仓都要，且不碰任何属主表
——正好落在 `aidcp-transport` 的准入判据（「三家都可能调用 + 不含任何属主表的 SQL」）上。

**为什么不当场加进包**：归属调整按 §8.1 是**先改控制仓定稿、再回写规则表**，
不能在实装途中顺手扩共享包的职责范围。这里先把实测摆出来、把判据摆出来，等这条裁决落下再动手。
落下之后是纯机械操作：`scripts/sync-split-repos` 的成员清单加八行。

**在此之前 content 的 `main()` 写不完** —— 它的三个存储构造第一行就要 `schemaEnsurer`。
这是批次 2 目前唯一的硬阻断，其余全部就绪（十条契约已落、内容段 import 逐条核对可用）。

### 9.6 执行进度（2026-07-26，按上面的顺序推进中）

**十条契约已全部落地并部署 dev（2026-07-26）。内容段对基础段的依赖里，跨域项归零。**

> **⚠️ 先记一条口径教训，它让这一节从「6 条」变成「10 条」。**
> §9.3 把 8 项判成「本地可建」，判据是**「构造是否绑池」**——**这个判据是错的**：
> 它只看见一个东西是用哪个存储建出来的，**看不见它的闭包里读了谁**。
> 文本出口不绑任何池，可它的模型解析读三张 api 属主配置表、密钥来自 api 属主凭据表；
> 精选库绑内容池，可它的去重守卫要问 automation；素材库同理要问 api。
> **判「本地可建」必须做传递性检查，只看构造实参会漏。** 第二次复核才补出四条（7–10）。

| # | 契约 | 状态 |
| --- | --- | --- |
| 1 | 候审卡投递判定 | ✅ `aidcp-cloud@f9b1d46` |
| 2 | 发布台账窄写（四方法） | ✅ `aidcp-cloud@036f5c3` |
| 3 | 发布管线日志 sink | ✅ `aidcp-cloud@20b52eb` —— 同批 **`apiPool` 从内容段彻底消失** |
| 4 | 卡片出口（发卡 / 发通知 / 传图 / 默认群 / 落点解析 / 免审授权写，六方法一组） | ✅ `aidcp-cloud@76b0daf` —— 同批 **飞书从内容段彻底消失** |
| 5 | 账号显示名 | ✅ `aidcp-cloud@7037ca9` —— **不需要端口**，见下 |
| 6 | 图片模型选择 | ✅ `aidcp-cloud@7037ca9` —— 异步取源 + 同步读本地镜像 |
| 7 | 角色模型解析（厂商/模型/温度/思考） | ✅ `aidcp-cloud@bab9ee4` —— 属主侧**预解析**再送，非送三张表 |
| 8 | 厂商密钥读取 | ✅ `aidcp-cloud@bab9ee4` —— 启动期几次调用，**不需要镜像** |
| 9 | 参照稿触发去重（问 automation） | ✅ `aidcp-cloud@e739c43` |
| 10 | 账号平台读（问 api） | ✅ `aidcp-cloud@e739c43` |

全部部署 dev 并验证（`7037ca9`：三个契约门全过、零 error、飞书长连接已建立）。

**内容段现状（机械口径，从源码现算）**：仍需基础段提供 16 项，逐项分类为
**本地建 8**（内容池或无池）/ **已是窄端口 5** / **跨段闸恒缺席 2** / **直接跨域 0**。
它里面**不再有任何绑别域连接池的存储**；那 8 项「本地建」经传递性复核后，
其跨域出边也已全部收进 7–10 四条端口。

**顺带消掉两条本来要开的契约**——两条都不是「优化」，是判据本身：

- **候审预览读**：原先无条件发起，而它的唯一消费者是自动化段的界面推送口，在 content 进程里恒缺席。
  改成「取用不到就不去读」后，那条跨进程读根本不需要存在。
  **判「要不要为某个调用开跨进程契约」时，先看它的结果在本进程里有没有去处。**
- **账号显示名**（原以为要做本地镜像）：它只喂审批卡，而那个字段在卡片契约里**本就是可选**的、
  构造器缺它回落账号 id；契约 4 又把构卡挪到了属主侧 ⇒ 属主构卡时自己解析即可，调用方不必传。
  单体下是同一个函数、同一份缓存，只是晚一跳；拆开后它比任何镜像都新鲜（解析发生在渲染那一刻）。
  **「同步读」不一定意味着要做镜像——先问这个值是不是非得由调用方提供。**

**四种失败语义，刻意各不相同，抄错就是事故**（每条都有机械断言，含「对端根本没起」这个拆进程后最常见的形态）：

| 口 | 失败时 | 为什么 |
| --- | --- | --- |
| 候审卡投递判定 | **fail-open**（照发卡） | 少发一张 = 没人知道要审；多发一张 = 多看一眼 |
| 发布台账写 | **原样抛** | 「以为落库了其实没落」是红线点名的静默假成功 |
| 发布管线日志 | **吵闹放过** | 观测是 best-effort，绝不因一条日志中断发布；但静默吞掉会让「日志断了」看起来像「没有日志可写」 |
| 卡片出口（六方法） | **一律原样抛** | 发卡失败由发布出口角色自己接住并如实记账；授权写失败吞掉 = 稿子既不候审也不下发 |
| 图片模型选择镜像 | **保留上一份好值 + warn** | 从未取到过才回保守默认；厂商猜错会静默走错供应商 |

**三条落地时才会发现的事，记在这里省得下一个人再撞一遍：**

1. **角色声明的「窄接口」不一定就是你要的端口。** 发布出口角色上那个 `PublishLogStore` 描述的是
   **组合根注入的适配器**（宽松、方法可选、`status: string`），不是属主存储。
   把两者合成一个，会把适配器的宽松度传染给跨进程那一侧。**两条缝就该有两份形状。**
2. **端口的入参类型 MUST 照抄属主的真实签名。** 我先按那个窄接口手写了一份更宽松的入参类型，
   编译器当场指出属主实际要的是另一个（必填字段、多一个多图字段）。
   宽松版会让「端口编译过、真调用时字段对不上」变成可能。
3. **`init()` 不进端口。** 那是属主探测自己 schema 的动作。它已从内容段上移到属主段——
   单体下逐字等价（内容段紧跟基础段跑），拆开后内容域也就没有立场去初始化别人的表。

**两条口的失败语义刻意相反，别抄错**：投递判定 **fail-open**（判不出来照发卡，
少发一张 = 没人知道要审，多发一张 = 多看一眼）；台账写 **必须原样抛**
（「以为落库了其实没落」是红线点名的静默假成功）。两者都有机械断言钉住，
包括「对端根本没起」这个拆进程后最常见的形态。
