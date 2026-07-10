## ADDED Requirements

### Requirement: Facebook self-driving browse loop reuses the cloud role orchestration

Facebook automatic browsing SHALL run over the same cloud event-driven role orchestration as xhs (`feed.entered` → pick card → open → deep-read → interact → back → `feed.entered`), and the cloud roles SHALL decide on structured reports (`page.cards`, `note.detail`) rather than on Facebook selectors. All Facebook-specific difference MUST be pushed below the edge driver's selector/atomic/mapping layer; the cloud orchestration and roles MUST remain platform-neutral and free of any Facebook selector knowledge. The protocol MUST remain platform-neutral: this change SHALL NOT add any new message type and SHALL reuse the existing platform-neutral messages and optional payloads (no `facebook.*` messages).

#### Scenario: Facebook session runs the same feed→open→back loop

- **WHEN** a Facebook account starts a browse session
- **THEN** the same cloud role dispatcher drives the `feed.entered` → pick → open → deep-read → interact → back → `feed.entered` loop
- **AND** no Facebook-specific orchestrator or state machine is introduced

#### Scenario: Cloud roles consume structured page.cards only

- **WHEN** the edge reports the Facebook feed
- **THEN** it reports as structured `page.cards`, and the cloud role that picks a card decides from that structure with no Facebook selectors present in cloud code

#### Scenario: No new protocol message types are added

- **WHEN** the Facebook browse loop communicates edge↔cloud
- **THEN** it uses only existing platform-neutral message types with optional payloads, adds no `facebook.*` message, and the two `protocol.ts` files remain a word-for-word pair

### Requirement: Facebook like is atomic with post-action verification and never fakes success

The Facebook like SHALL be an atomic edge action. After the like, the edge MUST verify that the like button/state truly toggled before reporting `ok`; if the target button is not found or the state did not change, the edge MUST report `no_target` and MUST NOT report a fake success. The edge MUST NOT `count||1` and MUST NOT fabricate a like count — it reports by real observed state. Like-success accounting MUST ride the cloud `RiskController.record` PG path; the edge MUST NOT maintain any parallel in-memory like counter, and `like`/`view` MUST stay within the existing risk actions and quotas.

#### Scenario: Verified toggle reports ok and records via PG path

- **WHEN** the Facebook like button state truly toggles to liked after the click
- **THEN** the edge reports `ok`
- **AND** the like is counted through the cloud `RiskController.record` PG path, not a separate counter

#### Scenario: Missing target or unchanged state reports no_target

- **WHEN** the like target is not found, or the button/state does not change after the action
- **THEN** the edge reports `no_target` and does not report a success and does not `count||1`

#### Scenario: No parallel in-memory like counter

- **WHEN** a Facebook like succeeds
- **THEN** the count flows only through the cloud risk PG record path and no edge-local parallel like counter is incremented

### Requirement: Facebook browse commands enter the edge active-command allowlist with a bounded idle watchdog

Facebook browse/like standalone commands (independently dispatched, not part of a `plan.response` step) MUST be added to the edge `onMessage` active-command routing allowlist so they reach the browse handler; otherwise they are silently dropped by the "other active message ignored" branch. Each Facebook browse/like command MUST have a bounded timeout and, on timeout, MUST return an honest `timeout`/`no_target` receipt. The Facebook browse path MUST carry a bounded idle watchdog (reusing browse-loop-resilience bounded-idle) so a cloud-`sent` command that yields no edge action and no receipt cannot livelock the session. A route regression assertion MUST guard the allowlist membership.

#### Scenario: Facebook command routes to the handler, not dropped

- **WHEN** the cloud sends a standalone Facebook browse or like command
- **THEN** the edge active-command router dispatches it to the browse handler
- **AND** it is not swallowed by the "other active message ignored" branch

#### Scenario: Command timeout returns an honest receipt

- **WHEN** a Facebook browse/like command exceeds its bounded timeout
- **THEN** the edge returns an honest `timeout`/`no_target` receipt rather than hanging

#### Scenario: Idle watchdog bounds a stuck Facebook session

