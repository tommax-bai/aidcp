# Tasks

## 1. aidcp-edge — 首帖滚动测量与实际滚动容器对齐

- [x] 1.1 在 `native/page-engine/src/facebook-router/20-feed.js` 把「解析真正在滚的元素」提成一个共享 helper，`feedScrollMetrics` 由它派生，行为不变。 <!-- aidcp-edge d6d60c7 feedScrollNode/feedScrollBy/feedScrollMovement 提出共享 helper，feedScrollMetrics 由其派生 -->
- [x] 1.2 `native/page-engine/src/facebook-router/90-dispatch.js` 的滚动分支改用该 helper 实际滚动并测量位移/到底，替换 `window.scrollBy` 与窗口坐标读数。 <!-- aidcp-edge d6d60c7 滚动分支改用 feedScrollBy + feedScrollMovement -->
- [x] 1.3 补回归：文档不可滚（滚动条在 feed 祖先容器）时，位移非 0、到底判据不恒真、四轮预算可跑满；窗口正常可滚时行为不变。 <!-- aidcp-edge d6d60c7 facebook-router-contract：内层容器承担滚动时位移非 0/不判到底；文档可滚时仍走窗口分支 -->
- [x] 1.4 `20-feed.js` 新增 `Đi đến Bảng feed` 的唯一可见目标探针并随 `feed_probe` 上报；JS 只返回视口坐标，不调用 DOM `click()`，模糊/离屏均失败关闭。 <!-- aidcp-edge d6d60c7 feedRecoveryTarget + feed_recovery_target 路由；router contract 全绿；未出包 -->
- [x] 1.5 Native Feed 初扫/滚动在看到该探针后前台化并重新定位，发送一次 CDP `mouseMoved → mousePressed → mouseReleased`；控件消失且 home surface 确认后才继续，否则按是否已发点击返回未开始/结果不明。 <!-- aidcp-edge d6d60c7 recover_facebook_feed_prompt：前台化后重取点位 + 一组 CDP 点击 + 后置状态确认；fake-CDP 37/37、lib 102/102；未出包 -->
- [x] 1.6 补路由与 fake-CDP 回归：精确越南语文案可识别、近似文案/多目标不可执行、零 DOM click、仅一组 CDP 点击、缺失 home 后置状态不报成功。 <!-- aidcp-edge d6d60c7 路由 2 条（精确文案/零 DOM click；近似文案、多目标、离屏均失败关闭）+ fake-CDP 2 条；实装中另修一条时序脆弱：该用例会话 timeout_ms 只有 2s < 8s 恢复窗，命令原子预算取的是它，改 deadline 无效 → 取 90s -->

## 2. aidcp-edge — 首帖时间预算与命令上限

- [x] 2.1 `native/page-engine/src/facebook/runtime.rs`：首帖身份回读窗 8s → 20s，首帖评论框绑定窗 4s → 12s。 <!-- aidcp-edge d6d60c7 FIRST_POST_EDITOR_TIMEOUT 4s→12s、FIRST_POST_DETAIL_TIMEOUT 8s→20s -->
- [x] 2.2 首帖开帖命令的原子上限从默认 30s 提到 90s，**三处同步**：请求值 `src/native-page-engine/browse-session.ts`、准入校验 `src/native-page-engine/client.ts`、引擎天花板 `native/page-engine/src/engine.rs`；仅对「首帖选择」这一形态生效，按 URL 开帖不变。 <!-- aidcp-edge d6d60c7 请求值；aidcp-edge 99bed5b 补齐漏改的准入校验与引擎天花板 —— 只改请求值的后果不是「没生效」而是每次首帖开帖毫秒级被判 invalid_request、命令根本不下发，云端却读成「群内未找到合适的可评论帖子」（2026-07-29 01:41 真机实证 ads-k1enonmg） -->
- [x] 2.3 补回归：首帖开帖命令取到 90s 上限，关键词开帖与其他命令仍取默认值。 <!-- aidcp-edge d6d60c7 browse-session.test（桩运行时，只验请求值）；aidcp-edge 99bed5b 补两条走**真实准入校验**的回归（client.test）+ 引擎天花板单测 —— 桩测绕过校验正是这次回归漏网的原因 -->
- [x] 2.4 加群侧任何预算**不得改动**（proposal「Constraint To Resolve Explicitly」）。 <!-- aidcp-edge d6d60c7 已核：group_join 相关 4 个预算常量零改动 -->

## 3. aidcp-edge — 租约抑制命令必须回执

