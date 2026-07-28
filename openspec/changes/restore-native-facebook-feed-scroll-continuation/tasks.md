> **集成顺序铁律**：`aidcp-edge/native/page-engine/src/facebook/feed.rs` 是热点文件。并行 session 的活跃 change
> `restore-native-facebook-residual-parity` 已在其分支上提交 `9176dcb`（2026-07-28 20:23，改
> `facebook_unconfirmed_scroll_reason` 与 `facebook_feed_height_grew`），**尚未**合入 `aidcp-edge` master
> （master=`845ef0d`）。开发可从当前 master 起（两边改的函数不重叠），但**集成前必须 rebase 到最新 master**，
> 且实装期间 **MUST NOT** 触碰那两个函数体——它们的口径由那条 change 负责。

## 1. aidcp-edge — 前置对账

- [ ] 1.1 记录开工时 `aidcp-edge` master 的 sha 与 `9176dcb` 是否已合入（`git merge-base --is-ancestor 9176dcb master`）；未合入时照常从当前 master 开工，但把「land 前 rebase + 复核那两个函数未被本 change 改动」列为 5.4 的前置
- [ ] 1.2 逐行读 `native/page-engine/src/facebook/feed.rs` 的 `execute_facebook_initial_feed`（`:70-112`）尾段与 `execute_facebook_feed_scroll`（`:168-231`），确认两者的差异点仍与 design.md 表格一致（rebase 后行号会漂，按符号名定位）
- [ ] 1.3 逐行读退役实现 `src/facebook/facebook-session.ts` 的 `scrollFeed()` 与 `src/facebook/feed-reader.ts` 的 `settleCards()` / `confirmHomeEmpty()`，把要恢复的判据抄成清单（只作对照，**不复活**这些 TS 代码）

## 2. aidcp-edge — 抽共享尾段（design D1 / D2）

- [ ] 2.1 把启动首扫尾段的证据阶梯抽成一个共享函数（暂名 `facebook_zero_card_terminal`）：入参为最终 probe 与 session，返回「present-but-unreportable 观察 / explicit-empty 观察 / 无阶梯可用」三态；判据逐位照抄 `execute_facebook_initial_feed` 现有实现，**不放宽**
- [ ] 2.2 让 `execute_facebook_initial_feed` 改调该共享函数，行为逐位不变（回归零变更是本任务的验收标准）
- [ ] 2.3 让 `execute_facebook_feed_scroll` 在八轮耗尽、落到 `facebook_unconfirmed_scroll_reason` **之前**先走该共享函数：命中 present-but-unreportable ⇒ 返回 `(EffectPhase::Confirmed, PageCards)`（0 卡 + `list_state = PresentUnreportable`）；命中 explicit-empty ⇒ 返回 `(EffectPhase::Confirmed, PageCards)`（0 卡 + `list_state = Empty`）；两者都不命中才落今天的原因码分类
- [ ] 2.4 复核 `facebook_page_cards(..., only_new, ...)` 在 0 卡场景下不会污染 `seen_post_ids`、不会把 `list_state` 覆写成 `Ready`（`:600-615` 附近有一处 list_state 归一，确认它不吃掉 `PresentUnreportable`）
- [ ] 2.5 确认阻断态（登录 / 验证码 / 同意浮层）在共享函数里**先于**阶梯判定短路——`present_unreportable` 绝不在阻断态下产出（红线：MUST NOT 静默假成功）

## 3. aidcp-edge — settle 零卡等满预算（design D3）

- [ ] 3.1 给 `settle_facebook_feed`（`:348-367`）的提前返回加上「本轮样本卡数 ≥ 1」条件；零卡样本一律继续轮询到预算耗尽后返回最后一次样本
- [ ] 3.2 确认该改动只影响 feed settle，不波及 `confirm_facebook_feed_bottom` / `confirm_facebook_home_empty` 各自的独立轮询（它们有各自的预算与判据，不共用早退条件）
- [ ] 3.3 评估最坏时长：8 轮 × 3.5s ≈ 28s，加手势与探测开销后仍须显著小于云端闲置看门狗 240s；把该结论写进代码注释，避免后人再把预算削掉

