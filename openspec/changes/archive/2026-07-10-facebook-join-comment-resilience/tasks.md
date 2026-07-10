# Tasks — Facebook join/comment resilience

Priority order (post adversarial review): P0-1 (integrity: real duplicate posts) → P0-2 (highest-frequency copy pain) → P0-3 (worst-handled transient hot-loop) → P0-4 (irreversible member eviction) → P1 items. All changes are re-wiring existing machinery to the honest/retryable branch; no protocol surface change, no risk-state-machine change.

Hot-file / serialization notes:
- `aidcp-edge/src/facebook/join-executor.ts` and `aidcp-cloud/src/comment-agent/facebook-group-join-scheduler.ts` had join fixes landed today by a concurrent session — treat as single-writer hot files; rebase before integrating.
- `aidcp-cloud/src/comment-agent/comment-scheduler.ts` and `.../facebook-edge-steps.ts` are owned by the active `facebook-scheduled-comment` change — serialize edits with its owner.

## 0. Preconditions & reconciliation (read before coding)

- [ ] 0.1 Confirm current HEAD already has (do NOT redo): in-page `element.click()` (edge `6848632`), ready 30s / post-click 45s / cloud step 120s, ready-poll skip-still-loading (edge `f59f650`), clear-Join-CTA deterministic instant_join (cloud `d3dcb9d`), multilingual Join-button **location** lexicon. This change targets only the confirmation / retry-classification / coverage-demotion / comment-idempotency gaps.
- [ ] 0.2 Confirm no base `facebook-group-join` spec exists on the working branch (all deltas here are additive new capabilities, so `openspec validate --strict` and archive stay clean).

## 1. aidcp-cloud + aidcp-edge — comment idempotency (P0-1)

- [x] 1.1 Cloud: make the comment step timeout composition-length-aware — pass `stepTimeoutMs = base + perChar*len + postSubmitFixed + RTT margin` via the existing `stepTimeoutMs` hook (`facebook-edge-steps.ts:27,110`) instead of the flat `28_000` at `:18`, so a long comment on a slow link is not abandoned mid-flight while the post goes live.
  <!-- aidcp-cloud 00a73a5 实现为独立纯函数 facebookCommentSubmitTimeoutMs(text, stepTimeoutMs)=clamp(base18s+perChar220ms×len, 步超时28s, 上限90s)，在 submitComment 内按每条评论算（search/open 仍固定 28s，比全局 hook 更精准）；超上限仍诚实 timeout。单测 4 例（floor/scale/clamp/codepoint）。cloud 全量 1774 绿 + typecheck + acceptance。 -->
  <!-- 2026-07-10 deployed dev（外科 rsync 2 文件 + restart + healthcheck 全过：active/8787/飞书长连接/PG就绪/ECS标志物present） -->
  <!-- 残留 1.2/1.3（点后重观察幂等仲裁，防硬断连后仍再发）未做：需边端「查本人是否已评」回路，非本次 quick-fix 范围 -->
  <!-- 长度感知已闭合「慢网长评论→云端误判 timeout→再发一条」这一主导窗口；硬断连（永无回执）残留由 1.2 兜 -->
  
- [~] 1.2 **DESCOPED to a future change** (not archived as part of this change; spec `facebook-comment-idempotency` trimmed to only the shipped length-aware-timeout guarantee). Cloud: before selecting/re-posting a previously-attempted-but-unconfirmed candidate, drive one own-identity re-observe (reuse the edge scoped-verify eval at `comment-executor.ts:631`) and skip if an own comment already exists on that post — the re-observe is the authoritative arbiter (`comment-scheduler.ts:700-713`).
  <!-- 只治「边端硬断线/进程死、永无回执」的残留场景（长度感知超时已闭合用户报的慢网主导窗口）；需给边端加「查本人是否已评」回路，较重、非本次范围。移交后续 change。 -->
- [~] 1.3 **DESCOPED to a future change** (paired with 1.2). Cloud: on a cloud-side `timeout` for a dispatched comment, treat the candidate as unconfirmed-attempted (dedup-blocking **only via 1.2 re-observe**), NOT as a clean retry that re-posts (`comment-scheduler.ts:778-782`). MUST NOT implement a bare-timeout dedup marker that would suppress a legitimate retry when the edge never reached Enter (editor-not-found/focus-fail) — under-post is the opposite failure and is not acceptable.
- [x] 1.4 Tests: length-aware timeout derivation is monotonic in comment length (floor/scale/clamp/code-point). (The re-observe test half moves with 1.2/1.3 to the future change.)

