## Context

Facebook 浏览已整体迁到 Rust Native 引擎（`aidcp-edge/native/page-engine/`），退役的明文 TypeScript 实现仍在树上（`aidcp-edge/src/facebook/facebook-session.ts`、`feed-reader.ts`），可逐行对照。首页 feed 的滚动有两条独立入口：

| 入口 | 函数 | 触发时机 | 轮次耗尽后的行为 |
| --- | --- | --- | --- |
| 启动首扫 | `execute_facebook_initial_feed`（`facebook/feed.rs:70-112`） | 会话建立、首次进 feed | 有物理卡 → 上报 `page.cards`（0 卡 + `present_unreportable`）；否则做空态确认 → `empty`；再不行才 `no_target` |
| 常规滚动 | `execute_facebook_feed_scroll`（`facebook/feed.rs:168-231`） | 云端每次下发滚动命令 | **直接** `facebook_unconfirmed_scroll_reason(...)`，零卡即裸 `no_target` |

云端对滚动回执原因码的归宿是一张封闭表（`aidcp-cloud/src/orchestrator/role-dispatcher.ts`）：`feed_continuation_unconfirmed` → 续滚（`:3746-3752`）；`feed_exhausted` → 刷新 + Reels 授权（`:3759-3769`）；`feed.empty.confirmed` / `feed.present_unreportable.confirmed` → Reels 授权（`:3468-3474`）。**`no_target` 不在表内**。因此常规滚动一旦落到裸 `no_target`，账号就没有任何前进路径，只剩闲置看门狗（240s）每 4 分钟补一次滚动，而那次滚动会以完全相同的方式再次失败——这就是 2026-07-28 线上 17 分钟空转的机制。

第二处退化在 settle：退役实现的 `settleCards()` 只在「已扫到卡 + 稳定 + 不 loading」三条同时成立时提前返回，零卡时会一直轮询到 3500ms 预算耗尽；Rust 的 `settle_facebook_feed`（`feed.rs:348-367`）只判「稳定 + 不 loading」，零卡视口约 500ms 就返回。八轮因此在约 10 秒内跑完（线上 `sendCommand`→`action.completed` 实测 11 秒），Facebook 的懒加载批次根本来不及渲染。

约束：`native/page-engine/src/facebook/feed.rs` 是热点文件，并行 session 的活跃 change `restore-native-facebook-residual-parity` 正在改它（提交 `9176dcb`，2026-07-28 20:23，尚未合入 `aidcp-edge` master=`845ef0d`）。

## Goals / Non-Goals

**Goals:**

- 让常规滚动的终态分类与启动首扫**逐位一致**：物理卡在场时产出云端可消费的 `present_unreportable` 观察，而不是裸 `no_target`。
- 恢复「滚 → 等加载 → 再滚」的节奏：零卡视口等满有界 settle 预算。
- 保持红线：loading / 登录 / 验证码 / 同意浮层 / 非首页 / 无物理卡，一律维持今天的诚实失败。
- 云端零改动、协议零改动、不新增原因码。

**Non-Goals:**

- **不改** `facebook_unconfirmed_scroll_reason` 的分类口径（见过卡→`feed_continuation_unconfirmed`、零卡→`no_target`）——`restore-native-facebook-residual-parity` 任务 4.2 已落。
- **不改**懒加载增高阈值（1px→100px）——同 change 任务 4.6 已落。
- 不给非首页列表面（搜索 / 群组）的 `feed_continuation_unconfirmed` / `feed_exhausted` 定义终局——那是同 change 任务 4B.2 的范围。
- 不给「每个原因码都必须有云端归宿」加覆盖式断言——那是同 change 任务 4B.4 的范围。本 change 只消除**当前这一条**没有归宿的路径。
- 不动退役 TypeScript 实现（只作为对照读物，不复活）。
- 不调 `FACEBOOK_FEED_SCROLL_ROUNDS`（8）与 `FACEBOOK_FEED_SETTLE_IN_PLACE`（3500ms）的取值。

## Decisions

### D1：把启动首扫的证据阶梯抽成共享函数，两条入口共用

常规滚动的尾段与启动首扫的尾段是同一套判据（首页 + 物理卡 + 不 loading + 不阻断 → `present_unreportable`；否则空态确认 → `empty`）。**抽一个共享的尾段函数，两处调用**，而不是在常规滚动里复制一份。

- **为什么不复制**：本次事故的成因正是「两条入口各写一份、其中一份漏了一段」。复制第二份等于把同一个坑再挖一遍，且下次只会有一处被修。
- **备选（已否决）**：让常规滚动在零卡时直接转调 `execute_facebook_initial_feed`。否决理由——首扫会 `navigate(FACEBOOK_HOME_URL)` 并清空 `seen_post_ids`，把用户当前的滚动深度整段丢掉，等于每次读不出内容就回顶，正是历史上「一直刷新、永远下不去」那个已修复的病。
- **effect phase 口径**：常规滚动尾段返回的 `page.cards` 用 `EffectPhase::Confirmed`（观察已确认），与首扫一致；首扫今天在失败分支用 `NotStarted`，那是因为它是未经命令的自举，本 change 不动它。