## 4. aidcp-edge — Rust 单测

- [ ] 4.1 八轮零卡 + 最终 probe 为首页且 `article_count > 0` 且不 loading 不阻断 ⇒ 断言返回 `PageCards`、0 卡、`list_state = PresentUnreportable`，且**不**返回 `no_target` 回执
- [ ] 4.2 八轮零卡 + 无物理卡 + 空态确认成立 ⇒ 断言返回 `PageCards`、0 卡、`list_state = Empty`
- [ ] 4.3 八轮零卡 + 最终 probe 为 loading / 非首页 / 无物理卡且空态确认不成立 ⇒ 断言保持今天的诚实失败分类，且两种零卡观察都**不**产出
- [ ] 4.4 阻断态（登录 / 验证码 / 同意浮层）下八轮耗尽 ⇒ 断言既不报 present-but-unreportable 也不报 empty
- [ ] 4.5 settle：零卡且连续两次样本一致 ⇒ 断言**不**提前返回、继续轮询到预算耗尽
- [ ] 4.6 settle：非空且连续两次样本一致且不 loading ⇒ 断言**立即**提前返回（保证正常路径不变慢）
- [ ] 4.7 `execute_facebook_initial_feed` 回归：抽函数前后行为逐位一致（可用既有首扫用例作为不变量）

## 5. aidcp-edge — 验证与集成

- [ ] 5.1 `cargo test`（Native 引擎）全过
- [ ] 5.2 `npm run typecheck` 全过
- [ ] 5.3 `npm run test:acceptance` 再 `npm test` 全过（顺序按 CLAUDE.md §4 回归纪律）
- [ ] 5.4 `scripts/land-change aidcp-edge restore-native-facebook-feed-scroll-continuation` 集成（rebase 到最新 master 后 ff 合入）
- [ ] 5.5 回写本文件：每条完成项标 `[x]` 并附 `<!-- aidcp-edge <sha> 备注 -->`；sha 必须取自**已推送**的提交

## 6. 部署与真机观察

- [ ] 6.1 本 change 改的是 Rust 引擎，**仅 push 不生效**——需重新编译边缘产物才能在运营机上验证；按 CLAUDE.md §6 打包属用户显式触发，本任务只登记前置条件，不自动出包
- [ ] 6.2 dev 上取一个当前处于「只滚不读」的 Facebook 账号观察：一次滚动命令内应产出 `present_unreportable` 或 `empty`，云端应在同一分钟内授权 Reels 切换，而不是等 240s 看门狗
- [ ] 6.3 云端侧零改动确认：`aidcp-cloud` 无需部署，`handler.ts` 的零卡 `page.cards` 消费路径与 dispatcher 的 Reels 授权路径均已在线

## 7. 真机验收 backlog 登记

- [ ] 7.1 把「8 轮 × 3.5s 的 settle 预算在 Native 版式 + 跨语言（越南语等）首页下是否够 Facebook 懒加载出一批」登记进 `docs/real-machine-acceptance-backlog.md`；判据：预算内能观察到新批渲染。若不够，后续以「连续 N 轮无增长」而非单纯抬预算的方式修正
- [ ] 7.2 把「`present_unreportable` 的实际上报频率是否导致账号过频掉进 Reels」一并登记（云端已按 startup/generation 幂等去重，但真实频率未测）

## 8. 范围外事项（登记，不在本 change 做）

- [ ] 8.1 记录：2026-07-28 现场另有两个独立致停因素——慢启动第 1 天的小时浏览配额（5 次/小时，用满休眠约 58 分钟）与账号未绑人设。二者不在本 change 范围，验收时不要把它们的表现算作本修复失败
- [ ] 8.2 记录：「每个滚动原因码都必须有云端归宿」的覆盖式断言由 `restore-native-facebook-residual-parity` 任务 4B.4 承接；非首页列表面的终局由其 4B.2 承接。本 change 只消除当前这一条无归宿路径，不提前实现那两条
