## 1. Cloud customer content boundary

- [x] 1.1 Add account-scoped curated list/detail storage reads with SQL-level creatable filtering, consistent total, limit/offset bounds, and honest null counts.
- [x] 1.2 Add customer-auth curated list/detail routes that recheck `client_env_scope` ownership per request and return a minimum-disclosure DTO.
- [x] 1.3 Add the customer reference-creation route using the server-owned curated snapshot and existing structured delegated-task queue, with stable honest rejection reasons.
- [x] 1.4 Add Cloud storage and customer-auth tests for pagination, DTO disclosure, cross-account isolation, ownership revocation, reference modes, queue receipts, and rejection paths.
  <!-- aidcp-cloud: commit 1daec99 on codex/client-content-workspace-navigation; focused store/client-auth tests 45/45. -->

## 2. Edge authenticated bridge

- [x] 2.1 Add main-process customer API helpers and narrow IPC handlers for curated list, detail, and reference creation using the selected environment.
- [x] 2.2 Expose typed/validated preload methods without exposing customer tokens, arbitrary URLs, or unverified account selectors to the renderer.
- [x] 2.3 Add Edge main/preload tests for request construction, session failure, selected-environment scoping, and honest error propagation.
  <!-- aidcp-edge: renderer receives only named IPC methods; static security tests lock path/method/parameter allowlists and main-owned token/envKey injection. -->

## 3. In-window content workspace

- [x] 3.1 Add the shared content workspace shell and page-stack navigation while preserving titlebar, environment rail, runtime health, close-to-home, and back behavior.
- [x] 3.2 Implement the current-account inspiration library with creatable/all filters, pagination, loading/empty/error states, honest count rendering, and per-account list-state restoration.
- [x] 3.3 Implement inspiration detail and reference-mode confirmation with image availability gating, request busy state, queue receipt, and no false generation/publish success.
- [x] 3.4 Replace the draft preview drawer with a full main-content review page while preserving approve/cancel, non-optimistic image deletion, version CAS, last-image guard, and named failures.
- [x] 3.5 Add stale-response and account-switch invalidation so old list/detail/draft state cannot render under a new account.
- [x] 3.6 Add renderer tests covering navigation restoration, pagination/filtering, reference-mode gating/receipts, draft review safety states, and account switches.
  <!-- aidcp-edge: commit 02268ec on codex/client-content-workspace-navigation; final focused content/companion tests 63/63. -->

## 4. Validation and handoff

- [x] 4.1 Run focused and full Cloud tests plus typecheck; record any unrelated baseline failures without masking them.
  <!-- aidcp-cloud: focused 45/45; npm test exit 0; acceptance 54/54; npm run typecheck pass. No baseline failures observed. -->
- [x] 4.2 Run focused and full Edge tests plus typecheck without invoking Electron packaging; record any unrelated baseline failures without masking them.
  <!-- aidcp-edge: focused 63/63; npm test 1506/1506; acceptance 22/22; npm run typecheck pass; syntax checks pass. No packaging invoked and no baseline failures observed. -->
- [x] 4.3 Run `openspec validate client-content-workspace-navigation --strict`, update this checklist with repo commit SHAs/validation notes, and push only the isolated feature branches without merging or deploying.
  <!-- Strict validation passed. aidcp-cloud 1daec99 and aidcp-edge 02268ec were pushed to codex/client-content-workspace-navigation. The control-repo commit is recorded by this checklist's own history. No default branch merge, deploy, Electron package, or PR was performed. -->

## 5. Compact titlebar inspiration entry

- [x] 5.1 Add an account-scoped authoritative reference-draft count to the customer curated-list projection without exposing publish rows or internal fields.
  <!-- aidcp-cloud d2437a8: counts persisted publish_log rows with source_reference for the authorized envKey; queued-only tasks are excluded and an unavailable count is omitted instead of fabricated. -->
- [x] 5.2 Replace the runtime-home inspiration card with the compact titlebar reserve entry, including honest unknown/zero states, accessible entry labeling, bounded reserve fill, and the approved blue/teal palette.
  <!-- aidcp-edge 174af20: uses a main-owned fixed summary IPC, 30-item visual saturation, independent draft facts, and per-account stale-response invalidation. The old home card is removed. -->
