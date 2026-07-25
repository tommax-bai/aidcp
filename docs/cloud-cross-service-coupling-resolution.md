# 拆仓真耦合 103 条 · 处置清单（多 agent 调查产物）

> **产出**：2026-07-25，20 个 agent 的并行调查 + 对抗性核验（3 路分域调查 → 逐条 A/B/C/D 判定 → 独立核验推翻 → 合成）。
> **性质**：**只读调查产物**，全程未改任何文件、未跑 `boundaries:refresh`、未碰 ECS。
> **定位**：这是批次 2/3/4（三仓各写自己的 `main()`）的**执行输入**。上位方案见
> `docs/cloud-composition-root-trisection.md`，本文回答的是它 §1 里那句「真业务耦合只有 103 条」之后怎么办。
>
> **落地前必读的三条**：
> 1. **一律按符号名定位，行号只作导航**。清单行号基于 `aidcp-cloud@18a33b7`，产出当天 HEAD 已到 `b4694df`，
>    核验方实测 `src/comm/handler.ts` 的 import 行号已漂 1–2 行。照抄行号会改错地方。
> 2. **§7 逐条标了低置信度项与三件明确未查实的事**。那一节不是免责声明，是待办：落地对应条目前先补上。
> 3. **§4 是本文最有价值的一节**：17 个「看着像纯契约」的目标里 **13 个进不了 kernel**，卡点分五类，
>    其中两类在四条硬禁之外 —— 只查四禁会得出相反结论。动手前先读它。

---

> 只读调查产物。全程未修改任何文件、未跑 `boundaries:refresh`、未碰 ECS。
> **落地前必看**：三路核验的行号基于 `18a33b7`，任务书给的 `00d30a3` 是更早的祖先，而我核验时仓库 HEAD 已到 **`b4694df`**。我实测 `src/comm/handler.ts` 的 import 行号已漂 1–2 行（报告里的 51/53/64/67/75/78 现为 52/53/65/68/76/79）。**本清单一律按符号名定位，行号只作导航提示，照抄行号会改错地方。**

---

## 0. 口径对账

| 口径 | 数 | 说明 |
|---|---|---|
| 交办 | 103 | api 56 / automation 26 / content 21 |
| 实测（import 语句数） | **104** | api **57**（+1：`panel/types.ts` 静态列表看不见的内联 `import('../comm/protocol.js')`，在 `panel-server.ts` 动态导入处）/ automation 26 / content 21 |
| 去重后（唯一 `(from,to)` 边） | ~95 | automation 26 语句 = 24 边；content 21 语句 = 17 边。**主线核销 `import-exemptions.json` 条目时用「边」口径** |
| 台账基线（我实测） | `frozenTotal` = **96**，entries 96；`kernelRoster.members` = **57**；`rejected` = **11** | 11 条拒入名册逐条对上了三路引用：`protocol.ts` / `curated-content-store.ts` / `client-user-store.ts` / `content-schedule-store.ts` / `session-limits.ts` / `resume-limits.ts` / `event-bus/index.ts` / `event-bus/types.ts` / `platform/registry.ts` / `platform/index.ts` / `agents/base-role.ts` |

---

## 1. 总账

| 判定 | 语句数 | 占比 | 说明 |
|---|---|---|---|
| **A 提升进 kernel** | **33** | 32% | 其中 **11 条走「追加进已是花名册成员的 kernel 文件」**，完全不动 `boundaries/*.json` |
| **B 抽接口注入** | **44** | 42% | 大半是「消费侧只用一个方法」，已经是 `Pick<>` 或闭包注入形态 |
| **C 跨进程调用** | **1** | 1% | 只有面板写风控这一条是运行时真 RPC |
| **D 本地消除** | **23** | 22% | 三种形态：改归属 13 / 就地重声明 6 / 删死代码·死注解 4 |
| **⛔ 被终局裁决否决，维持豁免** | **3** | 3% | `content → event-bus/types.ts` 的 `NoteDetailData`×2 + `ConceptPool`×1 |
| 合计 | **104** | | |

**最大的七簇**（占 104 条里的 40 条）：

| # | 簇 | 条 | 判 | 一句话 |
|---|---|---|---|---|
| 1 | 4 个 content 角色 `extends BaseRole` | 8 | B | 本批唯一的「大」，要新建 2 文件 + 改 4 角色 + 改 `RoleFactory` + `server.ts` 一行 |
| 2 | 三个限频配置外观归属判错 | 7 | D | 文件头自己写着「归 automation」，清单标了 api；改归属零代码 |
| 3 | 边云协议载荷被 api 当自家响应形状 | 6+2 | D+B | 协议 6 条重抄，验证码协助 2 条是运行时真调用、必须走端口 |
| 4 | 发布审批闸角色归属判错 | 6 | D | 30 个 content 角色里唯一一个 api，机械上无解 |
| 5 | 平台 id 归一函数 | 5 | B | 5 个 api 文件为一个 6 行归一器直连 automation 注册表 |
| 6 | 风控词表三组枚举 | 5 | A | `risk/types.ts` 零 import，最干净的一块 |
| 7 | 面板注入端口的纯载荷类型 | 4 | A+B | 3 条搬 DTO，AlertStore 那条只能抽窄端口 |

---

## 2. 三条贯穿三路的合并结论（不合并就会重复劳动或互相打架）

这三条是单路视角看不见的，**主线排工前必须先吃掉**：

**① 一个文本补全接口，三路各造了一份。**
automation 的 `handler.ts` + `simple-planner.ts` 要 `LlmClient.complete`；content 的 `persona-generator.ts` 要 `RoleLlmLike.complete`；`agents/base-role.ts` 自己还私藏一个 `type RoleLlm`。**三者签名逐字相同**。→ 在**已是花名册成员**的 `src/kernel/llm-contract.ts` 里加**一个** `TextCompletionPort`（别名 `RoleLlmLike` 保兼容），一次消 3 条边、零花名册变更。命名红线：新名里不得出现 `LlmClient` / `ChatLlmClient` 子串（门禁正则直接锚这两个 token）。

**② `publish-scheduler.ts` 的结果类型，automation 和 content 各要一半，两路给了两个不同的 kernel 落点。**
automation 要 `TriggerOutcome` + `ReferenceNote`（`delegated-task/executors.ts`），content 要 `BeginRewriteResult` + `ReferenceNote`（`first-post-onboarding-coordinator.ts`）。一路提议新建 `publish-trigger-contract.ts`，另一路提议进已有的 `publish-generation-types.ts`。**我实测 `src/kernel/publish-generation-types.ts` 已经存在、已在花名册、且第 17 行已有 `SchedulerApprovalCardResult`**（正是这两组类型的公共依赖）。→ **统一落在 `publish-generation-types.ts`，复用已有符号，不新建文件**：一次编辑消 3 条边（automation 2 + content 1），**花名册零变更**。

**③ `publish-log-store.ts` 是三路共同的热点，`panel/types.ts` 是六簇共同的热点。**
`publish-log-store.ts`：api（schema 端口）+ automation（`DispatchDraft` / 台账三方法）+ content（`draft-refinement-worker`）三路都要动，且 `DispatchDraft` 被两路同时要 → **必须并成一个工作项、一个 kernel 落点**。
`panel/types.ts`：api 的协议重抄 / 事件扇出 / 载荷类型 / 风控写 / 死字段 5 簇 + automation 的节奏配置契约 1 簇 + 归属改判产生的 3 条反向边，**共 6 簇写同一个文件** → 单人串行，一次做完。

---

## 3. 落地顺序（按依赖与风险排，共 6 个阶段）

标记说明：`🔒` = 触碰禁改文件（只出方案，主线串行落地）；`📒` = 需改 `boundaries/*.json`（新 kernel 成员 / 归属改判）；`✅` = 既不碰禁改文件也不碰台账。

---

### Phase 0 — 零台账、零 server.ts（11 条）✅ **已完成**

> **落地记录（2026-07-25）**：`aidcp-cloud` master `525f483`，已部署 dev、四个属主仓已同步
> （kernel `4ebe412` / api `b7d5ec2` / automation `1ecde21` / content `138af56`）。
>
> **实测净效果：跨边界豁免 96 → 86 条，零新增。** 比清单预估多消一条 —— 收口后
> `persona-generator` 对 automation 侧那个别名的依赖也随之可以直取 kernel。
> 口径提醒：清单按 **import 语句**数 11 条，台账按**唯一边**记，11 条语句 = 10 条边。
>
> **一处更正（清单的假设不成立）**：P0-4 写「删掉角色名标注 = 丢掉写错就编译红那道闸」，
> 实测**只对一个角色成立** —— 另两个继承的基类本身就把该字段声明成角色名联合，标注删了基类照样拦。
> 真正失去防线的是**不继承基类**的那一个。新增的合同夹具 `test/agents/content-role-names.test.ts`
> 精确补这一处，并**双向验证过**：继承基类的改错 → 基类当场拦；不继承的改错 → 夹具当场拦。
>
> 验证：typecheck 0 / acceptance 117·0 / 全量 3324 pass 0 fail 10 skip；`src/server.ts` 零改动；
> dev 三个契约门全过、零 error、47 项子系统就绪。

全部是「追加进已有 kernel 成员」或「删消费方注解」，不新增 kernel 文件 = **不触发 `AC-BOUND-03` 的花名册 deepEqual**，可最先合、风险最低。