- **WHEN** a cloud command is `sent` but the Facebook edge produces no action and no receipt
- **THEN** the bounded idle watchdog recovers or ends the session within a finite bound instead of hanging indefinitely

### Requirement: Facebook browse-capability flip lands atomically with the BrowseSession implementation

Declaring the `browse` capability for Facebook (which flips the edge assembly gate) MUST land in the same change as the Facebook-specific BrowseSession implementation; splitting them across changes/commits is forbidden, because a `browse` flip without a Facebook BrowseSession would make the assembly gate mount the xhs BrowseSession on a Facebook edge. Facebook payloads MUST map faithfully into the existing structured shapes: because Facebook has no collect/favorite, `collect` MUST be an honest default/absent value and MUST NOT be fabricated.

#### Scenario: Browse flip without a Facebook BrowseSession is forbidden

- **WHEN** the `browse` capability is declared for Facebook
- **THEN** the Facebook BrowseSession implementation is present in the same change, so the assembly gate resolves the Facebook BrowseSession and never the xhs one

#### Scenario: Absent collect is honestly defaulted

- **WHEN** the edge maps a Facebook post into the structured card/detail shape
- **THEN** the `collect` field is an honest default/absent value, never a fabricated number, because Facebook has no favorite/collect

### Requirement: Facebook automatic browse and like are default-off and shadow-first

Facebook automatic browsing and liking SHALL be controlled by the default-off kill switch `AIDCP_FB_BROWSE_AUTO`. When the switch is off, missing, invalid, or false, no automatic Facebook browsing or liking occurs. A shadow mode SHALL run first: browse-only, or likes logged but not executed. Real likes MUST only be enabled after a shadow observation passes.

#### Scenario: Kill switch off prevents any automatic browse or like

- **WHEN** `AIDCP_FB_BROWSE_AUTO` is off, missing, or false
- **THEN** no automatic Facebook browse loop or like runs, even if Facebook accounts exist

#### Scenario: Shadow mode browses or logs likes without executing them

- **WHEN** shadow mode is active
- **THEN** the loop only browses, or produces like decisions that are logged but not executed, and records no like success/risk

#### Scenario: Real likes require the switch on after shadow passes

- **WHEN** real Facebook likes are to be executed
- **THEN** the kill switch is on and the shadow observation has already passed

### Requirement: Facebook browse selectors are robust across wide/narrow layouts and DOM variants

Facebook renders responsive wide and narrow layouts (plus logged-in variant / A-B rollout differences) that place the feed cards, post/detail body, like control, and scroll container in different DOM structures. Every Facebook edge selector used by browsing and liking MUST resolve DOM-first — by stable roles/attributes/scoped structure, never by pixel coordinates or a single brittle absolute path — and MUST match BOTH the wide and narrow layouts. When more than one layout variant renders the same logical control (a duplicated wide+narrow control), the selector MUST pick the visible/active one rather than blindly taking the first DOM match. A selector that matches only one layout MUST be treated as a defect, not shipped. On any layout where a required target cannot be resolved, the edge MUST report `no_target` (never a fake success), so the DOM-first three-gate escalation can flag a systematic layout/version change instead of silently acting on the wrong element.

#### Scenario: Wide layout targets resolve

- **WHEN** the Facebook feed renders in the wide layout
- **THEN** the feed card, like control, and scroll container all resolve via the width-agnostic DOM-first selectors and the action proceeds

#### Scenario: Narrow layout resolves via the same selectors

- **WHEN** the same account renders the Facebook feed in the narrow layout
- **THEN** the same logical targets resolve through the same width-agnostic selectors, with no layout-specific fork required at the call site

#### Scenario: Duplicated wide+narrow control picks the visible one

- **WHEN** both a wide-layout and a narrow-layout copy of the same like control exist in the DOM
- **THEN** the selector acts on the visible/active control, never blindly the first match

#### Scenario: Unresolvable target on a layout is honest

- **WHEN** a required feed/like/detail target cannot be resolved on the current layout or Facebook version
- **THEN** the edge reports `no_target` and never a fake success, letting the three-gate escalation flag a systematic layout change
