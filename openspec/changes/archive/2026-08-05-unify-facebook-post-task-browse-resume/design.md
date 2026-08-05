## Context

Cloud currently drives normal browsing through `scroll` commands mapped to `page.scroll`. Edge task release removes the task owner and unblocks the ordinary browse lane, but Native `resumeAfterTask()` intentionally preserves the current page and only schedules a passive probe. No Cloud command is produced by that release path, so a group page can remain open until the 240-second idle nudge.

Facebook Reels entry is also selected in Cloud through two reason strings and an `idle | pending | confirmed` state. `confirmed` means that a readable Reel existed at some earlier time; it is not evidence of the page currently open after a task navigates to a group. Using it as a current-page gate can suppress the command that should return a Reels-primary session to Reels.

The change crosses the Cloud coordinator/dispatcher, the shared protocol payload, and the Edge Native page engine. It must preserve the existing single-writer lease, quota, risk, pause, and session gates.

## Goals / Non-Goals

**Goals:**

- Give all active browse continuation one Cloud command shape: `page.scroll{reason:'resume_redrive', targetSurface}`.
- Resume immediately after the final group/comment lease release acknowledgement, including after a terminal ambiguous submission receipt.
- Let Edge determine the actual current page at execution time and reconcile it to the requested target.
- Remove `confirmed` as a long-lived proxy for the current Reels page while keeping entry retries bounded and idempotent.
- Keep existing success honesty: a Reels route is not success until a canonical active Reel is reported.

**Non-Goals:**

- Changing task priority, lease expiry, comment confirmation, or action accounting semantics.
- Bypassing view quota, risk, pause, dispatch, persona, or session gates.
- Adding a new protocol message type, packaging Edge, or deploying Cloud.
- Making intermediate releases inside a multi-step task navigate away from that task's page.

## Decisions

### 1. Reuse `page.scroll` and add one explicit target

Cloud SHALL emit `reason='resume_redrive'` with `targetSurface='feed' | 'reels'`. The optional payload field is backward compatible for unrelated scroll reasons, but it is required for Facebook `resume_redrive`. Cloud will stop choosing `facebook_reels_primary` versus `empty_feed_reels_fallback` as different command shapes; legacy reasons can remain temporarily decodable by Edge for version skew.

Alternative considered: add `browse.resume`. Rejected because the existing scroll channel already carries the command, routing, receipts, pacing, and task-ownership checks.

Alternative considered: omit the target and let Edge infer it. Rejected because the pinned primary surface and fallback policy are Cloud authorities and are not currently part of the Native session contract.

### 2. Probe the actual page at the Edge execution boundary

For `targetSurface='reels'`, Native checks the live surface. If a canonical Reel is already active it reports that current card without redundant navigation or input; otherwise it runs the verified Reels entry path. For `targetSurface='feed'`, it first pins the primary list back to Facebook home—temporary group/search tasks may have overwritten `active_list_url`—then runs the existing verified feed-scroll path. Navigation alone never completes the command: the existing structured card or honest no-target receipt remains authoritative.

This avoids synchronizing task navigation into another Cloud page-state variable. Cloud stores the stable session target and only a bounded in-flight attempt; Edge owns the volatile current-page fact through a fresh probe.

### 3. Redrive at workflow settlement, after release acknowledgement

The consumption coordinator owns the join/comment action chain, including recursively created `nextAction` work. Mode executors report whether each page-task lease produced an acknowledged release and preserve the lease's `edgeId`. The coordinator retains the last settlement across the root chain and calls the runtime redrive port exactly once, targeting that same account and Edge connection, after the chain returns a terminal result. A `submitted_unknown` receipt is terminal for execution and qualifies; it is not promoted to success.

Intermediate observe/click/prepare releases do not directly redrive. A missing release acknowledgement suppresses immediate redrive because the Edge may still have an owner; existing lease expiry/release retry and idle recovery remain the safety path.

Alternative considered: redrive on every `edge.task.released`. Rejected because a release can be the handoff between task phases or queued exclusive tasks.

### 4. Replace sticky confirmation with bounded attempt state

Cloud will retain only transient data needed to deduplicate and bound a Reels redrive attempt: whether one is in flight and its recovery count. A canonical `page.cards{listKind:'reels'}` clears the attempt; it does not set a permanent `confirmed` page state. A later task completion can therefore always request reconciliation to the pinned target.

Feed-empty fallback also uses the same command and transient attempt. Per-session retry/re-entry limits remain, so removing `confirmed` does not create an unbounded Feed/Reels loop.

## Risks / Trade-offs

- [Older Edge ignores `targetSurface`] -> Cloud and Edge protocol/runtime changes ship together; Edge keeps legacy entry reasons for version-skew compatibility, and Cloud treats absent terminal card evidence honestly.
- [A late pre-navigation event attempts another redrive] -> transient in-flight deduplication and existing per-session recovery bounds limit duplicates; Edge execution is idempotent and probes the live page.
- [Final release acknowledgement is lost] -> immediate redrive is suppressed; idempotent release retry/expiry and the idle watchdog remain recovery paths.
- [Redrive is requested while quota or pause blocks browsing] -> the existing RoleDispatcher command gate rejects it without changing task outcome or accounting.

## Migration Plan

1. Add the optional payload field to both TypeScript protocol copies and Native strict decoding, plus compatibility tests.
2. Add target-aware `resume_redrive` execution to Native and its embedded Facebook router.
3. Centralize Cloud active resume dispatch and replace Reels sticky confirmation state.
4. Add final-release metadata to consumption executors and one coordinator-level redrive callback.
5. Run focused Cloud/Edge tests, Rust tests, TypeScript typechecks, protocol drift checks, and strict OpenSpec validation.

Rollback is code-only: restore the previous Cloud reason selection and Edge decoder/executor together. No persistent-data migration is required.

## Open Questions

None. Packaging, DEV deployment, and real-account acceptance remain explicit follow-up work.
