## Context

评论迁移闩 `pendingMigration` 是一个**单槽**状态：同一时刻最多持有一条已批准评论，等它的导航回执。它被三处写、被两处终局清理，而这五处对「什么时候该清、清了要不要回报」没有统一口径。

现状（按符号定位，行号必漂）：

| 位置 | 行为 | 缺口 |
| --- | --- | --- |
| 武装 | `armMandatoryCommentOutcomeTimer(delivery)` | 第一行 `if (!trace) return`，**普通交付不武装** |
| 消费 | `if (this.pendingMigration && payload.action === 'open_note')` | **先清后判**，无相关性判据 |
| 支线终局 | `expireCommentSubline(noteId)` | 清在途标记与时钟，**不碰闩** |
| 会话终局 | `settlePendingMandatoryCommentAsUnknown(reason)` | 覆盖闩，形态正确 —— **可当模板** |
| 抢占 | `payload.action === 'open_note'` 时清闩（抢占分支） | 与消费分支同族，须一并核 |

**已经守住的红线不要重做**：落地判据 `landed` 要求 `payload.ok === true && surface === 'detail' && payload.noteId === mig.noteId`。已批准的评论**不会**被发到未经证实的页面。本 change 补的是消费准入与生命周期，不是落地判据。

## Goals / Non-Goals

**Goals:**

- 不相关的开帖回执不再吃掉闩、不再制造错误归因。
- 每一次已批准交付都有有界终局，无论有没有免审审批 trace。
- 支线终局与闩终局一致，不再各清一半。
- 每一条终局都有操作员可见的回报 —— 一条已批准的评论没送到，操作员必须知道。

**Non-Goals:**

- 不改落地判据（已守住红线）。
- 不改评论内容生成、审批链、去重台账。
- 不改边缘：**纯云端改动**，边缘对侧无需配合。
- 不把闩从单槽改成队列。今天的并发模型是一个会话一条评论支线，多槽会引入一整套新的匹配与过期语义而没有需求支撑（YAGNI）。

## Decisions

### D1. 清闩必须在判定之后，而不是判定之前加一句判据

这是①的**结构性**修法。今天的形状是「先 `pendingMigration = null`，再算 `landed`」。若只在原地补一句相关性 `if`，写法上很容易变成「先清、发现不相关、再放回去」——那是把一个竞态改成两个（放回去这一步之间可能已经有别的写入），且读起来像是已经修好了。

**做法**：先读闩、先判相关性；不相关 ⇒ **原样返回、闩不动**，交给后续正常路径处理这条回执；相关 ⇒ 才取出并清、再判落地。

### D2. 相关性判据取 noteId 匹配，不取更宽

可选的更宽判据（比如「只要闩存在且这条回执带 detail 观测」）会把另一条笔记的详情导航误认成本次迁移。noteId 是闩里已有的字段、也是落地判据已经在用的字段 —— 用同一个键，两处不会分叉。

**注意不要顺手把落地判据合并进准入**：准入只判「这条回执是不是在说本次迁移的那条笔记」；落地判 `ok` 与观测面。合并会让「相关但导航失败」被当成「不相关」而不清闩 —— 那条已批准评论就永远挂着了。**两者必须分开：相关性决定要不要处理，落地判据决定处理成成功还是失败。**

### D3. 超时武装的条件由「有审批 trace」改为「有已批准交付」

`armMandatoryCommentOutcomeTimer` 的名字与它今天的守卫都绑在免审强制评论上。改法有两种：

- **放宽守卫**（选它）：去掉 `if (!trace) return`，让每一次交付都武装；到期回报时按有无 trace 走各自的上报口径（有 trace 走 `reportMandatoryCommentOutcome`，无 trace 走 `reportApprovedNotDelivered` —— 消费分支里的两条上报路径已经是这个形状，照抄即可，不新造）。
- 新增一个并行定时器：会引入两个定时器互相不知道对方的问题，且到期竞态要另写一套。**否决。**

放宽后函数名与实际职责不符，**须一并改名**（它不再只管 mandatory 那一支）；名字不改会让下一个人按名字判断适用面，正是这次缺口的成因。

### D4. 支线超时复用会话终局那条路径的形态

`settlePendingMandatoryCommentAsUnknown` 已经是正确形态：清定时器 → 有 pending 就回报 → 清两个槽。`expireCommentSubline` 照它补上闩的部分即可，不另造一套。

**顺序要求**：与它同口径 —— **先清态、再发唯一终局事件**（`expireCommentSubline` 现有注释已明写这条理由：避免同步监听器看到仍在途或重复清理）。补闩的清理要落在「清态」那一段里，不能落在 emit 之后。

### D5. 终局必须有操作员回报，且回报口径按有无审批 trace 分

消费分支已有的形态：有 trace ⇒ `reportMandatoryCommentOutcome(mig, 'failed', reason)`；无 trace ⇒ `reportApprovedNotDelivered(mig.noteId, reason)`。**两条都要发的场合与只发一条的场合，照消费分支现有写法**，不在本 change 里重新设计上报语义。

## Risks / Trade-offs

- **[不相关回执改为不清闩后，闩可能挂更久]** 原本一条乱入的回执会「顺手」清掉闩（以错误方式）→ 现在它不清了 → 必须依赖 D3 的超时兜底。**这两条是一个整体，不能只做一半**：只做相关性判据不做超时扩展，会把「错误地清掉」换成「永远不清」，是更糟的形态。tasks 里两者绑在同一段。
- **[改名牵动调用点]** `armMandatoryCommentOutcomeTimer` 与配套的 `clearMandatoryCommentOutcomeTimer` / `mandatoryCommentOutcomeTimer` 是一组 → 一并改名，逐处核对；改名不改行为，与行为改动分成两次提交，便于 review 分辨。
- **[单槽假设]** 若将来一个会话内出现两条并发迁移，单槽会静默丢一条 → 本 change 不做多槽，但**在武装处加一条断言**：武装时若闩已被占，如实回报而不是静默覆盖。这是低成本的诚实兜底，不引入队列。
- **[拆仓期属主]** `role-dispatcher.ts` 归 `automation`，本 change 不跨属主 → 仍须在改动前后各跑一次边界门禁，确认豁免清单未上涨（棘轮只许降）。
- **[热点文件]** `role-dispatcher.ts` 是并行开发的高频文件 → 开工前 `openspec list` 核对有无并行流压着；集成前 `fetch` + rebase。

## Migration Plan

无数据迁移、无协议变更、无部署顺序依赖。纯云端逻辑改动，随 dev 部署生效。

回滚＝还原提交。行为改动与改名分开提交，可分别回滚。

## Open Questions

- 普通交付的超时预算取值：免审那一支用的是 `mandatoryCommentOutcomeTimeoutMs`。普通交付是否沿用同一个值，还是需要一个独立值？倾向沿用（两者等的是同一件事：一条已下发命令的回执），实装时若发现两者的等待面确实不同再拆。
- 抢占分支（`payload.action === 'open_note'` 时清闩的那一处）与消费分支的相关性判据是否应共用一个判定函数：实读后再定，倾向共用，避免两处分叉。
