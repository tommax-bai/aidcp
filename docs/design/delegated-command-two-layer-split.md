# 委托任务 ↔ 命令：分两层的设计

> 状态：设计稿（2026-07-16）。产出方式＝多 agent 编排（4 路坐实现状 → 3 套独立方案 → 3 评委打分 + 对抗评审）。落 openspec change 前的定案文档。
> 触发问题（用户）：「委托任务和命令，是不是应该分两层，委托任务可以调用命令，而不是所有任务都通过委托命令？」

## 0. 一句话结论

**是，应该分两层，方向对。** 但「让精确命令彻底绕开委托层」这一步有一个**相对今天线上态的真实回归**（精确命令会从后台任务列表消失、失去 `/task` 控制动词，并绕开簇 86 刚接的来源会话路由），必须产品拍板、不能静默上。因此推荐**分阶段**：

- **阶段 1（立即、安全、不动可见性）**：让编排层的执行器**调用命令层**（操作员授权路径），而不是自己重新实现一遍。这一步就修掉了发帖丢越权（A）、评论静默失败（B）、并顺手收口免审信任缺口（C），且**精确命令仍留在任务机里、后台照常可见可控**。
- **阶段 2（结构性、产品门控）**：把精确命令的**入口**从委托层前门分流出去（route-around，或抽一层共享执行接口 ActionPort）。这才是「不是所有任务都通过委托」的那一半，它带着可见性权衡，单独决策、单独上。

阶段 1 已经兑现了用户架构直觉的核心——**「委托任务调用命令」**；阶段 2 兑现另一半——**「精确输入不必都走委托建模」**。两步都是「分两层」，只是一个动执行、一个动入口。

---

## 1. 现状：为什么会有这些冲突

今天**所有飞书对外写**都被收口到唯一前门：命令路由 → `actions.delegate()` → 委托服务 → 建 `delegated_tasks` 行 → worker → 执行器。`/publish`、`/comment` 精确命令被解析成任务（来源 `legacy_command`）静默入队；自然语言目标（来源 `feishu`）先出确认卡。

前门只有一个，就逼着委托层把命令本来会做的事（授权策略、触发回执、结果卡）**重新实现一遍**。上一轮审计确认的冲突，根因都在这层「二次实现」跑偏：

- **A（高）发帖丢了操作员越权**：执行器把所有发帖统一走风控强制路径 `triggerDelegated`（`publish-scheduler.ts:386-389`，非 normal / 超额即拒），而老命令走的是越权路径 `triggerManual`（`publish-scheduler.ts:312-332`，第 329-330 行明写「越过风控 canDo + 强制发布（人工授权）」）。同形的 `/comment` 却保住了越权（执行器评论分支 `executors.ts:279-284` 的 `legacySingle → manualOverride`）。**发帖丢、评论没丢**。
- **B（高）评论触发前失败被静默吞**：评论的「人设未绑 / 边端离线 / 联系方式缺 / 非 FB 带 --join / FB 未接线」在异步任务起跑前就早退（`comment-scheduler.ts:376-456`），结果卡永不触发；委托层又按 silent 入队、兜底只认发帖族（`notification.ts:31`）→ 运营零反馈（踩「绝不静默失败」红线）。
- **C（潜伏）结构化入口可自带免审**：客户端/后台/API 建草稿把请求体 `approvalMode` 原样吃进去、不校验（`types.ts:187-208` 无 clamp），非飞书来源又跳确认卡 → 带 `auto_approve` 就两道审批闸全绕过。当前出货界面都硬编码 'review' 没触发，是埋雷。

一句话：**当初想要的是「策略统一」（统一准入、诚实回执、绝不静默假成功），却做成了「代码路径统一」，逼编排层重造执行层。** 分层就是把这两件事拆开。

---

## 2. 坐实现状：分层必须尊重的约束（带 文件:行）

四路 grounding 钉下的关键约束，任何方案都不能违背：

