## 1. Preconditions

- [ ] 1.1 Confirm `platform-abstraction-layer` is archived with xhs zero-regression.
- [ ] 1.2 Confirm `facebook-browser-env-and-login` has recorded passing F1 and F2 Phase-0 gates. This change explicitly revises the env-change gate (its task 7.5 permits proceeding "or the design is revised"): F3 multi-day low-frequency stability observation is NOT a blocker for feature work — the team pushes features fast and batches all long-duration stability observation into a final completion pass (see section 8). F1 (server-confirmation mechanism) IS required and can be unblocked immediately by having the disposable account publish its own test post (a self-owned post removes permission-gate variables and isolates verification of the mechanism itself). F2 (login/checkpoint honest-stop) is already passed.
- [ ] 1.3 Decide whether target configuration UI is in scope; if yes, open `aidcp-console` same-name worktree, otherwise keep config to cloud/API/storage.

## 2. Cloud Target Config and Cron

- [ ] 2.1 Add Facebook comment target storage/API keyed by account and platform; ensure missing targets fail closed.
- [ ] 2.2 Route Facebook automatic comments through the EXISTING two comment entry points instead of a new cron: the schedule-driven comment action (`commentEnabled`/`commentDailyCap`) and the Feishu `/comment` command. Both already resolve the per-account platform profile via the account store; add a `facebook` entry to `PLATFORM_REGISTRY` and let both entry points reach the Facebook targeted-comment execution for `accounts.platform='facebook'`. Before dispatch check account status, kill switch, target config (missing targets fail closed), risk gate (`canDo('comment')`), and the existing daily cap (`commentDailyCap`/`commentedTodayCount`).
- [ ] 2.3 Add shadow mode that runs selection/composition/validators without posting, recording risk, marking cooldown, or deduping as posted.
- [ ] 2.4 Ensure Facebook scheduled accounts are never added to xhs/manual comment quota-bypass collections.
- [ ] 2.5 Provision account platform at handshake insert-time so brand-new Facebook accounts are not deadlocked: `ensureAccount` accepts the edge-declared platform and writes it only when INSERTing a new row (never overwriting an existing row's platform), refreshing the platform cache on the same write path so a rejected first handshake cannot poison the cache. Operator escape hatch (pre-insert a `platform='facebook'` row via psql before first connect; correcting an existing row still requires psql + cloud restart) goes in the runbook, not code.
- [ ] 2.6 On login-required / checkpoint / temporarily-blocked outcomes, raise an alert via the existing alert store plus a Feishu card (reuse the store-then-Feishu, cooldown-deduped pattern used for captcha coordination) and skip that account on subsequent triggers until an operator re-logs-in and resumes it; recovery is manual `/resume` (or next preflight probe pass) in v1.
- [ ] 2.7 Persist one audit row per comment trigger (outcome + reason; shadow runs write to the same table with a shadow flag) so shadow results and silent stalls are queryable rather than journalctl-only; raise an alert after N consecutive blocking outcomes (login_required / quota_denied / no_targets / compose_skipped) so an unattended stall has bounded detection latency.
- [ ] 2.8 Add a platform gate at session start so a Facebook account (whose registry entry does not declare `browse`) never starts the xhs browse role loop: gate `canStartSession` on the platform registry capabilities and refuse with a named reason instead of spinning up a zombie session and watchdog.
- [x] 2.9 Persist Facebook account nickname from verified hello identity: edge may send an optional nickname only after numeric-id identity is established, and cloud may write it only after handshake platform validation and only when no nickname exists.
  <!-- aidcp-edge master 6d4cdca: added /me verified nickname probe, hello accountNickname, startup/reconnect propagation. aidcp-cloud master 8ab3199: trims hello nickname onto session and persists after platform validation only when nickname is empty. Validation: edge acceptance 16 pass, full npm test 821 pass, typecheck pass; cloud acceptance 47 pass, full npm test 1685 pass, typecheck pass; openspec validate facebook-scheduled-comment --type change --strict pass. Deployment: cloud dev deployed 2026-07-09 23:19 CST from aidcp-cloud master 8ab3199 after ECS backup /opt/aidcp/backups/cloud.20260709-231837.tar.gz and env backup /opt/aidcp/backups/cloud.env.20260709-231837.bak; service active; ports 8787/8090 listening; panel /api/health ok; PG ready; Feishu WSClient ready. Edge master pushed; no ECS edge deployment applies. -->

## 3. Composition and Validators

- [ ] 3.1 Extract shared compose/cleanup helper if needed while keeping xhs approval behavior unchanged.
- [ ] 3.2 Implement Facebook deterministic validators for URLs/domains/contact info/@mentions/length/spam phrases/relevance/empty text.
- [ ] 3.3 Add tests for validator reject matrix and for no auto-fix/template fallback after rejection.

## 4. Edge Facebook Browse and Comment

- [ ] 4.1 Implement Facebook targeted browse capability for configured Page/Group/post URLs with bounded candidate extraction.
- [ ] 4.2 Implement Facebook comment editor input and pre-submit checkpoint/login detection.
- [ ] 4.3 Implement server-confirmed verification using F1-approved permalink/id or delayed requery strategy.
- [ ] 4.4 Return honest non-success reasons for no target, editor failure, blocked state, submit failure, and ambiguous verification.

## 5. Risk, Cooldown, and Accounting

- [ ] 5.1 Wire automatic Facebook comment success to `interaction.occurred`/`RiskController.record('comment')` only after verified `ok:true`.
- [ ] 5.2 Reuse the existing global comment cooldown for Facebook automatic comments through the shared pipeline (no Facebook-specific long cooldown — accounts run one platform per environment, so per-account isolation suffices); the cooldown timestamp is still marked only after verified success.
- [ ] 5.3 Add tests proving shadow, failed submit, validator rejection, and ambiguous verification do not record risk or cooldown.

## 6. Console/UI If Included

- [ ] 6.1 Add target management UI/API integration only if required for operations in this change.
- [ ] 6.2 Run console focused tests, full tests, typecheck, and build if console is touched.

## 7. Rollout and Validation

- [ ] 7.1 Run cloud focused tests for cron, validators, kill switch, platform account enumeration, risk, and cooldown.
- [ ] 7.2 Run edge focused tests for Facebook browse/comment/verification, then edge full tests, acceptance, and typecheck.
- [ ] 7.3 Run a short shadow sanity pass on one disposable account (hours, not days — enough to confirm audit rows, validator reject rate, target relevance, and that the login/checkpoint alert loop fires); record findings without secrets. Multi-day shadow observation is deferred to section 8.
- [ ] 7.4 Enable real posting on one disposable account with a 1-2/day cap (the existing global comment cooldown applies unchanged) and confirm one full verified-success path end to end. Multi-day real-posting observation is deferred to section 8.
- [ ] 7.5 Commit sibling repo work, record commit SHAs and validation/probe/deployment notes in this `tasks.md`.
- [ ] 7.6 Run `openspec validate facebook-scheduled-comment --strict`.

## 8. Deferred Stability Completion (batched at the end)

Long-duration stability work is intentionally deferred out of the fast feature push and completed together once the feature functions end to end. None of these gate feature landing; all MUST be done before scaling beyond one disposable account or raising caps.

- [ ] 8.1 F3-style multi-day low-frequency AdsPower/Facebook environment stability observation (>=3 counted calendar days), recorded without secrets.
- [ ] 8.2 Multi-day real-posting observation on the disposable account (sustained 1-2/day) to confirm no delayed checkpoints, verification drift, or alert-noise regressions.
- [ ] 8.3 Cooldown / daily-count persistence across restarts (currently in-memory) — required before multi-account restart-burst scenarios.
- [ ] 8.4 Per-profile proxy/egress management and egress-stability observation before productionization.
- [ ] 8.5 Re-evaluate caps and the Scale-out boundary checklist (proposal) using the accumulated stability evidence.
