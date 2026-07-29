## Context

Cloud already distinguishes its inactivity recovery scroll from ordinary browse progression by sending `page.scroll.reason = "idle_recover_nudge"`. The value survives the command bridge and Native command projection, but the Native Facebook runtime currently ignores it and activates the bound page before every scroll. A second unconditional activation exists inside the Feed recovery-control click.

The watchdog is a coarse liveness signal, not proof that a particular input RPC stalled. The selected product rule nevertheless authorizes foreground disruption for that recovery intent and forbids it for ordinary automatic browsing.

## Goals / Non-Goals

**Goals:**

- Make the existing watchdog reason the sole automatic Facebook scroll path allowed to activate AdsPower.
- Ensure one watchdog `page.scroll` produces at most one foreground activation.
- Keep routine automatic Feed, Search, Reels, resume, continuation, rescan, and action-recovery scrolls in the background.
- Preserve exact-target binding, fresh location, trusted Native input, and same-page postconditions.

**Non-Goals:**

- Proving that a specific CDP input stalled or adding an independent movement readback channel.
- Adding retries, shorter timeouts, fallbacks, configuration, or a new protocol field.
- Changing watchdog thresholds or Cloud dispatch gates.
- Changing explicit operator foreground actions, guided login, WeChat, packaging, or installer delivery.

## Decisions

### 1. Treat the existing watchdog reason as the foreground authority

The Native Facebook common `page_scroll` entry will compare `PageScrollParams.reason` with the exact value `idle_recover_nudge`. Only an exact match may call `Page.bringToFront`; missing and all other values remain background-only.

Reusing the existing value keeps Cloud, Edge transport, and wire shape unchanged. Adding a new boolean or message type was rejected because the existing Cloud-owned reason is already emitted and covered by integration tests, and the requested change does not need another compatibility path.

### 2. Activate at most once in a watchdog scroll

The conditional activation remains at the common Facebook Feed/Reels entry, so it applies consistently before that watchdog command inspects and actuates the exact bound page. The Feed recovery-control helper will no longer activate independently. It will still re-probe the control immediately before input, because fresh coordinates are required regardless of foreground state.

Keeping the recovery helper's second activation was rejected because a watchdog command could then activate twice, while an ordinary command could still cover the operator's desktop.

### 3. Verify the negative path, not only ordering

Fake-CDP regressions will assert:

- ordinary Facebook scrolls emit zero `Page.bringToFront`;
- `idle_recover_nudge` emits exactly one activation before the first scroll input;
- no-target ordinary scrolls emit zero activation and zero input;
- Feed recovery-control clicks do not independently activate, while preserving one pointer sequence and the existing home-surface postcondition.

The protocol document will name the watchdog-only side effect. No new receipt or accounting behavior is introduced.

## Risks / Trade-offs

- [A normal background scroll can still hang] → The existing bounded command timeout and later watchdog recovery remain; this change intentionally prioritizes non-disruptive normal browsing.
- [The watchdog can represent inactivity unrelated to a stuck scroll] → This is the explicitly selected business boundary; existing Cloud gates and the multi-minute inactivity threshold limit its frequency.
- [An older or malformed command omits the reason] → It remains background-only and fails honestly if input cannot proceed; unknown reasons never gain foreground authority.
- [Feed recovery coordinates can change without foreground activation] → The helper retains its immediate fresh re-probe and same-page postcondition.

## Migration Plan

1. Update Native Facebook routing and Feed recovery behavior in the isolated Edge worktree.
2. Add focused fake-CDP regressions, then run the proportionate Edge tests and typecheck.
3. Update the control protocol documentation and validate this OpenSpec change strictly.
4. Commit, rebase, fast-forward integrate, and push the control and Edge default branches.
5. Do not build or distribute a desktop installer without explicit release scope.

Rollback is a revert of the Edge and control commits. There is no database, configuration, or wire-format migration.

## Open Questions

None.