**P0-1 · 文本补全端口收口（4 条，A）**
- 改哪：`src/kernel/llm-contract.ts` 末尾追加 `export interface TextCompletionPort { complete(prompt: string, opts?: LlmCallOpts): Promise<string> }`；再加 `export type LlmThinkingMode = Exclude<LlmThinkingModeOpt, 'default'>;`
- 改成什么形状：`src/llm/qwen.ts` 的 `export interface LlmClient` 改成 `extends TextCompletionPort {}`（运行时零变化，api/content 侧既有用法不动）；`comment-search-term-generator.ts` 本地 `RoleLlmLike` 改为等值再导出 kernel 符号；`handler.ts`（`LlmClient`）、`simple-planner.ts`、`persona-generator.ts`、`qwen.ts:19`（`ThinkingMode` 用 `as` 别名导入，四处使用点一字不改）改指 kernel。
- **红线**：`ThinkingMode` **不得**直接换成三值的 `LlmThinkingModeOpt`——`'default'` 会穿过 `buildThinkingParams` 的 `if (!mode)` 守卫，把「不干预」发成 `{thinking:{type:'disabled'}}` / `enable_thinking:true`，违反该文件自己写的「零回归、请求体逐字一致」；现有 `test/thinking-mode.test.ts` 抓不到。
- 验证：`npm run typecheck`；`npm test -- thinking-mode` 全绿；`grep -rn "from '../config/role-catalog" src/llm/` 零命中。

**P0-2 · 写作语言守卫解锁（1 条 + 顺带 api 内 3 处，A）**
- 改哪：`src/soul/writing-language.ts` 的模块级 `const WRITING_LANGUAGE_SET = new Set(...)`（约 13 行）。
- 改成什么形状：把 `WRITING_LANGUAGE_VALUES` + `isWritingLanguage` **追加**进已有成员 `src/kernel/writing-language.ts`，实现改 `(ARR as readonly string[]).includes(value)`；`src/soul/writing-language.ts` 退化为纯 re-export shim。**必须走 shim 形态**——整文件 `git mv` 会打断 `src/soul/index.ts` 的桶链，而 `src/server.ts` 正是经桶链拿 `checkWritingLanguage`。
- 验证：`typecheck`；`grep -n "new Set" src/soul/writing-language.ts` 零命中；`git diff --stat src/server.ts src/soul/index.ts` 为空。

**P0-3 · 发布触发结果类型收口（3 条，A）**——见 §2 结论②
- 改哪：`src/publish-agent/publish-scheduler.ts` 的 `ReferenceNote` / `ClaimRejectReason` / `TriggerOutcome` / `BeginRewriteResult` 四段定义。
- 改成什么形状：搬进 `src/kernel/publish-generation-types.ts`（复用其已有 `SchedulerApprovalCardResult`，**别加第三份拷贝**）；`publish-scheduler.ts` 原位 `export type { ... } from kernel` 保住 `server.ts` 与三个测试零改动；`delegated-task/executors.ts` 两行并一行、`first-post-onboarding-coordinator.ts` 一行改指 kernel。
- 验证：`typecheck`；`grep -rn "publish-scheduler" src/delegated-task/ src/onboarding/` 零命中；`npm test -- publish-scheduler-reference` 绿。

**P0-4 · content 角色的 `RoleName` 自标注（3 条，D）**
- 改哪：`curated-comment-evaluator.ts` / `persona-generator.ts` / `valuable-comment-archivist.ts` 各一行 `import type { RoleName }`。
- 改成什么形状：整行删除，字段声明改 `readonly roleName = 'xxx' as const`（`as const` 保住字面量类型不塌成 `string`，下游 `browse:${roleName}` 的模型解析键逐字不变）。**完全不碰 `event-bus/types.ts`。**
- **必须同批补防线**：删掉注解 = 丢掉「角色名写错编译红」这道闸。加一个极小合同夹具测试，把这 5 个 roleName 与 `src/config/role-catalog.ts` 的 roleId 对拍（**只读** role-catalog）。这正是 `kernel-non-members.json` 那条裁决自己开的药方。
- 验证：新夹具测试绿；故意把某个 roleName 改错一个字母，夹具应当红。

---

### Phase 1 — 归属再裁决（13 条，D）🔒📒 主线独占 ✅ **部分完成（-5 / 13）**

> **落地记录（2026-07-25）**：`aidcp-cloud` master `ff7fddf`，**源码零改动**（`git diff src/` 为空）。
> 跨边界豁免 **86 → 81**。定稿两处修正见控制仓 `docs/cloud-service-decomposition-proposal.md`
> §4.6.3 / §4.6.8 的修正注；四个属主仓已同步（审批闸角色从 api 仓移到 content 仓）。
>
> **P1-2（审批闸角色，-5）✅ 已落。** 我亲自按定稿 §4.6.3 **自述的机械判据**复核，证据比清单给的更硬：
> 引模型客户端 ✓、引边缘协议 0 命中、`publish_log` / 授权记录 / INSERT / UPDATE **全部 0 命中**。
> 清单说 6 条，实测 **5 条边**（口径差同 Phase 0：语句 vs 唯一边）。
>
> **P1-1（三个限频配置门面，-7/+3）⏸ 定稿已改、归属表延后到 P2 批。**
> 清单说「必须与 P2-1 同批」，**理由被棘轮当场证实**：豁免清单只许下降、不许静默追加，
> 翻转带来的 3 条新反向边被直接拒绝，只能走「问责冻结」通道占额度。
> 决定延后的判据是——**今天是单进程，这条违背没有活体形态**，它只在 api 真正独立成进程时才成立。
> 与其先欠 3 条问责额度，不如与 P2-1 同批落、3 条新边当场归零。
>
> **顺带查实了 P2-1 的真实深度（本清单未提，排 P2 工时前必看）**：那四个 `Panel*Config` 接口牵着
> —— 风控的两个枚举（`RiskQuotaLevel` / `RiskAction`，即 P2-6）、**一个被 §10.9 终局裁决拒入 kernel 的
> 协议类型**（`PacingOp`，只能降裸串或另想办法）、以及一个同样在拒入名册上的会话预算类型
> （`SessionInteractionBudget`，与 P3-1 同文件）。**P2-1 不是独立小活，是 P2 lane 的核心结点。**

**零源码改动，13 条边直接消失**，是全批性价比最高的一步。但改的是 `boundaries/ownership-rules.json` 的 `fileOverride` + 控制仓定稿，属人判，`refresh` 代不了劳。

**P1-1 · 三个限频配置外观归属（7 条）**
- 依据：`quota-config-facade.ts` / `session-config-facade.ts` / `resume-config-facade.ts` 三份文件头**逐字**写着「本外观即该表后台编辑的唯一窄内部写口，归 aidcp-automation」，与已判 automation 的孪生兄弟 `pacing-config-facade.ts` 结构完全相同。定稿 §4.6.8 的表只点名了 pacing 一个。
- 改哪：控制仓 `docs/cloud-service-decomposition-proposal.md` §4.6.8 表 5 行→8 行、计数同步；`boundaries/ownership-rules.json` 加 3 条 `fileOverride`（layer=automation）；refresh 删 7 条豁免。
- **代价必须一并写进 change**：翻转后三个外观对 `src/panel/types.ts` 的 import 各变成 1 条 automation→api 反向边（与 pacing 今天的形态一样）→ **必须与 P2-1 同批**，否则只是把窟窿挪个位置。

**P1-2 · 发布审批闸角色归属（6 条）**
- 依据：`publish-agent/roles/approval-gatekeeper.ts` extends 内容段 `BasePublishRole`、注入 `ChatLlmClient` 调模型、用内容段 prompt 构造与重试兜底、被注册进内容生成管线——同目录 30 个角色里唯一一个 api。定稿 §4.6.3 把「运营审批台账」与「生成管线里的审批闸角色」两个『审批』混成了一个。
- **反证很硬**：若坚持留 api，就得把基类 / 管线上下文 / prompt 构造 / 重试策略 / `ChatLlmClient` 五样一起抬进 kernel，**五样全部撞准入门**——机械上无解。
- 改哪：§4.6.3 表把该文件从 api 行移进 content 行（7→6 / 54→55）；`ownership-rules.json` 改 `fileOverride`；refresh 删 6 条。
- 验证（两条都是）：`npm run boundaries:refresh` 后 `frozenTotal` 由 96 降到 83，`npm run test:acceptance` 的 `AC-BOUND-01/03/05` 全绿，源码 `git diff` 为空。

---

### Phase 2 — `panel/types.ts` / `panel-server.ts` 契约析出（23 条）🔒📒 ✅ **八簇全完 + Phase 1 延后的那条**

