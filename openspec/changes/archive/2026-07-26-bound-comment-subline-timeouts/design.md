## Context

评论支线通过 `comment.appraising` / `comment.appraised` 把 `RoleDispatcher.commentInflight` 置为 true，并暂停 `SessionMonitor` 时钟；只有 `comment.skipped` 或 `comment.approved` 才释放钉页标志。这个机制解决了撰写 / 审批期间页面被滚走的问题，但也把“下游一定会产生终局”变成了浏览恢复的硬前提。

2026-07-20 dev 事故中，`CommentComposer` 收到 `comment.appraised` 后先执行 `getCorpusReferences()`。该调用被注释为 best-effort，却直接 `await` 无超时；Promise 悬空后既未进入 `browse:comment_composer` 模型调用，也未 emit `comment.skipped`。同一账号后续 `scroll` 与约四分钟后的 idle nudge 均被 `commentInflight` 正常抑制。现场执行相同 SQL 约 0.016ms，因此修复对象不是 SQL 计划，而是可选依赖与整条暂停窗缺少有界失败。

约束：

- 未获人审或结构化站立授权的评论绝不能下发；超时只能“不评并继续浏览”。
- 正常评论仍要在目标帖上等待，不能为了恢复浏览撤掉既有钉页保护。
- LLM 单次调用已有 180 秒默认上限，审批已有 90 秒窗口；新增总超时是最后保险，不能替代各阶段的局部超时。
- Cloud-only，不新增协议，不改 Edge。

## Goals / Non-Goals

**Goals:**

- 可选语料召回在 3 秒内未完成时按空参考继续撰写，并留下稳定降级日志。
- 评论暂停窗自 `comment.appraising` 首次进入起最多持续 15 分钟；重复 `comment.appraised` 不续期。
- 总超时只产生一次 `comment.skipped{reason:'comment_subline_timeout'}`，释放 `commentInflight` 并恢复看门狗。
- 超时后的迟到角色事件失效：不能重开暂停窗、不能发审批后的评论命令。
- 正常快速路径、既有 90 秒人审、mandatory auto-approve 通知和真实回执记账均保持。

**Non-Goals:**

- 不调大或调小全局 `AIDCP_LLM_TIMEOUT_MS`，不改变角色模型。
- 不取消 PostgreSQL 查询；超时后只忽略迟到的只读结果。
- 不新增评论自动重试、模板兜底或无人审直发。
- 不解决手动 / 排期 `CommentScheduler` 的边端租约问题；本 change 只处理浏览闭环内部 `RoleDispatcher` 评论支线。

## Decisions

### D1：可选语料召回采用短 `Promise.race`，超时 fail-open 到空参考

`CommentComposer` 新增可注入的 `corpusLookupTimeoutMs`，生产默认 3,000ms。召回与计时器竞速：成功则使用最多三条参考；异常或超时都回落 `[]`，但超时打印稳定 `corpus_lookup_timeout` 日志。计时器在任一终局清理并 `unref`；迟到数据库 Promise 的 resolve/reject 被竞速 Promise 消费，不形成 unhandled rejection。

选择 3 秒是因为该查询本地命中应为毫秒级，且它只增强 prompt，不值得占用可见浏览停留。备选“给 pg Pool 配全局 query_timeout”会影响同一 store 的归档与其他调用，范围过宽；备选“查询失败即跳过整篇评论”把可选增强错误升级成业务失败。

### D2：`commentInflight` 自身拥有不可续期的总 deadline

`RoleDispatcher` 在首次有效 `comment.appraising` / `comment.appraised` 时保存 note/source/actions 快照并启动总计时器；相同 note 的第二个入口保持幂等，绝不重新计时。生产默认 15 分钟，可由 `AIDCP_COMMENT_SUBLINE_TIMEOUT_MS` 正数配置覆盖；取较宽上限是为了不抢在既有多段 LLM 与 90 秒人审的正常超时前触发，它只兜住永不 settle 的异常。

计时器到点时先把本 note 标为 expired、清 `commentInflight`、恢复 `comment_subline` 时钟，再 emit 一次 `comment.skipped{reason:'comment_subline_timeout'}`。这样 `AuthorEvaluator` / 回 feed 仍走既有唯一终局出口，不另造导航分支。

备选“只修语料查询”可解决本次复现，但下一处未有界的审批端口 / 外部调用仍可能重现同一活锁；备选“让 idle nudge 绕过 `commentInflight`”会把页面滚离待评论目标，复活此前已修复事故。

### D3：超时 note 建立迟到事件墓碑，安全优先于迟到授权

dispatcher 生命周期内维护超时 noteId 集合。四段角色在异步 await 后、向下一段 emit 前检查墓碑；dispatcher 的 `enterCommentSubline` 与 `comment.approved` 也检查。命中即停止推进，迟到 approved 只记录 `late_after_comment_subline_timeout`，绝不下发评论。墓碑不在会话重启时清除，避免旧 Promise 跨会话回来后复活；集合只记录实际超时的 note，数量天然很小，随连接 runtime 销毁释放。

这意味着极端情况下已发送但迟到的审批卡可能最终不提交；这是诚实的 fail-closed 取舍，优于账号恢复浏览后在错误页面或错误时机发送旧评论。

### D4：两个超时均显式走服务装配并可测试注入

服务装配用现有 `readEnvNumber` 读取 `AIDCP_COMMENT_CORPUS_LOOKUP_TIMEOUT_MS`（默认 3,000）和 `AIDCP_COMMENT_SUBLINE_TIMEOUT_MS`（默认 900,000）；角色 / dispatcher 构造处再次做正数下限保护，非法值回落默认。测试复用 dispatcher 已有 `setTimeoutFn` / `clearTimeoutFn` 注入口，以短实时时限或受控计时器覆盖，不依赖不推进的固定业务 clock。

## Risks / Trade-offs

- [迟到审批卡可能已送达但评论被总超时作废] → 卡片授权不等于平台成功；dispatcher 丢弃迟到 approved 并写稳定日志，绝不假成功。
- [总超时过短误杀合法慢模型] → 默认 15 分钟，显著大于常见三段模型 + 90 秒审批路径；可按环境正数覆盖，局部 3 秒只作用于可选数据库参考。
- [Promise.race 不会取消底层 PG 查询] → 查询只读且结果被忽略；不尝试危险的跨 Pool 取消。总暂停状态已释放。
- [超时 skip 与正常终局竞态造成重复] → timer callback 与终局清理都先核对当前 note/state；首次结算清 timer，超时墓碑使迟到事件 no-op。

## Migration Plan

1. 在独立 `aidcp-cloud` worktree 实现局部语料超时、总 deadline、墓碑和稳定日志。
2. 聚焦测试覆盖 never-resolve 语料、总超时恢复、迟到 approved 不下发、正常路径不回归；再跑 acceptance、全量测试与 typecheck。
3. 合入并推送 cloud `master`，从干净 canonical checkout 部署 `dev`。
4. 验证服务、监听、健康接口、PostgreSQL 与日志；观察新连接正常浏览。回滚只需恢复前一 cloud master 提交并重启服务，无数据迁移。

## Open Questions

无。
