# facebook-reels-inline-follow Specification

## Purpose
TBD - created by archiving change facebook-reels-inline-follow. Update Purpose after archive.
## Requirements
### Requirement: Reel follow is bound to the canonical active Reel and author

The Edge SHALL execute a Facebook Reel follow only when `interaction.follow.noteId` is a canonical Facebook Reel URL, the same Reel is the unique active video, the Reel exposes exactly one current author identity, and exactly one Follow/Following control can be associated with that author. Zero matches MUST return `no_target`; multiple credible controls or author matches MUST return `ambiguous_target`. The executor MUST NOT fall back to the first Follow control, a fixed button index, or another mounted Reel.

#### Scenario: Exact active Reel has one author Follow control
- **WHEN** a follow command names the canonical active Reel and its unique author area exposes one Follow control
- **THEN** that control is the only eligible target
- **AND** no neighbouring or unrelated Follow control is eligible

#### Scenario: Reel changed before the command executes
- **WHEN** the command's `noteId` does not equal the canonical active Reel at the immediate pre-write probe
- **THEN** the Edge returns `ok:false, reason:'no_target'`
- **AND** dispatches no click

#### Scenario: Author or Follow target is ambiguous
- **WHEN** the active Reel has more than one credible author match or more than one associated Follow/Following control
- **THEN** the Edge returns `ok:false, reason:'ambiguous_target'`
- **AND** dispatches no click

### Requirement: Reel follow uses trusted input and same-Reel verification

For a unique unfollowed target in real mode, the Edge SHALL dispatch one trusted CDP pointer click and SHALL report a real new-follow success only after a bounded fresh probe finds the same canonical Reel, the same unique author association, and exactly one associated Following/已关注 state. Counter changes, control disappearance, command dispatch, or a state on another Reel MUST NOT prove success.

#### Scenario: Trusted click flips the same control to Following
- **WHEN** the unique Follow control is clicked and the bounded verifier reads Following/已关注 on the same Reel and author
- **THEN** the Edge reports `{ action:'follow', ok:true }` without a reason

#### Scenario: Click dispatched but state cannot be proved
- **WHEN** a trusted click was dispatched but the same-Reel verifier never observes a unique Following state
- **THEN** the Edge reports `ok:false` with `state_unchanged` or `verify_indeterminate`
- **AND** the result records that a write was attempted without claiming success

### Requirement: Existing state and mode gates remain truthful

If the associated control is already Following/已关注, the Edge SHALL return the existing good no-op `{ action:'follow', ok:true, reason:'already_followed' }` without clicking. In shadow mode it SHALL return `ok:false, reason:'shadow'` without clicking after target validation. Outside Reels mode, Facebook `interaction.follow` MUST remain `capability_unsupported` in this change.

#### Scenario: Author is already followed
- **WHEN** the unique associated control is already Following/已关注 before the write
- **THEN** the Edge reports `ok:true, reason:'already_followed'`
- **AND** dispatches no click or unfollow action

#### Scenario: Shadow mode proves target without following
- **WHEN** the active Reel and unfollowed control are unique but Facebook browse mode is `shadow`
- **THEN** the Edge reports `ok:false, reason:'shadow'`
- **AND** dispatches no click

#### Scenario: Feed surface remains unsupported
- **WHEN** Facebook receives `interaction.follow` while the session is not in Reels mode
- **THEN** it reports `ok:false, reason:'capability_unsupported'`
- **AND** does not search the Feed for a Follow control

### Requirement: Live Reel follow probe is explicitly write-gated

The maintained probe SHALL be read-only by default. It MUST require an explicit AdsPower profile id, exact target author match, canonical active Reel, unique eligible control, and `AIDCP_FB_PROBE_FOLLOW=1` before a real click. It MUST never choose a replacement author or automatically unfollow after validation.

#### Scenario: Default probe is read-only
- **WHEN** the probe resolves one valid unfollowed target without the explicit real-follow flag
- **THEN** it reports a shadow result and dispatches no click

#### Scenario: Real probe verifies a new follow
- **WHEN** the user authorizes a real probe, all target gates pass, and the click changes the same control from Follow to Following
- **THEN** the probe reports the concrete Reel identity plus verified Following label
- **AND** leaves the account followed