> **落地记录（2026-07-26）**：`aidcp-cloud` master `0bbc43b`，已部署 dev、七个仓/包已同步。
> **跨边界豁免 68 → 39（近腰斩），棘轮 `raises` 仍为空。** 共享层成员 64 → 72。
> typecheck 0 / acceptance 118·0 / 全量 3328 pass 0 fail 10 skip；`refresh` 幂等（第二次跑新增 0 删除 0）。
>
> **P1-1 那条延后的翻转随本批落，结果比预期好得多**：它不但没长出预言的 3 条反向边，
> **反而多消 6 条**——三个门面翻到 automation 后，它们对配置存储与三个风控模块的引用从跨域变同层。
> **这 6 条没有任何一份计划提到过。** 同时实测坐实了「必须在 P2-1 之后」：
> 在未做 P2-1 的基线上单独翻转，棘轮当场拒绝、报出的正是预言的那三条。
>
> **三处合并态才暴露的修正**：
> ① P2-5 与 P2-4 撞车（改同两个文件同一行）→ 验证码形状由 api 侧端口独占，P2-4 删掉两个文件
>    （留着就是第二份 api 侧副本，**正是漂移闸要防的东西**）；
> ② 翻转三个门面**只加 fileOverride 会让 `AC-BOUND-01` 当场红**——那三个文件还在「已裁决名册」里，
>    覆盖与名册重叠即失败，必须同批从名册删掉那三行；
> ③ 八份计划**每一份**都低估了符号闭包。
>
> **红线自证**：`protocol.ts` / `risk-state-machine.ts` / `role-catalog.ts` / `event-bus/types.ts`
> 四个禁改文件**零改动**；组装根只动 1 增 2 删（删一个面板侧零读点的死字段）。
>
> **新增漂移闸的两条性质写进了闸的文件头**：① MUST NOT 用「双向可赋值」那种朴素写法——
> 它把 `never` 当中间结果传下去而 `never extends true` 恒真，一侧判定失败反而回落成放行；
> ② **这闸的牙齿在 `typecheck` 不在 `test`**（测试运行器只剥类型不做检查）。第二条我反向验证过。
>
> **本轮登记、不修的两处残留**：kernel 内部出现第三份风控枚举（两个 kernel 文件逐字重复，门禁无感，
> 收口方案已被验证可行）；发布管线 barrel 里 9 个素材池再导出是死代码。

六簇写同两个文件，拆开做必冲突。建议一个 session 独占这两个文件直到收工。

**P2-1 · 四个 `Panel*Config` 抬 kernel（1 条 + 抵消 P1-1 的 3 条反向边，A）📒**
- 改哪：`src/panel/types.ts` 的 `PanelQuotaConfig`(≈926) / `PacingConfigRowView`(≈938) / `PacingConfigCatalogView` / `PacingConfigPatchInput` / `PacingConfigSetResult` / `PanelPacingConfig`(≈967) / `PanelSessionLimits`(≈1022) / `PanelResumeConfig`(≈1098)。（我已实测这些符号确在此文件，行号如上，随 HEAD 漂移。）
- 改成什么形状：新建 `src/kernel/config-panel-ports.ts` 装这一组；`panel/types.ts` 原位等值再导出（api 侧 panel-server 零改动）；四个 facade 改指 kernel。
- **唯一的坑（必须照此形状）**：`PacingConfigRowView.operation` 与 `PacingConfigPatchInput.operation` 的类型 `PacingOp` 定义在 `src/comm/protocol.ts`（禁改 + §10.9 终局裁决 MUST NOT 进 kernel）。→ **kernel 版把该字段收窄成裸 `string`**，词表校验留 automation 侧 facade（它本来就有 `PACING_OPS` / `isKnownOp(op: unknown)`，签名不用动）。**MUST NOT 在 kernel 里另抄一份 op 字面量联合**——那是第二份穷举、漂移 typecheck 抓不到。现成先例：`src/kernel/panel-automation-types.ts` 的 `PanelActionTotal.action` 注释就写着「action 为裸串；词表收窄留面板侧」。
- 顺手净收益：把 `minMs` / `maxMs` 改成可选（现在声明必填、facade 却按 `undefined` 判，`panel-server.ts` 因此塞了三处 `as never` 强转，改完可删，运行时零变化）。
- 验证：`typecheck`；`grep -n "as never" src/panel/panel-server.ts` 三处消失；`AC-BOUND-03` 花名册对齐。

**P2-2 · 面板注入端口的纯载荷类型（3 条 A + 1 条 B）📒**
- 改哪 / 搬什么（**行号已被核验方修正，按修正版搬，照原稿搬会编译不过或反手把 kernel 拽回业务层**）：
  - `src/cache/group-route-store.ts` **L29-40**（`GroupRoute` + `SetGroupRouteResult`）→ 新建 `src/kernel/group-route-types.ts`。这一段零依赖，是最干净的一块。
  - `src/metrics/token-usage-store.ts` **L158-204**（6 个声明，**不是原稿说的 191-204**——`LlmUsagePayload` 传递依赖 `LlmUsageRow` / `LlmUsageBucket` / `LlmUsageCostEstimate` / `LlmUsageCostPricingBasis`）→ `src/kernel/llm-usage-types.ts`。
  - `src/metrics/billing-price-refresh.ts` **L6-38**（4 个声明，**不是 30-38**，且**止于 L38**，`BillingPriceRefreshTokenUsage` 会把 token-usage-store 拽回来、panel 也不需要它）→ `src/kernel/billing-price-refresh-types.ts`。
  - `AlertStore` 那条**不搬类型**（`AlertStore` 传递依赖 `AlertSeverity`，来自 automation 的 `alert-notification.js`，整体抬会造 kernel→automation 禁止边）→ 新建窄端口 `AlertResolutionPort { resolveById(alertId: number, at?: number): Promise<number> }`，`panel/types.ts` 的 `Pick<AlertStore,'resolveById'>` 改指它。
- 形状：三个属主文件 import + 原位 re-export，属主侧消费者零改动；`panel/types.ts` 四行 import 全删净（已核实该文件对这四个模块没有别的 import）。
- 验证：`typecheck`；`PgAlertStore` 仍结构性满足端口 → `server.ts` 注入点零改动；refresh 后这四条豁免（含两条计入门禁 `involvingContent` 的）归零。

**P2-3 · 面板事件扇出端口（2 条，A）📒**
- 依据：已 grep 全 `src/panel`，对 `eventBus` 的使用只有 `panel-ws.ts` 一处 `onAny(...)`。`EventBus` 类持模块级 `handlers = new Map` / `wildcardHandlers = new Set`，且在拒入名册里。
- 改哪 / 形状：新建 `src/kernel/event-fanout-port.ts`：`PanelEventHandler = (event: string, data: unknown, originTs?: number) => void` + `EventFanoutPort { onAny(h): () => void }`；`panel/types.ts` 与 `panel-ws.ts` 改导端口。`EventBus` 结构上已满足，组合根一行不改（只是类型收窄）。
- 验证：`typecheck`；`grep -rn "event-bus" src/panel/` 零命中。

**P2-4 · 协议载荷在 api 段重抄（6 条，D-重声明）✅**
- 依据：§10.9 终局裁决——`protocol.ts` MUST NOT 进 kernel（进了等于三边共导、把这 6 处就地合法化），且同节第 2 条明写「api 与 content MUST NOT 导入边云协议文件，**包括仅类型导入**」。所以落点**不是 kernel，是 api 段自己的 contracts 目录**。
- 改哪：新建 `src/api-contracts/{publish-approval-wire, ui-usage-wire, notification-wire, pacing-op}.ts`，逐字重抄 `PublishApprovalActionPayload` / `ActionResultPayload` / `PublishDraftImageRemovePayload` / `ResultPayload` / `UiDailyUsagePayload` / `UiSlowStartPayload` / `NotificationItem` / `PacingOp`；六个消费方（`client-auth-server.ts` / `panel/types.ts` / `panel-server.ts` 含那处内联动态 import / `notification-contact-store.ts` / `client-publish-approval.ts` / `draft-image-remove.ts`）改导本地契约。`protocol.ts` 一个字不改。
- **重抄必须同批配漂移闸**：在 `test/` 下加一个纯类型断言用例（`test/` 不在归属清单内，可同时导两侧），对每对形状做双向可赋值断言。**没有这一步，这就是一处静默漂移入口**——协议改字段两边悄悄分家、typecheck 全绿。
- 验证：漂移闸测试绿；故意给 `protocol.ts` 侧某形状加一个必填字段，该测试应当红。

**P2-5 · 验证码协助端口（2 条，B）🔒(server.ts 装配)**
- **这条是核验推翻的重点之一**：`panel/types.ts` / `panel-server.ts` 对 `captcha-assist.ts` 的依赖**不是类型借用，是运行时真调用**——`panel-server` 在五处实调 `deps.captchaAssist.verifyToken / noteViewerPresence / getIncident / requestCapture / submitClick`。按「重声明类型」一刀切会编译通过、但**面板的验证码协助端点整条失效**。
- 改哪 / 形状：`deps.captchaAssist` 已是结构化依赖位 → 在 api 侧声明五方法窄端口 + 三个返回形状（`CaptchaAssistTokenVerifyResult` 是唯一自足的；`DispatchResult` 与 `IncidentView` 都传递内嵌 `BlockingOverlaySnapshotPayload` / `CaptchaAssistSnapshotPayload` 协议载荷，**必须与 P2-4 同批用重抄的本地形状**）。属主留 automation，按 §4.6.4 走窄内部接口。
- 验证：`typecheck` + 面板验证码协助端点的既有测试全绿（不能只看编译）。

