## Context

The Native Reels entry executor sends `Page.navigate('https://www.facebook.com/reels/')` and currently gives each of its initial and optional retry navigation attempts eight seconds to observe an `interactive` or `complete` document. In the observed OL session, Chrome committed `/reels/`, passed through `/reel/`, and reached a canonical `/reel/<id>` after about 20 seconds, so the eight-second inner wait returned `probe_failed` before the successful route finished loading.

This readiness wait is distinct from the existing 15-second canonical Reel identity/card hydration window, which starts only after a Reels surface is available. The production `page.scroll` request, Edge admission, Native command ceiling, and Facebook Native session ceiling are already aligned at 180 seconds; Cloud's idle recovery threshold is 240 seconds.

## Goals / Non-Goals

**Goals:**

- Give both the initial and optional retry Reels entry navigations up to 30 seconds to produce a ready document.
- Keep one source of truth for that Reels-specific duration and add a regression assertion for it.
- Prove mechanically that the longest named entry path still fits inside the existing 180-second scroll budget with receipt/probe margin.
- Preserve all current entry, blocker, cancellation, identity, and success semantics.

**Non-Goals:**

- Change the eight-second document-readiness windows used by Facebook identity, note, search, group, publish, or ordinary Feed recovery paths.
- Change the 15-second canonical Reel hydration window, retry count, input authority, outcome classification, or Cloud continuation behavior.
- Raise the 180-second Facebook scroll/session ceilings or lower the 240-second Cloud idle watchdog.
- Package, install, deploy, or operate a real account.

## Decisions

### Add one Reels-entry-specific 30-second readiness constant

Define `FACEBOOK_REELS_ENTRY_READY_TIMEOUT = Duration::from_secs(30)` beside the entry executor and use it for both calls surrounding the initial and optional retry `Page.navigate('/reels/')`. This keeps the observed slow route local to the only path that needs the larger window.

Alternative considered: replace every `wait_for_facebook_ready(..., 8s)` call with 30 seconds. Rejected because the incident proves only the multi-step Reels landing route is slow; widening unrelated navigation failures would delay their honest terminal results without evidence.

### Keep identity hydration independent

The existing 15-second canonical-card window continues to begin only after a ready Reels surface is observed. Document readiness proves only that inspection may continue; it does not prove that a canonical Reel exists or that a view occurred.

Alternative considered: merge readiness and identity hydration into one 45-second wait. Rejected because readiness and canonical identity are different postconditions and have different terminal evidence.

### Retain the 180-second end-to-end scroll budget

The longest named Reels entry path contains two 30-second readiness windows and at most two 15-second canonical-card windows, for 90 seconds total. The existing 180-second request/admission/engine/session chain therefore leaves about 90 seconds for probes, one foreground activation, key dispatch, scheduling, and receipt delivery. A source-level timeout-contract test will assert that the named waits plus a 30-second non-wait margin remain below the existing scroll budget.

Alternative considered: raise the four 180-second Facebook scroll/session constants. Rejected because no shorter outer layer preempts the new inner windows, and raising them would broaden every Facebook scroll command rather than this Reels entry path.

### Keep the 240-second Cloud watchdog unchanged

Even the 90-second worst named wait remains well below the 240-second idle nudge. The change therefore does not create a legitimate Reels entry that should overlap the watchdog. No Cloud delta is needed.

## Risks / Trade-offs

- [A page that never becomes ready now holds one entry attempt 22 seconds longer] → Keep the wait bounded at 30 seconds and retain the existing one-retry maximum and 180-second command ceiling.
- [A ready document could still lack a canonical Reel] → Preserve the separate 15-second canonical identity/card proof and honest failure result.
- [A later timeout change could silently make the 30-second window ineffective] → Add a timeout-chain tripwire covering two readiness windows, two identity windows, and explicit non-wait margin.

## Migration Plan

Implement and validate in an isolated `aidcp-edge` worktree, integrate source and OpenSpec evidence, and do not build or install an Edge package. Rollback is a source revert from the named 30-second constant to eight seconds; there is no data, protocol, configuration, or deployment migration.

## Open Questions

None.
