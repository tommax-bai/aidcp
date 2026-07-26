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
| **`aidcp-transport`** 共享传输包 | ✅ 已建仓、**28 个成员**（18 条契约三件套 + schema 整族 10）、typecheck 0、已纳入对账；**构建布局曾整包指错**，见 §9.7.3 |
| **三仓 + kernel 的 `test/`** | ✅ 302 个已按派生归属就位（96 个跨属主留守，随耦合消除自动减少） |
| **批次 2** content `main()` | ✅ **已落地**（`aidcp-content@6977ff2`）：`tsc` 578 → **0**，`npm test` **438 pass / 0 fail**，启动烟测两条纪律各自自证。见 §9.7 |
| **批次 3/4** api / automation `main()` | ◐ **测绘 + 对抗性复核完成**（§10）；**第一个岔口已拍板**（发帖调度器归 automation，§10.7 已落地四仓）。余 **约 40 条契约 + 11 条同步读镜像**，按 §10.4 分四段推进 |
| **批次 5** dev 三服务部署 + soak + ol | ⏸ 未开始 |

**距离实测（2026-07-26 收尾时）**：组装根错误 content **0** ✅ / api 399 / automation 358 ——
后两者**全部集中在那一个启动文件里**，业务代码早已归零。
**dev 已到主干 `031e58e`**（三个契约门 enforce 全过、32 角色装配完整、飞书长连接已建、零 error）；
**ol 停在 `ae8eb06`**（今早的风控修复），其后两个提交行为零变更、按规矩等用户明确要求才动。

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

> **接手第一句话就照这里做**：下一步 = §10.4 的**第 1 段**（api 那些不需要对面回头调用的契约：
> 面板投影 / 告警勾销 / 风控命令）。这三条的 **kernel 接口都已备好**（`panel-automation-types.ts`
> / `alert-resolution-port.ts` / `risk-command-types.ts`），只差 `aidcp-transport` 里的三件套；
> 风控命令那条**连三件套都已存在**（`risk-command-http.ts`，2026-07-26 才补进包）。
> **动手前 MUST 读 §10.6** —— 那两份测绘各有判错，照原样写会写错。

1. ~~**⚠️ 先看 §0.0.2：风控状态机在 dev 与 ol 上都持久化不了。**~~ **已修并部署 dev**
   （`aidcp-cloud@8d903dd`，2026-07-26）。同批抓到并修掉第二处同形缺陷，
   并加了门禁 `AC-OWN-06` 防第三次。**ol 仍未部署**，需用户明确要求 + 走发布分支。
2. ~~**批次 2（content `main()`）**~~ **✅ 已完成（2026-07-26），见 §9.7。**
   下一步是**批次 3 / 4**：api 与 automation 各自的 `main()`。两仓 `src/server.ts` 仍是单体逐字节副本，
   照 §9.7 的做法即可（先按段解构算依赖集 → 分「本地建 / 走端口 / 恒缺席」→ 写 `main()` → 真编译器验）。
   **content 那两处 `cross_segment_drop`（审批后下发触发、候审界面推送）由批次 4 接实**。
   **距离已量化**：三个仓的业务代码断裂 2026-07-26 重测已全部归零（0 / 0 / 0），
   剩余断裂 107 / 107 / 138 **全部来自组装根副本**——写完 `main()` 就一次全消（content 已实测：578 → 0）。
   三仓可并行，组装根改动期间彼此不冲突（各写各的仓）。复现命令见交接文档 §2.1。
3. **批次 5** —— dev 三服务部署 + soak，再按用户明确要求上 ol。
   **注意**：批次 2 能自证的边界只到「启动序列走到第一个缺席依赖处如实停下」，
   「三个进程真的能互相说上话」是批次 5 才验的事，见 §9.7.4。
4. **补上迁移的同步机制**（见 §0.0.3）——`sync-split-repos` 现在管 `src/` + 共享包 pin + `assets/`，
   **迁移文件仍靠手工放**。

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

> ✅ **已解（2026-07-26）**：裁决落在 §4.7.1，schema 整族并入 `aidcp-transport`，
> `sync-split-repos` 成员清单加十行（八个 + `ddl-scan` / `ddl-objects`）。阻断解除，`main()` 已写完（§9.7）。

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

---

## 9.7 批次 2 完成 —— content 的 `main()` 已落地（2026-07-26）