- [x] 5.3 Add focused Cloud and Edge tests for count semantics, account isolation, summary refresh, navigation, stale responses, and color/state classes.
  <!-- Cloud focused 14/14 and typecheck pass; the full Cloud suite also passed 2276 with 5 gated skips. Edge content/security focused 10/10, companion/content regression 66/66, syntax checks, and typecheck pass. -->
- [x] 5.4 Run proportionate tests and typechecks, validate OpenSpec strictly, commit and push only the isolated feature branches, and do not merge, deploy, or package.
  <!-- Strict validation passed. Cloud d2437a8 and Edge 174af20 were pushed on codex/client-content-workspace-navigation. The control-repo checklist commit is pushed after this note. No merge, deploy, or package was performed. -->

## 6. Adversarial review fixes（2026-07-17，多 agent 对抗式评审后）

评审覆盖租户隔离 / 诚实红线 / 渲染层状态机 / 稿件审批回归 / spec 一致性 / 测试质量六个维度，
每条发现经三名「默认证伪」的复核 agent 独立复核。下列为存活并已修的项；每条修复都做了**变异验证**
（把修复改回原样，对应测试必红），确保不是又一条空过的断言。

- [x] 6.1 `countReferenceDraftsForAccount` 把从未生成的稿计成「已成稿」。PublishExecutor 有两条**出生即 failed**
      却照样写 `source_reference` 的路径（M=0 全部生图失败 / 合规闸否决），客户标题栏据此虚报成稿数（静默假成功红线）。
      改为排除 `status='failed'`。已知保守偏差（宁可少报绝不虚报，已写进 docstring）：到过待审、后被
      PublishDispatcher 置 failed 的行也被一并少计——当前 schema 无「是否到过待审」的列，SQL 层无法区分两类 failed。
  <!-- aidcp-cloud 5b62ca0 on codex/client-content-workspace-navigation -->
- [x] 6.2 `POST /curated-contents/:id/create-post` 原样回 `createDraft` 结果，把服务端内部视觉诊断泄漏进客户域
      （`task.sourceConstraints` 里的 `referenceImages[].formGuess.{model,provider}` 与
      `visualAnalysis.{provider,model,cacheKey,…}`，且 `buildDelegatedTaskConfirmation` 又把它们字符串化进
      `confirmation.constraints`），与同文件 list/detail DTO 特意剥掉这些字段的约定正面冲突，并可经既有
      `GET /delegated-tasks` 二次读出。改为显式窄回执 `{triggered, created, task{id,status,version}}`；
      服务端任务行仍保留完整快照供下游 referenceNote 使用。
  <!-- aidcp-cloud 5b62ca0 -->
- [x] 6.3 `listForClient` 在 offset 越过结果集末尾时把 total 谎报为 0（`COUNT(*) OVER()` 无行可读），
      陈旧页码会让 UI 宣称「精选池还是空的」。零行且 offset>0 改为按同一筛选条件补一次独立 COUNT。
  <!-- aidcp-cloud 5b62ca0 -->
- [x] 6.4 每次状态心跳把首页从开着的灵感库 / 稿件审核底下掀出来。`#legacy-workspace` 显隐是两个工作区共享的状态：
      互动工作区 `setVisible(false)` 无条件归还首页，而 `render()` 对所有非视频号账号每次心跳都会走到它；
      内容工作区在「账号未变」分支直接早返回、不重新主张自己的可见性。两端同修。
  <!-- aidcp-edge 901ea91 -->
- [x] 6.5 `createBusy` 永久泄漏：陈旧响应守卫写在解锁**之前**，请求在途时离开创作页即把锁留死，
      回到创作页只剩禁用的「正在排队…」。解锁移到守卫之前。
  <!-- aidcp-edge 901ea91 -->
- [x] 6.6 同一分钟内重复提交被去重到已在执行 / 已完成的同一任务时，UI 把「非 queued」一律报成失败——
      对已受理的任务谎报失败，会把操作员推去再点一次、反而制造重复稿件。改为所有已受理状态如实回报，
      只有 cancelled/failed 与未知状态才算未受理。
  <!-- aidcp-edge 901ea91 -->
- [x] 6.7 汇总读失败后标题栏永远宣称「数据加载中」（aria-busy=false、无错误态）——未加载 / 加载中 / 失败
      三态都塌进同一个空值。补显式失败态。储备条另把「未知」画成 0% 宽度、与真实「0 条」像素级等同，
      改为 `.is-unknown` 虚底纹以区分。
  <!-- aidcp-edge 901ea91 -->
