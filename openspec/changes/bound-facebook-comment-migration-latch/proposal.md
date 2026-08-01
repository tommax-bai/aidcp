## Why

Facebook 的评论迁移是两步：先发一条「导航用途开帖」，等它的动作回执确认落在目标详情页，才发评论。中间那段等待由一个**迁移闩**（`pendingMigration`，`aidcp-cloud/src/orchestrator/role-dispatcher.ts`）持有一条**已经批准过的评论**。这个闩今天有三个生命周期缺口，三个都会让一条已批准的评论消失，且其中两个会把消失归因到错的地方。

**① 消费准入没有相关性判据。** 进入分支的条件只有「闩存在 + 动作是开帖」，随后**第一件事就是清闩**，之后才去判是否落地：

```
if (this.pendingMigration && payload.action === 'open_note') {
  const mig = this.pendingMigration;
  this.pendingMigration = null;        // ← 无条件清，判定在后面
  ...
  const landed = payload.ok === true && echoedSurface === 'detail'
    && !!payload.noteId && payload.noteId === mig.noteId;
```

于是一条**与本次迁移无关**的开帖回执（另一条笔记、另一次导航）会：清掉闩 ⇒ 这条已批准的评论再也发不出去；落进 else 分支 ⇒ **把失败归到那条不相干的回执带来的原因上**，回报操作员、emit 失败终局。操作员看到的是「迁移导航失败，原因 X」，而 X 来自一件与它无关的事。

**必须说清没坏的那一半**：落地判据本身守住了红线 —— `landed` 要求 noteId 相等且观测面为详情页，所以**已批准的评论绝不会被发到未经证实的页面上**。缺的不是安全，是**相关性**：危害方向是「诚实但归因错误的失败」，不是假成功。

**② 超时清闩只武装了一支。** `armMandatoryCommentOutcomeTimer` 第一行就是 `const trace = this.mandatoryApprovalTrace(delivery); if (!trace) return;` —— 没有免审强制评论的审批 trace 就直接返回。也就是说**普通的已批准交付根本没有超时清闩**：边缘一直不回执，闩就一直挂着，评论支线的时钟不解冻，而操作员**收不到任何「已批准未送达」**。

**③ 支线超时与闩各清一半。** 评论支线的硬超时（`expireCommentSubline`）清掉在途标记、解冻时钟、发 `comment.skipped`，但**不碰 `pendingMigration`**。于是支线已经宣告结束，闩还挂在那里 —— 下一条开帖回执会撞上缺口①，把一条已经被判定超时的迁移，用一条不相干的回执再"失败"一次。

**为什么是现在单独立项**：这三条原本混在 `restore-native-facebook-residual-parity` 里，2026-07-31 用户按「Rust 迁移碰过它没有」的判据裁定摘出（`docs/cloud-orchestration-residuals-descoped-2026-07-31.md` A 节）—— 它们是云端编排层自己的老毛病，与 Native 迁移无关，混在迁移修复里会让那条线永远收不了口。摘出**零开工**，缺陷仍在。

## What Changes

- **闩的消费加相关性判据**：进入迁移分支须额外满足「该回执与武装这次闩的那次迁移相关联」（至少 noteId 匹配）。不相关的开帖回执 MUST NOT 进入该分支、MUST NOT 清闩、MUST NOT 产生本次迁移的失败归因。
- **清闩的时机后移到判定之后**：不再无条件先清再判。这是①的结构性修法 —— 只要「清」还在「判」之前，任何相关性判据都只是在已经清掉之后补一句解释。
- **超时清闩扩到每一次已批准交付**：无审批 trace 的普通交付同样武装有界超时；到期清闩 + 上报「已批准未送达」+ emit 终局事件，与免审那一支同口径。
- **支线超时同时清闩**：`expireCommentSubline` 在清在途标记时一并清 `pendingMigration` 并回报操作员，两者不再各清一半。
- **会话结束与断连两路一并核对**：这两路已有 `settlePendingMandatoryCommentAsUnknown` 覆盖 `pendingMigration`，本 change 补断言确认它对**普通交付**也成立，而不是只在有审批 trace 时才走到。

## Capabilities

### Modified Capabilities

- `platform-browse-surface`: 「评论迁移是回执驱动且 fail-closed」这条今天只规定了落地判据与失败时不发评论；补上闩本身的生命周期——消费须相关、清闩不先于判定、每一次已批准交付都有有界终局、支线终局与闩终局一致。

## Impact

- **aidcp-cloud（唯一受影响仓）**
  - `src/orchestrator/role-dispatcher.ts`：迁移闩的消费准入、清闩时机、超时武装条件、支线超时清理。属主层 `automation`（`boundaries/module-ownership.json` 实查）。
  - 测试：`test/` 下角色调度器相关用例增相关性、超时、支线三组断言。
- **不涉及**：边缘、console、Edge-Cloud 协议、Native IPC。**这是纯云端改动**——边缘对侧无需任何配合。
- **拆仓期约束**（根 `CLAUDE.md` §8）：`role-dispatcher.ts` 归 `automation`，本 change 不跨属主、不新增跨域引用；改动前后跑一次边界门禁确认豁免清单未上涨。
- **原 change 的指针**：`restore-native-facebook-residual-parity` 的 tasks.md 里留有一段指向摘出文档的说明，本 change 立项后须回去更新为「已由本 change 承接」。