`aidcp-content/src/server.ts` 从「单体四段组合根的逐字节副本」换成本进程真正的 `main()`，
`src/index.ts` 同批重列。**实测：`tsc` 578 error → 0；`npm test` 438 pass / 0 fail。**

| 交付物 | 状态 |
| --- | --- |
| `aidcp-content/src/server.ts`（content `main()`） | ✅ `aidcp-content@6977ff2` |
| `aidcp-content/src/index.ts`（公共出口重列） | ✅ 同上 |
| kernel 新成员 `model-config-defaults.ts` | ✅ `aidcp-cloud@05e4d61` → `aidcp-kernel@32868ff` |
| `aidcp-transport` 构建布局修复 | ✅ `aidcp-transport@f53ab02` |
| `assets/` 随仓同步 + pin 对账扩到 transport | ✅ `scripts/sync-split-repos` |

### 9.7.1 十六个句柄的最终落点

内容段原先从上下文解构 16 个句柄，现在逐个落在本进程够得着的东西上：

- **本地建 8**：精选素材库 · FB 发帖素材池 · token 用量记账 · 文本出口 · 图片出口 ·
  对象存储 · 厂商运行时 · 图片总开关。全部只连内容库或压根不连库。
- **跨进程窄端口 6**：发布台账窄写 · 管线日志 · 卡片出口 · 候审卡投递判定 ·
  图片模型选择（本地镜像）· 角色模型解析（本地镜像）。另有厂商密钥 / 账号平台 / 参照稿去重
  三条在存储构造里注入。
- **恒缺席 2**：界面推送口与审批后下发触发，经响亮闸记 `cross_segment_drop:`。

### 9.7.2 三条纪律写进了文件头，且都可验证

① **只对内容库开池**，schema 契约门同步收窄到单属主。启动日志自证：
`schema 契约门（warn） 账本连接目标 1 个：content（本进程只连 content）`。

② **缺跨进程通道就拒绝启动**。没有 api 就没有模型配置、没有发布台账、发不出审批卡；
「起来了但大部分不工作」比「没起来」危险得多。实测：不配 `AIDCP_API_URL` 时抛
`AIDCP_API_URL_missing` 并点名后果，一行不含糊。

③ **不把「查过、没有」和「没查成」抹平**。这条的实现全在 transport 那十个客户端里，
`main()` 的职责只是**不在外面包一层 try/catch**。

### 9.7.3 四个只有真编译 / 真启动才暴露的坑（都不是「写错了」，是「谁也没试过」）

1. **`aidcp-transport` 的每一条 `exports` 都指向不存在的路径。** `tsconfig` 的 `rootDir` 是 `"."`
   而 `package.json` 映射 `"./*.js" → "./dist/*.js"`，于是产物全埋在 `dist/src/` 下。
   **包自己编译通过、发得出去**，直到第一个真去 import 它的仓一次性撞上 17 条 `TS2307`。
   在此之前没有任何东西会报 —— 因为在此之前没有任何东西 import 过它。
   修在 `f53ab02`（`rootDir: "src"`，与 kernel 同口径）。**长效守卫是结构性的**：
   三个仓今后都对它编译，再坏一次会在它们的构建里现形。

2. **共享包里那个「往上两级找 `migrations/`」的默认基准，装进 `node_modules` 之后就指向包自己。**
   包里没有 `migrations/`。消费方 MUST 显式传自己的目录 —— content 的 `main()` 里传了两个
   （`migrations/` 与 `boundaries/table-ownership.json`）。漏传会撞上包里那道空目录守卫如实抛错，
   **而不是**读到零条迁移、让契约门说「通过」。

3. **`assets/fonts` 从来没进过任何一个新仓。** 文字卡渲染出口按 `<仓根>/assets/fonts` 解析字体与
   度量清单，读不到时工厂返回 `null`、封面**静默退回生成式**：不崩、不报，日志里只有一行
   「渲染出口不可用」。content 仓 12 条渲染测试全 `ENOENT` 才让它露头；真部署上去只会表现为
   「文字卡功能好像没生效」。已加进 `sync-split-repos` 的 `REPO_ASSETS`（二进制安全、只给用得上的仓）。

4. **共享包的 pin 是派生事实，transport 也是。** 原先只对账 kernel pin。content 一依赖 transport，
   同一类漂移立刻多了一条 —— 而 transport 里装的是**跨进程路由名**，pin 过期的表现正是
   「两端各自编译通过、只有真跑起来才 404」。pin 对账已泛化到两个包；扩上去一分钟后
   它就抓出了本次真实的一条（content 的 transport pin 停在上一版）。

