## Why

Facebook group-join, in-container search, and commenting are already sophisticated and hold the "never silently fake success" red line everywhere. But operators observe that group-join **often fails on network speed or copy/text (button labels/text)**. Root-cause analysis (5-subsystem code map + adversarial review) shows the defect is narrow and systemic: the stack is **over-honest-then-terminal** — it collapses "page was slow / label not recognized" into the same terminal fate as "genuinely absent / failed", so a transient network blip or an unsupported UI locale permanently parks a joinable group or evicts an already-joined one. Two amplifiers and one true integrity bug compound this:

1. A **half-multilingual confirm layer**: the edge can *locate and click* a Join control in ~25 locales (shared lexicon), but can only *confirm* membership/pending/questionnaire in EN/ZH (exact-equality literals + EN/ZH-only regexes). A successful join on a non-EN/ZH group is reported as `join_failed`; an already-member non-EN/ZH group returns `no_button`.
2. An **absorbing outcome model**: the retry ladder is wired to branches that rarely fire, while the most common network transients (lease acquire/drop, slow-render observation, coverage nav-error) get terminal/permanent fates with zero or wrongly-costed retry — including one path that hot-loops every scheduler tick until it hits the permanent attempt cap, and one that evicts a warmed membership to `left` on a single nav-error blip.
3. A **duplicate-comment integrity bug**: a long comment on a slow link goes live on the platform (Enter fires) before the fixed 28s cloud step cap elapses; cloud then sees `timeout`, does not mark dedup, and the next round re-posts a second real comment.

The fixes are almost entirely **re-wiring existing machinery to the correct branch**, not new patterns. This change does NOT rewrite the join/search/comment stack; it hardens the honesty-vs-terminal boundary.

## What Changes

- **(P0) Route member/pending/questionnaire confirmation through the existing multilingual lexicon** (normalized contains-match, not EN/ZH exact-equality), on both edge and the cloud judge — so a real join on a supported non-EN/ZH group is recognized instead of being reported as `join_failed`/`no_button`.
- **(P0) Wrap edge-task-lease acquisition so lease/disconnect errors become honest, audited, retryable transients** that do NOT strand the membership in `joining` with no cooldown and do NOT hot-loop to permanent failure.
- **(P0) Require the same left-confirmation threshold for coverage navigation errors** as for permission-gated signals — stop irreversibly evicting a joined membership on one network blip.
- **(P0) Stop the slow-network duplicate comment**: make the comment step timeout composition-length-aware so a slow-but-successful long comment returns its dedup-marking receipt before the cloud gives up (the reported bug). (The deeper own-identity re-observe arbiter for the rarer hard-disconnect residual is descoped to a future change.)
- **(P1) Add a not-ready outcome for slow-render observations** (carry readiness diagnostics) and route it to a short retry tier instead of a terminal fate or a fail-closed model call.
- **(P1) Tier the retry backoff**: minutes-scale jittered cooldown for pure-network transients that does NOT consume the permanent attempt cap; keep the long backoff for account-level (login/captcha) states only.
- **(P1) Drift-guard the cloud judge lexicon against the edge lexicon** and confirm member-before-join evaluation so a localized already-member label is not misread as an instant-join.
- **(P1) Stop blindly Escape-dismissing unrecognized post-click modals**; report honestly rather than destroying a real membership questionnaire.

## Capabilities

### New Capabilities

- `facebook-group-join-resilience`: Multilingual membership/pending/questionnaire confirmation, honest transient classification for lease failures and slow renders, tiered network-vs-account backoff, confirmation-gated coverage demotion, and non-destructive handling of unrecognized modals.
- `facebook-comment-idempotency`: A slow-but-successful Facebook automatic comment is not spuriously timed out into a duplicate — the comment step timeout is composition-length-aware so the edge's dedup-marking receipt reaches the cloud before it gives up; genuine non-submissions stay retryable. (The own-identity re-observe arbiter for the hard-disconnect residual is deferred to a future change.)

### Modified Capabilities

- None. All deltas are additive new capabilities so the change stays validate-clean and archive-clean (no base facebook-group-join spec exists on this branch; the comment path's base capability is still being introduced by the active `facebook-scheduled-comment` change).

## Impact

- Affected repos: `aidcp-edge` (join confirmation classifiers + not-ready outcome + non-destructive modal handling + comment re-observe/length timeout), `aidcp-cloud` (join scheduler lease guards + tiered backoff + coverage demotion policy + judge lexicon; comment scheduler idempotency + step timeout).
- Already landed (do NOT redo): in-page `element.click()` actuation (edge `6848632`), generous join timeouts ready 30s / post-click 45s / cloud step 120s (edge `21ec924` + cloud `e246168`/`0759ec3`), ready-poll "don't judge a still-loading page" (edge `f59f650`), clear-Join-CTA deterministic instant_join not fed to the LLM (cloud `d3dcb9d`), multilingual Join-button *location* lexicon + chrome-scope exclusion (edge `2d60984`/`a6f0f3f`). This change targets the *confirmation*, *retry-classification*, *coverage-demotion*, and *comment-idempotency* gaps those did not touch.
- Operational impact: strictly reduces false-fails and one class of duplicate posts; no new default-on behavior, no protocol surface change, no risk-state-machine change. Comment idempotency is a platform-visibility fix (fewer duplicate comments).
- Coordination: the comment-idempotency delta touches the Facebook comment path owned by the active `facebook-scheduled-comment` change — serialize edits to `comment-scheduler.ts` / `facebook-edge-steps.ts` with that change's owner. The join-side deltas touch files a concurrent session actively landed join fixes on today (edge `join-executor.ts`, cloud `facebook-group-join-scheduler.ts`) — treat those as single-writer hot files and rebase before integrating.
