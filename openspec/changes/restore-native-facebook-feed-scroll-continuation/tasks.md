> **集成顺序铁律**：`aidcp-edge/native/page-engine/src/facebook/feed.rs` 是热点文件。并行 session 的活跃 change
> `restore-native-facebook-residual-parity` 已在其分支上提交 `9176dcb`（2026-07-28 20:23，改
> `facebook_unconfirmed_scroll_reason` 与 `facebook_feed_height_grew`），**尚未**合入 `aidcp-edge` master
> （开工时 master=`845ef0d`）。开发可从当前 master 起（两边改的函数不重叠），但**集成前必须 rebase 到最新 master**，
> 且实装期间 **MUST NOT** 触碰那两个函数体——它们的口径由那条 change 负责。
>
> **（实装实测记录）** 本 change 于 2026-07-28 先行 land（edge `a7f9edc`，master 845ef0d→a7f9edc 为 ff）。
> 落地时 `9176dcb` 仍未合入 master，故**未**发生 rebase；本 change 逐字未碰那两个函数体，
> `restore-native-facebook-residual-parity` 落地时在 `a7f9edc` 之上 rebase 即可，两边改动函数不重叠。

## 1. aidcp-edge — 前置对账

- [x] 1.1 记录开工时 `aidcp-edge` master 的 sha 与 `9176dcb` 是否已合入 <!-- aidcp-edge a7f9edc 开工时 master=845ef0d；9176dcb 未合入，从 845ef0d 起分支 -->
- [x] 1.2 逐行读 `execute_facebook_initial_feed` 与 `execute_facebook_feed_scroll`，确认差异点与 design.md 表格一致 <!-- aidcp-edge a7f9edc 确认：首扫有零卡阶梯、常规滚动没有，其余逐位相同 -->
- [x] 1.3 逐行读退役实现 `src/facebook/facebook-session.ts` 的 `scrollFeed()` 与 `feed-reader.ts` 的 `settleCards()` / `confirmHomeEmpty()` <!-- aidcp-edge a7f9edc 对照读毕，未改动任何 TS 文件 -->

## 2. aidcp-edge — 抽共享尾段（design D1 / D2）

- [x] 2.1 抽共享函数 `facebook_zero_card_terminal`，返回 present-but-unreportable / empty / none 三态 <!-- aidcp-edge a7f9edc 三态枚举 FacebookZeroCardTerminal + 纯判据 facebook_present_unreportable_home -->
- [x] 2.2 让 `execute_facebook_initial_feed` 改调该共享函数 <!-- aidcp-edge a7f9edc **偏离原计划，须知**：原任务写「行为逐位不变」，实装为**收紧**。首扫此前只判 `article_count > 0` 就报 present_unreportable，因此 loading 中或非首页时也会报；共享判据按已合并规格 facebook-feed-browse 的末条 Scenario 收紧为「首页 + 不 loading + 有物理卡 + 探测自判不可上报」，首扫因此不再在 loading / 非首页时误报。收紧方向是更诚实、且是那条规格的原意，故按收紧落地而非维持原状；真机复核见 backlog 118.5 -->
- [x] 2.3 让 `execute_facebook_feed_scroll` 在落原因码分类**之前**先走该共享函数 <!-- aidcp-edge a7f9edc 命中即返回 (Confirmed, PageCards)，0 卡 + 对应 list_state；未命中才落 facebook_unconfirmed_scroll_reason -->
- [x] 2.4 复核 `facebook_page_cards` 在 0 卡场景不污染 `seen_post_ids`、不覆写 `list_state` <!-- aidcp-edge a7f9edc 0 卡时循环体不执行、seen_post_ids 不写入；list_state 归一分支是恒等映射，PresentUnreportable 原样透传 -->
- [x] 2.5 阻断态先于阶梯短路 <!-- aidcp-edge a7f9edc 两条入口都在循环前经 ensure_facebook_action_gate 拦 login/captcha/unknown/consent；阶梯判据再要求 surface=="home"，classify() 把 /login 与 /checkpoint 归为非 home，双保险 -->

## 3. aidcp-edge — settle 零卡等满预算（design D3）

- [x] 3.1 `settle_facebook_feed` 早退加「本轮样本卡数 ≥ 1」条件 <!-- aidcp-edge a7f9edc 判据抽成纯函数 facebook_feed_settled(stable, probe) 以便单测 -->
- [x] 3.2 确认不波及 `confirm_facebook_feed_bottom` / `confirm_facebook_home_empty` <!-- aidcp-edge a7f9edc 两者各有独立轮询与判据，不调用 facebook_feed_settled -->
- [x] 3.3 把「最坏 8×3.5s 仍远小于云端 240s 闲置看门狗」写进代码注释 <!-- aidcp-edge a7f9edc 注释写在 settle_facebook_feed 与滚动尾段两处 -->
- [x] 3.4 **（实装新增）** 记录副作用：`execute_facebook_search` 的零结果路径也共用该 settle，故搜索空结果的判定会从约 0.5s 变为等满预算 <!-- aidcp-edge a7f9edc 与退役实现一致（搜索与 feed 共用 settleCards），且给搜索页懒加载同样的机会，判为期望行为 -->

