# facebook-reels-browse Specification

## Purpose
TBD - created by archiving change facebook-empty-feed-reels-fallback. Update Purpose after archive.
## Requirements
### Requirement: Facebook Reels identifies exactly one active video card

Edge SHALL accept a Reel only on a canonical Facebook `/reel/<id>` route and SHALL select the active video from preloaded videos by greatest viewport intersection, using viewport-center distance only as a tie-breaker. The canonical Reel URL SHALL be the card and note identity. Missing, ambiguous, off-route, or identity-changing observations MUST fail closed and MUST NOT fabricate a card.

#### Scenario: Current Reel wins over preloaded neighbours
- **WHEN** previous, current, and next videos coexist in the DOM
- **THEN** Edge reports only the video with the greatest current viewport intersection and binds it to the current canonical Reel route

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

### Requirement: Facebook Reels advances through the global next-card control

For `page.scroll` while in the authorized Reels list mode, Edge SHALL use the far-right global lower navigation control rather than page wheel scrolling or an in-video media control. Success SHALL require the canonical Reel URL or active video identity to change and the new active card to pass the same identity and summary probe before reporting. Disabled/missing/ambiguous controls or unchanged identity MUST fail honestly.

#### Scenario: Next control changes active Reel
- **WHEN** the unique enabled global lower navigation control is clicked and the route changes to a new canonical Reel
- **THEN** Edge reports exactly the new Reel card and marks it seen for deduplication

#### Scenario: Wheel does not count as navigation
- **WHEN** page wheel input leaves `scrollY`, route, and active video identity unchanged
- **THEN** Edge MUST NOT claim a new card or a successful scroll

#### Scenario: In-video control is not used as next Reel
- **WHEN** a bottom media/attachment control exists inside the active video
- **THEN** Edge ignores it and only considers the unique far-right global navigation control

