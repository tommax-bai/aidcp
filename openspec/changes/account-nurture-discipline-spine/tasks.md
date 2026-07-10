# Tasks — account-nurture-discipline-spine

## 1. Preconditions

- [x] 1.1 Ground on `origin/main` (control repo) and `aidcp-cloud` / `aidcp-edge` `master`; rebase the worktree branch onto the latest default branches before starting. <!-- grounded on cloud master 8a35cbe; rebase-before-merge deferred to §7/§8 integration -->
- [x] 1.2 Confirm `ColdStartPlanner` still exists as dead code (Day1–7 bands + `quotaOverride(createdAt)`) and that `effectiveQuotas()` currently ignores `created_at`; capture the exact `file:line` before wiring so the connection is surgical. <!-- confirmed: cold-start-planner.ts dead (no runtime consumer); risk-controller.ts effectiveQuotas ignored created_at pre-change -->
- [x] 1.3 Confirm scope boundaries with the design: this change does NOT modify `protocol.ts` (either copy), does NOT add any `RISK_ACTIONS`, and does NOT change the risk state-machine transition table. Any task that would require these is out of scope. <!-- honored: no protocol / RISK_ACTIONS / transition-table edits in d606d45 -->
- [x] 1.4 Confirm `accounts.platform` is populated for Facebook accounts (from the scheduled-comment handshake insert-time provisioning) so platform-selected cold-start curves resolve correctly. <!-- mechanism = ensureAccount insert-time platform (account-store.ts); getNurtureMeta reads created_at+platform; missing → safe no-clamp fallback; live-data check at ol rollout -->

## 2. aidcp-cloud — cold-start quota wiring

- [x] 2.1 Wire `effectiveQuotas()` to compute the cold-start age quota from `created_at` via `ColdStartPlanner` and clamp with `min(ageQuota(created_at), riskScaledQuota)` (min semantics: age ramp and risk backoff stack, neither overrides the other). <!-- aidcp-cloud d606d45: applyColdStartClamp + minWindowQuotas; deterministic coldStartDailyCap (upper-bound, no random flicker); createdAt/platform threaded via registry nurtureMetaResolver + account-store getNurtureMeta -->
- [x] 2.2 Select the cold-start curve by `accounts.platform`; add a strictly-more-conservative Facebook curve (D1–3 browse + minimal likes, comments from D3, publish/group-join from D5) while leaving the xiaohongshu curve byte-for-byte unchanged. <!-- aidcp-cloud d606d45: FB_COLD_START_PLANS; coldStartDailyCap picks FB curve when platform==='facebook'; xhs COLD_START_PLANS untouched -->
- [x] 2.3 Add an env knob for the cold-start ramp (default on, safe-direction); when off, `effectiveQuotas()` returns the exact pre-change risk-scaled values (zero regression). <!-- aidcp-cloud d606d45: AIDCP_COLDSTART_RAMP !== 'false' (default on); coldStartRampEnabled=false short-circuits applyColdStartClamp -->
- [x] 2.4 Unit tests: Day 1 clamped to cold-start band (not `normal` full); `warned` + young takes `min` (both in force); graduated account unchanged; ramp knob off = zero regression; Facebook Day 1 has zero comment/publish quota; Facebook Day 5 opens small publish/group-join; xiaohongshu curve unchanged. <!-- aidcp-cloud d606d45: test/risk-cold-start-clamp.test.ts 9 cases green -->

## 3. aidcp-cloud — Facebook throttling-signal backoff

- [x] 3.1 Extend the overlay/text library with Facebook soft-block phrases ("Action Blocked" / "we limit how often you can do this" / "misusing this feature" / "you can't use this feature right now" / silently-hidden-comment detection) alongside the existing checkpoint/login/captcha entries.
- [x] 3.2 Feed recognized Facebook throttling signals into the existing `applySignal` input so the account migrates to `restricted` (browse-only); do NOT change the transition table and keep the write single-sourced in `RiskController`. <!-- aidcp-cloud 88b7ccb: captcha-coordinator maps FB throttle overlay.text → confirmed(restricted); transition table untouched; single-write preserved -->
- [ ] 3.3 Treat N consecutive post-action verification failures on the same action as a systemic-throttling signal → report and escalate to `restricted` (N is an Open Question; see design.md). <!-- DEFERRED: coupled to per-action post-check which lands with Change B (browse/like verified actions); revisit when B post-check exists -->
- [~] 3.4 Unit tests: soft-block toast → `restricted` (interactions stopped, browse only); N consecutive post-check failures → `restricted`; recovery window auto-downgrades (existing behavior intact); final state is a cloud single write and the edge cannot set it. <!-- aidcp-cloud 88b7ccb: test/facebook-throttle-signal.test.ts covers soft-block→restricted + non-match→warned regression guard + captcha unchanged + cloud single-write via coordinator; N-consecutive deferred with 3.3 -->