**P2-6 · 风控词表（5 条，A）📒**
- 改哪：`src/risk/types.ts`（113 行，**零 import**、无 SQL / HTTP / LLM / 模块级 Set|Map，全批最干净的一块）整文件搬为 `src/kernel/risk-contract.ts`。
- 形状：`src/risk/index.ts` 的 `export * from './types.js'` 改指 kernel（**barrel 本身留 automation、不进 kernel**——它 `export *` 覆盖 22 个业务模块，连带 24 条 SQL + `risk-state-machine.js`）；四个消费方（`panel/version.ts` / `panel-server.ts` ×2 / `panel-store.ts` / `client-auth-server.ts`）改指 kernel。risk/ 内部 20+ 消费者无感。
- ~~**`RiskSignalKind` 不要跟着搬**——它定义在 `risk-state-machine.ts`（禁改）。~~
  **更正（2026-07-26 落地时实测）**：`RiskSignalKind` 定义在 `src/risk/types.ts:72`，**不在状态机文件里**。
  本条原文记错了。它随 `types.ts` 一起进 kernel，**而 `risk-state-machine.ts` 与 `risk-controller.ts` 逐字节未改**
  ——「风控单写域一个字节不碰」这条不变量**成立且已自证**（落地 commit 里那两个文件零改动）。
- **核验补的漏项**：`panel/types.ts` 也 import risk barrel，取的是 `RiskController`（类）与 `SessionInteractionBudget`——**两者都不在 `types.ts` 里**，本次提升闭合不了，它们属 P5-1（风控写侧）。别默认「lift types.ts 就把 panel→risk 全清了」。
- 验证：`typecheck`；`grep -n "from '../risk/index" src/panel/` 只剩 `types.ts` 一处（等 P5-1 清）。

**P2-7 · Facebook 发布配图 DTO + 跨进程错误守卫（2 条，A）📒**
- 改哪：`facebook-publish-media-store.ts` 的四个纯 DTO（`FacebookPublishImageInput` / `MediaListView` / `SetPatch` / `UploadResult`）→ 新建 `src/kernel/facebook-publish-media-types.ts`；宿主 import + re-export（宿主建 pg 池 + 走对象存储，整文件进不了 kernel）。
- **本簇必须同批修的隐患**：`panel-server` 现在用 `err instanceof FacebookPublishMediaError ? err.reason : 'unavailable'`——**拆进程后 `instanceof` 恒 false，会静默退化成 `'unavailable'` 吞掉真实原因**，正是「静默假成功」红线那一类。→ 错误那条**不靠搬类解决**：在 kernel 文件加结构化守卫 `isFacebookPublishMediaError(e): e is { name: 'FacebookPublishMediaError'; reason: string }`（按 name + reason 两字段判，跨进程/跨包都成立），`panel-server` 改用它；属主侧错误类保持原样、只确保 `name` 已设。
- 验证：`typecheck`；加一个用例：把错误对象结构化克隆（`JSON.parse(JSON.stringify(...))`）后仍能被守卫识别、`reason` 不退化成 `'unavailable'`。

**P2-8 · 概念池死字段（1 条，D）🔒(server.ts)**
- 依据：我已实测——`conceptStore` 在整个 `src/panel/` 只出现在 `types.ts:173` 的字段声明**一处，零读取点**，组合根仍在往里传。与主干 `1d5ac18`「drop the one ctx field nobody reads」同类。
- 改哪：删 `panel/types.ts` 的 import 与 `conceptStore?: ConceptStore;` 字段，再删 `server.ts` 面板 deps 里那一项。**只删面板这一处**——`server.ts` 另外五处 `conceptStore` 是浏览闭环真在用的，一个都不能碰。
- 验证：worktree 里 `typecheck` 确认零引用；`grep -n conceptStore src/server.ts` 仍有 5 处。

---

### Phase 3 — 新增 kernel 成员（13 条，A）📒 ✅ **八条全部完成**

> **落地记录（2026-07-25）**：`aidcp-cloud` master `5b3b9fc`，已部署 dev、四仓已同步
> （kernel `3761197` / api `76dc814` / automation `ec16cf4` / content `cc6ccac`）。
> **跨边界豁免 81 → 68，共享层成员 57 → 64，`src/server.ts` 零改动。**
> 三批落：`ac36672`（P3-8）/ `9d297d5`（P3-1~P3-6）/ `5b3b9fc`（P3-7）。
>
> **本批的真判据不是「整文件能不能进」，而是「哪一段能进」**：八条里有四条的属主文件本身在拒入名册上
> （理由是承载业务判定，不是四条准入正则），所以一律**只析出纯段**、残壳留原处保持原属主并具名再导出。
>
> **一处对复核方案的再改进（P3-7）**：原方案把行为类搬进共享层（撞判例——现有导出类全是错误类型，
> 且判例文件头明写路由客户端类留 content）；复核给的退路是「消费方本地重建装配」（等于把编排复制第二份）。
> 两者都不好。**采用第三条：把类里被共用的那段无状态纯编排提成函数，类留原处当薄壳** ——
> 判据一份、词表一份、编排一份，共享层里没有行为类，且没有任何行为被复制。
>
> **采用了复核对 P3-4 的修正**：原方案会改组装根 + 一个 automation 文件（复核实测去掉再导出后组装根 5 处连带报错），
> 违反本批「零组装根改动」的承诺；改用其降级形态。
>
> **复核给的一条排期提醒必须记住**：这八条只把「一端是 content 的跨边界条数」从 **29 降到 25**，
> 其余都花在 api↔automation 上。**这批不足以打开提 content 仓的门**，别按「做完就能拆 content」排期。

这一批**代码文件互不重叠**，可分给不同的人；但每一条都要往 `boundaries/ownership-rules.json` 的 `fileOverrides` + `kernel-non-members.json` 的 `kernelRoster.members` 各加一行（`src/kernel/` **没有目录规则**，57 个成员全走 fileOverride，且 `AC-BOUND-03` 对二者做 `deepEqual`）→ **台账合并必须串行**。

| ID | 条 | 从哪析出 → 新 kernel 文件 | 形状要点 | 验证 |
|---|---|---|---|---|
| **P3-1** | 3 | `src/risk/session-limits.ts` 的周历段（`WEEK_ACTIVE_MASK_LEN` / `isValidWeekActiveMask` / `mondayBasedDayIndex` / `isWeekActiveAt` / `msUntilNextActive` + 私有 `HOUR_MS`）→ `src/kernel/week-active-mask.ts` | **只能部分析出**：整文件在 `rejected` 名册（理由是「承载会话预算的业务判定」，**不是四禁**），而 `AC-BOUND-03` 断言拒入路径**不得是已删路径** → 残壳必须留在 `src/risk/` 且保持 automation。**残壳末尾加 `export * from '../kernel/week-active-mask.js'`**，则 `server.ts`（有一处直接 import `isWeekActiveAt`）、`role-dispatcher`、两个 store、两个测试**全部不用动**，只改 3 个 api 消费方 | `typecheck`；`git diff src/server.ts` 为空；`test/weekly-active-window.test.ts` 绿 |
| **P3-2** | 2 | `src/llm/providers.ts` 的身份段（`TextProviderId` / `DEFAULT_TEXT_PROVIDER` / `TEXT_PROVIDER_META` 四字段 / `isKnownProvider` / `normProvider` / `isAllowedCredential`）→ `src/kernel/text-provider-registry.ts` | **`baseUrlDefault` / `baseUrlEnv` 必须留 content**（厂商端点 URL 撞禁令③），`providers.ts` 保留一张局部端点表 + 等值再导出。已核实两个 api 消费方与 `server.ts` **都只读身份字段**（`server.ts` 走 `resolveProviderBaseUrl(id)` 函数），所以 `server.ts` 一行不用改。照抄已落地判例 `src/kernel/image-provider-registry.ts` | `typecheck`；`panel/version.ts` 两行 import 并排都指 kernel（图片/文本厂商表终于对称） |
| **P3-3** | 1 | `src/hot-lead/heat-velocity.ts` 的 `HotLeadGateConfig` + `DEFAULT_HOT_LEAD_GATE_CONFIG` → `src/kernel/hot-lead-gate-config.ts` | `parsePublishedHoursAgo` / `heatVelocity` / 布尔过滤闸**留 automation**（「什么算热帖」是业务判定，整文件搬会与 session-limits 同理被拒） | `typecheck` |
| **P3-4** | 1 | `src/risk/ownership.ts` 的 `ClaimExecutionTargetResult` + `AccountOwnershipPort` → `src/kernel/account-ownership-port.ts` | **放 kernel 不放 api**——automation 的握手路径也要持这个接口，放 api 会造 automation→api 反向边。同批把 `import-exemptions.json` 那条的 `eliminatedBy` 结清（该条 note 早写好了消除路径） | `typecheck`；豁免条目结清 |
| **P3-5** | 2 | `src/config/mirror-stop-work.ts` 的 `CONFIG_MIRROR_STALE_REASON` + `PERSONA_UNAVAILABLE_REASON` → `src/kernel/config-stop-work-reasons.ts` | 整文件进不了 kernel（模块级 `ReadonlySet<string> = new Set([...])`——**类型标注救不了它**，门禁正则 `[^=\n]*` 会把标注整段吃掉；且它自己 import 两个 api 文件）。**只做「原位再导出」不消边**，必须同批把 `comment-scheduler.ts` / `worker.ts` 的 import repoint 到 kernel | `typecheck`；`grep -n "mirror-stop-work" src/comment-agent/ src/delegated-task/` 零命中 |
| **P3-6** | 1 | `src/cache/curated-content-store.ts` 的 `normalizeTextCardTranscription` **+ 5 个私有 helper + 1 个常量** → 新建 `src/kernel/text-card-transcription.ts` | **原稿漏了 `isTextCardTranscriptionCardStatus`**（被主函数调用），按原稿那份 4-helper 清单搬**编译不过**。**别并进 `kernel/curated-content-types.ts`**——那是 265 行纯类型文件，塞运行时函数会让它从 type-only 变成有 runtime 产物。属主文件的 3 个通用 helper 有大量本地调用，import 回来、**不要复制**。这条正是 `dbb227e` 自己登记的 residual，是补账不是新账 | `typecheck`；`grep -c "cleanOptionalString" src/cache/curated-content-store.ts` 仍为原值（说明是 import 回来不是复制） |
| **P3-7** | 1 | `src/publish-agent/prompts.ts` 的 `BANNED_PHRASES` → `src/kernel/ai-flavor-phrases.ts`；`src/publish-agent/post-processor.ts` 主体 → `src/kernel/ai-flavor-post-processor.ts` | 两个新文件（原文件卡在「值导入 content 的 prompts.ts」）。**消费方 `comment-de-ai-flavor.ts` 必须 repoint 到 kernel**——只把原文件留成 shim 的话，automation 仍在导入一个 content 文件，**这条边根本没消掉、只是换了马甲**。注意 `BANNED_PHRASES` 另有 4 个消费方，且 prompts.ts 注释明写「后处理与 prompt 共用同一份」，拆仓后靠双方都从 kernel 取来维持 | `typecheck`；`grep -rn "publish-agent/post-processor" src/agents/` 零命中 |
| **P3-8** | 2 | `src/interactions/reply-config.ts` 的 5 个纯函数 + 私有 helper → **追加进已有成员 `src/kernel/interaction-reply-contract.ts`**（**无花名册变更** ✅） | 需一次等价重写：5 个模块级 `new Set`（`VARIABLE_SET` / `HARD_RISK_SET` / `INTENTS` / `MESSAGE_TYPES` / `RISK_TAG_SET`）改写成对 kernel 已有常量数组的 `includes`（元素数 3~18，无可观测差异）。`validateFinalReplyText` **已经在 kernel**，本地那行只是再导出 | `typecheck`；`npm test -- interactions` 全绿（**这条我没跑过等价性测试，见 §7**） |

