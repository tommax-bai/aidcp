# facebook-reels-inline-follow Specification

## Purpose
TBD - created by archiving change facebook-reels-inline-follow. Update Purpose after archive.
## Requirements
### Requirement: Reel follow is bound to the canonical active Reel and author

The Edge SHALL execute a Facebook Reel follow only when `facebook.user.follow.noteId` is a canonical Facebook Reel URL, the same Reel is the unique active video, the Reel exposes exactly one current author identity, and exactly one Follow/Following control can be associated with that author. Zero matches MUST return `no_target`; multiple credible controls or author matches MUST return `ambiguous_target`. The executor MUST NOT fall back to the first Follow control, a fixed button index, or another mounted Reel.

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

If the associated control is already Following/已关注, the Edge SHALL return the existing good no-op `{ action:'follow', ok:true, reason:'already_followed' }` without clicking. In shadow mode it SHALL return `ok:false, reason:'shadow'` without clicking after target validation. Outside Reels mode, Facebook `facebook.user.follow` MUST remain `capability_unsupported` in this change.

#### Scenario: Author is already followed
- **WHEN** the unique associated control is already Following/已关注 before the write
- **THEN** the Edge reports `ok:true, reason:'already_followed'`
- **AND** dispatches no click or unfollow action

#### Scenario: Shadow mode proves target without following
- **WHEN** the active Reel and unfollowed control are unique but Facebook browse mode is `shadow`
- **THEN** the Edge reports `ok:false, reason:'shadow'`
- **AND** dispatches no click

#### Scenario: Feed surface remains unsupported
- **WHEN** Facebook receives `facebook.user.follow` while the session is not in Reels mode
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

### Requirement: French Reel Follow controls preserve author-bound action honesty

The Edge SHALL classify the exact French `Suivre <author>` label as an unfollowed Reel control and the exact French `Suivi(e) <author>` or `Ne plus suivre <author>` label as an already-followed control. Every French control MUST remain bound to the canonical active Reel and exactly one nearby visible author using the existing geometry, uniqueness, fresh-resolution, trusted-input, and same-Reel verification gates. French free text, an authorless control, control disappearance, or a state on another Reel MUST NOT authorize or confirm a Follow.

#### Scenario: French Follow is associated with the exact author

- **WHEN** the canonical active Reel exposes one `Suivre <author>` control and exactly one nearby visible author text equal to `<author>`
- **THEN** Edge resolves that control as the only eligible neutral Follow target

#### Scenario: French already-followed state is a no-op

- **WHEN** the unique author-bound control is `Suivi(e) <author>` or `Ne plus suivre <author>` before dispatch
- **THEN** Edge reports the established already-followed success and sends no click

#### Scenario: French post-state remains same-Reel verified

- **WHEN** Edge dispatches one trusted click to a unique `Suivre <author>` control
- **THEN** it confirms success only after a fresh probe resolves `Suivi(e) <author>` or `Ne plus suivre <author>` for the same canonical Reel, video key, and author

#### Scenario: Authorless or ambiguous French controls fail closed

- **WHEN** a French Follow-state control omits its author association or more than one credible French control or author witness exists
- **THEN** Edge reports not-found, ambiguous, or unconfirmed according to the existing lifecycle and sends no replacement click

