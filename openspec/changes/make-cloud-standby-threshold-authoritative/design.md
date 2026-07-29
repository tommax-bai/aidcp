## Context

Cloud already computes `browserStandby.eligible`, `wakeAt`, and `minWaitMs`
from current risk and session state. Edge nevertheless persists its own
`browserColdStandbyMinWaitMs` and compares the two thresholds with `Math.max`.
Because the hidden Edge value is materialized into `userData/settings.json`,
an old default survives application upgrades and silently vetoes newer Cloud
policy.

This change crosses the Cloud hint contract, Edge execution policy, persisted
desktop settings, and the OpenSpec baseline. It does not change the wire shape.

## Goals / Non-Goals

**Goals:**

- Establish Cloud as the single owner of the standby wait threshold.
- Preserve Edge's visible local opt-out and all local execution safety gates.
- Make missing or malformed Cloud evidence fail safe by keeping the browser
  open.
- Stop legacy hidden values from affecting or re-entering persisted settings.
- Keep mixed-version rollout backward compatible.

**Non-Goals:**

- Changing Cloud's default five-minute threshold or wait-source calculation.
- Changing `warmupMs`, the three-minute `minHoldMs`, browser-slot scheduling,
  or wake/retry behavior.
- Removing `minWaitMs` from the protocol or introducing a protocol version.
- Packaging or releasing a desktop installer as part of source implementation.

## Decisions

### Cloud hint is the only wait-threshold authority

Edge will compare current `remainingMs = wakeAt - now` directly with the
validated `browserStandby.minWaitMs`. It will not combine that value with an
Edge default, persisted setting, or Edge environment variable.

Keeping the comparison on Edge remains necessary: a hint can arrive late or be
re-applied after the post-wake hold, at which point its remaining wait may have
fallen below the Cloud-selected threshold.

Alternatives rejected:

- Expose an Edge threshold UI: there is no observed per-machine product need,
  and customers would still have to understand two asymmetric authorities.
- Keep a compiled Edge fallback: this preserves the same silent drift whenever
  Cloud later lowers its threshold.
- Trust only `eligible=true`: this can close a browser after the qualifying wait
  has mostly elapsed.

### Missing Cloud evidence never starts a new standby cycle

The existing `browserStandby` payload remains optional. A missing payload does
nothing; a payload with missing or invalid required fields is rejected; and
Edge's existing `cloud === connected` gate remains required before entering
standby. No local threshold attempts to reconstruct Cloud's decision.

An environment already in standby retains the wake timer created from its last
valid hint and its existing Cloud reconnect behavior. This preserves the
deterministic wake path without allowing new decisions from incomplete data.

### Legacy settings are ignored immediately and removed through normal writes

On load, Edge removes `browserColdStandbyMinWaitMs` from the in-memory settings
object before it can reach `settings:get` or standby evaluation. The central
save path also drops the key from incoming patches, so a renderer or older
caller cannot re-inject it. The next successful normal settings save writes the
sanitized object and removes the stale disk key.

This avoids an unconditional startup rewrite of a settings file that may
contain unrelated customer configuration. Rollback to an older package before
the next save may temporarily restore the old behavior; after cleanup, an older
package falls back to its packaged default.

### Protocol shape and mixed-version compatibility remain unchanged

Cloud continues sending `minWaitMs`. Old Edge builds may remain more
conservative because they still apply their local maximum; new builds use the
Cloud value. This mixed period affects resource efficiency, not irreversible
browser actions or task correctness, so no capability split is required.

The active `browser-slot-scheduling` delta also modifies the cold-standby safety
requirement. Its wording must be reconciled with this authority change before
either change is archived, so a later archive cannot reintroduce “local
threshold” semantics.

## Risks / Trade-offs

- **[Upgraded clients may close browsers earlier than before]** → Preserve the
  visible opt-out, all local safety gates, the three-minute hold, and focused
  regression coverage using a stale 20-minute setting with a five-minute Cloud
  hint.
- **[An operator relied on the undocumented Edge environment override]** →
  Treat removal as a breaking hidden-control change and document Cloud's
  centralized override as the supported operational control.
- **[Old and new clients differ during rollout]** → Keep the wire contract
  unchanged and report the installed-client boundary honestly; package rollout
  is separate and explicit.
- **[A concurrent OpenSpec delta restores old wording]** → Reconcile
  `browser-slot-scheduling` in the control-repo commit and require rebase before
  archive.

## Migration Plan

1. Land the Cloud comment/contract clarification without changing runtime
   behavior.
2. Land the Edge source change and tests.
3. Land and validate the OpenSpec/protocol updates.
4. Existing installed clients remain unchanged until a separately authorized
   installer release.
5. Rollback is an Edge source/package rollback; the unchanged Cloud wire field
   remains compatible with both versions.

## Open Questions

None for this change. Ownership of `warmupMs` and other hidden overrides can be
reviewed separately if product evidence shows the same divergence.