## 4. aidcp-cloud — cooldown quiet period + online day window

- [x] 4.1 Add a per-account post-restart cold-start quiet period (default a few minutes) that suppresses burst dispatch after process start; leave persisted daily quotas untouched (replayed from PostgreSQL). <!-- aidcp-cloud 3ef7230: ActionCooldownGate restartQuietMs (AIDCP_RESTART_QUIET_MS default 180000); suppresses no-history interactions in window; daily PG quotas untouched -->
- [x] 4.2 Add a per-Facebook-account daily online-minutes budget (roughly 0.5–6h) reusing the existing daily online budget + active-window machinery; give Facebook a non-zero default window and fall back to it when unconfigured; never proactively log accounts out. <!-- aidcp-cloud 07b6c18: effectiveDailyMaxMinutes helper + DEFAULT_FB_DAILY_ONLINE_MINUTES=360; canAutoResume applies FB fallback when global maxMinutes=0; AIDCP_FB_DAILY_ONLINE_MIN override; edge never logs out (unchanged) -->
- [x] 4.3 Unit tests: first post-restart batch is paced not bursted; quiet period expiry resumes normal cooldown; daily quotas survive restart untouched; Facebook account at online ceiling does not continue/open a session; within-budget continues; missing ceiling uses safe default. <!-- aidcp-cloud 3ef7230 (test/action-cooldown.test.ts) + 07b6c18 (test/resume-daily-online-budget.test.ts); daily-quota-survives-restart is inherent (PG replay, counters untouched by these changes) -->

## 5. aidcp-edge — egress reporting + FB throttling-overlay recognition (minimal)

- [ ] 5.1 On Facebook session start, report the session's real egress IP/geo by reusing the existing fingerprint WebRTC = proxy probe; never leak the real-machine IP; report unknown honestly on probe failure. <!-- DEFERRED: egress report needs a data channel to cloud (an optional protocol field/message), which is OUT of this change's no-protocol-change scope. Split into a separate small change (protocol-touching) together with §6. -->
- [x] 5.2 Extend Facebook throttling-toast/overlay recognition (inline block toasts + silently-hidden-comment) and report each as a throttling signal to the cloud. Keep the edge change minimal (recognition + report only; no local risk-state decision). <!-- aidcp-edge 9981888: classifyFacebookOverlayFromSignals extended to full FB soft-block phrase set → 'unknown' blocking → reported via existing risk.captcha_detected with overlay.text (no protocol change) → cloud §3 escalates to restricted. THROTTLE WIRE now end-to-end. NOTE: silently-hidden-comment detection not yet done (needs per-comment post-check, couples with §3.3/Change B). -->

## 6. cloud/console — egress alerting

- [ ] 6.1 Cloud: on egress matching a risk feature (mainland-China / datacenter / same-subnet-as-real-machine) raise an operations alert; never block, delay, or downgrade any action (warn-only per v1 decision). <!-- DEFERRED: depends on §5.1 egress report (blocked on the protocol data-channel decision). -->
- [ ] 6.2 Console (read-only): surface the egress alert and the account's current risk state; no write path. <!-- DEFERRED with §5.1/§6.1; console repo not yet touched. -->

## 7. Verification

- [x] 7.1 aidcp-cloud: `npm run test:acceptance` → `npm test` → `npm run typecheck`, all green; the `AC-RISK-*` red lines MUST pass (never self-harm; a denied `record` returns false). <!-- cloud: acceptance 47 + full 1770 + typecheck all green across d606d45/88b7ccb/3ef7230/07b6c18; AC-RISK intact -->
- [x] 7.2 Prove Day-1 clamp with a stub-injected `created_at` (no real machine): fixture accounts at nurture-day 1/5/graduated assert the clamped bands and platform-curve differences. <!-- aidcp-cloud d606d45: createdAtForDay fixtures in risk-cold-start-clamp.test.ts; typecheck + acceptance 47 + full 1754 green -->
- [x] 7.3 Prove throttling backoff with a stub-injected Facebook soft-block signal: assert migration to `restricted` and that the edge cannot self-set the final state. <!-- aidcp-cloud 88b7ccb: test/facebook-throttle-signal.test.ts — soft-block text via coordinator → restricted (cloud single-write); non-match → warned regression guard -->

## 8. Rollout (isolation window → ol)

- [ ] 8.1 Deploy from the integration branch to `ol` following the mandatory safe sequence (target check → sub-repo tests pass → ECS backup → rsync excluding `.env`/`node_modules`/`.git` → restart → healthcheck → rollback on failure). Never touch same-machine isales.
- [ ] 8.2 Ship cold-start ramp + Facebook throttling backoff default-on (safe direction); run egress alerting in observe mode.
- [ ] 8.3 Register real-machine verification items (Facebook soft-block toast → `restricted`; Day-1 quota clamp under a live new account; egress alert on a China/datacenter exit) into the real-machine acceptance backlog.
