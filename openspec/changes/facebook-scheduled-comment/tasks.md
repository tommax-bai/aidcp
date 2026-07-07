## 1. Preconditions

- [ ] 1.1 Confirm `platform-abstraction-layer` is archived with xhs zero-regression.
- [ ] 1.2 Confirm `facebook-browser-env-and-login` has recorded passing F1/F2/F3 Phase-0 gates. F1 can be unblocked immediately by having the disposable account publish its own test post (a self-owned post removes permission-gate variables and isolates verification of the server-confirmation mechanism itself). Cloud-only work in this change (sections 2/3/5: target storage, entry-point routing, validators, shadow) MAY proceed in parallel during the F3 observation window because it never touches the Facebook real machine; real-posting tasks (section 4, 7.3, 7.4) remain gated behind F1 + F3.
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
- [ ] 7.3 Run shadow mode on one disposable account and record audit findings without secrets.
- [ ] 7.4 Enable real posting only on one disposable account with a 1-2/day cap (the existing global comment cooldown applies unchanged); record multi-day observation.
- [ ] 7.5 Commit sibling repo work, record commit SHAs and validation/probe/deployment notes in this `tasks.md`.
- [ ] 7.6 Run `openspec validate facebook-scheduled-comment --strict`.