**P3-9 · 发布草稿契约（并入 Phase 4 的发布链工作项，见 P4-5）**：`DispatchDraft` / `RefineDraftPatch` / `RefineDraftSelection` / `EditDraftReason` / `EditDraftResult` / `RefineDraftResult` / `ScheduledPublishRecord` 被 automation 与 content 两路同时要 → 单一落点 `src/kernel/publish-draft-contract.ts`，一次搬完。

---

### Phase 4 — 端口注入（29 条，B）🔒 ✅ **全 29 条一次落**

> **落地记录（2026-07-26）**：`aidcp-cloud` master `77e58c4`，已部署 dev、七个仓/包已同步。
> **跨边界豁免 39 → 10**，棘轮 `raises` 仍为空。共享层成员 72 → 77。
> typecheck 0 / acceptance 118·0 / 全量 3330 pass 0 fail 10 skip。
>
> **最有结构意义的一条**：`automation→api`（10）、`content→api`（3）、`api→content`（6）
> **三个方向整体归零**。剩余 10 条全是本轮范围外、基线里本就存在的。
> **「一端是 content」的边 20 → 9 —— 这是提 content 仓的准入取值。**
>
> 本批是唯一大量触碰组装根的一批（15 处装配、66 增 11 删）；四个禁改文件零改动（已自证）。
>
> **复核驳回两条，理由都是「两份计划给同一个符号造了两个家」**：一份要在消费方就地写端口而另一份
> 已在共享层建了家（同一形状两个可独立漂移的声明，**没有任何机械手段会发现它们分叉**）；
> 两份各自为三个上限常量选了不同落点（合并进已有成员，省掉一个新文件与一对台账条目）。
>
> **六处修正**，其中三处是「计划说的数不对，以当场跑为准」。另有一处必须记住的性质：
> 某个回落构造在**生产链路上真会被走到**，改后经注入的闸读陈旧度、而闸在组装根已接线 ⇒ 生产行为不变；
> 但在「装了事实源却没注入闸」的测试形态下语义会变（全量无一依赖该形态）。
>
> **把抛错改成结果型返回那处，复核没只信桩测试**：接真外观跑了三种输入，两种原因仍逐一可分、
> 对外文案逐字未变。
>
> **新增一道类型级漂移闸**，理由是一处真缺口：面板写入外观与人设生成器这两条依赖**在组装根里根本没接线**，
> 编译器不会替它们在装配处校验一次，改签名就静默漂移。已反向验证。
>
> **复核明确未验的五项**（已入 backlog 簇 60 精神，落地前后须真机确认）：全部运行期/真机验证未做；
> 停手闸在真实基础设施故障下是否照常触发；发布台账注入后能否真连库探到两张表；人设向导主链路；
> **以及最要紧的一条——拆仓后这些端口的契约保真在单仓态根本验不了**，
> `test/server-startup-order.test.ts` 那条装配守卫**必须跟着复制到 automation 仓并指向它自己的组合根**，
> 否则守卫在拆仓当天蒸发（已写进该测试的注释）。

**P4-1 · `handler.ts` 依赖面一次做完（5 条）**
`src/comm/handler.ts` 有 **8 簇**指向它（其中 qwen 那 2 条已在 P0-1 做掉），**必须一个人一次改完**，否则反复冲突。剩余 5 条各自的形状：

| 符号 | 目标 | 形状 |
|---|---|---|
| `PanelPersonaConfig` | `panel/types.ts` | handler 本来就写 `Pick<...,'setPersona'>` → kernel 新建 `PersonaWritePort { setPersona(accountId, persona, updatedBy): Promise<PersonaSetResult> }`（`PersonaSetResult` 是纯联合，一并析出）。同一端口顺手掐掉 api 内 `account-persona-service.ts` 的同型用法 |
| `PersonaGenerator` | `agents/persona-generator.ts`（content，调 LLM，三重不可入 kernel） | handler 只用 `Pick<...,'generate'>` → kernel `PersonaGeneratorPort` + 搬 `PersonaGenerateInput` / `PersonaGenerateOutcome` 两个纯类型（`PersonaGeneratorOptions` **不搬**，那是实现侧构造参数） |
| `MAX_PERSONA_KEYWORDS` / `..._LENGTH` / `AccountPersonaService` | `config/account-persona-service.ts` | **四条硬禁全过、卡第五条**（import content 的 persona-generator + api 的 panel/types + soul + automation 的 platform）。两个裸数字常量析出，服务面按 `Pick<...,'generate'|'persist'>` 抽 `AccountPersonaPort` |
| `BotChatStore` | `cache/bot-chat-store.ts`（pg + SQL） | 只用 `getDefaultChat` → kernel `DefaultChatProvider`。**同批把 `roles/publish-executor.ts` 里那份 3 行本地手抄也换掉**——仓里已经有两份手抄，正说明该收口 |
| `AccountStateManager` | `account-state.ts` | **四条硬禁全过、卡第五条**。只调 `pauseStateOf` → 析出 `AccountPauseState` 三态联合 + `AccountPausePort` |

验证：`typecheck`；`grep -n "^import" src/comm/handler.ts | grep -cE "panel/types|agents/persona|account-persona|bot-chat-store|account-state"` 归零；组合根注入点全部靠结构兼容零改动（这五条**不需要改 `server.ts`**）。

**P4-2 · 配置镜像新鲜度与停手闸（4 条）+ 一条必须单独立项的 C**
- 形状：两段拆。① 契约（`MirrorReadState` / `ConfigMirrorFreshnessSource`）并入已有 `src/kernel/config-mirror-bump-types.ts`；② ambient 那一整块（`installedSource` 顶格 `let` + install/isInstalled/mirrorStateOf/isMirrorStale/noteMirrorStaleRefusal）在 automation 仓落成本地实现，**函数体逐字复制**，由 automation 自己的组合根 install。`staleGateMirrors` / `platformActionHalt` / `hasStaleGateMirror` 同法落 automation 本地。三个消费点（`handler.ts` / `role-dispatcher.ts` / `risk-controller.ts`）只改 import 路径，判定逻辑一字不动。
- 前置：`src/config/mirror-registry.ts` 四禁全过、唯一 import 改指 kernel 后自身干净 → 可先整体抬进 kernel（顺序不能反，否则 kernel→业务层反向边当场红）。
- **⚠️ 必须同批登记、本批不修的结构性缺口**：automation 仓的 `src/config/` 只有 6 个文件，`mirror-refresher.ts` / `mirror-registry.ts` / `mirror-version-store.ts` / `mirror-stop-work.ts` **一个都没有**（都判给 api），而全仓唯一的 install 点在 `mirror-refresher.ts`。**照现状拆完、只把 import 改通，automation 进程永远没人安装新鲜度事实源 → `mirrorStateOf` 恒返 `fresh` → 停手闸零日志失效**，正是「静默假成功」红线的形态。改 import 只解决编译。真正的补位是 automation 侧要有自己的版本轮询（跨服务读 api 的 `config_mirror_version`），**属独立 C 项，建议单独立项**。