- [x] 3.1 `src/main.ts` 租约抑制分支由「打日志后 return」改为回一条具名的未执行回执（成功位为假）。 <!-- aidcp-edge d6d60c7 新增 reportLeaseSuppressed，两条路由共用；ok=false reason=task_lease_suppressed -->
- [x] 3.2 补回归：抑制时回执被发出、成功位为假、原因具名；正常归属命令不受影响。 <!-- aidcp-edge d6d60c7 test/execution/lease-suppressed-command-receipt.test.ts（源码契约，main.ts 单测起不来） -->
- [x] 3.3 接上 `facebook-first-post-comment-confirmation` task 5.6（该 change 明确留给后续）。 <!-- aidcp-edge d6d60c7 兑现 facebook-first-post-comment-confirmation task 5.6 -->

## 4. aidcp-cloud — 首帖开帖步上限

- [x] 4.1 `src/comment-agent/facebook-edge-steps.ts`：新增仅用于首帖开帖的步上限 105s（= 边端 90s + 传输余量），关键词开帖仍用现值 45s。 <!-- aidcp-cloud 816eb5e FACEBOOK_FIRST_POST_OPEN_STEP_TIMEOUT_MS=105s；按 URL 开帖仍 45s -->
- [x] 4.2 更新该常量处的注释推导（边端窗口构成 + 为何云端只做兜底上界）。 <!-- aidcp-cloud 816eb5e 常量注释写清边端窗口构成与「云端只做兜底上界」 -->
- [x] 4.3 补回归：首帖步用新上限、关键词步用旧上限。 <!-- aidcp-cloud 816eb5e facebook-edge-steps.test：首帖 >= 边端 90s 上限且 > 45s；45s 不动 -->

## 5. aidcp-cloud — Reels 再入死锁与滚动无目标处置

- [x] 5.1 `src/orchestrator/role-dispatcher.ts`：把 Reels fallback 状态解回可授权态的证据改为**滚动无目标回执**，并按场有界（至多两次）。 <!-- aidcp-cloud 816eb5e 实装中修正：原计划用 feed.empty.confirmed 解锁，但它在 Reels 期间到达多半是切面前的迟到旧报告，既有 3 条用例正为此而立；改用当下这一跳的滚动回执，既有断言全部保持原值 -->
- [x] 5.2 `src/orchestrator/role-dispatcher.ts`：为「滚动回执失败且原因为无目标」补处置分支——给出下一步或诚实终止会话，杜绝无命令无终态悬停。 <!-- aidcp-cloud 816eb5e scroll no_target 分支：先试重开 Reels，发不出则 endSession(scroll_no_target_without_next_step) -->
- [x] 5.3 补回归：空首页账号被送回首页后仍可再次授权切 Reels；滚动无目标不再产生零命令悬停。 <!-- aidcp-cloud 816eb5e 三条用例：重开 / 必给下一步 / 重开按场有界；既有 11 条断言全部保持原值 -->

## 6. 验证

- [x] 6.1 edge：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全过（含 native 引擎构建）。 <!-- aidcp-edge d6d60c7 test:acceptance 30 绿、npm test 2561 绿 0 失败、typecheck 过；native cargo test 全绿 -->
- [x] 6.2 cloud：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全过。 <!-- aidcp-cloud 816eb5e test:acceptance 166 绿、npm test 3833 绿 0 失败、typecheck 过 -->
- [x] 6.3 安全红线全过：`AC-PROTO-*`、`AC-PUB-*`、`AC-RISK-*`。 <!-- aidcp-edge d6d60c7/aidcp-cloud 816eb5e AC-PROTO-* / AC-PUB-* / AC-RISK-* 均在上述全量内通过 -->

## 7. 集成与部署

- [x] 7.1 edge / cloud 分别 `land-change` 合回各自 master。 <!-- aidcp-edge d6d60c7 + aidcp-cloud 816eb5e 均已 land-change 合回各自 master 并推送 -->
- [x] 7.2 cloud 部署 dev（按 CLAUDE.md §5 安全序列：先备份 → rsync → restart → healthcheck）。 <!-- 2026-07-28 deployed dev：备份 cloud.bak.20260728-2131.tar.gz → rsync src/ → restart → active + 8787/8090 监听 + 飞书长连接已建立 + PG 锚点缓存就绪 -->
- [ ] 7.3 edge 改动**须重新打包桌面客户端**才在运营机生效；按 CLAUDE.md §6，打包属用户显式触发动作，本 change 不含出包。

## 8. 真机验收（登记 backlog，不在本 change 内判定）

- [ ] 8.1 慢群页（越南代理）加群后首帖评论一次跑通：确认四轮下滚真的发生、身份回读在 20s 内完成。
- [ ] 8.2 空首页账号被送回首页后可再次切到 Reels，不再出现零命令悬停到冷待机。
- [ ] 8.3 取一次首帖返回的目标身份原值，判定 design §6 那条「就地绑定指纹不含固链、身份回读却依赖固链」的线索成立与否。
