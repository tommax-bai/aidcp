## Why

Content publishing is implemented for Xiaohongshu (xhs) only. The publish
pipeline navigates to `creator.xiaohongshu.com`, drives a `PublishCommandKind`
sequence whose steps are xhs-shaped (the "上传图文" tab `select_mode`, xhs
topic `@`/hashtag semantics, xhs cover selection), and its success and
approval flows assume xhs. Facebook has zero publish implementation: the edge
Facebook driver deliberately does not declare `publish`, and the cloud
platform registry entry for `facebook` only declares `comment`. So a Facebook
account cannot publish a post at all.

To give Facebook posting we must NOT clone or weaken the publish approval
model. The safety-critical part of publishing — the three-layer defense in
depth that guarantees "no unauthorized silent publish" — is fully platform
neutral and MUST be reused 100% as-is. The genuinely new surface is small and
edge-local: a Facebook-specific publish executor and a Facebook-specific
publish command semantics that drive the Facebook composer instead of the xhs
creator page. This capability depends on the account-nurture discipline spine
(nurture-disciplined quotas + real rate-limit backoff) and on the Facebook
browse capability (which is the change that first makes `facebook` declare a
non-comment capability and exercises the driver capability-assembly gate).

## What Changes

- Facebook posting reuses the existing publish approval three-layer defense in
  depth (approval signal file contract, edge lease quiesce, step-by-step
  command sequence, version gate against approve-then-edit TOCTOU) plus the
  existing banned-phrase validation; no bypass path is added for Facebook.
- Facebook publish command semantics are Facebook-specific, NOT xhs-shaped:
  no `creator.xiaohongshu.com` entry, no "上传图文" tab `select_mode` step, no
  xhs topic-`@`/cover semantics. Facebook drives an inline/dialog single flow.
- Publish post-verification prevents false success: a post counts as published
  only when it actually appears on the account's own timeline / target
  surface; a half-executed submit reports honest failure, never silent `ok`.
- Default-off `AIDCP_FB_PUBLISH_AUTO` kill switch plus shadow dry-run
  (composition + approval dry-run, never a real post) before real posting.
- Target zero change to `protocol.ts`: the new publish command kind is
  edge-side (internal to the Facebook executor), not a new protocol message
  type; the two `protocol.ts` copies and `docs/protocol.md` counts stay put.

## Capabilities

### New Capabilities

- `facebook-publish`: Defines Facebook post publishing that reuses the publish
  approval three-layer defense in depth and banned-phrase validation, drives a
  Facebook-specific publish command semantics (not the xhs publish shape),
  verifies server-side that the post actually appears before reporting success,
  and is default-off with a shadow dry-run mode.

### Modified Capabilities

- `platform-runtime-abstraction`: The Facebook driver/registry declares the
  `publish` capability, with the edge driver and cloud registry capability
  vocabularies kept byte-for-byte aligned.

## Impact

- Affected repos: `aidcp-edge` (`src/facebook/`: Facebook publish executor +
  Facebook `PublishCommandKind` semantics + post-verification), `aidcp-cloud`
  (platform registry `facebook` gains `publish`; Facebook publish orchestration
  wired to the existing publish approval path), `aidcp` (this change/doc only).
- Target zero change to `protocol.ts`: the new publish command kind is edge-side
  and MUST NOT become a new protocol message type; `AC-PROTO-*` must stay green.
- Reuse-first: reuse the publish approval signal file contract
  (`/tmp/aidcp-publish-approve-<id>.json`, byte-identical path on both ends),
  edge lease quiesce, the `CommandSequencer` step-by-step sequence, the version
  gate that defeats approve-then-edit TOCTOU, the `BANNED_PHRASES` validation,
  and the existing publish approval UI. Publishing already sits inside the
  existing risk actions and quota accounting (PG-backed counting path).
- Dependencies: `account-nurture-discipline-spine` (A: nurture quotas +
  rate-limit backoff) and `facebook-browse-and-like-loop` (B: first exercises
  the registry/driver capability-assembly gate). This change (C) lands AFTER B.
- Rollout: default-off `AIDCP_FB_PUBLISH_AUTO`, shadow dry-run first, deploy to
  `ol` during the isolation window; real posting gated on the F1 production
  verification executor being re-proven and per-profile proxy being ready.
- Red line: NEVER add a Facebook-only silent-publish shortcut that bypasses the
  approval gate.
