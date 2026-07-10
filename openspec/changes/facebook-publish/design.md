## Context

Content publishing is Xiaohongshu-only. The publish chain is hardcoded to xhs
at three levels: the entry navigates to `creator.xiaohongshu.com`, the
`PublishCommandKind` step sequence is xhs-shaped (the "上传图文" tab
`select_mode` step, xhs topic-`@`/hashtag semantics, xhs cover selection), and
the success/approval flows assume xhs. Facebook has zero publish
implementation: the edge Facebook driver deliberately does not declare
`publish`, and the cloud registry `facebook` entry declares only `comment`.

The safety-critical part of publishing — the approval three-layer defense in
depth (approval signal file contract, edge lease quiesce, `CommandSequencer`
step-by-step sequence, version gate against approve-then-edit TOCTOU) plus
`BANNED_PHRASES` validation — is platform neutral. This change reuses it
verbatim and adds only the small edge-local Facebook surface.

This change (C) depends on A `account-nurture-discipline-spine` (so a fresh
Facebook account is not on the normal full quota tier on Day 1) and on B
`facebook-browse-and-like-loop` (the change that first makes `facebook` declare
a non-comment capability and exercises the driver capability-assembly gate). C
lands after B.

## Decisions

- Reuse the publish approval three-layer defense 100%, do not re-build it.
  - Rationale: the "no unauthorized silent publish" invariant is the whole
    point of the publish safety model and is platform neutral. The approval
    signal file contract, lease quiesce, step-by-step sequence, and version
    gate all apply unchanged to Facebook.
  - Alternative rejected: a Facebook-only publish branch. That risks a bypass
    path and duplicate divergent approval logic.

- Facebook publishing gets net-new DOM, not the xhs `PublishCommandKind` shape.
  - Rationale: the xhs sequence encodes `creator.xiaohongshu.com`, the
    "上传图文" `select_mode` tab, xhs topic-`@`/hashtag, and xhs cover. None
    of those exist on Facebook, whose composer is an inline/dialog single flow.
    Reusing the xhs shape would be a source of false `no_target` and wrong
    steps.
  - Alternative rejected: parameterize the xhs `PublishCommandKind` with a
    platform branch. That over-couples two unrelated composer flows.

- Success is server-confirmed post visibility, not optimistic DOM state.
  - Rationale: Facebook can optimistically render or hold-for-moderation a
    submitted post. Success must be the post actually appearing on the
    account's own timeline / target surface. A half-executed submit reports
    honest failure; a timeout reports honest timeout.
  - Alternative rejected: "composer closed" as success. That is exactly the
    silent-false-success reverse pattern the red line forbids.

- Depend on B to first trip the registry/driver capability-assembly gate.
  - Rationale: B is where `facebook` first declares a non-comment capability
    and the edge/cloud capability vocabularies must agree. Publish builds on
    that gate; it only adds the `publish` capability string on both ends.

- Zero change to `protocol.ts`.
  - Rationale: the new publish command kind is edge-side (internal to the
    Facebook executor and its command sequencing). It is not a new generic
    action, so it must not become a protocol message type. `AC-PROTO-*` guards
    this.

## Open Questions

- Facebook composer wide/narrow layout variants: the composer (inline on
  timeline vs. modal dialog vs. Page composer) may differ; real-machine probes
  must pin down each layout's selectors before selectors are trusted.
- Image attachment in v1 vs. text-only status first: whether v1 includes image
  attachment or ships text-only `status` posts first (lower surface, faster to
  a verified end-to-end path) is open pending probe cost and the F1 production
  verification re-proof.
