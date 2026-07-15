# Tasks — comment-approval-target-hold

> cloud-only（`aidcp-cloud`），边缘无改动。`role-dispatcher.ts` 为热点单写文件、与活跃 change `lease-strict-preemption` + `mandatory persona interactions` 同区 → 集成串行：landed 前经两轮 rebase 解冲突（reconcile 了 mandatory auto_approve 豁免）。
>
> **实装偏离说明（landed decd7f1）**：进入暂停态**不用** `setBrowseSuspended`（那是布尔、与巡视/昵称采集并发会互相覆盖），改用 **dispatcher 私有 `commentInflight` 布尔**在 `sendCommand` 统一出口与 `browseSuspended` 取并集——各自独立、互不覆盖。`should_end` 推迟由 **`pauseClock('comment_subline')`（refcount by reason）** 自然实现（checkSession 在 clockPaused 时 early-return + resume 补发），无需单独 stash。起点 = `comment.appraising`（appraiser 过阈后经微任务 emit，排到 like/collect 下发之后）+ `comment.appraised` 两入口，`enterCommentSubline(noteId)` 幂等、以 `currentNote` 命中为守卫；终局 `comment.approved` 先清 `commentInflight`、`comment.skipped`/`comment.done` resumeClock。

## 1. aidcp-cloud — 评论支线暂停态（进入 / 出口）

- [x] 1.1 进入暂停态覆盖评估-LLM/撰写/去AI味/审批全程：起点前移到 `comment.appraising`（+`comment.appraised`）经 `enterCommentSubline` 置 `commentInflight` + `pauseClock('comment_subline')`。<!-- aidcp-cloud decd7f1 commentInflight 私有标志入 sendCommand 出口；comment.appraising 经微任务 emit 避免扣住本次互动 -->
- [x] 1.2 终局解除（D4）：`comment.approved` 先清 `commentInflight` 再下发评论/迁移；`comment.skipped`/`comment.done` resumeClock。<!-- aidcp-cloud decd7f1 -->
- [x] 1.3 防"同步 skip 卡死"：`currentNote?.noteId===noteId` 守卫（命中=下游走 await、不同步 skip）。<!-- aidcp-cloud decd7f1 test(c2)+platform-browse-protocol 回归 -->
- [x] 1.4 并发复用处理：不复用 `browseSuspended` 布尔，改 dispatcher 私有 `commentInflight` 与之在出口取并集；`pauseClock` refcount by reason 与 patrol/view_quota 并存。<!-- aidcp-cloud decd7f1 -->
- [x] 1.5 移除旧 `approvalInFlight` 单点补丁（全仓已无 code 引用）。<!-- aidcp-cloud decd7f1 -->

## 2. aidcp-cloud — 覆盖两条滚走源 + 推迟结束

- [x] 2.1 撰写窗 no_target 重扫（H1）：`rescan_after_stale_target` 经 sendCommand 被扣 + 显式 `commentInflight` 早退门控。<!-- aidcp-cloud decd7f1 test(a)(h) -->
- [x] 2.2 审批窗 stray 命令（H2）：`open_note`/`scroll`/`refresh`/feed 续滚经 sendCommand 全扣。<!-- aidcp-cloud decd7f1 test(b) -->
- [x] 2.3 推迟 `session.should_end`（D3）：`pauseClock('comment_subline')` → checkSession early-return，终局 resumeClock 补发。<!-- aidcp-cloud decd7f1 test(c) -->

## 3. aidcp-cloud — 测试（回归纪律：先 test:acceptance 再全量再 typecheck）

- [x] 3.1–3.5 acceptance/回归：role-dispatcher.test.ts 新增 (a)-(h) 八例（撰写窗 no_target 不重扫 / stray 命令全扣+终局恢复 / pauseClock-resumeClock 接线 / currentNote 守卫防卡死 / 终局先清后发 / 抢占解冻 / 迁移抑制收敛 / 巡视让位+补跑 / appraising 覆盖窗）；platform-browse-protocol.test.ts 更新 2 例到新起点。<!-- aidcp-cloud decd7f1 -->
- [x] 3.6 红线保持：AC-PUB / AC-PROTO 全过；XHS 直发路径零回归。<!-- aidcp-cloud decd7f1 acceptance 54/54 -->
- [x] 3.7 `test:acceptance`(54/54) → `test`(2247 pass/0 fail) → `typecheck` 全过。<!-- aidcp-cloud decd7f1 -->

## 3b. aidcp-cloud — 对抗性复核修复（wf_71b324de：5 CONFIRMED，全修 + 回归）

- [x] A 被抢占（lease-strict-preemption）的 comment/迁移 open_note 回执在 action.completed 原因级短路前解除 comment_subline 时钟暂停 + 清 pending（尊重抢占语义，不 emit done）；只对 comment/open_note 动作解冻，不误清非评论动作在途的 commentInflight。<!-- aidcp-cloud decd7f1 test(e) -->
- [x] B FB 两步迁移 open_note{navigate}/comment 检 sendCommand 返回值，被软暂停/配额拦下时清 pending + emit 终局收敛（不永冻时钟），对称直发路径已有守卫。<!-- aidcp-cloud decd7f1 test(f) -->
- [x] C NotificationGatekeeper.admit 让位评论支线（记 deferredForComment、终局微任务补跑；unsubscribe 清残留防跨场 spurious 巡视）。<!-- aidcp-cloud decd7f1 test(g) -->
- [x] D appraiser-LLM 残留窗：CommentAppraiser 过阈后经微任务 emit `comment.appraising`，dispatcher 提前置位覆盖该窗。<!-- aidcp-cloud decd7f1 test(h) -->

## 4. 集成 / 部署 / 回写

- [x] 4.1 合入 master：两轮 rebase 解 `role-dispatcher.ts` 与 mandatory-persona/其它已 landed change 的冲突（reconcile mandatory auto_approve 豁免 + mandatoryInteraction 透传），复跑 acceptance+full+typecheck 全绿。<!-- aidcp-cloud decd7f1 landed master -->
- [x] 4.2 默认部署 `dev`：clean snapshot(git archive decd7f1) rsync（deps 未变、免 npm ci）→ restart → healthcheck 全绿（svc active / 8787+8090 监听 / 飞书长连接已建立 / 无错误、无重启循环）。<!-- 2026-07-15 deployed dev 121.89.85.150; 备份 cloud.bak.20260715-211742.tar.gz -->
<!-- 注：dev 部署即当前 master decd7f1，含同批 landed 的 mandatory-persona/auth/migrations/feishu-queue 等他人 change（dev 追随 master）。 -->

- [x] 4.3 tasks.md 回写 commit-sha；真机灰度项归 `docs/real-machine-acceptance-backlog.md`。<!-- 见 backlog 簇 -->
- [x] 4.4 `openspec validate --strict` 通过 → landed+deployed → archive（真机验收解耦到 backlog 簇4）。<!-- 2026-07-15 archived -->