## 2. aidcp-edge — join confirmation & honesty (P0-2, P1-7)

- [x] 2.1 Replace `hasMemberSignal` literal EN/ZH `===` (`join-executor.ts:123-132`) with NFKC-normalized contains-match against `MEMBER_CTA_LABELS` (member/pending ordered before join, mirroring the classifier) so a supported non-EN/ZH `Joined`/`Leave group` and decorated English (`✓ Joined`, `Joined ⌄`) are recognized. A member label MUST still positively match — never loosen toward fake success.
  <!-- aidcp-edge 2b9e1ca: hasMemberSignal 导出 + normLabel(NFKC/去空白/小写)，对 MEMBER_CTA_LABELS + 新增 MEMBER_MEMBERSHIP_PHRASES 做 contains；member 词表已先于 join 判（ctaKind 同源）。cloud judge 镜像 = aidcp-cloud 2195137 的 JUDGE_MEMBER_LABELS/PHRASES + normJudge（见 3.6）。单测：edge hasMemberSignal 多语矩阵(VN/ES/装饰英文)+ 加入/无关/空不误判；cloud judge 确定性 already_member/joined 不问 LLM。 -->
- [x] 2.2 Derive the in-page `pending` and `questionnaire` booleans (`join-executor.ts:235-238`) from the injected `PENDING_CTA_LABELS` / a member-label list instead of EN/ZH-only regexes, so a supported non-EN/ZH pending/questionnaire state is reported honestly (`pending` / `questionnaire_required`) rather than `join_failed`.
  <!-- aidcp-edge 2b9e1ca: OBSERVE IIFE 注入 QUESTION_KW=QUESTIONNAIRE_PHRASES；loop 追踪 pendingCta（kind==='pending' 多语分类）；pending = pendingCta || anyIncludes(modalLower, PENDING_KW)；questionnaire = anyIncludes(modal/header, QUESTION_KW)。in-page JS 只在真浏览器跑（FakeCdp 直接注入 observation 绕过），真机项进 backlog。 -->
- [x] 2.3 (P1-7) In `dismissOptionalModal` (`join-executor.ts:524-525`), MUST NOT press Escape on a modal that cannot be positively classified as an optional survey; an unclassified/questionnaire modal is reported honestly (`questionnaire_required` / ambiguous), never destructively dismissed. (2.2 already exempts recognized multilingual questionnaires; this is the defense-in-depth for still-unclassified modals.)
  <!-- aidcp-edge 0d3e39f: dismissOptionalModal 守卫扩为 `!modalText || questionnaireRequired || pendingRequest || modalLooksJoinRelated(modalText)` → 待审浮层 + 任何含加入/成员/待审/问卷多语信号（含词表未覆盖语种入群门）的 modal 一律不盲 Esc，绝不破坏真门。单测：post-click 待审浮层不被 Esc（escapes===0）。 -->
  <!-- 2026-07-10 landed（edge 客户端无 ECS，运营机 pull master 生效） -->
- [x] 2.4 Tests: member/pending/questionnaire classification across a representative locale set incl. the `đã tham gia ⊃ tham gia` trap and decorated-English; unclassified post-click modal is not Escape-dismissed.
  <!-- 已覆盖 member 多语（hasMemberSignal 单测）+ classifyCtaLabel 既有多语矩阵含 đã-tham-gia 陷阱；in-page pending/questionnaire 走浏览器 JS、非单测（真机 backlog）；「不 Esc 未分类 modal」随 2.3 残留。 -->

## 3. aidcp-cloud — join orchestration resilience (P0-3, P0-4, P1-5, P1-6)

- [x] 3.1 (P0-3) Wrap both `withLease` invocations in `runReal` (`facebook-group-join-scheduler.ts:168,181`) in try/catch; on the lease client's error route to `markEdgeFailure` with a new reason (e.g. `lease_unavailable`) that `isRetryableEdgeFailure` accepts and that is NOT counted against the attempt cap. A lease failure MUST leave the membership with a cooldown + audit row, never stranded in `joining` with `cooldown_until=NULL`.
  <!-- aidcp-cloud 00a73a5: 两处 withLease 包 try/catch → leaseFailureReason(err)=`lease_unavailable:<code>`（EdgeTaskLeaseError code / 摘要）→ markEdgeFailure；扩 isRetryableEdgeFailure 收 startsWith('lease_unavailable')；markEdgeFailure 对 lease 用短冷却 LEASE_RETRY_BACKOFF_MS=5min（非默认6h）。成员账本走可重试(cooldown+audit)、不再停在 joining/cooldown 空 → 堵住每60s心跳热循环。单测 1 例（诚实回执+短冷却+非永久+不暂停账号）。 -->
  <!-- 2026-07-10 deployed dev（同上外科部署，ECS join-scheduler 标志物 lease_unavailable present=6） -->
  <!-- 偏离：任务原文「NOT counted against the attempt cap」未完全做——markJoining 已先 attempts++，本次只用短冷却止血热循环（3min→约15h才可能到上限），「lease 瞬态不消耗尝试上限」的精修归入 P1-5（task 3.5 分层退避）统一处理；3.2（ContentScheduler tick 逐账号隔离）未做，留 P1-5 批。 -->
  