**执行层已就绪、可复用**
- 老直连处理器 `runPublish`/`runComment`（`commands.ts:383-425`）+ 其闭包 `actions.publish`/`actions.comment`（`server.ts:1607/1643`）**还活着、只是死代码**（`actions.delegate` 恒接线，`commands.ts:337/339` 永走 delegate 分支）。它们读真实终态、映射诚实颜色——**可直接复用**。
- 发帖并发正确性依赖**零 await 原子 claim**：任何新入口都必须经 `doTrigger/tryClaim`（`publish-scheduler.ts:171-184`）。已验证：`triggerManual` 也走这条 claim，**所以直连命令与自动任务在同一把权威锁上串行、不会撞车**。评论侧是每账号 `running` 集（`comment-scheduler.ts:356/395`，有历史 TOCTOU 但本改动不碰、不放大）。
- 越权是**入口编码**的：`triggerManual` = 不查风控；`triggerDelegated` = 查。想要越权就得**调 `triggerManual`**，没有参数开关（现状）。人审在两条路径下都强制（AC-PUB 红线，`publish-scheduler.ts:330-331`）——**越权只越风控/配额，绝不越人审**。

**编排层独有、且有东西依赖它**
- 确认卡纯由来源决定：`source!=='feishu'` 自动确认跳卡（`service.ts:216-222`）。分层必须守：精确/结构化＝不出卡，自然语言＝出卡。
- 成功计数只认平台已验证的写（`store.ts:459`、`types.ts:225-239`）；红线：精确命令路径也**绝不能拿「已下发」当成功**。
- **后台可见性完全由 `delegated_tasks` 表撑**（`panel-server.ts:418-478`）。**今天精确命令也建行、因此在后台可见、可按 id 暂停/取消**（`server.ts:1580-1590` 的 autoQueued 分支）。**不建行 = 后台看不见、`/task` 控制动词失效。**
- 任务级 dedup 是非终态上的部分唯一索引 + 23505 归并（`store.ts:65-67, 307-317`），做的是「~20s 内重复推送折叠成一条」。绕开它 = 退化成「串行两发、第二发拿 already_running」。
- 任务级 `hasActiveOwnership`（`worker.ts:92`）是 **advisory**；真正的锁是调度器 claim。

**不碰热点单写文件**：两份 protocol.ts、command-bridge 动作映射、RoleName 注册、risk-state-machine.ts——四路确认本改动全链**都不进**（风控只经注入的只读端口消费、绝不写）。✅

---

## 3. 目标架构：两层

**下层 · 命令 / 执行** —— 把一件具体的写操作，在一个账号上，现在就做掉；按「操作员授权」或「受管（风控强制）」二选一；如实回卡（同步触发回执 + 异步结果/审批卡两条独立通道）。它拥有：授权策略、原子 claim 并发、真正的触发、诚实回执、终态观测的交付。

**上层 · 委托 / 编排** —— 把一个模糊目标翻成一串具体写操作；出确认卡、按目标数量重试、守截止/排期、任务级 dedup、暂停/取消控制动词。它**调用下层**、只**消费**终态观测做记账，**绝不重发下层已发的卡**。

「委托调用命令」有两种落法，对应用户那句话的两半：

| | 落法 | 兑现的那半 | 代价 |
|---|---|---|---|
| **执行侧** | 编排器的执行器改**调命令层的操作员授权路径**（而非平行的 `triggerDelegated` 二次实现） | 「委托任务调用命令」 | 无（不动入口、不动可见性） |
| **入口侧** | 精确命令的**入口**从委托前门分流，不再建任务 | 「不是所有任务都通过委托」 | **可见性回归 + 簇86 碰撞 + dedup 退化**（见 §4） |

关键洞察：**执行侧的落法本身就修掉了 A/B/C 的全部 bug，且零可见性代价。** 入口侧才是带权衡的那一步。所以把它们拆成两个阶段。

---

## 4. 入口侧 route-around 的真实代价（必须产品拍板）

这是评审团挖出、**修正我此前口径**的一点：route-around 不是「恢复 funnel 之前的行为」，而是**相对今天线上态的回归**——因为 funnel 已经在生产跑了很久：