### 9.7.4 批次 2 之后剩什么

- **批次 3 / 4**：api 与 automation 各自的 `main()`。两仓 `src/server.ts` 仍是单体副本
  （`sync-split-repos` 报 `⊘` 只报不改）。content 那两处 `cross_segment_drop` 由批次 4 接实。
- **批次 5**：三服务 dev 部署 + soak。**本批次没有、也无法自证的一件事是「三个进程真的能互相说上话」**
  —— 本机没有内容库、更不该起 cloud，能证到的边界就是「启动序列走到第一个缺席依赖处如实停下」。
  跨进程往返本身另有机械断言（transport 各契约的 round-trip 测试，含「对端根本没起」这个形态），
  但**组装起来跑通**是批次 5 的事，不要在此之前声称它已被验证。
- **一处已知的表面瑕疵（不改）**：schema 契约门的日志前缀写死 `[aidcp-cloud]`，
  而这一族现在由三个进程共用。三进程各有 systemd 单元名可区分，故只记不改，避免为一行前缀
  再动一次共享包 + 四仓同步。

---

## 10. 批次 3 / 4 测绘 —— **规模不是批次 2 的两倍，是三倍以上，且形状不同**（2026-07-26）

> 方法：两个 agent 各测一仓（真编译器 + `boundaries/module-ownership.json` 定属主 + 传递性检查），
> 各配一道对抗性复核。**完整清单（逐条带 file:line、方法面、失败语义）在
> `docs/data/batch34-composition-root-survey.json`**，本节只讲结论与排期含义。

### 10.1 实测总账

| | 组装根错误 | 本地建 | 已有契约可用 | **需新开契约** | 恒缺席 | **同步读（须做镜像）** |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| content（批次 2，已完成） | 578 | 8 | 6 | **10** | 2 | 2（最后消掉 1） |
| **api（批次 3）** | 385 | 23 | 14 | **17** | 11 | **6** |
| **automation（批次 4）** | 361 | 16 | 9 | **16** | 6 | **5** |

**33 条新契约、11 条同步读。** 批次 2 是 10 条契约、2 条同步读（其中一条还被判掉了）。

### 10.2 三条让它比批次 2 难得多的结构差异

1. **依赖是双向的。** content 只有出边 —— 没有任何人依赖 content 的运行时，所以它的
   `main()` 写完就能独立成立。api 与 automation **互相**依赖：api 要 automation 的 16 条
   （风控命令、面板投影、四类限频配置、FB 群运营面、群路由、收件箱写侧、边缘在场…），
   automation 要 api 的 11 条（账号花名册、发布台账读写、授权台账、互动写入闸、回复策略…）。
   **任何一侧单独写完都跑不起来**，这与批次 2 的「写完就能自证」根本不同。
2. **同步读多了 5 倍，且踩在热路径上。** automation 侧尤其重：人设解析、账号显示身份、
   配置镜像新鲜度闸 —— 后者读的是**模块级 ambient 单例**（由刷新器安装），
   调用点遍布消息处理器与下发闸。这类不能包 HTTP（会改掉每个调用点签名 + 给热路径加网络跳），
   只能「异步取源 + 本地镜像」，而镜像的陈旧语义要逐条定（照 `fresh_until` 陈旧即拒的判例）。
3. **api 侧有一条通道不是「加个客户端」那么简单**：面板实时事件现在是 api **直连 automation 的
   `event_outbox`** 轮询 + `LISTEN`。拆库后要么改成 automation 主动推、要么给 outbox 开读 route
   —— 这是一次通道形态的重新设计，不是端口包装。

### 10.3 已经确定可以**不做**的（测绘的直接收益）

两侧合计 **17 项判为恒缺席**，即**本进程里根本没有消费者**，MUST NOT 为它们开跨进程契约：

- **api 侧 11 项**：锚点缓存 / 规划器 / 概念池（只喂 automation 的消息处理器与搜索角色）、
  对象存储与参照图转存（只被两个 content 属主存储用）、三个模型密钥相关量、
  FB 评论审计、账号守卫投影、配置镜像中继与入队器（api 是**落地端**不是生产方）、
  首作协调器、人设取值口三件、**边-云 WebSocket 服务端与飞书入站**（都属 automation）。
