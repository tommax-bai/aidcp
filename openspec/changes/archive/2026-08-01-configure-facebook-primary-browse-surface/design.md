## Context

The integrated Facebook operation policy already makes `persona`, `slow_start`, `rule`, and `consumption` mutually exclusive and Cloud-authoritative. Edge nevertheless starts every Facebook browse session by reporting the ordinary Feed, and Cloud currently authorizes Reels only from evidence-based Feed fallback. The existing Reels reader, list navigation, note routing, like/follow execution, view attribution, and rule/consumption accounting already consume `page.cards{listKind:'reels'}`.

Primary surface is independent from operation mode: it selects the list that supplies content, not the cadence, risk policy, action plan, or durable progress definition. The client must expose both choices for environment creation and editing. This change depends on the integrated source from `add-configurable-facebook-consumption-mode` but remains a separate OpenSpec change because that earlier change is at its delivery boundary.

## Goals / Non-Goals

**Goals:**

- Persist one environment-level `feed | reels` primary surface with Reels as the default for new and existing Facebook environments.
- Keep surface changes independent from operation-policy revisions so rule and consumption progress is not reset.
- Make the Edge client show one four-way operation-mode choice and one independent Feed/Reels choice.
- Let Cloud suppress the initial Feed batch before any evaluation or accounting and authorize the existing Reels entry path.
- Preserve the existing evidence-based Feed-to-Reels fallback when Feed is primary.

**Non-Goals:**

- A second Reels reader, action planner, counter, or risk path.
- Immediate mid-session surface switching; a saved value is pinned for the next session.
- Console editing, client packaging, DEV/OL deployment, or live Facebook acceptance.
- Old-client notices, capability negotiation, compatibility routing, or extra fallback behavior.

## Decisions

### 1. Keep surface authority independent from operation-mode revision

Cloud will store `primary_surface` and its own revision/audit in an environment-keyed table owned by the existing Facebook operation-policy store. The operation-policy projection returned to the customer client will include the surface value and surface revision, but mode writes and surface writes remain separate compare-and-swap operations.

This avoids changing the immutable operation-policy revision used by rule and consumption runtime rows. Putting surface on the existing operation-policy revision was rejected because a Feed/Reels-only edit would supersede unrelated counters and in-flight work. A target-global switch was rejected because the client edits one selected environment and must not alter other customers or environments.

### 2. Seed every Facebook environment to Reels

The additive migration will create one Reels row and one migration audit record for every existing Facebook environment. Provisioning will create the same row atomically with the environment operation policy. Missing rows after schema readiness are invalid authority rather than an implicit Feed default.

### 3. Keep Cloud as the list selector

At session start Cloud pins the environment's primary surface. Edge may still report its ordinary Feed bootstrap, but when Reels is pinned Cloud will intercept any initial `listKind:'feed'` observation before card identity collection, content evaluation, interaction appraisal, or view accounting. Cloud then sends the existing `page.scroll` command with a new reason, `facebook_reels_primary`.

The existing Feed fallback reason remains evidence-specific and is not reused for configured primary entry. The existing Reels pending/confirmed state machine is generalized only enough to remember the entry reason and drive bounded hydration recovery.

### 4. Reuse the existing Edge Reels entry and confirmation

Facebook Edge routing will map both `facebook_reels_primary` and the existing fallback reason to `enterReels()`. Navigation alone is not success: the existing `route_ready`, `reels_pending`, and reportable Reel-card checks remain authoritative. Once `page.cards{listKind:'reels'}` arrives, all four operation modes continue through their current paths.

### 5. Present two independent client choices

Existing-environment UI will replace the four switch-like mode rows with one four-option select. A separate two-state Feed/Reels control writes the surface authority. Creation uses the same two concepts and defaults the surface control to Reels. Both mutations remain non-optimistic and use Cloud write-after-read truth.

## Risks / Trade-offs

- [Edge still opens Feed briefly as a bootstrap] → Cloud returns before evaluating or counting that batch; a pre-navigation handshake is intentionally out of scope.
- [Reels cannot produce a reportable first card] → Keep the existing honest pending/failure result and do not claim the session has started browsing.
- [Schema is added to shared DEV/OL PostgreSQL] → Source delivery stops before deployment; any later deployment must pass the existing shared-schema gate.
- [Existing environments change behavior together] → The migration is explicit, audited, and defaults every Facebook environment to Reels as requested.

## Migration Plan

1. Add the surface policy and audit tables, then seed all existing Facebook environments to `reels`.
2. Deploy Cloud source and schema only in a separately authorized delivery after shared-schema compatibility is proven.
3. Publish/install the updated Edge client separately; packaging is not part of this change.
4. Rollback, if later authorized, changes selected environments to `feed`; the additive tables can remain without affecting operation-mode runtime history.

## Open Questions

None. The user selected Reels for new and existing environments and explicitly excluded old-client messaging and packaging.