1. **后台可见性回归**：今天精确 `/publish`·`/comment` 都建任务行、在后台任务列表可见、可暂停取消。绕开后它们**从列表消失、失去 `/task` 控制动词**。运营可能已经依赖这个。
2. **和簇 86 直接碰撞**：`restore-delegated-command-card-origin-chat`（`f248a1e`）刚投入把命令触发的发帖审批/失败卡**经委托层**路由回来源会话。route-around 让精确命令**整层绕过**——来源会话路由改由直连路径自己的 `manualApprovalChatId = sourceChatId`（`server.ts:1607`）+ ws-receiver 的 `message.chat_id` 承担。**能保住，但迁移必须实测验证卡还落对会话**。
3. **dedup 从「合并」退成「串行」**：飞书 ~20s 重推，今天折叠成一条；绕开后变成两发、第二发拿诚实的 `already_running` 卡。对「操作员说做就做」的精确命令，这其实是**更正确**的语义，但仍是相对今天的改变，要承认、不能静默。

**并发不回归**（已验证）：直连命令与自动任务在调度器同一把原子锁上串行（`publish-scheduler.ts:171-184`），不撞车。keep-open 租约也不受影响（评论租约用调度器内部本地 `lease.taskId`、非委托任务 id，`comment-scheduler.ts:806-827`）。

**结论**：可见性/控制动词是**能力取舍、不是正确性 bug**（发帖仍有可查的 publish_log、评论仍发结果卡、要管理用自然语言形式）。但必须**显式让运营签字**，或用一条轻量 `command_log` 行补可见性——**二择一，不能以「恢复旧行为」的说法蒙混上线**。

---

## 5. 推荐：分阶段迁移

### 阶段 1 —— 修 bug + 兑现「委托调用命令」（立即、安全、不动可见性）

三个小改动，互相独立、可分别上：

1. **A 修复｜执行器精确类走操作员授权**：执行器发帖分支（`executors.ts:301-312`）对「精确类」（`source==='legacy_command' && manualSingle`）改调命令层的**操作员授权路径**（复用 `triggerManual`，或给执行端口加一个 `authority: 'operator'|'governed'` 选择器、精确类置 operator）。**自然语言 + 结构化 edge/console/api 一律留在受管 `triggerDelegated`**——这是硬边界（见 §6 砍项）。这就是「编排器调用命令」，与评论分支 `legacySingle → manualOverride` 对称。任务行照建，**后台可见性零损失**。
2. **B 修复｜兜底扩到评论族（fallback-only）**：把 `delegatedPublishOutcomeReceipt`（`notification.ts:30-31`）从「只发帖族」放宽为**评论族兜底**——仅当 worker 的 `onTaskUpdated` 终态没有别的卡时补发（fallback-only，绝不与结果卡双发）。这把 B 在**精确和自然语言两侧**都补上。
3. **C 修复｜approvalMode clamp（单函数、正交）**：在 `validateDelegatedTaskIntent`（`types.ts:187-208`）或 `createDraft` 落库前，把**不可信客户端体**（panel/edge draft）的 `auto_approve` 夹成 'review'；**白名单服务端自建的洗稿调用**（已传 'review'，`panel-server.ts:2351/2382`）。一处收口审批授权，不耦合 A/B 路由。

阶段 1 出货前的**硬门**：重跑验收，证明操作员 `/publish` 越风控/配额但**人审仍强制**（AC-PUB 绿，`publish-scheduler.ts:330-331`）；补三条测试——路由断言、AC-PUB 仍绿、评论 gate-fail → 非静默 CommandResult。

### 阶段 2 —— 入口侧分流（结构性、产品门控）

在阶段 1 之后、且**运营对可见性取舍签字之后**再做，二选一：

- **2a 极简 route-around**：删 `commands.ts:337/339` 两个三元，精确 slash 直达已复活的 `runPublish`/`runComment` → 调度器操作员路径。零新文件、trivially 可回滚。
- **2b 共享 ActionPort**：抽一层 `ActionPort.execute`，直连入口与编排 worker 共用；顺带用**一张归一表**消灭 Finding E 那类「两处状态映射漂移」（`executors.ts:148-150` vs `server.ts:1615-1638`）。**仅当真有第二个消费者（E 消解/复用）来撑，才值得建**——否则就是为 A/B 造超前抽象（见 §6）。

评委共识：**2a 是可立即上的第一步，2b 是可选演进、不是前置**。若走 route-around，必须同时：实测来源会话卡仍落对（簇86）、给可见性回归产品签字或补 `command_log`、注解/删除随之变死的 `legacySingle` 分支（`executors.ts:279-284`）与 parser 的 slash→legacy_command 打标（`parser.ts:119/137`）——**别留 split-brain 死代码**（CLAUDE.md 反复的教训）。