- **automation 侧 6 项**：飞书**入站**平面整组（15 个文件全判 api；真正要跨进程的是反方向）、
  发布排期器与内容排期器、稿件调整 worker 与人设生成器、视觉链路三件、
  segD 面板层专供品整组、api 属主的三张配置镜像（本进程对它们**只有刷新器一处引用**，不是业务读）。

**这一类的判据是同一个**：先问「它的结果在本进程里有没有去处」，没有就别开契约。
批次 2 靠这一问消掉两条本来要开的契约；这里一次消掉 17 项。

### 10.4 排期含义（**这是给下一个 session 的**）

**MUST NOT 按「照批次 2 再做两遍」估这件事。** 建议切成四段，每段自成一个可验收单元：

1. **3a · api 单向可用的那部分**：落五个契约簇、28 个异步方法：
   面板投影 6 个、四类限频配置读写 8 个、FB 群运营事实 10 个、群路由 3 个、告警勾销 1 个。
   其中 FB `importTargets` / `replaceTargetScopes` 会在 scope 判否前反向刷新 api 账号花名册，
   **不属于单向面**，与 4a 的账号花名册端口配对后再落；不得把当前 10 方法客户端注入成完整 FB 面板依赖。
2. **3b · 双向那几条**：风控命令（含 `recoverRestricted`）、审批后下发触发、面板实时事件通道。
   **这三条必须与 automation 侧配对设计**，否则会出现「两侧各写一份、各自编译通过、只有真跑才 404」。
3. **4a · automation 要的 api 侧 11 条**：发布台账读写（**注意与 content 那条窄写口不是同一条**，
   它有 10 个方法）、授权台账、互动写入闸、回复策略解析、人设服务、握手回写。
4. **4b · 11 条同步读的镜像层**：单独排，别混进「包个 HTTP 客户端」里估。

**每一段仍保持 server-first，但验收证据必须按运行形态拆开**：
直接 loopback HTTP 契约测试证明 route/client；部署 dev 单体只证明现网零回归，且按既有红线不启动
automation 内部监听器；只有独立 api/automation 进程都启动后，才能声明真实跨进程通信。

### 10.5 一条已经能确定的边界纪律

`aidcp-automation` **不依赖 `aidcp-transport` 包，用自己 `src/` 里的那份**：
它是那些文件的属主，且它的 14 个存储直接 import 本地的 schema 能力 —— 装包会让同一个模块在
一个进程里出现两份（`schema-capability` 的一次性告警旗标会打两遍）。
`aidcp-api` 与 `aidcp-content` 没有本地副本，用包。
**两端一致由消费方的 pin 对账保证**（已实装，见 §9.7.3 第 4 条）。

### 10.6 对抗性复核结论：**两份分类都判「需要修订」**（同批完成）

复核逐条实测（真编译器 + `module-ownership.json` + `git blame`），合计找出
**判错 10 条 · 整个漏掉 18 条**。完整证据在 `docs/data/batch34-composition-root-survey.json`
的 `verdicts` 段。**在按 §10.4 动手之前必须先吸收这一节 —— 否则会照着一份错的分类写代码。**

**先记一条方法论：复核自己也会错，MUST 逐条验，别照单全收。**
它最严厉的一条是「委托任务执行链的启动守卫没有 else、没有 warn ⇒ /delegate 收得下、
存得住、永远不执行」。**证据是错的** —— `server.ts:6019` 就是
`} else if (delegatedTaskService) { console.warn(...) }`，拆开后那条 warn 会打。
但**结论方向仍然成立且重要**：告警只在启动时响一次，之后每条委托任务照常被接收、落库、
永不执行，收任务那一侧没有任何提示。这是一条真的需要处置的缺口，只是形态不是「完全静默」。

#### api 侧要改的三条判错

1. **`publish-card-exit` 那条 route 不是「零跨属主」。** 它的 `resolveCardChatId` 传递到
   `groupRouteStore`（automation 属主）。而这条 route 是**服务给 content 的** ——
   读不到的后果是 content 每张审批卡**静默落默认群**。原分类把整组九条 route 写成
   「零跨属主取数、最省事的一段」，与它自己在别处承认的传递性缺口直接矛盾。