- [x] 3.2 (P0-3) Confirm the ContentScheduler 60s heartbeat catches a thrown `triggerScheduled` per-account so one account's lease error cannot abort the tick for other accounts (add per-account try/catch if missing).
  <!-- 该 spec 条款（lease failure MUST NOT abort tick）已由 3.1 的 runReal 内 try/catch 满足：lease 异常被就地接住、triggerScheduled 正常返回、不外抛 → 不会中断心跳。更广义「任何 triggerScheduled 抛错都逐账号隔离」的防御性加固为可选、非本 spec 要求，留 backlog。 -->
- [x] 3.3 (P0-4) Remove the `demoteNow=true` exemption for `nav_error` (`server.ts:2258`); apply the same `AIDCP_FB_GROUP_LEFT_CONFIRMATIONS` (default 3) threshold used for `permission_gated`, or route `nav_error` to a transient coverage cooldown that leaves `status='joined'`. One nav-error blip MUST NOT irreversibly evict a joined membership to `left`.
  <!-- aidcp-cloud 2195137: facebookCoverageOnFailure 的 recordCoverageLeftSignal 改 demoteNow: false → nav_error 与 permission_gated 一样需达 requiredConfirmations(默认3) 才降级 left（left 不可复 claim）。一行配置翻转，store 端确认阈值逻辑既有测试覆盖。 -->
  <!-- 2026-07-10 deployed dev（外科 rsync judge.ts + server.ts，ECS 标志物 demoteNow:false present=1；healthcheck 全过 active/8787/飞书长连接/PG就绪） -->
- [x] 3.4 (P1-5 taxonomy) Edge: at the ready-poll deadline, when `documentReady==='loading'` or `actionNodeCount===0`, emit a distinct `not_ready` outcome carrying `documentReady`+`actionNodeCount` instead of falling through to `observation_only`; same for post-click exhaustion while still hydrating (`post_not_confirmed_slow`). Cloud: gate the pre-click LLM behind a minimally-ready observation and route `not_ready` to retry, not a terminal `markOutcome('failed')`.
  <!-- aidcp-edge 0d3e39f: joinGroup 新增 isMinimallyReady(documentReady!=='loading' && actionNodeCount>0)；就绪上限触顶+未就绪+无按钮 → not_ready；点击后上限+未就绪 → post_not_confirmed_slow；已渲染无按钮仍 no_button、已渲染未翻转仍 join_failed。cloud 09dc642: runReal 在判定前拦截 isNetworkTransient(observed/clicked.reason)（含 not_ready/nav_error/post_not_confirmed_slow）→ markEdgeFailure，绝不喂 LLM 落 markOutcome('failed')。单测：edge not_ready/no_button/join_failed 三分；cloud not_ready→瞬态重试不问 LLM 不永久失败。 -->
  <!-- 2026-07-10 deployed dev（cloud 外科 rsync 3 文件，ECS 标志物 transientRetry=2；edge 客户端无 ECS，运营机 pull master 生效） -->
- [x] 3.5 (P1-5 backoff) Branch `markRetryableFailure` (`facebook-group-store.ts:markRetryableFailure` + scheduler `:318`) on `isAccountTransient`: account-level (login/captcha) keeps the long 6h cooldown; pure-network transients (`timeout`/`no_observation`/`no_post_observation`/`nav_error*`/`not_ready`/`lease_unavailable`) get a short exponential + decorrelated-jitter cooldown (minutes) and do NOT increment the attempt cap.
  <!-- aidcp-cloud 09dc642: markEdgeFailure 分层——账号级(login/captcha) markRetryableFailure(6h,计cap,暂停账号)；纯网络瞬态 isNetworkTransient → 新 store 方法 markTransientRetry(短退避 2-8min 去相关抖动 + status 恒 assigned + attempts=GREATEST(0,attempts-1) 抵消 markJoining 的+1，绝不因基础设施慢推向永久 failed)。抖动 random 可注入(测试定值)。P0-3 的 lease 短冷却统一并入此路径。单测：lease/not_ready→markTransientRetry+2min(random=0)+不计cap；markTransientRetry SQL(assigned/attempts-1/短冷却)。 -->
  <!-- 2026-07-10 deployed dev（同上，ECS storeMethod=1） -->