**P4-3 · 平台 id 归一（5 条）**——见 §4 第 3 条，这是被推翻的 A
- 形状（B）：由 kernel 定「平台归一 / 排期上限查询」窄接口，automation 侧 `registry.ts` 实现，组合根注入给 5 个 api 文件；`type PlatformId` **本就在 kernel**，直接改指即可当场消掉一部分导入面。
- 替代路（若主线认为 B 对一个纯字符串归一函数过重）：走控制仓 change 修 §4.7 / §9 定稿 + 回写 `kernelRoster`——该片段**机械上确实够格**，挡它的是治理裁决不是四禁。**这条只能由主线做**（必然要改 `boundaries/*.json`）。
- 同批必改一处注释：`src/kernel/platform-types.ts` 文件头把 `normalizePlatformId` 与读表函数一并归为「留 registry.ts」——那句**对它是事实错误**（它不读表），不改会让下一个人按注释把这条边加回来。

**P4-4 ~ P4-14（其余 20 条，逐条形状）**

| ID | 条 | 消费方 → 目标 | 形状 | `server.ts`? |
|---|---|---|---|---|
| P4-4 | 3 | `role-config-facade` / `category-config-facade` → `llm/index.ts` + `cover-form-sensor.ts` | ① Deps 加 `thinkingOnAvailable(provider, model)`；② `probeModel` 改**诚实结果型** `Promise<{ok:true}｜{ok:false;reason:'provider_key_missing'｜'model_unavailable'}>`，`instanceof ProviderKeyMissingError` 的分类挪到组合根闭包（外观内两处 if 随之删，对外 reason 串逐字不变）；③ 加 `getVisionModel` / `getVisionProvider`。两个外观本来就是 8 项闭包注入形态，加项零新概念 | 🔒 三处各补一行 |
| P4-5 | 5 | 发布链一把梭：`publish-log-store` schema 端口(1) + `publish-dispatcher`(1) + `scheduled-publish-reconciler`(1) + `draft-refinement-worker`(1) + `client-auth-server → draft-refinement`(1) | 新建 `src/kernel/publish-draft-contract.ts`（`DispatchDraft` / `RefineDraft*` / `ScheduledPublishRecord` / `EditDraft*`）+ 三个窄端口：`ScheduledPublishStore`（3 方法）、`DraftRefinementDrafts`（2 方法）、`DraftRefinementReadWritePort`（4 方法）。schema 那条：`publish-log-store` 是 17 个 schema 消费方里**唯一一个 api**，同层的 `content-schedule-store` 早就改成注入 kernel 的 `SchemaEnsurer` 了——照它抄，kernel 契约文件补一个 `SchemaProber` 类型 | 🔒 一处构造补两项 |
| P4-6 | 1 | `content-schedule-store` → `platform/index.ts` | kernel 的 `platform-types.ts` 末尾加 `ScheduledAutomationCatalogReader`（`normalizeForCatalog` / `availableActions` / `declarationsFor`，未知平台返 `null` 替掉今天的 try/catch fail-closed，语义逐字不变）。返回类型三个**已全在 kernel**。**保持同步方法**——三处在行映射热路径，改 Promise 会污染大片调用链；注册表是静态源码数据，拆进程按启动期快照注入 | 🔒 一行 |
| P4-7 | 2 | `role-prompt-preview` → `agents/base-role.ts` + `prompts-preview.ts` | ① 本地声明 `PreviewableRole { readonly roleName: string }`（全文只读 `.roleName`，预览能力早就用结构化守卫判定）；② 两张 roleId→构造函数表改由 options 注入，表缺失时走已有的「暂不支持预览」诚实分支 | 🔒 一行 |
| P4-8 | 1 | `account-persona-service` → `agents/persona-generator.ts` | 最省一刀：就地把 `Pick<PersonaGenerator,'generate'>` 展开成显式结构 | 否 |
| P4-9 | 1 | `first-post-onboarding-coordinator` → `first-post-onboarding-store.ts` | 就地展开成三方法显式端口（`claim`/`release`/`complete`，签名全是 `(accountId, sourceId[, reason]) => Promise<boolean>`，零 pg 泄漏）。只有一个消费方，**进 kernel 属过度设计** | 否（结构兼容） |
| P4-10 | 1 | `agents/concept-extractor-role` → `platform/registry.ts` 的 `XHS_COMMENT_PROFILE` | `platformProfile` 由可选改必填、删兜底；`role-dispatcher` 的工厂 options 加该字段。**behavior-zero 已核链路**：dispatcher 的 `commonOptions` 早就在传 `commentProfileForPlatform(...)`，且无平台退化路径解析出来**就是同一个对象**——那个 `?? XHS_COMMENT_PROFILE` 生产上从没被走到过，只有测试桩在用 | 否（改 role-dispatcher） |
| P4-11 | 1 | `agents/persona-generator` → `soul/index.ts` | kernel 新建 `SoulCodec { serialize; parse }` + api 侧 3 行实现。**`soul/loader.ts` 进不了 kernel**（三个模块级 `new Set` 都在 `loadSoulFromValue` 的调用路径上，不是能绕开的边角；另有 `node:fs` + `readFileSync`）；`serialize.ts` 倒是四门全过，但本批没有第二个消费方，按 YAGNI 不动 | 🔒 一行（构造补 `soulCodec`） |

---

### Phase 5 — 大件（12 条）

**P5-1 · 面板写风控 → 跨进程（1 条，C）🔒 ✅ 用户已拍板：走异步（2026-07-25）**

> **裁定：取 (a) 异步 outbox 路线。** 即用已建好但从未接线的风控命令 outbox，
> 后台的两个写接口**降级为「已受理」+ 命令 id**，由 console 轮询真态。
>
> **这条裁定带一条不可省的连带要求**：接口的**返回形状必须跟着改**，MUST NOT 保留今天那个
> 「写后真态」结构（当前态 / 变更前态 / 是否变更）。outbox 是异步 at-least-once，命令入队时
> 那三个字段**根本还不知道**，照原样返回就是凭空编一个乐观回显 —— 正撞本仓头号红线
> 「MUST NOT 静默假成功」，而且是最坏的一种：操作员在界面上看到「已改为受限」，
> 实际命令还在队列里、甚至可能失败，**没有任何地方会告诉他**。
>
> 因此本条的完成判据有三项，缺一不可：
> 1. 云端写接口返回 `{ accepted: true, commandId }`（或等价形态），**不含任何伪造的状态字段**；
> 2. console 侧改为按 `commandId` 轮询真态，并在**未收敛期间显式显示「处理中」**，
>    MUST NOT 乐观地先把界面切到目标态；
> 3. 命令**失败**时 console 要能看见失败原因 —— 异步化最容易丢的就是这一条。
>
> 风控状态机本身**一个字节都不碰**（`RiskSignalKind` 按 P2-6 的办法在面板侧本地声明三个运营态取值）。
> 「账号风控最终状态只由云端单写」这条铁律不受影响：单写者仍是自动化域的风控控制器，
> 异步化只改变**命令怎么送达它**，不改变谁有权写。

---

<details><summary>原始两条备选（已裁定，留档）</summary>

- 现状：`panel-server` 三个调用点——读 `effectiveQuotas().day`、**写** `getState() + applySignal()`、**写** `setQuotaLevel()`。CLAUDE §2 铁律「账号风控最终状态只由云端 `RiskController` 单写」，拆进程后单写者物理落在 automation，api 侧不能持有该类。
- 机件已建好但**从没接线**：`src/transport/risk-read-http.ts`（读端口，已被 `server.ts` 使用）、`src/transport/risk-command-outbox.ts`（写命令 outbox，**全仓 grep 除自身外零引用**）。
- 读侧：`riskRegistry.getController()` 换成注入 kernel 的 `RiskReadPort`。
- 写侧：**必须同批决定并写死，二选一**——outbox 是异步 at-least-once，而这两个接口今天**同步返回写后真态** `{state, statusBefore, changed}`，照搬会变成乐观回显，**正撞「MUST NOT 静默假成功」红线**：
  - (a) 接口降级 202 + 命令 id，console 轮询真态；
  - (b) 不用 outbox，照 `risk-read-http.ts` 的手法补 `src/kernel/risk-admin-types.ts`（写端口）+ `src/transport/risk-admin-http.ts`（同步内部 HTTP），保住同步回显。
- `RiskSignalKind` 按 P2-6 的办法本地声明，**风控状态机不碰**。

</details>

**P5-2 · 4 个 content 角色脱离 `BaseRole`（8 条，B）🔒 本批唯一 effort=大**
- 为什么不是 A：`base-role.ts` 在 `rejected` 名册；机械上 ③ 命中（**错误提示字符串 `` `${this.roleName} 需要 LlmClient` `` ——门禁只 `stripTsComments`、不剥字符串字面量**，改文案即可消，是次要伤），**真正终局的是第 ⑤ 条**——它 import `event-bus/index.ts` 与 `event-bus/types.ts`，两者都在拒入名册且是终局裁决，而它的整个公开面（`roleName: RoleName` / `eventBus: EventBus` / `emit<K extends keyof RoleEventMap>`）就是由这两者定型的。摘掉这两个 import，这个类就没有存在理由。
- 三个化简前提已实测：四个角色**只订阅、从不 emit**；合计只用 3 个事件名（`note.detail.arrived` / `note.image_snapshot.arrived` / `comment_like.confirmed`）；`valuable-comment-archivist` 连 soul / LLM 都不用。→ 端口可以做得很窄，且拆进程后是**单向**投递、不需要反向通道。
- 形状：① kernel 新建 `RoleRuntime`（`subscribe` / `soul` / `complete` / `log`）+ `RegisteredRole`；② content 侧新建 `content-role-base.ts`，把样板逐字搬来、依赖改注入、`roleName` 从 `RoleName` 降为 `string`；③ 四个角色改继承、订阅点改走 `runtime.subscribe`；④ `role-dispatcher` 的 `RoleFactory` 返回类型改 `RegisteredRole` + 加 5 行 `EventBusRoleRuntime` 适配器（`commonOptions` 已带 eventBus/getSoul/llm/platformProfile）；⑤ `server.ts` 那行 `import type { BaseRole }` 跟着改（工厂体本身不动）。
- **拆进程后的实现换挡红线**：**不能复用** `src/transport/eventbus-outbox-bridge.ts` 的 `panel.event` firehose——那条文件头明写是纯观测流、best-effort、6 小时保留、可截断；这 3 个事件是**承重的**（直接决定精选库落不落库），必须另开承重 topic，照 `curated-content-http.ts` 的 register/Client 范式接线。

