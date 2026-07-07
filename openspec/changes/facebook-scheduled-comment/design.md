## Context

This change depends on two prior gates: `platform-abstraction-layer` must have archived with xhs zero-regression, and `facebook-browser-env-and-login` must have passed F1/F2/F3. Facebook scheduled comments are unattended, unlike the current xhs manual-approved comment path, so the safety model changes from "human approves every text" to "deterministic validators, quota/cooldown, server-confirmed verification, and kill switch fail closed."

Official Meta Pages APIs may be useful for operator-owned Pages in a later capability, but this feature targets operator-specified Pages/Groups/posts through the real browser session. Facebook Groups API cannot be assumed available for this use case, and internal GraphQL doc IDs are too brittle and too close to private platform internals to be a core dependency.

## Goals / Non-Goals

**Goals:**
- Schedule Facebook automatic comments only for accounts with `accounts.platform='facebook'`.
- Use operator-configured target URLs; no full-site Facebook search in v1.
- Run shadow mode before real posting.
- Compose comment text through the existing LLM path but require deterministic hard validators.
- Execute Facebook comments through the platform driver and verify server-confirmed posting before reporting success.
- Gate every automatic attempt by kill switch, account status, login/checkpoint state, risk `canDo('comment')`, daily caps, and synchronous cooldown.
- Record risk/cooldown only after verified success.

**Non-Goals:**
- Add Facebook posting, reactions, follows, notifications, or group joining.
- Bypass Facebook login, checkpoints, 2FA, or moderation.
- Use internal Facebook GraphQL doc IDs as production interface.
- Weaken xhs comment human approval or reuse xhs manual-comment "skip quota" sets.
- Claim success from optimistic DOM insertion alone.

## Decisions

- Build a separate Facebook scheduled-comment path rather than altering the xhs comment approval loop.
  - Rationale: xhs comments are manual-reviewed and event-loop attached; Facebook v1 is scheduled and unattended. Sharing composer helpers is useful, but approval semantics must not cross-contaminate.
  - Alternative considered: remove/parameterize xhs `CommentApprovalGate`. That risks deleting an existing safety gate.
- Use target list configuration and bounded post selection.
  - Rationale: v1 business goal is operator-specified Pages/Groups, not discovery. This keeps risk and implementation scope lower.
  - Alternative considered: site-wide Facebook search. That creates extra anti-abuse and relevance risk and belongs in a later change.
- Treat server-confirmed verification as the only success signal.
  - Rationale: Facebook can optimistically render local comments before server acceptance/moderation. Success must be permalink/id or delayed reload/requery confirmation scoped to the target post and own identity/text.
  - Alternative considered: editor cleared plus visible row. That is acceptable for xhs only because prior probes proved its shape; for Facebook it is specifically unsafe.
- Validators reject, not repair.
  - Rationale: unattended auto-repair can transform a risky output into a still-risky but posted output. Rejecting produces `compose_skipped`, preserving safety.
  - Alternative considered: run an LLM "fix" pass. That hides deterministic violations and adds drift.
- Keep automatic Facebook comments out of `manualCommentAccounts`.
  - Rationale: xhs manual comments skip quota because a human is in the loop. Facebook automation has no human in-loop and must be counted.
  - Alternative considered: reuse the xhs manual comment task wrapper unchanged. That would silently disable the main rate safety net.
- Use shadow mode as the first rollout state.
  - Rationale: text quality and target relevance can be audited without posting, recording risk, or deduping.
- Reuse the existing two comment entry points (schedule-driven comment action with `commentEnabled`/`commentDailyCap`, and Feishu `/comment`) routed by account platform; do NOT add a separate Facebook cron.
  - Rationale: both entry points already converge on the platform-aware command-style comment pipeline that resolves the per-account platform profile; Facebook only needs a `PLATFORM_REGISTRY` entry and a targeted execution path behind it. Daily caps reuse the existing per-account `commentDailyCap`/`commentedTodayCount`; `RiskController.canDo('comment')` stays the risk gate; kill switch stays an env flag (`AIDCP_FB_COMMENT_AUTO`, fail-closed default off).
  - Alternative considered: a dedicated Facebook cron. Rejected — duplicates trigger/cap/re-entrancy machinery that already exists and creates a second scheduling surface to operate.