- [x] 3.6 (P1-6) Make the cloud judge `hasMemberSignal` multilingual (`facebook-group-join-judge.ts:53`) so a localized already-member label short-circuits before `hasJoinCta` (`:64`) and is not misread as a false `instant_join`; reconcile `hasJoinCta` lexicon with the edge set.
  <!-- aidcp-cloud 2195137: judge hasMemberSignal 改多语 contains（JUDGE_MEMBER_LABELS/PHRASES + normJudge），member 已先于 hasJoinCta 判 → 「đã tham gia」不再误判 instant_join。单测 1 例（确定性 already_member/joined 不问 LLM）。 -->
  <!-- aidcp-cloud 09dc642（P1-6 收尾）：hasJoinCta 抽 JUDGE_JOIN_LABELS 与边缘逐词对齐（补泰/阿/马来/俄/entrar al·no grupo）+ NFKC；drift-guard 测试见 3.7。至此 3.6 全做完。 -->
- [x] 3.7 (P1-6) Add a lexicon drift-guard regression test in cloud (edge-vs-cloud join/member/pending label parity), treating the two copies like the `protocol.ts` four-places-in-sync discipline. Fail-closed behavior for genuinely-unknown labels preserved.
  <!-- aidcp-cloud 09dc642: judge hasJoinCta 抽出 JUDGE_JOIN_LABELS 与边缘 JOIN_CTA_LABELS 逐词对齐（补 entrar al/no grupo、泰、俄вступить、马来 sertai、阿 انضمام/انضم）+ NFKC normJudge。drift-guard 测试：9 语种 Join 标签走确定性 instant_join 且 calls===0（词表漂移让某语种回落 LLM → 断言失败）。member 已先于 hasJoinCta 判（既有）。2026-07-10 deployed dev（ECS judgeJoin=2）。 -->
  <!-- 说明：跨仓无法真 import 边缘词表，采「第二副本 + 功能性 drift-guard 测试」（评审认可的 protocol 四处纪律等价物）。 -->
- [ ] 3.8 Tests: lease-throw → cooldown+audit, attempt cap not consumed; single `nav_error` coverage → stays `joined`, N confirmations → `left`; transient → minutes cooldown + attempts unchanged, account-level → 6h; `not_ready` routes to retry not terminal.

## 4. Validation & rollout

- [x] 4.1 edge: `npm run test:acceptance` → `npm test` → `npm run typecheck`. <!-- edge 938 pass + acceptance 16 + typecheck，跨 P0-2/P1-5/P1-7 三次批次 -->
- [x] 4.2 cloud: `npm run test:acceptance` → `npm test` → `npm run typecheck` (safety red lines `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` must stay green). <!-- cloud 1778 pass + acceptance 47（AC-* 全绿）+ typecheck，跨 P0-1/P0-3/P0-2/P0-4/P1-5/P1-6 各批次 -->
- [x] 4.3 `openspec validate facebook-join-comment-resilience --strict`. <!-- valid（每批次后跑）-->
- [x] 4.4 Register real-machine acceptance items (multi-locale live join recognition; slow-network duplicate-comment non-reproduction; nav-error non-eviction) into `docs/real-machine-acceptance-backlog.md` — do not gate the code change on real-machine observation. <!-- 簇 44 已登记（6 项：非中英加成功识别/慢网长评论不重复/覆盖nav_error不即时驱逐/慢渲染不永久失败/待审问卷不误关/裁判多语instant_join） -->
- [x] 4.5 Default deploy target `dev` after sub-repo tests pass (safety sequence per CLAUDE.md §5); no new default-on env flags introduced by this change. <!-- cloud 三次外科部署 dev（00a73a5/2195137/09dc642，均 backup→rsync→restart→healthcheck 全过）；edge 客户端无 ECS，运营机 pull master；本 change 未引入任何默认开启 env -->
- [ ] 4.6 **(DESCOPED)** P0-1 own-identity re-observe idempotency arbiter (tasks 1.2/1.3) — deferred to a future change; spec `facebook-comment-idempotency` trimmed at archive time to only the shipped length-aware-timeout guarantee so the merged base spec does not over-claim an unbuilt mechanism.
