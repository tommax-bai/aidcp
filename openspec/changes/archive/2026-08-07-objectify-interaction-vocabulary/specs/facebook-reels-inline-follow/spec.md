## MODIFIED Requirements

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
