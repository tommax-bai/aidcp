## Context

The live Xiaohongshu failure occurs after `EdgeTaskCoordinator` has correctly granted a `comment_prepare` lease. Its takeover calls `NativeBrowseSession.quiesceForTask()`, which marks the session blocked; the same session then rejects the lease owner's `search.execute`. That generic rejection omits the negotiated search-activity terminal fields, so Cloud drops it and waits for a step timeout.

The live Facebook failure occurs after Cloud correctly authorizes an explicit-empty Feed fallback. `FacebookReelsReader.enter()` navigates to Reels but returns `null` when the active card is not readable within its initial settle budget. `FacebookBrowseSession` therefore keeps Feed ownership even though the browser is already on a canonical Reel route, while Cloud consumes its one-shot authorization. The generic idle nudge later executes as a Feed scroll and navigates back home.

Both fixes must preserve current message names, risk ownership, task priority, fail-closed page writes, mixed-version compatibility, and the rule that `received/dispatched` is not execution proof.

## Goals / Non-Goals

**Goals:**

- Separate ordinary-browse quiescence from admission of the current task lease's Native commands.
- Make every Native search rejection consumable under the negotiated search-activity receipt contract.
- Preserve Facebook Reels surface ownership once the route transition is confirmed, even when the first semantic card is late.
- Retry a pending Reels transition immediately and within a fixed attempt bound; never wait for the generic idle watchdog or navigate the pending Reel back to Feed.
- Cover the live failure sequences with focused cross-module tests.

**Non-Goals:**

- Changing Edge/Cloud message names, expanding the `feed|detail` protocol surface union, or moving Facebook into Native.
- Treating an unreadable Reel card as a successful view or interaction.
- Raising search, browse, or interaction quotas.
- Building or releasing a desktop installer.

## Decisions

### D1. Keep coordinator admission authoritative and make Native quiescence lane-specific

`EdgeTaskCoordinator.canExecute(taskId)` remains the single page-lease admission source in `main.ts`. `NativeBrowseSession` will interpret its quiesced flag as “ordinary browse lane blocked”, not “all Cloud commands blocked”: an envelope carrying a non-empty task ID may execute after the coordinator has admitted it; an unowned ordinary command still receives an explicit quiesced failure.

This is preferred over temporarily unblocking the whole session on acquire because that would reopen the ordinary browse lane and weaken the single-writer invariant.

### D2. Derive Native search terminals from the original Cloud envelope

Native IPC continues to receive only allowlisted high-level command fields. Electron retains `activityId`, `purpose`, and `scope` from the Cloud envelope and adds them to `action.completed` when Native search is rejected or fails before actuation. The terminal is `ok=false`, `actuated=false`, `searchOutcome=not_submitted`.

When Native returns search `page_cards`, Electron reports the cards and a correlated `results_ready` or `no_results` terminal with the observed result count. This keeps activity accounting honest without passing orchestration metadata into the Rust page-rule payload.

### D3. Model Facebook transition state separately from first-card readiness

The Reels reader will return a structured transition result: `ready` with a card, `route_ready` when a canonical Reels route is confirmed but no active card is yet readable, or `failed` when navigation itself is unconfirmed. On `route_ready`, Edge commits `listMode=reels` and marks the transition pending, but reports no view/card success.

The next Reels scroll while pending first settles and reports the current card; it does not advance to another Reel. This prevents both false view accounting and the Feed `ensureFeed()` rollback.

### D4. Cloud tracks Reels authorization as pending versus confirmed

Cloud replaces the consumed boolean semantics with an explicit `idle|pending|confirmed` state and a small retry counter. Reels `page.cards` confirms the transition. A `reels_pending` scroll terminal causes an immediate surface-aware retry up to a fixed bound. A terminal navigation failure resets authorization to `idle`, preserving future fallback eligibility.

The retry uses the existing `page.scroll` message and still passes through normal pause, comment-hold, session, and view-quota gates. No synthetic page success is generated.

### D5. Keep generic idle recovery as a final watchdog only

The 240-second idle nudge remains unchanged for unknown stalls. Known transition-pending terminals receive their own bounded recovery path, so the watchdog never becomes the primary state-machine edge.

## Risks / Trade-offs

- [A task envelope could bypass Native quiescence] → `main.ts` continues to reject task IDs that do not match the active coordinator lease; focused tests cover owned, stale, and absent task IDs.
- [Duplicate search accounting] → Cloud's existing activity-ID dedup remains authoritative; Electron emits one correlated terminal per Native command.
- [A Reels route is confirmed but never becomes semantically readable] → retries are bounded and remain honest failures; no view or interaction is counted.
- [Mixed Edge/Cloud versions use `no_target` instead of `reels_pending`] → pending Cloud state treats an immediate fallback `no_target` as an unconfirmed transition and preserves bounded retry/reset behavior.
- [View quota blocks a retry] → the existing quota gate remains authoritative and the transition stays pending rather than being declared successful.

## Migration Plan

1. Implement and validate Edge behavior first in an isolated worktree; no installer is built.
2. Implement Cloud pending/confirmed fallback state and focused mixed-version tests in an isolated worktree.
3. Rebase, run Edge/Cloud acceptance, full tests, and typecheck, then fast-forward both default branches.
4. Restart the local source Electron client for installed-runtime evidence and deploy the clean Cloud default branch to DEV only.
5. Verify one Xiaohongshu task-lease search and one read-only Facebook empty-Feed fallback from logs. Roll back Cloud first if the fallback retry misbehaves; Edge remains protocol-compatible.

## Open Questions

- None. The live DEV traces provide the required failure timing and page-route evidence.