2. **四类限频配置的面板外观本身就是 automation 属主**，api 仓里连 `createQuotaConfigPanel`
   等四个工厂都 import 不到。**3a 已裁决并落地**：四个 facade 整体留在 automation，
   kernel 的四个窄接口统一改为显式 `Promise<T>`，api 的异步面板 handler 经 HTTP 等待 owner 真态；
   不用 `T | Promise<T>` 掩盖漏 `await`，也不为人工面板读另造轮询镜像。
3. **`roleConfigPanel` 的三个注入指向 content 属主模块**（封面形态的模型/厂商解析、思考参数构造）。
   它们确实是纯函数 + env 读，但「纯不纯」与「本仓有没有这个文件」无关 ——
   这是一项必须做的处置决定（提 kernel / 就地内联），不是可以略过的注脚。

#### automation 侧要改的四条判错（另三条略，见 JSON）

1. **`PublishDispatcher` 漏了第三个跨属主实参 `FacebookPublishMediaStore`（content 属主 + content 池）**，
   而它在构造里是 **optional** —— 漏传**不会编译失败、不会报错**，只是 FB 发帖素材的
   预留释放 / 标记已用 / 隔离三个写**全部静默消失**（预留泄漏 + 图片可能被重复选用）。
   **这正是「传递性检查必须做」那条纪律的又一个实例，而且是 optional 参数这种最难发现的形态。**
2. **`ReplyWorkflow` 的第三个实参 `ReplyAiService` 是 content 属主的具体类**，不是 LLM 客户端本身 ——
   就算模型出口那条口裁决走 HTTP，这个类仍然是本仓没有的东西。
3. **三张 api 配置镜像被误判成「恒缺席」**：只对自动化段成立，对本仓 `main()` 不成立 ——
   角色→模型的解析闭包在基础段、**三张都同步读**，还要 api 的分类目录。
   **而 `aidcp-transport` 里已有现成解法**（`role-model-selection-http.ts` 自带轮询镜像），
   批次 2 的 content 就是这么接的。**把一个已有契约当成了恒缺席。**
4. **委托任务端口的方法面不含 `createFromText`**（路由表只有 7 条，kernel 接口也只有 7 个方法），
   而飞书 `/delegate` 的自由文本入口调的正是它 —— 拆开后飞书入站在 api、服务在 automation，
   这恰恰是必须跨的一条，且是带意图解析的重活，**不能让 api 侧自己拼 intent 绕过去**。

#### 一条结构性发现（比上面任何一条都重要）

**委托任务的执行器同时需要评论调度器（automation）与发帖调度器（api 属主）。**
两者拆到两个进程后，那条 `if` 恒不成立。这不是「补一个端口」能解决的 ——
**它要求先裁决发帖调度器的归属**（留 automation / 搬 api / 拆成两半），
而那个裁决会连带影响：发布生成触发口的客户端该装在哪、`likedStore.recentSince` 与
同步风控视图这两项 automation 事实怎么给到 api 侧。**这是批次 3/4 的第一个必须由人拍板的岔口。**

#### 修订后的真实工作量

原测绘 33 条新契约；复核补出 **18 条漏项**，其中至少 6 条是真新契约
（`getAccountCommentMode` / `appendEvents` / 首作进度读 / `TokenUsageStore.add` /
`listAccountAutomationCatalog` 反向读 / `rolePromptProvider`），另有 2 条是
**已有契约没被认出来**（厂商密钥窄读、角色模型解析镜像），可直接省掉。
**结论：按「40 条上下的新契约 + 11 条同步读镜像」排期，不要按 33 条。**

### 10.7 第一个岔口已拍板：**发帖调度器归 automation**（用户 2026-07-26）

落地：`aidcp-cloud@031e58e` + 四仓同步（api 出、automation 进，源码与测试各一份）。

**改判理由是一条结构约束，不是就近原则**：委托任务的执行器守卫（`server.ts:5894`）
**同时**需要评论调度器与发帖调度器，前者是 automation 属主。两者分处两进程 ⇒ 那条 `if` 恒不成立 ⇒
`/delegate` 收得下、存得住、永远不执行。**端口修不了一个「同时要两个对象」的守卫。**

它读的三类数据本来就跨三个域（点赞记录 automation / 精选库与概念池 content / 发布台账 api），
所以留哪侧都要跨；改判只是换跨的方向，却消掉了唯一一处端口解决不了的。

