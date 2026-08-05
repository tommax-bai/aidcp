# Tasks

## 1. aidcp-edge — 「回通知首页」回到通知页并重报三栏

- [x] 1.1 把 Native 小红书规则脚本里「回通知首页」分支的目的地从信息流改为通知页：不在通知页则经通知入口进入并等页面身份成立，已在通知页则直接沿用；终局观测改为通知首页三栏未读读数。 <!-- aidcp-edge 04215b6 与 notification_open 收敛成同一份实现 enterNotificationHome(actionName)，只有失败回执的动作名不同——抄成两份正是本次故障那一类漂移的温床 -->
- [x] 1.2 该分支的失败保持诚实分型（入口找不到 / 点击未生效 / 导航未确认 / 分类栏读不到），分类栏读不到时回未确认，MUST NOT 回全 0 三栏读数；动作名保持 `notification_back_home`（云端失败恢复入口按该名匹配）。 <!-- aidcp-edge 04215b6 -->

## 2. aidcp-edge — 修正被锁错的契约与补测

- [x] 2.1 修正行为契约测试：原用例断言的是「回到信息流」，改为断言「回到通知页 + 终局是三栏读数」，并保留原有的「入口找不到 / 点不动 / 导航未确认」三态断言。 <!-- aidcp-edge 04215b6 xhs-navigation-command-contracts.test.ts：8 条 back_home 用例重写，成功路径断到具体读数（不只断「回了个通知读数」，否则栏与数字错位会漏过） -->
- [x] 2.2 修正回执声明对账表里这条命令的合法产出（信息流卡片 → 通知首页读数）。 <!-- aidcp-edge 04215b6 同时消除冻结缺口表里的两条（declared_but_unreachable:notification.home / reachable_but_undeclared:page.cards），FROZEN_GAP_BUDGET 14→12。注：command-manifest.json 本来就声明着 ["notification.home", "action.completed"]，无需改动，故能力摘要不变、打包侧期望常量不受影响 -->
- [x] 2.3 补一条用例：分类栏读不到时回未确认，且产出里不含任何三栏读数（守「不得用全 0 冒充已清零」）。 <!-- aidcp-edge 04215b6 另补一条正面回归守卫：页面上同时摆着首页入口与信息流卡片时，仍不得点它、不得回 page_cards -->
- [x] 2.4 更新 `command-postconditions.json` 里这条命令的后置证据（原文描述的是走岔了的 /explore 行为）。 <!-- aidcp-edge 04215b6 陈旧描述留着就会被后来者当事实转抄；该文件不参与能力摘要哈希（build.rs 只哈希 command-manifest.json），改动不触发打包侧常量 -->

## 3. 构建与验证

- [x] 3.1 重编 Native 引擎（规则脚本在构建期编进二进制，只改脚本不重编＝线上行为不变），确认构建脚本的 rerun 触发到位。 <!-- 2026-08-05 cargo 1.97.1（不在 PATH，须指 rustup toolchain bin）；产物摘要 8961ef46…51d7d。canonical checkout 的暂存产物已按新源码重建，`electron:dev` 起动时的 ensure 步骤本就会按源码摘要自动重建 -->
- [x] 3.2 跑 edge `npm run test:acceptance`、`npm test`、`npm run typecheck`，全绿。 <!-- 2026-08-05 acceptance 39/39；全量 3151 pass / 0 fail / 1 skip（AC-E2E gated）；typecheck 0。另 cargo test --release 24 个测试目标全 ok / 0 failed；land 时的 gate:native（fmt + clippy + test）通过 -->
- [x] 3.3 变异验证：把修好的分支临时改回「导航到信息流」，确认 2.1 / 2.2 的用例真的红——闸恒真通过就等于没有闸。 <!-- 2026-08-05 变异（back_home 直接 return done(cards())）→ 行为契约用例 8/8 转红。**但回执对账那条用例仍绿**：它的「可达产出」读的是测试文件里手工维护的 ROUTER_OUTPUTS 表、不是路由源码，所以 2.2 那处修改是「把声明改对」，不承重。承重的是 2.1/2.3 的行为用例。该手抄表的对账缺口另见 4.4 -->

## 4. 收口

- [x] 4.1 `openspec validate restore-notification-home-return --strict` 通过。
- [x] 4.2 合回 edge `master` 并推送；控制仓 change 与 tasks.md 回写 sha（sha 必须取自已推送的提交）。 <!-- aidcp-edge master 04215b6（origin/master 已 ff 到该 sha）；worktree/分支已清理 -->
- [x] 4.3 登记真机验收项到 `docs/real-machine-acceptance-backlog.md`：一趟巡视要走完「评论和@ → 回通知首页 → 赞收藏 → 回通知首页 → 新增关注 → 三栏清零 → 回信息流」，并确认「赞收藏 / 新增关注看一眼是否真清零」。桌面安装包不在本 change 收尾范围（按 CLAUDE.md §6，打包需用户显式触发）。 <!-- 簇 136，5 项 -->
- [x] 4.4 登记后续缺口：回执对账用例的「可达产出」表（`runtime-contracts-command-receipts.test.ts` 的 `ROUTER_OUTPUTS`）是手工维护的，与路由源码之间没有任何机械对账——本次变异验证当场证实它抓不住实现走岔。归属 `harden-native-engine-runtime-contracts`，不在本 change 扩范围。
