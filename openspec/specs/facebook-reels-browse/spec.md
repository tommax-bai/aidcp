# facebook-reels-browse Specification

## Purpose
TBD - created by archiving change facebook-empty-feed-reels-fallback. Update Purpose after archive.
## Requirements
### Requirement: Facebook Reels identifies exactly one active video card

Edge SHALL distinguish a structurally targetable active video from a reportable Reel card. On `/reel/` or `/reels/`, Edge MAY resolve one unique visible video by greatest viewport intersection, using viewport-center distance only as a tie-breaker, and bind it to a session-local `videoKey` for navigation even when canonical identity is absent. Edge SHALL emit a Reel card only when that same active video is bound to a canonical Facebook `/reel/<id>` identity; the canonical Reel URL SHALL be the card and note identity. Missing or ambiguous active video, off-route observations, and identity-changing reads MUST fail closed and MUST NOT fabricate a card.

#### Scenario: Current Reel wins over preloaded neighbours
- **WHEN** previous, current, and next videos coexist in the DOM
- **THEN** Edge resolves only the video with the greatest current viewport intersection
- **AND** it reports that video only if a canonical current Reel identity is available

#### Scenario: Anonymous Reel landing is navigation-only
- **WHEN** `/reel/` exposes one unique active video but no canonical Reel id
- **THEN** Edge exposes its stable video observation only to the Native navigation actuator and emits no Reel card

#### Scenario: Route is not a Reel
- **WHEN** the current top-level route is home, login, checkpoint, another Facebook surface, or a non-Facebook URL
- **THEN** Edge reports no Reel target and performs no Reels action

### Requirement: Facebook Reels reads the active video's visible text honestly

For a feed-surface note open, Edge SHALL derive the summary from the active video's bottom-left content overlay, exclude author/follow/audio/action labels, and bind every expansion/read step to the same canonical Reel identity. If an anchored expand control cannot be used without identity drift, Edge SHALL return the real visible snippet or an honest no-target result and MUST NOT claim hidden full text was read.

#### Scenario: Active Reel summary is reported as video detail
- **WHEN** the active Reel has a bottom-left textual summary
- **THEN** Edge reports that text as the note content with `mediaType:video` and the canonical Reel URL as noteId

#### Scenario: Expansion changes identity
- **WHEN** an attempted summary expansion changes the route or active video identity
- **THEN** Edge rejects the expanded result and MUST NOT attribute another Reel's text to the requested note

### Requirement: Facebook Reels like is a single verified action

When Cloud authorizes `interaction.like`, Edge SHALL require the command noteId to match the active canonical Reel, locate exactly one like action in the active video's right-side action rail by structural relationship, and perform at most one trusted click. `ok:true` SHALL require the same Reel to expose a positive selected-state witness such as an unlike semantic or selected reaction icon after the click. Rounded count text alone MUST NOT prove success; ambiguous target, already-liked state, identity drift, missing witness, or timeout MUST be reported honestly and MUST NOT be recorded as success.

#### Scenario: One click produces an unlike state
- **WHEN** exactly one unselected active-Reel like control is found and one trusted click changes it to a positive selected state on the same Reel
- **THEN** Edge reports a successful like with DOM-derived noteId and observation for existing Cloud arbitration and risk recording

#### Scenario: Rounded count does not change
- **WHEN** the selected-state witness is positive but a rounded count such as `5.8K` remains unchanged
- **THEN** the like may still be confirmed from the selected state, and the count is not used as the proof

#### Scenario: Like target is ambiguous or stale
- **WHEN** the requested noteId differs from the active Reel or more than one structural like candidate remains
- **THEN** Edge clicks nothing and returns `no_target` or `ambiguous_target`

### Requirement: Reels re-entry MUST NOT require a non-empty ordinary feed as its only unlock

An account whose ordinary home feed produces nothing SHALL still be able to be re-authorized onto the Reels surface. Re-authorization MUST NOT depend solely on a non-empty ordinary feed returning, because an account is on Reels precisely when its ordinary feed produced nothing — that unlock can never fire for the accounts that need it.

The re-entry evidence SHALL be a scroll receipt reporting no available target on the ordinary feed. A stale ordinary-feed empty/exhaustion report arriving while the account is already confirmed on Reels MUST NOT unlock re-entry: such a report is most likely a late signal from before the surface switch, and treating it as current would mistake stale emptiness for a genuine return to an empty home feed.

Re-entry SHALL be bounded per session. Once the bound is spent, the browse loop MUST reach a terminal state rather than alternating between two surfaces that both yield nothing.

#### Scenario: Confirmed on Reels, returned to an empty ordinary feed
- **WHEN** an account confirmed on Reels is returned to its ordinary home feed and a scroll there reports no available target
- **THEN** the fallback state returns to its authorizable state and Reels is authorized again
- **AND** the account is not left on a surface that yields no work

#### Scenario: Stale ordinary-feed empty report does not unlock
- **WHEN** an ordinary-feed empty or exhaustion confirmation arrives while the account is already confirmed on Reels
- **THEN** it does not reopen the fallback epoch
- **AND** the existing epoch idempotency is unchanged

#### Scenario: Non-empty ordinary feed keeps its existing behaviour
- **WHEN** a non-empty ordinary feed arrives for an account confirmed on Reels
- **THEN** the fallback state becomes authorizable as it already did
- **AND** ordinary browsing continues on that feed

#### Scenario: Re-entry is bounded
- **WHEN** re-entry has already been used its allowed number of times in one session
- **THEN** further no-target scroll receipts do not reopen the epoch
- **AND** the session reaches a terminal state instead of alternating indefinitely

### Requirement: Facebook Reels advances through an axis-specific global next-card control

For `page.scroll` while in the authorized Reels list mode, Edge SHALL classify the current global navigation controls as one unambiguous vertical or horizontal rail relative to the active video. Vertical navigation MAY use its lower global next control after the vertical key and wheel fallbacks; horizontal navigation MAY use its right global next control after the horizontal key fallback. Edge MUST NOT use an in-video media control or a control from another axis. Success SHALL require the applicable canonical Reel URL plus active-video transition rule and the new active card to pass the same identity and summary probe before reporting. Disabled, missing, ambiguous, stale, or axis-drifting controls and unchanged identity MUST fail honestly.

#### Scenario: Vertical next control changes active Reel
- **WHEN** the unique enabled lower control in a proven vertical rail is clicked and a new canonical active Reel is proven
- **THEN** Edge reports exactly the new Reel card and marks it seen through the existing canonical deduplication path

#### Scenario: Horizontal next control changes active Reel
- **WHEN** the unique enabled right control in a proven horizontal rail is clicked and a new canonical active Reel is proven
- **THEN** Edge reports exactly the new Reel card and marks it seen through the existing canonical deduplication path

#### Scenario: Wheel does not count as navigation
- **WHEN** vertical wheel input leaves route and active-video identity unchanged
- **THEN** Edge MUST NOT claim a new card or a successful scroll

#### Scenario: In-video control is not used as next Reel
- **WHEN** a bottom media or attachment control exists inside the active video
- **THEN** Edge ignores it and considers only the unique global control belonging to the proven navigation rail

#### Scenario: Generic single next control has no axis proof
- **WHEN** only one generic next-labelled control is visible and neither a structural pair nor directional semantics proves its axis
- **THEN** Edge clicks nothing and emits no fabricated progress