**零代价的机械依据**（这条值得抄）：该文件的 **import 全部指向 kernel**，依赖一律靠构造注入的接口
⇒ 换层不产生任何新的跨层边。实测 `crossBoundaryEdges` 仍为 0、豁免清单一行未动。
同段其余 6 个文件维持 api ——它们是真的台账与审批。

**连带确定的三件事**（原测绘把它们当成待办，现在有答案了）：
- 发布生成触发口的客户端仍装在 automation 侧（原复核指出的「client 该在 api」随本裁决作废）。
- `likedStore.recentSince` 与同步风控视图**不需要新开反向端口** —— 它们本来就在 automation。
- 委托执行链**不需要跨进程重构**。

**同批还发现并补掉一条**：`risk-command-http.ts`（风控写命令三件套）从落地起就没进过共享包，
而它的 server 在 automation、client 在 api，是最典型该共用一份定义的形态。
漏的原因是**在此之前两端恰好还在同一个进程里，没有任何东西被迫跨仓 import 它**。
已补进 `TRANSPORT_MEMBERS`（**当时**为 28 个成员；3a 发布五个新成员后为 33 个），
并同批写下同目录里**有意不进包**的六个文件及判据
（outbox 家族与账号投影是 automation 私有，「在 `src/transport/` 目录下」不是准入判据）。

### 10.8 3a 已交付：**五个契约簇可用，不等于三进程已上线**（2026-07-26）

本批按上面的修订范围交付 28 个方法：

| 契约成员 | 方法数 | 交付边界 |
| --- | ---: | --- |
| `panel-automation-http.ts` | 6 | 今日动作、点赞浏览、批量风控态、告警、互动投影；失败不染成零/空 |
| `panel-config-http.ts` | 8 | quota / pacing / session / resume 各读写一条；校验、落库、写后真态都留在 automation facade |
| `facebook-group-ops-http.ts` | 10 | 列表、筛选、启停、进度、分配、回收、scope 计数与最近排期结果；`Map` 显式按 entries 往返 |
| `group-route-http.ts` | 3 | `getRoute` / `listRoutes` / `setRoute`；合法未配置 `null` 与 owner/transport 失败分开 |
| `alert-resolution-http.ts` | 1 | 只勾销告警并返回真实 `0 | 1`；不迁移风控态、不恢复 Edge |

**明确未交付**：FB `importTargets` / `replaceTargetScopes`、`weekActiveMask()`、边缘在场与其他同步镜像、
风控命令/审批后触发/实时事件通道，以及 automation 反向读取 api 的 4a 能力。尤其不能用这批部分
Facebook 端口冒充完整面板依赖。

交付版本已按 kernel → transport → api/automation/content 的依赖顺序快进并推送：

- `aidcp-cloud@5b35d0a`：事实源、五组 route/client、单体注册与直接 HTTP 契约测试；
- `aidcp-kernel@f7bceaf`：四个异步配置端口与 FB 群运营窄端口；
- `aidcp-transport@b754bc8`：33 个逐文件成员，五个新增成员的构建产物与导出可解析；
- `aidcp-api@72858c9`：精确 kernel/transport pin、await-safe 面板 handler 与客户端契约测试；
- `aidcp-automation@7c7848f`：精确 kernel pin、owner facade 与本地 transport 副本；
- `aidcp-content@c023f70`：精确 kernel/transport pin。

验证边界如下：

- `aidcp-cloud`：五组 focused transport/server 测试 27 通过；acceptance 123/123；
  全量 3401 通过、0 失败、11 跳过；typecheck 通过；
  `AC-BOUND crossBoundaryEdges=0`，`AC-OWN crossLayerWrites=0 / crossLayerReads=0`。
- `aidcp-transport`：build/typecheck 与五个运行时导出探针通过；
  `aidcp-content`：438/438 与全量 typecheck 通过。
- `aidcp-api` 的 3a focused 24/24 与严格切片 typecheck 通过；全量仍为 404/409 通过，
  5 个失败都来自提取仓既缺的 `src/soul/soul.yaml`，全量 typecheck 仍被未重写的单体组装根阻断。
- `aidcp-automation` 的 owner/transport focused 62/62 与严格切片 typecheck 通过；
  全量为 1597/1626 通过、26 个既有 migration/boundary fixture 失败、3 跳过，
  全量 typecheck 同样被未重写的单体组装根阻断。两仓红项均未被写成绿色，也不是 3a 新增回归。