- Keep cooldown global/uniform for Facebook — no Facebook-specific long cooldown.
  - Rationale: accounts run on separate environments and one account never runs xhs and Facebook simultaneously, so per-account isolation already suffices; the existing global comment cooldown is reused as-is. This drops the `interaction-cooldown` delta from this change.
- Reuse platform-neutral protocol messages for Facebook comment execution; do not add `facebook.*` message types.
  - Rationale: `note.open` (extended with an optional `url` payload field to express "open the configured target") and `interaction.comment` are already routed in the edge active-command allowlist; payload extension keeps the message-type count unchanged and only needs the two `protocol.ts` files + docs in sync.
  - Alternative considered: a `facebook.*` command family. Rejected — violates the platform-neutral protocol contract and adds another allowlist sync point.
- Unsupported commands on a Facebook edge MUST return an honest failure receipt, never log-and-drop.
  - Rationale: today an edge with no browse session logs "session not created, ignored" with no receipt, reproducing the notification-monitor silent-drop symptom — and this path has no patrol watchdog to recover it. Command routing must dispatch by driver capability and reply `capability_unsupported` when unhandled.
- Execute Facebook comments through an optional driver `comment` capability object, not by bypassing the driver.
  - Rationale: keeps the platform abstraction intact and prevents a second hardcoded fork. Facebook targeted flow MUST NOT reuse the `'browse'` capability string, or the edge assembly gate would attach the xhs browse session on a Facebook edge. Add a `facebook` entry to `PLATFORM_REGISTRY` rather than a side-channel config source (a side channel would fork the cloud platform source-of-truth).

## Risks / Trade-offs

- [Risk] Facebook verification remains ambiguous despite F1. -> Mitigation: ambiguous verification returns `state_unchanged`/non-commented and does not record success.
- [Risk] Validators are too strict and skip most attempts. -> Mitigation: alert on sustained `compose_skipped`/`no_strong_candidate`; loosen only with logged evidence.
- [Risk] Account logs out and scheduled triggers repeatedly hit the login wall. -> Mitigation: preflight login probe before target selection; on login/checkpoint outcomes raise an alert (existing alert store + Feishu card) and skip the account on subsequent triggers until manual relogin and resume.
- [Risk] Cooldown/risk record async path races. -> Mitigation: pre-run `canAct` and synchronous `markActed` only after verified success.
- [Risk] Console target configuration adds scope. -> Mitigation: v1 may use cloud storage/API first; console UI is only included if necessary for operations.

## Migration Plan

1. Confirm Change 1 F1/F2/F3 are recorded as passed. F1 can be unblocked immediately by having the disposable account publish its own test post; cloud-only work (target storage, entry-point routing, validators, shadow) MAY proceed in parallel during the F3 observation window, while real-posting tasks stay gated behind F1 + F3.
2. Implement cloud target storage/API and entry-point routing (schedule-driven + Feishu `/comment`) with `AIDCP_FB_COMMENT_AUTO` default off, plus handshake insert-time platform provisioning.
3. Implement edge Facebook targeted-comment driver capabilities.
4. Run unit and acceptance tests for validators, risk gating, kill switch, shadow mode, and honest failure matrix.
5. Run shadow on one disposable account; inspect the persisted audit rows.
6. Enable real posting on one disposable account with a 1-2/day cap for several days (the existing global comment cooldown applies unchanged).
7. Only after stable observation, deploy/publish through the documented safe paths.

## Open Questions

- (resolved 2026-07-07) v1 target configuration lives in cloud storage/API only; console UI is deferred to a later change (a single disposable account is served by psql/API).
- (resolved 2026-07-07) Trigger/cap/cooldown: reuse the existing schedule-driven and Feishu `/comment` entry points, the per-account `commentDailyCap`, and the unchanged global comment cooldown; kill switch is an env flag.
- Whether Page-owned targets can later use official Pages API as a separate, lower-risk capability.
- What minimum evidence window is sufficient before raising caps beyond 1-2/day.
