# Tasks — delegated-terminal-failure-reason

> 单仓变更：全部落 `aidcp-cloud`（`../aidcp-cloud`，默认分支 `master`）。中控仓只回写本文件。
> 实装前先 `ls -d ../aidcp-cloud` 确认 sub-repo 存在（CLAUDE.md §0）。

> **落地**：全部改动在 `aidcp-cloud` 一个提交里 —— `<!-- aidcp-cloud b5a3302 landed on master -->` `<!-- 2026-07-16 deployed dev（backup cloud.bak.20260716-203650.tar.gz，healthcheck 绿）-->`
> 部署源＝`git archive b5a3302` 干净快照（主 checkout 有他人残留文件 `1`，按 CLAUDE.md §6 不从脏工作区 rsync）。

## 1. aidcp-cloud — store 读路径

- [x] 1.1 `src/delegated-task/store.ts` 的 `DelegatedTaskStore` 接口加 `listAttempts(taskId: string): Promise<DelegatedTaskAttempt[]>`（放在 `listUnsettledAttempts` 旁；**不动**后者）
- [x] 1.2 PG 实现：`SELECT * FROM delegated_task_attempts WHERE task_id=$1 ORDER BY ordinal`，复用 `mapAttempt`（走现有索引 `idx_delegated_task_attempts_reconcile`）
- [x] 1.3 memory 实现：按 `taskId` 过滤、按 `ordinal` 排序、`structuredClone` 返回（与既有方法同构）
- [x] 1.4 单测：已 settle 的 `failed` 在 `listAttempts` 结果里、而 `listUnsettledAttempts` 对其返回 `[]`（D2 支点，防有人把两者合并）
      <!-- 偏离：只测 memory 实现——PG 需真库、本地跑不了；PG 侧 SQL 与相邻方法同表同列，风险登记为真机项 7.1 -->
      <!-- 偏离：未做「两实现返回同序同内容」对拍（同上，PG 本地无法实例化）；按 memory「test-case-restraint」克制 -->


## 2. aidcp-cloud — 原因人话化（新文件、纯函数、无热点）

- [x] 2.1 新建 `src/delegated-task/reason-humanize.ts`，导出 `humanizeAttemptReason(reason: string): string`
- [x] 2.2 精确码白名单：`needs_persona_setup` / `candidate_record_missing` / `today_inspiration_unavailable` / `candidate_missing_during_reconcile` / `duplicate_target` / `empty_body` / `account_required`
      <!-- 实装时另补：candidate_not_found_after_write / candidate_account_or_platform_mismatch / candidate_id_or_version_missing / candidate_patch_missing / curated_target_snapshot_missing / duplicate_attempt_target / submitted_result_unknown -->