DEV 部署的是干净 `aidcp-cloud@5b35d0a` 单体：备份
`/opt/aidcp/cloud.bak.20260726-142613.tar.gz` 后只重启 `aidcp-cloud.service`；
content 20/20、automation 43/43、api 53/53 migration 均无 pending；`:8787` / `:8090` 正常，
`/api/health` 返回 `{"ok":true}`，schema gate、DEV writer lock、RiskControllerRegistry、panel 与
Feishu WebSocket 均就绪。**`:8093` 按单体红线保持关闭**；五组 route/client 的可达证据来自
21 个直接 loopback HTTP 契约测试，不是 ECS 上不存在的 automation listener。

最终七仓派生对账以 `aidcp-cloud@5b35d0a` 为 ref：api 105、automation 203、content 83、
kernel 90、transport 33 个受管源文件均零差异；api/content 的精确 transport pin 与
api/automation/content 的精确 kernel pin 对齐，三组 migration 分别为 53/43/20。
检查仍以非零退出指出 api/automation/content 的手写 `main()` / 组装根差异；
这些根本来就不由同步脚本覆盖，
不能为了“全绿”把它们机械复制，也不能据此声称 api 独立 `main()` 或三进程通信已经验收。

### 10.9 3b 源码、共享包与 DEV 单体已交付：独立 api/automation 仍未验收

3b 收口的是三条各自带状态机的双向接缝，不是再加一组普通 CRUD：

1. **restricted recovery 以 automation 写后真态为准。** api 只提交绑定
   `commandId + envKey + accountId + executionTarget` 的持久命令并按同一范围回读；
   automation 单写者串行调用 `RiskController.recoverRestricted()`，先持久化领域
   `applied`，确认写后 `normal` 后才领取并恢复对应 Edge。消费时已变成 warned/frozen
   会落稳定 `refused`，Edge 恢复失败与回执未知分别保留为稳定结局，不能把命令已受理写成恢复成功。
   Edge 对 `202` 只轮询同一 `envKey + commandId`，保持 restricted；仅匹配的
   `applied + normal` 能清掉本地受限态。
2. **publish approval 的 authority、trigger 与平台结局分层。** API 是七个授权
   read/list/void/progress 操作和 decision writer 的物理属主，automation 只能经带内部
   Bearer 鉴权的版本化 HTTP 端口访问；所有进度写都做同一授权 revision 的 CAS，不把一次
   dispatch progress 冒充新授权轮次。`decision_recorded` 与 `human_reconfirm` 是两种不同
   trigger：前者是持久批准后的低延迟唤醒，后者才有人工重批清熔断权。两者的短应答都不代表
   dispatch、submit 或 publish；事务型 approval outbox 与 target-filtered pending scan
   继续承担断链和重启补偿。
3. **panel event 从 automation 主动推到 api。** `panel.event` outbox、既有
   `panel-event-replay` cursor、轮询与 LISTEN 都留在 automation；handler 逐条 await
   HTTP ingress，失败不前移 cursor。api 只做本进程 fanout，单个订阅者失败相互隔离，
   无订阅者时只确认“进程级投递完成”，不声称浏览器已收到。响应丢失允许同一
   `deliveryId` 重投，因此仍是有序 at-least-once，不是 exactly-once；API source-mode
   路径不再读取 automation outbox，也不搬入 automation `EventBus`。

事实源已落在 `aidcp-cloud@67941e4`；最终聚焦切片 **148/148**、acceptance **127/127**，
全量 **3479 total / 3468 pass / 0 fail / 11 skip**，`npm run typecheck` 通过。
边界 census 为 **485 个 source / 485 个 ownership / 0 条 cross-boundary edge**。
这些结果证明契约、owner adapter、source-mode 组合根接线、HTTP/outbox/WebSocket loopback
与单体代码路径；它们**不是**提取仓手写 `main()` 的启动证明。

Edge 源码交付为 `aidcp-edge@c5c2baf`：恢复相关 focused **87/87**、全量
**2381/2381**、typecheck 通过。此批只交付源码，**未构建 installer，也未验证已安装客户端**；
因此不能把源码测试写成用户机器已经取得新恢复交互。

共享包与派生消费仓已按 kernel → transport → consumers 串行快进并推送；精确 pin 只写入实际
导入对应共享包的仓库：

- `aidcp-kernel@94fd279`：risk recovery / approval authority / panel delivery 纯端口；
  build/typecheck、聚焦测试 **26/26**、派生对账 **91/91** 通过；
