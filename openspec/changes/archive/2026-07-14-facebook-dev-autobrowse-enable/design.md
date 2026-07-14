## Context

`FacebookBrowseSession` is intentionally fail-closed: a missing or invalid `AIDCP_FB_BROWSE_AUTO` resolves to `off`. The Electron fleet currently supplies profile identity and the resolved cloud URL, but not this mode. As a result, a logged-in Facebook profile can connect to dev successfully and still never start its browse loop.

The Electron companion already prefers structured `[ui-event]` output over platform-specific log parsing. Facebook browse events currently report truthfully to cloud but use Facebook-specific log wording, so a successful read does not produce the local activity/presence projection or immediate fallback increment. The cloud `dailyUsage` snapshot remains authoritative for the account-wide daily total; structured events only close the gap until that snapshot refresh arrives.

The desktop process already has one authoritative `resolveCloudUrl()` result immediately before each core spawn. It includes a normalized environment key (`dev`, `ol`, or `custom`) and is used to stamp the actual connection target for that run.

## Goals / Non-Goals

**Goals:**

- Enable real Facebook browsing and liking for every Facebook AdsPower profile whose spawned core is connected to `dev`.
- Make the mode explicit in the final child environment, so inherited shell variables cannot accidentally alter the policy.
- Keep all existing risk quotas, pacing, dwell timing, error handling, and per-environment isolation unchanged.
- 当 Facebook 详情页的看图、评论或互动原子动作不被支持时，明确完成失败恢复并返回原列表上下文，绝不把详情页滚动伪装成 feed 进展。
- Keep `ol`, custom endpoints, and non-Facebook profiles out of this rollout.

**Non-Goals:**

- Adding a per-profile toggle, a new renderer setting, or a cloud-side configuration API.
- Changing Facebook selectors, interaction evaluation, quotas, or the shadow-mode implementation.
- Adding any new wire message type, cloud-side configuration API, database migration, or `ol` deployment.

## Decisions

### Derive mode from the resolved cloud environment, not from profile metadata

The Electron main process will derive the mode after resolving the cloud target and after building the final spawn environment. A small pure helper in the fleet module receives the normalized platform and cloud environment key:

- `facebook` + `dev` resolves to `on`.
- Every other combination resolves to `off`.

This covers all Facebook profiles without a hand-maintained allowlist and keeps the decision at the same boundary that chooses the actual cloud target. Deriving from a raw URL or a profile remark would be ambiguous for custom endpoints and could accidentally enable a production-like endpoint.

### Override inherited browse mode explicitly

The main process will always assign `AIDCP_FB_BROWSE_AUTO` after inherited/provider environment merging. This deliberately overrides a shell-level `on`, `shadow`, or stale value: `dev` is the only automatic real-interaction lane; `ol` and custom endpoints remain `off` by default.

### Reuse existing restart semantics

Mode is read by the core only during process startup. Existing single-environment restart and "restart all for cloud switch" paths already recreate each child and will apply the new mode without adding an implicit restart or cross-profile side effects.

### Emit desktop UI events at confirmed Facebook action boundaries

`FacebookBrowseSession` will emit structured events only at confirmed boundaries: session start, feed availability, a successfully reported `note.detail`, and a successful `action.completed{action:'like', ok:true}`. The note-detail event increments the local view fallback by one; the confirmed like event increments likes by one. Shadow-mode, failed, already-liked, and no-target paths emit no success increment. The generic Facebook like-success log is excluded from the legacy parser so the structured confirmation is the single local increment.

For a confirmed `note.detail`, the activity sentence and presence text derive from the already-read author nickname and the first normalized characters of the post body (falling back to `title`). Both are bounded for a one-line desktop activity item. If either field is absent, the text degrades gracefully; it never substitutes a permalink or raw note ID as a label.

### Preserve canonical deep-read completion semantics across the edge/cloud boundary

`action.completed.action` is a cloud orchestration key (`browse_images`, `scroll_comments`), while the wire command names are dotted protocol types (`note.browse_images`, `note.scroll_comments`). The Facebook session must map every cloud-dispatchable command to its canonical completion action before reporting an unsupported failure. In particular, failed deep-read actions must reach `DeepReader` and `CommentReviewer`, which then progress to the ordinary return-to-list path.

The cloud ingress also normalizes legacy dotted action names before publishing them to the session event bus. This is a compatibility guard, not a replacement for the edge contract: it prevents an older client from making the dispatcher mistake a detail-page failure for an unknown command and issuing a feed scroll in the wrong page context.

Before executing `page.scroll`, Facebook edge re-enters the remembered list context. The context is the main feed or the active search results URL, so recovery from a detail page cannot produce a false `page.cards` report while also preserving search-result browsing.

## Risks / Trade-offs

- [All dev Facebook profiles can perform real likes] → The user explicitly approved this rollout. Existing cloud risk budgets, dwell delays, action validation, and failure paths remain active and are not bypassed.
- [A developer launches against dev unintentionally] → This policy is intentionally scoped to dev. `ol` and custom targets force `off`, and no environment variable can silently override that scope.
- [An environment is already running] → Saving or merging code does not change its current child process. A controlled restart is required, matching the existing cloud selection contract.
- [A core and legacy parser both emit success] → The legacy Facebook like line is deliberately ignored by the fallback mapper once the structured confirmation is present, preventing a visual double count.

## Migration Plan

1. Add the pure mode derivation helper and final spawn-environment injection with focused tests.
2. Validate Edge acceptance tests, full tests, and type checking.
3. Normalize deep-read action completions at the cloud ingress so current and older edge clients drive the same recovery state machine.
4. Integrate Edge and Cloud changes to their default branches, deploy Cloud to `dev`, then restart the local development Edge client and verify its Facebook profile logs show `mode=on`, actual browse activity, matching structured UI events / account today totals, and a return to the original list after a failed deep-read action.

Rollback is immediate: stop/restart the desktop client with an `ol` or custom target, or revert the single Edge change and restart the affected local client.

## Open Questions

None. The user explicitly authorized all Facebook profiles on dev and did not request an `ol` rollout.