### 明确不做（砍掉的过度设计）

- ❌ **为 A/B 造 3 文件 ActionPort/ExecutionPort 模块**：两行就能证明精确命令够得着操作员授权；端口的真正收益（E 归一、候选控制收口）在 A/B 范围外，该由 E/复用**自己**的 change 立项，别塞进 A/B。
- ❌ **把候选控制两条直连审批路由塞进新端口子分支**：它们已共享 `publish-<recordId>` 信号契约、能跑；强塞徒增「分叉信号路径」风险。保持原状。
- ❌ **把操作员越权扩到自然语言 + 结构化发帖**（Design 3 的越界）：那会让 edge 客户端的结构化发帖也跳过风控闸——**风控回归**。越权**只给精确命令类**。
- ❌ **现在就建 `command_log` 补可见性**：等运营真提出需要再补，别先造并行台账。
- ⏸ **Finding D（`worker.ts:280-291` 的 expireDueTasks 绕过 onTaskUpdated）、Finding E（submitted 当失败）**：各自单列 follow-up change，**不并进 A/B**。分层澄清了它们的归属边界，但不替它们修。「A/B 做完」≠「五个全做完」。

---

## 6. 五条不变量的落位（分层后每条只在一层、结构上不可违背）

| 不变量 | 落在哪层 | 为什么不可违背 |
|---|---|---|
| 单一授权/准入闸 | 命令路由入口 `isChatAuthorized`（`commands.ts:307/318`），**在分流之前** | 分流不动它，仍是最外层边界 |
| 诚实回执（绝不静默丢卡/假成功） | 执行层拥有回执；编排层只记账不重发卡 | 阶段 1 的 B 兜底扩到评论族后，任一终态都有卡兜底 |
| 风控最终态单写 | RiskController（只读端口消费，`publish-scheduler.ts:53-56/91`） | 本改动只**读**风控、从不写；越权=跳过读，不改写状态 |
| 单账号单边端并发安全 | 调度器原子 claim（`publish-scheduler.ts:171-184` / 评论 running 集） | 直连命令与任务同锁串行，已验证不撞车 |
| 操作员期望的幂等 | 精确命令＝「说做就做」串行；任务＝分钟桶合并 | 语义分层清晰：精确不承诺合并、任务承诺 |

---

## 7. 拆 change 建议

| # | change | 范围 | 依赖/门控 | 修 |
|---|---|---|---|---|
| **1** | `delegated-executor-operator-authority-parity` | 执行器精确发帖类走操作员授权 + 评论族兜底扩容 | 无（阶段 1 核心，先上） | **A、B** |
| **2** | `delegated-approvalmode-clamp` | 不可信来源 approvalMode 夹成 review | 无（正交、可并行） | **C** |
| **3** | `precise-command-entry-split`（阶段 2） | 入口 route-around 或 ActionPort | **产品签字（可见性）** + 实测簇86 卡落对 | 结构性收口，消灭二次实现 |
| F1 | `delegated-deadline-terminal-card`（follow-up） | expireDueTasks 走 onTaskUpdated + 待审豁免截止 | 独立 | D |
| F2 | `delegated-submitted-honesty`（follow-up） | submitted 降级为「已提交待确认」 | 独立 | E |

Change 1、2 建议先做（对运营有实感、零可见性代价）；3 待你拍板可见性后再定 2a/2b。真机验收归簇 86。

---

## 8. 需要你拍板的一个产品决定

阶段 2 的前提是回答一句话：**运营现在是否依赖「在后台任务列表里看到并管理精确 `/publish`·`/comment`」？**

- **依赖** → 阶段 2 走「精确命令仍建一条轻量记录以保可见」，或干脆只做阶段 1、不做 route-around（阶段 1 已修完 A/B/C）。
- **不依赖** → 阶段 2 走 2a 极简 route-around，精确命令回归 fire-and-forget（靠 publish_log + 结果卡观测），并给可见性回归签字。

在你回答前，我建议**先落 change 1 + 2**——它们无论上面怎么选都成立、且立刻修掉运营能直接感受到的两个高危 bug。