### D2：`present_unreportable` 的准入判据照抄启动首扫，不放宽

阶梯第一级用 `article_count > 0`（物理卡在场）而非「见过卡」（`saw_any_card`）。两者语义不同：`saw_any_card` 记的是整轮里任一时刻扫到过可上报卡，而阶梯要判的是**最终这一屏**是否仍有物理结构卡。已合并规格 `facebook-feed-browse:178` 的最后一条 Scenario 明确要求 loading / 登录 / 同意 / checkpoint / 未知 / 非首页 / 无物理卡一律不得走这条兜底，实现必须逐条守住。

- **备选（已否决）**：零卡即无条件报 `present_unreportable`。否决理由——那会把「页面还在加载」和「已被验证码顶掉」也说成「有内容读不出来」，云端据此切 Reels，属于静默假成功。

### D3：settle 的提前返回加「已扫到至少一张卡」条件

把 `settle_facebook_feed` 的早退条件从「稳定 且 不 loading」改成「稳定 且 不 loading 且 卡数 ≥ 1」，与退役实现 `settleCards()` 逐位对齐。零卡视口一律等满预算再返回当前样本。

- **代价**：单次滚动命令的最坏执行时长从约 10 秒回到约 30 秒（8 轮 × 3.5s）。这是恢复原有节奏，不是新增开销；换来的是懒加载有时间出批，以及「一次滚动内产出终态」而非「每 4 分钟空转一轮」。
- **备选（已否决）**：只在最后一轮等满预算。否决理由——懒加载是**每轮**滚动后触发的，只在最后一轮等，前七轮照样在页面还没渲染时就判零卡，等于把八轮压缩成一轮有效。

### D4：不新增原因码

阶梯产出的两种观察都复用既有的零卡 `page.cards` 列表态（`present_unreportable` / `empty`），云端 `aidcp-cloud/src/comm/handler.ts:658-671` 已经在消费。新增原因码而云端无归宿，正是本次事故的形态；本 change 不重犯。

## Risks / Trade-offs

- **[与并行 change 在同一文件上冲突]** → `restore-native-facebook-residual-parity` 的 `9176dcb` 改的是 `facebook_unconfirmed_scroll_reason`（`:476-484`）与 `facebook_feed_height_grew`（`:409-413`）；本 change 改的是 `execute_facebook_feed_scroll` 尾段（`:226-229`）与 `settle_facebook_feed`（`:348-367`）——函数不重叠，但在同一文件相邻区域。缓解：集成时**必须在 `9176dcb` 合入 master 之后再 rebase 本分支**，且本 change 的实装绝不触碰那两个函数体。
- **[单次滚动变慢，观感像"卡住"]** → 最坏 30 秒（原为约 10 秒）。缓解：这只发生在读不出内容的坏路径；正常路径一旦扫到卡就立即早退（D3 保留了非空早退）。且 30 秒远小于云端 240 秒的闲置看门狗窗口，不会引发误判。
- **[`present_unreportable` 报得过于频繁 → 账号频繁掉进 Reels]** → 云端已按 startup / documentGeneration 去重、每代只授权一次 Reels 切换（`facebook-feed-browse:178` 的幂等 Scenario），本 change 不改这层。仍需真机观察实际频率。
- **[8×3.5s 是否够跨语言版式的懒加载出一批，未经真机验证]** → 阈值取自 2026-06 的退役实现，Native 版式下未复核。登记为真机验收项，不在本 change 内拍板；若不够，后续以「连续 N 轮无增长」而非单纯抬预算的方式修正。
- **[修完之后账号仍不动]** → 本 change 只消除"没有归宿的终态"这一条。2026-07-28 现场还有两个独立因素：慢启动第 1 天的小时浏览配额（5 次/小时，用满后休眠约 58 分钟）与账号未绑人设。二者都不在本 change 范围，不要把它们的表现算作本修复失败。

## Migration Plan

1. 等 `restore-native-facebook-residual-parity` 的 `9176dcb` 合入 `aidcp-edge` master。
2. 本分支 rebase 到该 master，跑 `cargo test`（Native 引擎）+ `npm run typecheck` + `npm test`。
3. 合入 master → 打 dev 桌面客户端产物（本 change 涉及 Rust 引擎，必须重新编译才生效；仅 `git push` 不改变运营机行为）。
4. dev 上取一个当前处于「只滚不读」的 Facebook 账号观察：一次滚动命令内应产出 `present_unreportable` 或 `empty`，云端应在同一分钟内授权 Reels 切换，而不是等 4 分钟看门狗。
5. 回滚：本 change 是纯边缘引擎改动、无 schema / 无协议变更，回退提交并重打包即可。
