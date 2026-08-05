# Tasks

## 1. aidcp-automation — nurture provider over the sync-read mirrors

- [x] 1.1 Add an adapter that builds the account-nurture provider from the mirrors the process already keeps: account platform and creation time from the account projection, slow-start anchor and graduation time from the environment stream, Facebook curve from the operation-policy stream.
<!-- aidcp-automation 40b66d2 src/automation-nurture-provider.ts -->
- [x] 1.2 Express "the Facebook curve stream has never arrived" as **the method being absent**, not as a method returning empty or zero — the consumer's contract only accepts absence that way, and an empty curve would claim "this account has no daily ceiling".
<!-- aidcp-automation 40b66d2 实现为 getter：流的到位与否是运行期事实，取用口只构造一次，
     getter 是唯一能表达「按次判断在不在」的形态。消费方第二处取用 `?.().totalDays` 正是
     「存在但返回 undefined」会当场炸的那一处，用例按其逐字写法求值。 -->
- [x] 1.3 Keep every answer synchronous, IO-free and non-throwing; the consumer calls it on the per-action admission path.

## 2. aidcp-automation — composition root wiring

- [x] 2.1 Construct and initialise the safety-limit configuration store before the risk foundation, and pass it as the quota provider (the panel registration stays where it is).
<!-- aidcp-automation 40b66d2 新增第 3b 段；原第 1640 行那份构造删除，面板与判定共用同一实例 -->
- [x] 2.2 Pass the nurture provider, plus the two slow-start environment levers read in this process, into the risk foundation.
- [x] 2.3 State at startup which of the two current-read inputs are wired and, when one is not, what stops working because of it.
<!-- aidcp-automation 40b66d2 automation-risk-foundation.ts：接线成功一条 log，各自缺席一条具名 warn -->

## 3. Regression coverage

- [x] 3.1 Adapter unit coverage: fresh anchor is passed through; ambiguous or missing binding answers null; the curve method is absent while its stream is uninitialised and present once it is fresh.
<!-- aidcp-automation 40b66d2 test/acceptance/automation-nurture-provider.test.ts，5 例 -->
- [x] 3.2 Composition coverage: the risk foundation receives both inputs, so removing either one fails a test rather than silently changing behaviour.
<!-- aidcp-automation 40b66d2 test/acceptance/automation-main.test.ts 追加 2 例（结构断言）。
     变异验证：删掉 `nurture:` 那一行后该用例当场红且点名到具体项，恢复后复绿。 -->

## 4. Validation and delivery

- [x] 4.1 `npm run test:acceptance`, `npm test`, `npm run typecheck` in `aidcp-automation`.
<!-- acceptance 271/271 通过（新增文件需在 boundaries/ownership-rules.json 手工登记 + boundaries:refresh，
     否则派生归属账本 missing=1 直接红）；typecheck 干净；全量 npm test 2201 例中 4 例失败，
     **同一 commit 的 canonical master 上原样失败**（publish-agent 的 command-sequencer / fill-budget
     四例），与本 change 无关、未修。 -->
- [x] 4.2 `openspec validate restore-automation-risk-quota-inputs --strict`, integrate to `master`, push, deploy dev, and record evidence here.

## Delivery Evidence

- Repository `aidcp-automation`, commit `40b66d2` on `master` (rebased onto `65c88c8`, fast-forward).
<!-- 2026-08-04 deployed dev -->
- dev 部署 2026-08-04 20:13–20:16：备份 `automation.bak.20260804-201312.tar.gz` + `.env` 备份 →
  rsync（排除 `.git` / `node_modules` / `.env`）→ ECS 上 typecheck 干净 → 只重启 `aidcp-automation`
  （`aidcp-cloud` 单体此前已 stop + disable，故不会被交回写者锁）。
  启动日志出现新的接线行：`配额判定输入已接线：限额配置 + 养号事实（慢启动全局停用=关，年龄爬坡=关）`；
  8787 / 8094 均在，`NRestarts=0`，api / content 未动，isales 未碰。
- **真机验到（非推断）**，经 `127.0.0.1:8094` 的只读投影口逐账号打过：
  - 带今日锚点的 Facebook 账号（如 `61579018543302`）：`slowStartView` 回
    `state=active day=1 totalDays=5 binding=true`；`effectiveQuotas.day` = 浏览 20、其余全 0
    （分钟 2 / 小时 5 由日额派生）。`totalDays=5` 与 like=0 都不是编译期曲线的值 ⇒
    读的是**运营在后台配的那张表**，不是写死默认。
  - 无锚点账号（`default`）：日额 = 浏览 150 / 点赞 50 / 评论 8 / 关注 15 / 搜索 10 / **加群 20**，
    小时 = 浏览 150 / 评论 10 / 加群 10。加群日额与三项小时值都是 `quota_config` 里运营改过的数字
    （编译默认分别是 3 / 38 / 2 / 1）⇒ 限额配置这一路也真的接上了。
- 修复前的对照（同一台 dev，2026-08-04 19:26 客户端面板）：日额 150 / 10 / 50 / 8 / 15 / 1 / 3，
  逐位等于编译期 `normal` 档 + 按日额换算的时分窗口，两路输入都没生效。
- 顺带观察：本次重启后，此前每 10 秒复发的两条同步读拒收（`account_persona` /
  `automation_account_projection` 的 `same_cursor_payload_drift`）不再出现，账号投影恢复新鲜——
  这也是本次能真验到 clamp 的前提。**MUST NOT 读成「那个缺陷已修」**：它只是被重启清掉了内存游标。

## Deliberately Out of Scope

- The dev account-projection sync-read stream rejecting every refresh (`same_cursor_payload_drift`). It is a separate defect with its own shape; recorded here because it gates whether this change can be observed at all, and because this restart cleared it without fixing it.
- The old monolith service on dev. It was already stopped and disabled by the deploy that preceded this one.
