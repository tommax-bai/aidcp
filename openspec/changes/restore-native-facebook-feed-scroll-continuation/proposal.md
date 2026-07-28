## Why

2026-07-28 20:20–20:37，dev 上两个 Facebook 账号（`61592037808218` / `61591715201364`）连续 17 分钟只滚不读、零阅读零点赞。每次滚动都回 `ok=false reason=no_target`，两次滚动间隔恒为 ~4 分 15 秒——那不是节奏，是云端闲置看门狗（`aidcp-cloud/src/risk/resume-limits.ts:25`，`DEFAULT_IDLE_NUDGE_MS = 240_000`）在补发滚动。云端对滚动回执里的 `no_target` **没有任何归宿**：只有 `empty_feed` / `feed_exhausted` / `present_unreportable` / `feed_continuation_unconfirmed` 四种有处理路径（`aidcp-cloud/src/orchestrator/role-dispatcher.ts:1804`、`:3468-3474`、`:3746-3769`）。于是账号被钉在同一屏，靠看门狗每 4 分钟空转一次，直到 20:38 云端重启、会话重建走了「初始 feed」路径，才立刻报出 present-but-unreportable、拿到 Reels 授权、恢复正常。

根因是 JS→Rust 迁移时丢了两段行为，**且两段都能在退役 TS 实现里逐行找到**：

- **R1 · 轮次耗尽后的兜底尾巴只保留在「初始 feed」，「常规滚动」丢了。** 退役实现 `aidcp-edge/src/facebook/facebook-session.ts:1019-1101` 的 `scrollFeed()` 在 8 轮跑完且一张卡都没见过时，**必定**先做一次首页空态复检，据结果分档上报：确认空态 → `listState:'empty'`；首页有物理卡且不 loading → `listState:'present_unreportable'`；两者都不成立才回落 `no_target`。Rust 的 `execute_facebook_initial_feed`（`native/page-engine/src/facebook/feed.rs:70-112`）保留了这条尾巴，但 `execute_facebook_feed_scroll`（同文件 `:168-231`）没有——零卡即裸 `no_target`（`:476-484`）。
- **R2 · 懒加载的「等」被削短。** 退役实现 `aidcp-edge/src/facebook/feed-reader.ts:574-601` 的 `settleCards()` 提前返回需要 `cards.length >= minCards && stable && !loading`——**零卡时不提前返回**，会轮询到 3500ms 预算耗尽，给 Facebook 懒加载渲染时间。Rust 的 `settle_facebook_feed`（`feed.rs:348-367`）少了「卡数 ≥ 1」这一条，零卡页面两次探测一致（约 500ms）就返回。实测后果：8 轮在约 10 秒内跑完（线上 `sendCommand`→`action.completed` 实测 11 秒），而不是耐心等满 8×3.5s，懒加载根本来不及出内容。

R1 直接撞上两条**已合并规格**：`openspec/specs/facebook-feed-browse/spec.md:178` 要求「八轮有界续滚仍无可上报卡 ⇒ Edge SHALL 上报独立的 present-but-unreportable 列表态」，未限定只在初始 feed；`openspec/specs/facebook-feed-continuity/spec.md:108` 明写「MUST NOT remain idle on the same viewport waiting only for a later Cloud watchdog nudge」——线上行为逐字撞上这句禁令。所以这是**对已上线规格的回归修复，不是新能力提案**。

## What Changes

- **常规滚动补回兜底尾巴**：`execute_facebook_feed_scroll` 八轮无新卡后，不再直接裸报 `no_target`。先按与 `execute_facebook_initial_feed` 逐位一致的判据分档：确认在首页 + 存在物理卡 + 不 loading + 无阻断 ⇒ 上报 `page.cards`（卡数 0、`listState = present_unreportable`）；否则做首页空态确认，确认成立 ⇒ 上报 `page.cards`（卡数 0、`listState = empty`）；两者都不成立才落到今天的原因码分类。
- **零卡时的 settle 等满预算**：`settle_facebook_feed` 的提前返回加上「本轮已扫到至少一张卡」这一条件；零卡视口一律等满有界预算再返回，恢复「滚 → 等加载 → 再滚」的节奏。
- **云端零改动**：`aidcp-cloud/src/comm/handler.ts:658-671` 已经接受 `listKind='feed'` + `listState='present_unreportable'|'empty'` + 卡数 0 的 `page.cards` 并 emit 对应事件，dispatcher 已有 Reels 单点授权归宿。本 change 不碰 cloud。
- **不新增原因码、不新增协议字段**。新增原因码而云端无归宿，正是本次事故的形态。

**非目标（明确不做）**：不改 `facebook_unconfirmed_scroll_reason` 的分类口径，不改懒加载增高阈值——这两条已由并行的活跃 change `restore-native-facebook-residual-parity`（任务 4.2 / 4.6，提交 `aidcp-edge 9176dcb`）完成，本 change 绝不重做。

## Capabilities

### New Capabilities
（无）

### Modified Capabilities
- `native-facebook-behavior-parity`: 「Native Feed scanning preserves stateful continuation truth」当前的场景只落在**初始** feed 视口上，未覆盖云端命令驱动的**常规滚动**。补上两条义务——常规滚动的终态分类必须与初始扫描逐位一致（存在物理卡时绝不裸报「找不到目标」）；零卡视口的 card-set settling 必须等满有界预算而非见「稳定」即返回。

## Impact

- **代码**：只改 `aidcp-edge` 的 Rust Native 引擎 `native/page-engine/src/facebook/feed.rs`（`execute_facebook_feed_scroll` 尾段、`settle_facebook_feed` 提前返回条件），并补 Rust 单测。TypeScript 侧、协议侧、cloud 侧、console 侧零改动。
- **热点文件冲突**：`native/page-engine/src/facebook/feed.rs` 正被并行 session 的活跃 change `restore-native-facebook-residual-parity` 编辑（其提交 `9176dcb` 于 2026-07-28 20:23 落在分支上，尚未合入 `aidcp-edge` master=`845ef0d`）。集成时必须在 `9176dcb` 之后 rebase，不得先合本 change 造成对方重做。
- **运行时影响**：单次滚动命令的执行时长从约 10 秒回到最多约 30 秒（8 轮 × 3.5s 预算），这是恢复退役实现的原有节奏；换来的是首页读不出内容时能在**一次**滚动内产出云端可消费的终态，而不是每 4 分钟空转一轮。
- **红线**：MUST NOT 静默假成功。loading / 登录 / 验证码 / 同意浮层阻断 / 非首页 / 无物理卡，一律保持今天的诚实失败，绝不借 present-but-unreportable 通道跳 Reels。