## 4. aidcp-edge — Rust 单测

> **（实装实测偏离，须知）** 原 4.1–4.4 设想的是「跑满八轮」的端到端断言，但 `feed.rs` 的测试模块是**纯函数级**的，
> 没有可驱动 `EngineSession` / CDP 的桩（`facebook_zero_card_terminal` 需要 session 才能做空态确认）。
> 按「桩验不了的转真机」原则，改为：**准入判据与判稳判据各抽成纯函数后逐条断言**（这两处正是红线所在），
> 八轮编排层面的端到端验证转 backlog 簇 118。

- [x] 4.1 准入判据正向：首页 + 不 loading + 有物理卡 + 探测自判不可上报 ⇒ 准入 <!-- aidcp-edge a7f9edc unreportable_home_is_admitted_to_the_zero_card_ladder -->
- [x] 4.2 准入判据反向：loading / 六种非首页 surface / 无物理卡 / 探测判 Ready / 已有可上报卡 ⇒ 一律不准入 <!-- aidcp-edge a7f9edc zero_card_ladder_refuses_loading_blocked_and_non_home_pages -->
- [x] 4.3 判稳反向：零卡视口即便连续两次一致也不算判稳 <!-- aidcp-edge a7f9edc zero_card_viewport_is_not_settled_by_stability_alone -->
- [x] 4.4 判稳正向：有卡 + 稳定 + 不 loading ⇒ 立即早退；loading 或未稳定 ⇒ 不早退 <!-- aidcp-edge a7f9edc settled_non_empty_card_set_still_returns_early -->
- [x] 4.5 `execute_facebook_initial_feed` 回归由既有 Native 用例覆盖（106 + 35 全过，含 facebook_initial_scan_resets_a_persisted_reel_to_home_feed） <!-- aidcp-edge a7f9edc 未新增专用回归用例；2.2 的收紧属有意行为变更，真机复核见 backlog 118.5 -->
- [ ] 4.6 **（未做，转真机）** 「跑满八轮后产出 present_unreportable / empty」的端到端断言——需要可驱动 session 的桩，本轮未建；见 backlog 簇 118.1 / 118.4

## 5. aidcp-edge — 验证与集成

- [x] 5.1 `cargo test`（Native 引擎）全过 <!-- aidcp-edge a7f9edc 106 + 35 + 1 + 2 + 1 全过；另跑 cargo fmt --check 与 cargo clippy --all-targets 无告警 -->
- [x] 5.2 `npm run typecheck` 全过 <!-- aidcp-edge a7f9edc 本 change 零 TS 改动 -->
- [x] 5.3 `npm run test:acceptance`（30/30，含 AC-PROTO-20b 首页物理卡不可上报状态往返）再 `npm test`（2552 pass / 0 fail / 1 skipped=gated E2E） <!-- aidcp-edge a7f9edc land 前与 land-change 内各跑一遍 -->
- [x] 5.4 `scripts/land-change aidcp-edge restore-native-facebook-feed-scroll-continuation --yes` <!-- aidcp-edge a7f9edc ff 推送 845ef0d..a7f9edc，主 checkout 已同步，worktree/分支已清理 -->
- [x] 5.5 回写本文件并附已推送的 sha <!-- aidcp-edge a7f9edc -->

## 6. 部署与真机观察

- [x] 6.1 记录：本 change 改 Rust 引擎，**仅 push 不生效**，须重打边缘客户端包；按 CLAUDE.md §6 打包属用户显式触发，不进自动收尾 <!-- aidcp-edge a7f9edc 未出包 -->
- [ ] 6.2 dev 真机观察：一次滚动命令内产出 `present_unreportable` 或 `empty`，云端同分钟内授权切 Reels（见 backlog 118.1）
- [x] 6.3 云端零改动确认 <!-- aidcp-cloud 无改动；handler.ts 的零卡 page.cards 消费路径（listState=present_unreportable|empty + cards 长度 0）与 dispatcher 的 Reels 单点授权均已在线，无需部署 -->

## 7. 真机验收 backlog 登记

- [x] 7.1 8 轮 × 3.5s 预算在 Native 版式 + 跨语言首页下是否够懒加载出批 <!-- aidcp docs/real-machine-acceptance-backlog.md 簇 118.2 -->
- [x] 7.2 `present_unreportable` 实际上报频率与 Reels 切换次数 <!-- aidcp docs/real-machine-acceptance-backlog.md 簇 118.6 -->

## 8. 范围外事项（登记，不在本 change 做）

- [x] 8.1 记录：2026-07-28 现场另有两个独立致停因素——慢启动第 1 天的小时浏览配额（5 次/小时，用满休眠约 58 分钟，实测 `休眠浏览 3471s reason=quota:hour`）与账号未绑人设（dev 上 20 个 FB 账号全部未绑）。二者不在本 change 范围，验收时不要把它们的表现算作本修复失败
- [x] 8.2 记录：「每个滚动原因码都必须有云端归宿」的覆盖式断言由 `restore-native-facebook-residual-parity` 任务 4B.4 承接；非首页列表面的终局由其 4B.2 承接。本 change 只消除当前这一条无归宿路径
