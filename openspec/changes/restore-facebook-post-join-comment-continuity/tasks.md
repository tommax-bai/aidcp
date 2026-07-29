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

## 9. Facebook 时间预算整体 ×1.5（2026-07-29 用户口径；评论上限单独取 180s）

> 触发：长评论逐字输入没输完就撞命令 deadline，边端如实回 `comment_deadline_exceeded`、清空编辑框，
> 云端显示 `submit_failed:comment_deadline_exceeded`。真机实测：约 277 字符的越南语招聘长文，
> 预算 78s（= 18s + 220ms×277 − 1s），实测 78.1s 到点。
> 逐字输入实测均速约 165ms/字符（`input.rs`：对数正态中位 110ms + 标点 ×1.4 + 8% 概率插 300–600ms）。

- [x] 9.1 边缘请求值（`browse-session.ts`）：默认 30→45s、加群 90→135s、首帖 90→135s；
      评论 floor 28→42s / base 18→27s / per-char 220→330ms / **max 90→180s** / 回执余量 1→2s。 <!-- aidcp-edge 70f6947 -->
- [x] 9.2 边缘准入校验（`client.ts`）：默认 30→45s、发布选模式 40→60s、评论 90→**180s**、
      加群 90→135s、首帖 90→135s、发布填正文 400→600s；**新增会话准入上限 180s**
      （原先复用加群上限，会话超时一旦超过加群上限就 `openSession` 全断）。 <!-- aidcp-edge 70f6947 含新增 MAX_FACEBOOK_SESSION_TIMEOUT_MS -->
- [x] 9.3 边缘会话超时（`runtime.ts`）：默认 30→45s、Facebook 90→**180s**（须 ≥ 最大命令天花板，否则静默夹回）。 <!-- aidcp-edge 70f6947 -->
- [x] 9.4 引擎天花板（`engine.rs`）：默认 30→45s、发布选模式 40→60s、评论 90→**180s**、
      加群 90→135s、首帖 90→135s、发布填正文 400→600s。 <!-- aidcp-edge 70f6947 -->
- [x] 9.5 **引擎协议准入**（`protocol.rs` 的 `MAX_FACEBOOK_TIMEOUT_MS` 90→180s）——清点才发现的第五处，
      漏改则 `session.open` 被拒、整个平台一条命令都发不出。 <!-- aidcp-edge 70f6947 protocol.rs MAX_FACEBOOK_TIMEOUT_MS -->
- [x] 9.6 引擎内层窗口：详情水合 15→23s、feed 判稳 6→9s / 3.5→5.25s、加群就绪 30→45s、
      加群确认 45→68s、上传校验 20→30s、首帖绑定 12→18s、首帖身份 20→30s、Feed 恢复窗 8→12s；
      评论就地确认 9→13.5s、回读 3→5s、**提交前预留 12→21s**（不能机械 ×1.5：内容已是 18.5s，
      18s 是负余量）；提交窗预算 18.5→27.75s / 20→30s。 <!-- aidcp-edge 70f6947 判稳预算最终**未**放大：与并行落地的帖子身份采集冲突（其算式依赖 8 轮×3.5s 装进命令预算），且判稳本就不属容错 -->
- [x] 9.7 **不动**：逐字拟人节奏、点击前后静置、轮询间隔、刷新重载地板、首帖下滚轮数——
      它们是节奏/采样密度/限流，不是容错；放大只会变慢，不提高成功率。 <!-- aidcp-edge 70f6947 -->
- [x] 9.8 云端：搜索步 28→42s、按 URL 开帖 45→68s、首帖开帖 105→158s、加群步 120→180s、
      评论 base/per-char/max 同边缘、加群租约 180→270s、keep-open 租约 6→9min / 4→6min。 <!-- aidcp-cloud 9013a5f -->
- [x] 9.9 修一条**与 ×1.5 无关的既有缺陷**：云端算评论预算只数正文，边端逐字打的是「正文 + 换行 + 联系方式」，
      带联系方式时云端预算反而更小、必先掐断（既有单测里就并排写着 40 000 与 40 980）。已统一口径。 <!-- aidcp-cloud 9013a5f 云端按「正文+换行+联系方式」计字，与边端逐字口径一致 -->
- [x] 9.10 新增机械守卫 `test/native-page-engine/timeout-chain-contract.test.ts`：按源码字面量对账
      请求 ≤ 准入、请求 ≤ 天花板、会话 ≥ 所有可被夹的天花板、会话 ≤ 所有须通过的准入、
      提交前预留 ≥ 自身内容 + 回执余量、per-char 相对实测速度有余量、上限装得下 ≥800 字符评论。 <!-- aidcp-edge 70f6947 test/native-page-engine/timeout-chain-contract.test.ts 5 条 -->
- [x] 9.11 验证：edge `cargo test` 全绿 + `typecheck` + `test:acceptance` + `npm test`；cloud 同。 <!-- aidcp-edge 70f6947 cargo 全绿 / typecheck / 验收 30 / 全量 2702 中 2701 通过 0 失败；aidcp-cloud 9013a5f typecheck / 验收 166 / 全量 3833 通过 0 失败 -->

## 10. 上调后的可行性验算（留档）

- 评论上限 180s − 固定开销约 30s = 150s 可用于逐字输入 → 按 165ms/字符约 **880 字符**。
- 触发本次的 277 字符：新预算 = 27s + 330ms×277 = 118s，需要约 76s，**富余**。
- 校验器当前允许 500 字（`aidcp-cloud/src/platform/registry.ts`）→ 500 字需约 113s，**装得下**。
- 若今后放开到 800+ 字符，需再评估：那时上限会重新成为约束项。

## 11. 提交窗预算的事实源已搬家（集成时发现）

- [x] 11.1 合并期发现提交窗预算的事实源已从引擎移到宿主侧 `src/native-page-engine/client.ts` 的
      `NATIVE_COMMIT_WINDOW_BUDGETS`，引擎 `facebook/capability.rs` 里的同名数字只是镜像。
      两处已同抬（join 18.5→27.75s、comment/publish 20→30s）。 <!-- aidcp-edge 70f6947 -->
- [x] 11.2 顺带修一条既有时序脆弱：假引擎子进程启动预算 3s 在满负载下被吃掉，
      协议校验类用例拿到 engine_timeout 而非它要测的 invalid_protocol（单跑必过、全量偶发）。取 10s。
      <!-- aidcp-edge 70f6947 -->

## 12. 部署与出包

- [x] 12.1 cloud 部署 dev：备份 `cloud.bak.20260729-1259.tar.gz` → rsync src/ → restart →
      active + 8787/8090 监听 + PG 锚点缓存就绪 + 风控注册表就绪 + 飞书长连接已建立。 <!-- 2026-07-29 deployed -->
- [ ] 12.2 edge 改动须重新打包桌面客户端才在运营机生效；按 CLAUDE.md §6 属用户显式触发，本 change 不含出包。