- [x] 2.3 前缀式白名单：`risk_status(` / `risk_denied(` / `executor_exception:`（保留括号内状态值与异常原文）
      <!-- 另补前缀：candidate_approval_ / candidate_write_ / candidate_version_conflict( -->
- [x] 2.4 阶段级码（**精度上限，勿超**）：`candidate_terminal_<status>` / `publish_<status>` → 只表述到「稿件在发布派发阶段失败」层级，MUST NOT 渲染成具体边缘原因（spec「失败原因的精度不得超过已落库的证据」）
- [x] 2.5 未命中一律**原样透传**；超长裁到 ~120 字符并保留原文可辨识片段（中间截断，头尾都保住——异常文本的尾巴常是真因）
- [x] 2.6 单测：已知码翻中文；中文句原样；未知码原样（红线用例）；`risk_status(warned)` 带出状态值；派发期只说到阶段；超长裁剪后仍可辨识

## 3. aidcp-cloud — finishBudget 追加原因

- [x] 3.1 `src/delegated-task/worker.ts` 加 `budgetFailureSuffix`：读 `store.listAttempts`，取最后一条已 settle、非成功、`reason` 非空的 attempt。`listAttempts` 抛错则退回「只有记账」的既有行为并记日志——读原因失败绝不能连累终态收敛
- [x] 3.2 四支拼接（design D3），并抽出 `budgetHeadline` 供两个终态点复用
- [x] 3.3 既有前缀 `已达到最大尝试次数 / 已到截止时间；真实完成 N/M。` **原样保留**（追加而非替换）——既有子串断言实测仍过
      <!-- 偏离（收益向）：原因串收尾标点各家不一，统一剥尾标点再收句，免得拼出「…未生成稿件。（共 2 次尝试）」断句 -->
- [x] 3.4 `expireDueTasks` 的 deadline 终态同样接入（无 token 路径）
- [x] 3.5 `finishCancelled` **不接**（用户主动取消、自知原因），确认无回归
- [x] 3.6 单测：四支各一例；「全 deferred 耗尽」用例断言 `failureCount===0 && skippedCount===attemptCount`、文案为「N 次均未真正开始」且 **doesNotMatch 「最后一次未成原因」**（红线：不得暗示已在平台上动过手）

## 4. aidcp-cloud — 卡片顺手 additive

- [x] 4.1 `src/server.ts` 的 `onTaskUpdated` 失败卡调用点补 `platformName`
      <!-- 偏离（收益向）：用 platformRegistryEntry(task.platform).displayName 取展示名（「Facebook」/「小红书」），
           而非同类调用 server.ts:1577 那样直传原始 id（'facebook'）——卡是给运营看的，不该吐生 id -->
- [x] 4.2 确认 `delegatedTaskFailureReceipt`（`notification.ts:41`）无需改动——它已整段转发 `terminalOutcome.message`（本 change 零改动该文件）

## 5. 回归与验证

- [x] 5.1 `npm run test:acceptance` → 54/54 绿（含 `AC-PUB-*` / `AC-RISK-*`）
- [x] 5.2 `npm test` 全量 → 2298 pass / 0 fail / 5 skipped（既有子串断言实测仍过）
- [x] 5.3 `npm run typecheck` → 干净（`tsconfig.json` include 覆盖 `test/**`，故桩 store 若漏实现 `listAttempts` 会当场炸——实测无桩实现该接口）
- [x] 5.4 真驱一遍：memory store + 桩执行器 → 真 worker 终态 → 真 `delegatedTaskFailureReceipt` → 真 `buildCommandResultCard`，打印卡片正文肉眼核五支（撞车 / 全让开 / 编排真失败 / 混合 / 无原因可取），全部符合预期

## 6. 集成与部署

- [x] 6.1 `scripts/land-change aidcp-cloud … --yes` → rebase 到 origin/master（并发方 `f4a831e` 已在前）→ ff push → `b5a3302`；worktree/分支已清理
- [x] 6.2 部署前探 ECS：md5 比对确认本次改动未上线；确认 20:23 有并发方部署过、以 master 全树覆盖即含其改动
- [x] 6.3 安全序列部署 dev：备份 `cloud.bak.20260716-203650.tar.gz` + `.env.bak` → rsync 干净快照 → restart → healthcheck 全绿（active / 8787 + 8090 监听 / 飞书长连接已建立 / PG 就绪 / `DelegatedTaskWorker 已启动` / 无模块语法错误）；isales 80/8000 未受影响
      <!-- --delete 事后核对：与备份 diff，删除文件数 = 0（ECS 树本就等于 git 内容），非破坏性 -->
- [x] 6.4 回写本文件（sha `b5a3302` 已用 `git merge-base --is-ancestor` 确认是 origin/master 祖先）

## 6b. code review（high）抓到的真问题 — 本批一并修（均补回归测试）

> 全部 CONFIRMED，且都不是「风格」类。前两条是**我自己新代码的诚实性 bug**，第三条是修了第二条才暴露的。

- [x] 6b.1 **「均未真正开始」原本是拿不出证据的断言** — 原判据 `skippedCount === attemptCount`，但 `skipped` 同时覆盖「让开、执行器没跑」与「执行器跑了、搜了词开了页、最终判定不写」（`executors.ts:122-127` 的 `no_strong_candidate` / `note_not_found` 等），两者计数完全一样 → 会对「浏览器真的动过」的局面宣称平台没被碰过。改为**证据判据**：新增 `verificationKind: 'not_started'`（仅 deferred 前置让开时写，`verification_kind` 是无约束 TEXT → 零迁移），要求每条已 settle 的 attempt 都留下该证据。
      <!-- 回归测试已反向验证：把判据退回计数器版 → 新测试当场变红（2 fail），确认非装饰性用例 -->
- [x] 6b.2 **到期失败一张卡都不发（纯静默，红线）** — `expireDueTasks` 裸调 `store.complete`、绕过 `update()`，而 `update()` 是 `onTaskUpdated` 的唯一触发点（`grep onTaskUpdated` 全仓仅 3 处）→ 到期终态零通知，本 change 新写的原因在这条路上算出来就被丢掉。包上 `update()`。**用户 2026-07-16 明确授权纳入本批**（原范围只含「加失败原因」）。
- [x] 6b.3 **承 6b.2：到期时若派发仍在途 → 会谎报干净失败** — 租约失效 / 进程重启后 attempt 停在 `dispatched`，平台**可能已写入**；原逻辑排除在途 attempt、转而把更早那次的良性原因（如 `no_targets`）当成本次结局报出 → 反向假确定性。改为诚实标记 `submitted_result_unknown` + `submittedUnknown: true`，不叠加确定原因。（`processClaimed` 对同一状态早有此支，`expireDueTasks` 从前没有）
- [x] 6b.4 **人话化只接了预算终态** — `needs_persona_setup` 这类**只走** `non_retryable_failure` 那条路（blocked → `retryable:false`），从不经预算终态 → 白名单里最常见的几条永远吐生码给运营。`afterSettledAttempt` 的 fatalReason 也接上 humanize。
- [x] 6b.5 **原型链键裸取** — `EXACT[raw]` 对 `toString` / `constructor` / `__proto__` 会拿到 Function 并通过 truthy 判定返回；声明是 `Record<string,string>` → **typecheck 看不见**（同 CLAUDE.md §2 点名的裸 string 盲区）。后果不是文案难看，是调用方 `.replace()` 抛错、终态收敛被打断。改用 `Object.hasOwn`。

**评审提出但判定不改（记录理由，非遗漏）**：
- 「最后一次未成原因」在「末次成功但未达目标」时指向更早那次 → 措辞本就是「最后一次**未成**」，属实且正是缺口原因，不改。
- 评论家族 `max_attempts` 的原因到不了飞书卡 → 设计如此（`notification.ts` 对该支返回 null 防与评论链双发），原因仍可在后台 / API 读到。

## 7. 真机验收与收口

- [x] 7.1 真机项登记 `docs/real-machine-acceptance-backlog.md` 簇 86.23-86.27（含 PG `listAttempts` 只在 memory 实现上跑过单测、须真库验证一项）
- [x] 7.2 后继 change 登记（**勿静默**）：① `already_running` 类被误判可重试、1 秒热重试 2 秒烧光预算（`executors.ts:133` 死判断 + `publish-scheduler.ts` 形状，须串行）——**本投诉第一放大器**；② `failedAt` 落库抬精度天花板（`publish-log-store` + dispatcher）；③ `approvalCard.error` 从不被读致 `waiting_approval` 静默躺到 deadline；④ **（评审新增）** 起跑前停滞原因（`waiting_ownership` / `scheduler_busy` / `duplicate_target`）只写进 events 表、从不落 attempt 行 → 全程卡在等占用直到到期的任务，卡上仍只有记账（本 change 的覆盖缺口，非回归）；⑤ **（评审新增）** 异常原文未转义即进 lark_md 卡体，可能糊掉卡片排版（低危，卡是内部运维向）
- [ ] 7.3 与并发 change `facebook-write-action-visibility` 对账（若其落到 `publish-log-store` / dispatcher 则与本变更互补，避免重复造）
- [ ] 7.4 `openspec validate delegated-terminal-failure-reason --strict` → archive（MODIFY `user-delegated-tasks`，若同期另有 change 同改该 capability，归档须串行）