**P5-3 · 发布出口角色（3 条，B——但先花十分钟裁归属）**
- **先做零成本的那一步**：`§4.6.3` 把 `roles/publish-executor.ts` 划进「下发执行段 automation」，但该文件自己的头注（change `decouple-publish-generation-from-dispatch` 之后）写的是「**生成候审段的出口角色**……不再驱动边缘指令序列」，副作用只有落库待审稿 + 发审批卡，与已判 api 的 `approval-gatekeeper.ts` 同类；真正的下发段是 `publish-dispatcher.ts`；全仓只有 `server.ts` 与两个测试 import 它。
- 若重判为 content/api：3 条语句**零成本消失**。但**必须同时核算它反向新增的两条 content→automation 边**（`comm/feishu-card-contract.js`、`publish-agent/platform-profile.js`），否则只是把窟窿挪个位置。
- 若归属维持 automation 才走 B：`RoleConfig`（纯配置 DTO、四禁零命中）析出 kernel；`BasePublishRole` 的模板方法（~100 行、无外部依赖）在 automation 侧复制成自有基类；`PipelineContext` 抽窄端口 `PipelineBlackboard { snapshot; write; isAborted }`。
- **MUST NOT** 为省事把 `setTimeout` 从 `base-role` / `pipeline-context` 里抠掉硬塞 kernel——那是超时与中止语义的承重件。

---

### ⛔ 不做：被终局裁决否决，维持豁免（3 条）

`concept-extractor-role.ts` / `curated-note-evaluator.ts` 的 `NoteDetailData` + `concept-store.ts` 的 `ConceptPool` → `src/event-bus/types.ts`。

- `boundaries/kernel-non-members.json` 对该文件的裁决原文：「**不析出、整体维持 automation**」，并明写「`content→automation` 的 27 条 **MUST 全部留豁免并各挂消除 change**」。禁的是「析出」本身，不只是「整体提升」。
- 且 `NoteDetailData` 经 `images?: NoteImagePayload[]` 直挂在 §10.9 终局排除的 `protocol.ts` 上：kernel 直接 import → 第 ⑤ 条硬失败；复制一份 → 造出协议载荷的第二份定义，而两份 `protocol.ts` 的 `Record<MessageType,true>` 穷举**只覆盖消息名、不覆盖 payload interface**，漂移 typecheck 抓不到；砍掉 `images` 字段 → `curated-note-evaluator` 有 7 处实际取用，编译不过。
- 要动必须先推翻 2026-07-22 `cloud-service-boundary-gates` 的裁决并回写 §4.7，且需在 `event-bus/types.ts` 的串行独占窗口内做。**本批不产生任何文件改动。**
- **但必须登记一个隐患**：`ConceptPool.source` 是 `Map<string,string>`，**不可 JSON 序列化**。今天同进程传引用所以没事；拆完仓它变成 content→automation 的 HTTP DTO，Map 序列化后**静默变成 `{}`**——不报错、只让概念池变空、搜索词悄悄退化成种子词。**将来动这条时顺手把 `source` 改成 `Record<string,string>`**（3 个构造点：`concept-store.ts` / `role-dispatcher.ts` / `agents/search-evaluator.ts`），比拆完再改便宜得多。

---

## 4. 核验推翻的 A 判定（本节最有价值）

**17 个「看着像纯契约」的目标里，13 个进不了 kernel。**卡点分五类，其中**两类是四条硬禁之外的**——只查四禁会得出相反结论。

### 4.1 四禁全过，卡在第 ⑤ 条（kernel MUST NOT 导入业务层，无豁免通道）

| 文件 | 四禁 | 卡在哪一行 |
|---|---|---|
| `src/account-state.ts` | **全过** | import `account-store.ts` + `config-mirror-freshness.ts`（均 api） |
| `src/config/account-persona-service.ts` | **全过**（`new Map` 是**实例**字段不是模块级） | import content 的 persona-generator + api 的 panel/types + soul + automation 的 platform |
| `src/publish-agent/publish-scheduler.ts` | **全过**（`claims = new Map` 是类字段） | 一条 **value** import：`PERSONA_UNAVAILABLE_REASON` from `config/mirror-stop-work.ts`（api）。**全批最像纯类型宿主的文件，栽在一个字符串常量上** |
| `src/publish-agent/post-processor.ts` | **全过** | 一条 **value** import：`BANNED_PHRASES` from `prompts.ts`（content） |
| `src/platform/index.ts` | 全过 | 它 `export *` 的 `surface.ts` 有一条**值导入** `UI_DAILY_USAGE_ACTIONS` from `protocol.ts`（automation）。**`export * from` 在模块图里就是一条 import 边** |
| `src/risk/index.ts` | — | barrel `export *` 覆盖 22 个业务模块，连带把 24 条 SQL 和 `risk-state-machine.js` 全拖进来 |

### 4.2 四禁 + 第 ⑤ 条全过，卡在**治理裁决**（机械上够格，是人判挡的）

| 文件/片段 | 机械判定 | 挡它的是什么 |
|---|---|---|
| `src/comm/protocol.ts` | **五条全过**（零 import、全文最干净） | §10.9 终局裁决 + `AC-BOUND-03` 对 `rejected` 逐条断言 → 标 kernel 当场红。理由：进 kernel = 把 §10.9 点名要消除的 6 处 type-only 依赖**就地合法化**，与同节第 2 条互斥；且把协议同步点从五处变六处、新增那处无任何机械检查 |
| `platform/registry.ts` 的 `normalizePlatformId` + 三个 `*_DAILY_CAP_MAX` | **四禁全干净** | §9「平台能力由 automation 单写」+ `rejected` 名册（「不析出纯数据段、整体维持 automation」）+ `kernel/platform-types.ts` 文件头**上一轮已把 `normalizePlatformId` 的位置裁定过** |
| `src/risk/session-limits.ts` | **四禁全干净**（整文件也是） | `rejected` 用的**不是四禁**，是第五条人判「承载会话预算的业务判定」。→ 所以**周历段可以部分析出**（先例：`kernel/writing-language.ts` 的 basis 明写「不是整文件 git mv，是部分析出」），但**残壳必须留**，否则 `rejected` 指向死路径、`AC-BOUND-03` 红 |
| `src/event-bus/types.ts` | 四禁全过（`Map<string,string>` 是**类型标注**，不命中 `= new Map`） | ⑤ 命中 `protocol.ts`；**且「不析出」本身是终局裁决**——连窄析出都禁 |

### 4.3 卡在第 ④ 条，但**命中的不是 `new Set/Map`**（门禁比口头四禁严）

门禁真正的第 ④ 条正则是 `^(?:export\s+)?(?:let|var)\s | ^(?:export\s+)?const\s[^=\n]*=\s*new\s+(?:Map|Set)\b | \bsetInterval\s*\( | \bsetTimeout\s*\( | new\s+Pool\s*\(`。后三支**不锚定行首**。

| 文件 | 真正命中的东西 |
|---|---|
| `src/config-mirror-freshness.ts` | 顶格 `let installedSource`（定稿 §6.4 点名的「模块级可变单例」） |
| `src/cache/curated-content-store.ts` | `new Pool(`（**不是**两处 `new Set`——那两处都在函数体内、缩进） |
| `src/agents/base-role.ts` / `pipeline-context.ts` | 任意位置的 `setTimeout(` |
| `src/comm/captcha-assist.ts` | `setTimeout(...60_000)`；另有三个实例 Map（持租约 + timer），正则抓不到但语义上就是活状态 |
| `src/config/mirror-stop-work.ts` | `const X: ReadonlySet<string> = new Set([...])`——**`ReadonlySet<string>` 类型标注救不了它**，正则的 `[^=\n]*` 把标注整段吃掉 |

### 4.4 卡在第 ③ 条，但命中的是**字符串字面量里的一个词**

门禁只 `stripTsComments`，**不剥字符串字面量**。

- `src/agents/base-role.ts`：`` throw new Error(`${this.roleName} 需要 LlmClient`) `` → `\bLlmClient\b` 命中。
- `src/agents/comment-search-term-generator.ts`：`throw new Error('CommentSearchTermGenerator 需要 LlmClient')` → 同款。
- 反过来：`LlmUsageQuery` / `LlmUsagePayload` / `RoleLlmLike` **都不命中**（正则精确锚 `LlmClient` / `ChatLlmClient` 两个 token，`RoleLlm` 后接 `Like` 无词边界）。现成判例：`kernel/llm-contract.ts` 自己就住着 `LlmCallOpts`。

### 4.5 「类型借用」实为运行时调用（最危险的一类误判）

