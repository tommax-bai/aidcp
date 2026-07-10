## ADDED Requirements

### Requirement: Facebook publishing reuses the publish approval three-layer defense and never silently publishes unauthorized

Facebook post publishing SHALL reuse the existing publish approval three-layer
defense in depth without cloning or weakening it: the approval signal file
contract (`/tmp/aidcp-publish-approve-<id>.json`, byte-identical path on edge
and cloud), the edge lease quiesce, the `CommandSequencer` step-by-step command
sequence, and the version gate that defeats approve-then-edit TOCTOU. Facebook
publishing SHALL also apply the existing banned-phrase validation. When
authorization is missing or invalid (no approval signal, or a signal that does
not match), the system MUST NOT silently publish. If the content changes after
approval, the approval signature MUST be voided and the item MUST return to
pending review. If the edge is offline, publishing MUST have zero side effects
and the item MUST remain pending.

#### Scenario: Only a valid approval signal permits a real post

- **WHEN** a Facebook publish attempt runs
- **THEN** it posts only if a valid approval signal file matching the current content version is present
- **AND** with a missing or invalid approval signal it does not post and reports an unauthorized/pending outcome

#### Scenario: Approve-then-edit voids the signature and returns to pending

- **WHEN** a Facebook draft is approved and then its content is edited before the edge submits
- **THEN** the version gate detects the mismatch, the approval signature is treated as void, and the item returns to pending review instead of being posted

#### Scenario: Edge offline leaves the item pending with zero side effects

- **WHEN** the edge is offline at the time a Facebook publish would run
- **THEN** no post is made, no risk/quota is recorded, and the item stays pending for a later approved attempt

### Requirement: Facebook publish command semantics are Facebook-specific, not the Xiaohongshu shape

The Facebook publish command kind SHALL be Facebook-specific and MUST NOT reuse
the Xiaohongshu publish shape: no `creator.xiaohongshu.com` entry, no "上传图文"
tab `select_mode` step, no xhs topic-`@`/hashtag semantics, and no xhs cover
selection. Facebook publishing SHALL drive its own inline/dialog composer single
flow. The new command kind SHALL be edge-side (internal to the Facebook executor
and its command sequencing) and MUST NOT be introduced as a new protocol message
type; the two `protocol.ts` copies and `docs/protocol.md` message counts SHALL
remain unchanged by this change.

#### Scenario: Facebook publish navigates to the Facebook composer, not an xhs URL

- **WHEN** a Facebook publish sequence starts
- **THEN** it opens the Facebook composer surface (own timeline / target Page composer)
- **AND** it never navigates to `creator.xiaohongshu.com` or drives the xhs publish page

#### Scenario: Facebook publish has no select_mode step

- **WHEN** the Facebook publish command sequence executes
- **THEN** it contains no xhs "上传图文" tab `select_mode` step and no xhs cover/topic-`@` steps, driving the Facebook composer inline/dialog flow instead

#### Scenario: New publish kind is edge-side and the protocol is unchanged

- **WHEN** the Facebook publish command kind is added
- **THEN** it lives on the edge side and no new protocol message type is created
- **AND** `AC-PROTO-*` stays green with both `protocol.ts` copies and the `docs/protocol.md` counts unchanged

### Requirement: Facebook publish post-verification prevents false success

A Facebook publish sequence SHALL be bounded by a watchdog timeout and SHALL
return honest outcomes. Success SHALL be determined only by the post actually
appearing on the account's own timeline / target surface. A half-executed
submit MUST NOT be silently swallowed into `ok`; the executor MUST report an
honest failure. On sequence timeout the executor MUST report an honest timeout
rather than a fabricated success.

#### Scenario: Post visible on timeline reports ok

- **WHEN** after submit the post is verified to appear on the account's own timeline / target surface
- **THEN** the executor reports `ok:true`

#### Scenario: Half-executed submit reports honest failure, not false success

- **WHEN** the composer closes but the post is not visible (or is held for moderation)
- **THEN** the executor reports an honest failure reason and MUST NOT report `ok`

#### Scenario: Sequence timeout reports honest timeout

- **WHEN** the publish sequence exceeds its watchdog bound before verification
- **THEN** the executor reports an honest `timeout` and never a fabricated success

### Requirement: Facebook publishing is default-off with a shadow dry-run mode

Facebook publishing SHALL be controlled by a default-off kill switch
(`AIDCP_FB_PUBLISH_AUTO`). In shadow mode the system SHALL only compose and run
the approval dry-run and MUST NOT make a real post, record risk, or consume
quota. Real publishing SHALL occur only when the kill switch is on AND approval
has passed. Publishing counting SHALL flow through the existing risk actions and
the PG-backed quota accounting path.

#### Scenario: Kill switch off means no publish

- **WHEN** `AIDCP_FB_PUBLISH_AUTO` is false
- **THEN** no Facebook post is made regardless of approval state

#### Scenario: Shadow mode composes and dry-runs approval without posting

- **WHEN** Facebook publishing runs in shadow mode
- **THEN** it composes the post and runs the approval dry-run only, making no real post, recording no risk, and consuming no quota

#### Scenario: Real post only after switch on and approval passed

- **WHEN** the kill switch is on and a valid approval has passed
- **THEN** a real Facebook post is made, and the success is counted through the existing risk actions and PG-backed quota accounting