- `aidcp-transport@f9a7276`：对应版本化 route/client、Bearer 鉴权与运行时导出；
  build/typecheck、dist export **8/8**、派生对账 **37/37** 通过，并精确 pin kernel；
- `aidcp-api@4b6da8a`：API-owner authority、decision writer、panel ingress/fanout 消费侧；
  聚焦测试 **79/79**、受管严格 TypeScript slice、源码 **107/107**、migration **53** 通过，
  并精确 pin kernel/transport；
- `aidcp-automation@483f9c3`：automation-owner risk/trigger/replay 与本地 transport 副本；
  聚焦测试 **85/85**、受管严格 TypeScript slice、源码 **208/208**、migration **44** 通过，
  并精确 pin kernel；
- `aidcp-content@4a32427`：候审卡出口的内部鉴权 token 接线与精确 transport pin；
  全量 **444/444**、typecheck/build、源码 **83/83** 通过，并精确 pin kernel/transport。

最终 split-sync 对受管成员、pin 与 migration 均未发现漂移。命令仍以非零码报告手写组合根和
非受管测试残留：API 有 1 个手写 root、5 个 legacy tests；automation 有 1 个手写 root；
content 有 2 个手写 roots、1 个 auth test。它们被刻意保留，不是同步遗漏。API 全仓
typecheck 的 **414** 个错误只落在手写 `src/index.ts` / `src/server.ts`，automation 全仓
typecheck 的 **370** 行错误及全量测试 **26 fail** 也都落在既有组合根/fixture 缺口；
3b 受管严格切片均通过，不能据此反向宣称 4a/4b 已完成。

一条已知但**没有被 3b 修掉**的物理键边界必须单列：现有 approval 表与 outbox 仍以全局
`requestId` 为唯一冲突域。DEV/OL 共库时，若另一 target 先占同一 id，本 target 的冲突读回
只能查本地 target；本地无行就稳定 fail closed，绝不能复用另一 target 的决定、revision，
也不能据此发 `human_reconfirm`。把主键/唯一索引改成 target-scoped 需要约束替换，
属于独立 **contract migration change**，不得混进本批 expand migration 或用兼容分支掩盖。

DEV 已从 clean Cloud `master` 部署并只重启现役 `aidcp-cloud.service`，运行证据如下：

- deployed Cloud SHA：`67941e495ad52c22b08e4a85ef530245b2fac517`；
- backup：`/opt/aidcp/cloud.bak.20260726-180453.tar.gz` 与
  `/opt/aidcp/cloud/.env.bak.20260726-180453`；
- 部署前 automation 账本为 **43** 条、最高 `0079`；同步源码期间，`0080` 已由外部
  `release-20260726-ol-current` 以 `applied_from_target=ol` 于 2026-07-26 17:53 CST
  写入共享账本。本次 DEV **没有运行** `migrate up`，只读核对其 checksum 与本构建一致；
  最终 status 为 content **20**（最高 `0069`）、automation **44**（最高 `0080`）、
  api **53**（最高 `0078`），三属主 `migrate verify` 均为缺失对象 **0**，启动时
  enforce schema gate 全部通过；
- `aidcp-cloud.service` active、`NRestarts=0`，`:8787` 与 `127.0.0.1:8090`
  正在监听，panel `/api/health` 与客户鉴权 `:8091/health` 均返回 `{"ok":true}`；
  target=`dev` 的 automation advisory writer lock 恰有 **1** 个持有者，
  `RiskControllerRegistry` ready，飞书 WSClient `onReady`；
- 运行进程只有 `AIDCP_DEPLOY_ENV=dev`，没有 `AIDCP_SERVICE`；独立
  `aidcp-api.service` / `aidcp-automation.service` / `aidcp-content.service`
  均 `not-found/inactive`，`:8092` / `:8093` / `:8094` 均未监听。

这次 DEV 只验证了现役 **monolith** 零回归，只能证明默认四段同进程路径健康。
`aidcp-api` / `aidcp-automation` 的手写组合根仍有 4a 完整反向 authority 与 4b 同步镜像缺口；
只有两进程真实 boot、内部端口真实监听、双方不再连接对方属主数据库，并做过断链积压/恢复补投及
真实 panel WebSocket 探针后，才能声明独立 api/automation 或三进程运行验收。