- `panel/types.ts` + `panel-server.ts` → `captcha-assist.ts` 的 2 条：原判「与协议 6 条同批重抄类型」。**实际 `panel-server` 五处在运行时真调五个方法**——按重抄一刀切会**编译通过、面板验证码协助端点整条失效**。→ 改判 B。

### 4.6 三条通用教训（写给下一个做这件事的人）

1. **kernel 成员 ≠ 住在 `src/kernel/` 目录**（`src/time/shanghai-day.ts` 就在花名册里）。按目录推导会多报不存在的拦截点。（顺带：该文件导出裸 SQL 片段 `SHANGHAI_DAY_START_SQL` 却坐在花名册上，是花名册自身的既存张力，本批不裁。）
2. **新增 kernel 文件必改两份 `boundaries/*.json`**（`AC-BOUND-03` 对 kernel 文件集合与 `kernelRoster.members` 做 `deepEqual`）→ **追加进已是成员的 kernel 文件可完全绕开**。本批 11 条走了这条路（P0-1/P0-2/P0-3/P3-8）。
3. **「原位再导出」不消边**。只把属主文件改成 shim、不 repoint 消费方，那条边原样留着，只是换了个马甲。P3-5 / P3-7 都在这个坑上被核验方点过名。

---

## 5. 触碰禁改文件的簇（只出方案，主线串行落地）

| 禁改文件 | 触碰簇数 | 具体 | 改动量 |
|---|---|---|---|
| `src/server.ts` | **10 簇** | P2-8(删面板 deps 一项) / P4-4(三行) / P4-5(两项) / P4-6(一行) / P4-7(一行) / P4-11(一行 `soulCodec`) / P5-1(风控读写端口) / P5-2(`import type { BaseRole }` 一行) | 每簇 1–3 行，全是装配 |
| `boundaries/*.json` | **10 簇** | P1-1 / P1-2 需**人工加 `fileOverride`**（归属再裁决，refresh 代不了劳）；P2-1/2-2/2-3/2-6/2-7 + P3-1~P3-7 需进 `kernelRoster.members` + `fileOverrides` | 全批 land 时统一跑一次 `boundaries:refresh`，`frozenTotal` 从 **96** 下调 |
| `src/comm/protocol.ts` | **0 字节** | P2-4 重抄到 api contracts / P2-1 `operation` 降裸串 / ⛔ 那 3 条维持豁免 | 不改 |
| `src/event-bus/types.ts` 的 `RoleName` | **0 字节** | P0-4 只改消费方注解；⛔ 3 条正因「不许析出」而维持豁免 | 不改 |
| `src/config/role-catalog.ts` | **0 字节** | P0-1 的 `ThinkingMode` 从 kernel 派生；P0-4 的合同夹具**只读**它 | 不改 |
| `src/risk/risk-state-machine.ts` | **0 字节** | ~~`RiskSignalKind` 在 panel 侧本地声明~~ → 更正：该类型本就在 `risk/types.ts`，随其进 kernel；状态机文件实测零改动 | 不改 |

---

## 6. 可并行分组（直接决定怎么排工）

### 可并行：6 条代码 lane，文件互不重叠

| Lane | 归谁 | 覆盖 | 条数 | 独占的文件 |
|---|---|---|---|---|
| **L1 kernel-append** | 1 人 | P0-1 / P0-2 / P0-3 / P3-8 | 13 | `kernel/llm-contract.ts`、`kernel/writing-language.ts`、`kernel/publish-generation-types.ts`、`kernel/interaction-reply-contract.ts`、`llm/qwen.ts`、`soul/writing-language.ts`、`interactions/*` |
| **L2 panel** | 1 人（**最重的串行 lane**） | P2 全部 | 23 | `panel/types.ts`、`panel/panel-server.ts`、`panel/panel-ws.ts`、`panel/panel-store.ts`、`panel/version.ts`、`risk/types.ts` |
| **L3 handler** | 1 人 | P4-1 + P4-2 | 9 | `comm/handler.ts`、`config-mirror-freshness.ts`、`config/mirror-stop-work.ts`、`config/mirror-registry.ts`、`risk/risk-controller.ts` |
| **L4 publish** | 1 人 | P4-5 + P3-6 + P3-7 | 7 | `publish-agent/publish-log-store.ts`、`publish-dispatcher.ts`、`scheduled-publish-reconciler.ts`、`draft-refinement*`、`cache/curated-content-store.ts`、`publish-agent/prompts.ts`、`post-processor.ts` |
| **L5 kernel-new** | 1–2 人 | P3-1 / P3-2 / P3-3 / P3-4 / P3-5 | 9 | `risk/session-limits.ts`、`llm/providers.ts`、`hot-lead/heat-velocity.ts`、`risk/ownership.ts`、`config/*-config-facade.ts` |
| **L6 角色/编排** | 1 人 | P5-2 + P4-10 | 9 | `agents/base-role.ts`、4 个 content 角色、`orchestrator/role-dispatcher.ts` |

### 必须串行（同一写点，谁都绕不过）

1. **`boundaries/*.json`** — L2 / L4 / L5 / L6 全都要往花名册加条目。**建议：各 lane 只在自己的 change 里记「待加成员清单」，由主线在集成时一次性写台账 + 一次 `boundaries:refresh` + 一次下调 `frozenTotal`**。历史上「攒批归档时 spec-merge 失败 + 漏删一半静默」就是这类。
2. **`src/server.ts`** — 10 簇各 1–3 行，全部由主线在集成窗口串行落。各 lane 在 change 里写清「需要在 server.ts 哪个构造处补哪一项、实参是谁」。
3. **`src/panel/types.ts`** — 6 簇同文件（L2 独占；L3/L4 别碰）。
4. **`src/comm/handler.ts`** — 8 簇同文件（L3 独占；L1 的 qwen 那条已先做完，L3 起步前先 rebase）。
5. **`src/orchestrator/role-dispatcher.ts`** — L3（mirror 两处）与 L6（RoleFactory + platformProfile）都要动 → **建议整体划给 L6，L3 只提供 import 路径清单**。
6. **`src/publish-agent/publish-log-store.ts` / `publish-scheduler.ts`** — L1（P0-3）与 L4 都要动 → **L1 的 P0-3 必须先落、L4 再起**（有先后依赖，不是纯冲突）。

### 依赖顺序（跨 lane 的硬前置）

- **P1（归属再裁决）必须在 L2 的 P2-1 之前或同批**——否则那 3 条反向边裸奔。
- **P0-3 必须在 L4 之前**（同文件 `publish-scheduler.ts`）。
- **P4-2 的 `mirror-registry` 上提 kernel 必须在 stop-work 本地化之前**（顺序反了会造 kernel→业务层反向边，当场红）。
- **P5-1 / P5-2 建议排在最后**（一个要拍板同步/异步语义，一个动角色编排主干）。
- **P5-3 排在最后且先裁归属**——十分钟的归属核对可能省掉整个 effort=大 的工作项。

---

## 7. 诚实：低置信度与未查实项

**未经第二轮核验的判定（单路自证，confidence = medium）** —— 这些条目的四禁核实是各路 sub-agent 自己跑的、没有独立复核，落地前建议主线用真门禁正则（`test/acceptance/module-boundary.test.ts` 的 `KERNEL_ADMISSION_CHECKS`）再跑一遍目标文件：

- automation：P4-1 的五条端口（`PanelPersonaConfig` / `PersonaGenerator` / `account-persona-service` / `BotChatStore` / `AccountStateManager`）、P4-2 的 mirror 三件套、P4-5 的 `publish-log-store` 两条、P5-3 的 `publish-executor` 三条、**P3-8 的 `reply-config` 五个 Set→`includes` 等价重写（我没跑过 `npm test -- interactions` 验证等价性）**。
- api：P4-4 / P4-6 / P4-7 / P4-9 / P5-1 / P2-7（`facebook-publish-media`）/ P2-8。
- content：P5-2 的 `RoleRuntime` 端口设计（形状是 sub-agent 自己拟的，未经二次评审）、P4-9 / P4-10 / P4-11。

**明确未查实的三件事**：

1. **`publish-executor.ts` 的归属是否已被 `decouple-publish-generation-from-dispatch` 取代** —— 我没去控制仓核 §4.6.3 现行文本。这是 P5-3 的前置，十分钟的事，但没做就下结论会白花一份 effort=大 的工。
2. **P5-1 的同步/异步二选一** —— 这是**设计决策不是调查结论**，必须由主线/用户拍板。两条路的代价都写在 P5-1 里了。
3. **`docs/cloud-service-decomposition-proposal.md` 的 §4.6.3 / §4.6.8 / §4.7 现行行号与计数** —— P1 两条与所有新 kernel 成员都要回写这三处，我没打开控制仓定稿核对当前行号与文件计数。

**已知会随时间失效的东西**：本清单所有行号基于 `18a33b7`，HEAD 已到 `b4694df`，我实测 `handler.ts` 已漂 1–2 行。**按符号名定位。**

**另需主线知晓、不属本批但已登记的 5 个隐患**（每条都在对应条目里写清了）：
① `ConceptPool.source` 的 Map 跨进程静默变空；② `FacebookPublishMediaError` 的 `instanceof` 跨进程恒 false；③ 协议重抄的漂移入口（必须配 `test/` 双向断言）；④ automation 侧配置镜像 install 者结构性缺失 → 停手闸零日志失效（**独立 C 项，需单独立项**）；⑤ 删 `RoleName` 注解丢掉的编译期防线（用合同夹具补）。