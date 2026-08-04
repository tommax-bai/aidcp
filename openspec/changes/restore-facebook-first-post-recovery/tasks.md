# Tasks

## 1. aidcp-edge — 群根导航补真落地等待

- [x] 1.1 实读 `wait_for_facebook_ready`（`native/page-engine/src/facebook/shared.rs:812-836`）的**全部调用点**，
      判定是就地加地址判据、还是新增一个专用落地等待。**MUST NOT 在未清点调用点前改动共享函数语义。**
      <!-- aidcp-edge 994ac8b 清点调用点后判定新增专用等待，未改共享函数语义 -->
- [x] 1.2 落地等待判据 = 文档就绪 **且** 当前地址解析到请求的群根；有界超时。
      <!-- aidcp-edge 994ac8b facebook_group_root_landed（纯函数）+ wait_for_facebook_group_root_landing，窗口 10s -->
- [x] 1.3 `navigate_first_post_group_root`（`runtime.rs:327-337`）改为导航后等待落地再返回；
      落地失败按姿态类返回（可被纠正预算消费），**MUST NOT 复用帖子身份原因值**。
      <!-- aidcp-edge 994ac8b 具名 group_root_not_landed（姿态类），不复用帖子身份原因值 -->

## 2. aidcp-edge — 纠正预算与准备动作解耦

- [x] 2.1 `runtime.rs:191` 的 `root_navigated` 拆成两个变量：`prepared_navigation`（记准备阶段，仅供日志）
      与 `corrective_budget`（初值恒为满额、只被失败递减）。
      <!-- aidcp-edge 994ac8b 已拆；initial_first_post_corrective_budget 恒返回满额 -->
- [x] 2.2 `runtime.rs:227` 的自救分支改读 `corrective_budget > 0`；用后递减。
      <!-- aidcp-edge 994ac8b first_post_recovery_step 只看失败类别 + 预算余额，准备动作不是它的输入 -->
- [x] 2.3 预算耗尽的回执文案写「重试 N 次未成」，**不得**写成「做不到」。
      <!-- aidcp-edge 994ac8b 诊断分 retried_without_success / not_retried 两读数，叶子原因原样保留 -->

## 3. aidcp-edge — 下滚预算按失败类别消费

- [x] 3.1 把探测失败分成姿态类与身份类两组（穷举 `first_post_probe_failure` 的全部返回值，**不留兜底桶**；
      未识别的失败值按姿态类处置并具名标注）。
      <!-- aidcp-edge 994ac8b 三类穷举（姿态/身份/入参）；未识别值具名 unrecognized_probe_failure，不折进已有失败名 -->
- [x] 3.2 `select_first_post_candidate`（`runtime.rs:339-363`）循环：姿态类消费一轮后继续；
      身份类（绑定冲突 / 证据变了）立即返回。
      <!-- aidcp-edge 994ac8b 姿态类续跑、身份类立即返回 -->
- [x] 3.3 两类在返回值上可分，且能被上层与云端分别识别。
      <!-- aidcp-edge 994ac8b 原因与类别成对产出（FirstPostProbeFailure），回执写叶子原因、诊断带 failureClass -->

## 4. aidcp-edge — 群根同一性判定不因入参装饰而失败

- [x] 4.1 `facebook-router/40-group-join.js:173`：剥掉查询串与哈希后再比对，只对「非群地址形态」判无效。
      <!-- aidcp-edge 994ac8b 剥查询串/哈希后比对 -->
- [x] 4.2 该失败具名为「请求的群地址无效」，**MUST NOT** 复用帖子身份原因值。
      <!-- aidcp-edge 994ac8b 入参类（request）与身份类分开具名 -->

## 5. aidcp-edge — 测试

- [x] 5.1 Rust 单测：陈旧就绪文档不被当作已落地。
      <!-- aidcp-edge 994ac8b shared.rs 落地判据单测 -->
- [x] 5.2 Rust 单测：准备阶段跳过后，纠正预算仍为满额、自救分支可达（**这条是死分支的回归断言**）。
      <!-- aidcp-edge 994ac8b the_preparation_jump_never_shrinks_the_corrective_budget -->
      <!-- 已做突变验证：把预算接回准备动作（还原旧 bug）后，全 197 条 lib 用例中**唯有这一条**变红，
           命中首条断言「准备阶段跳过一次，纠正预算仍必须是满额」left 0 / right 1；反向还原后复绿。 -->
- [x] 5.3 Rust 单测：姿态类失败消费一轮后继续探测；身份类失败立即终止。
      <!-- aidcp-edge 994ac8b posture_failures_spend_a_scroll_round_while_identity_failures_stop_at_once -->
- [x] 5.4 JS 分片单测：带跟踪参数的群链接不再判无效；非群地址仍判无效且原因可分。
      <!-- aidcp-edge 994ac8b test/native-page-engine/facebook-router-contract.test.ts -->
- [x] 5.5 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全过。
      Rust 侧按 memory `native-engine-cargo-path` 取 cargo（不在 PATH，须指 rustup toolchain bin）。
      <!-- aidcp-edge 57d5a07 test:acceptance 39/39；npm test 3073 pass 0 fail 1 skip；typecheck exit 0；
           gate:native fmt+clippy+test OK（Rust 门禁只能经 scripts/gate-native.mjs 跑，直调 cargo 报 no such command） -->

## 5.6 追加（并行流交回）— 引擎诊断不得外泄原始页面串

- [x] 5.6 `log_first_post_group_root_decision` 原本把请求群路径与探针读回路径两个原始 URL 写进诊断行。
      `bounded_log_value` 只截长度、**截断不是脱敏**；同批的引擎诊断通路一打通，这些行会持续写进运营机日志。
      改为只报结论布尔量「当前地址是否落到请求的群根」，不匹配时「我在哪」由既有 `surface`（有限词表）回答。
      <!-- aidcp-edge 57d5a07 移除 expectedGroupPath / observedPath，新增 atRequestedGroupRoot；
           判据直接复用落地等待的 facebook_group_root_landed，杜绝两处对「群根」各有一份实现而漂移 -->

## 6. 交付

- [x] 6.1 `openspec validate restore-facebook-first-post-recovery --strict` exit 0。
      <!-- aidcp validate --strict exit 0 -->
- [ ] 6.2 提交推送 `aidcp-edge` master + 控制仓 main，回写本文件 sha。
      <!-- aidcp-edge 994ac8b + 57d5a07 已推 origin/restore-facebook-first-post-recovery（已 rebase 到 origin/master 0a36370）；
           合回 master 属集成步，留给 land 环节 -->
- [ ] 6.3 **不打安装包**（CLAUDE.md §6 长期授权：打包只在用户明确要求时做）。
      真机验收项登记 `docs/real-machine-acceptance-backlog.md`，写明「须等一次桌面打包才可观测」。

## 7. 明确不在本 change 范围（各自需配对的安全补充）

- 删除「区域唯一可解析」合取项 —— 必须与「给内容派生分支补同群校验」（`runtime.rs:459-473`，
  对照已有的 `:510-531`）**同批**落地，绝不只删不补。
- 查询串 / 哈希两项从硬合取降为「规范化后复测」。