- [x] 6.8 测试质量：IPC 安全测试以源码正则替代行为断言（改等价写法即红、真坏了却可能绿），
      且边界正则未右锚——`limit > 50` 同样匹配放宽后的 `limit > 5000`，offset 校验根本没断言。
      收敛为只保留源码层真能证明的静态约束（通道 / 路径 / 方法白名单、envKey/token 只由 main 注入），
      行为一律移到 jsdom 可执行测试；补 offset 断言与 preload 切片非空守卫（防 doesNotMatch 对空串永真）。
      另补齐 3.5 的账号切换失效保护——原先 3 个守卫点只覆盖 1 个（变异验证：删掉详情页守卫，旧套件仍全绿）。
  <!-- aidcp-edge 901ea91；变异验证 5/5：逐条改回原样，对应测试必红 -->
- [x] 6.9 复核后**未采纳**的报告项（记录以免重复排查）：
      「渲染层直接联网」不成立（`cleanReferenceUrl` 已有 http/https 白名单，且为既有未改行为）；
      「preload 切片塌成空串致断言空过」在分支尖端不成立（实测切出 373 字符真实代码，仍加了非空守卫防回归）；
      「跨仓 edge→cloud 契约错配」经逐字手工执行证伪（契约当前正确，只是零测试覆盖）；
      「入口计数读错字段永远显示 —」已被 174af20 自身修掉；
      `openDraft` 在无 envId 状态下静默 no-op 属实但生产不可达（主进程始终注入真实 envId），仅影响测试可信度。
  <!-- 无代码改动；结论来自复核 agent + 本地实测 -->
- [x] 6.10 回归闸：cloud acceptance 54/54、`npm test` 2277 pass / 0 fail、typecheck 通过；
      edge acceptance 22/22、`npm test` 1515/1515、typecheck 通过、`node --check` 全过。未打任何安装包、未部署、未合默认分支。
  <!-- aidcp-cloud 5b62ca0 + aidcp-edge 901ea91 均已推送到 codex/client-content-workspace-navigation -->

## 7. 合回主干（2026-07-17）

- [x] 7.1 三仓合回各自默认分支。**用 merge 而非 rebase**：分支已推送且共享，rebase 会要求对共享分支 force-push
      （§6 明确需先确认）；把默认分支 merge 进来后默认分支仍是 fast-forward，两全。
  <!-- aidcp-cloud c32254e / aidcp-edge ccaaf6f：分别 merge origin/master 解冲突 -->
- [x] 7.2 冲突解法（通例：两边语义都要，绝不择一）：
      · cloud `client-auth-server.ts`——主干新增 environment-provisioning intent/complete 两路由，
        与本分支的灵感库路由插在同一锚点，且**争用同一段 readJsonBody 样板**。解法＝两族路由都留、各自解析 body；
        import 段同时保留主干的 `clampClientApprovalMode` 与本分支的 curated/JsonValue。
      · edge `index.html`——主干把共享原始日志块 `#dev-section` 挪到工作区切换之外，与本分支新增的
        `#content-workspace` 撞同一锚点。解法＝两块都留（内容工作区在前、日志块在后），并核对无重复 element id。
- [x] 7.3 合并后回归闸（在合并树上重跑，非合并前的结论）：
      cloud acceptance 54/54、`npm test` 2353 pass / 0 fail / 6 skipped、typecheck 通过；
      edge acceptance 22/22、`npm test` 1612/1612、typecheck 通过、`node --check` 全过。
- [x] 7.4 **已知 flaky（不掩盖）**：`test/electron/interaction-workspace.test.ts` 的
      「环境 A→B 原子切换」与「批准/发送防双击」曾在某一次全量跑里以异常时长（39s / 76s）失败。
      已排查而非「重跑就当没事」：单文件隔离 19/19 过；带本次改动的全量连跑 4 次均 1612/1612 全过；
      把本分支对 `interaction-workspace.js` 的改动还原后行为一致。该改动是同步的 class 切换，
      不可能产生 76s 用例。判定为**既有的负载相关 flaky**，与本 change 无因果；登记在此备查。
  <!-- 若后续 CI 复现，从「全量并发下这两个用例被饿死」方向查，勿从本 change 找 -->
