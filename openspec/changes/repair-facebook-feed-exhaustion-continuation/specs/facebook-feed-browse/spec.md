## MODIFIED Requirements

### Requirement: Facebook feed stays continuous instead of reloading to top

The Facebook list reader MUST make navigation idempotent. A ready Facebook home MUST remain in place even when it has no hydrated cards or feed container, while search and group lists MUST retain their existing list-container readiness rule. Every path MUST still run login, checkpoint, consent, captcha, and blocking-overlay checks. Card scanning MUST report only newly appeared top-level hydrated cards keyed by a session-level canonical-id cursor. A zero-card home MUST NOT be treated as exhausted or empty unless the explicit loading-aware empty-state contract in `facebook-feed-continuity` confirms it.

When Edge reports an explicitly confirmed empty Facebook home through the existing optional `page.cards` observation fields, or honestly reports `feed_exhausted` after the terminal evidence required by `facebook-feed-continuity`, Cloud SHALL authorize the fallback by sending the existing scroll command with the deployed `empty_feed_reels_fallback` compatibility reason. Only that Cloud authorization MAY switch Edge to Reels. Authorization SHALL be idempotent within one fallback epoch: pending handshake reports and duplicate terminal evidence MUST NOT create another authorization, and readable Reels cards confirm the epoch. After confirmed Reels, a later non-empty `page.cards` batch with `listKind:'feed'` while the dispatcher is in its ordinary Feed source SHALL prove Feed re-entry, reset the epoch, and allow exactly one later truthful terminal observation to authorize a new fallback. Empty batches, search/group context, and batches received while fallback is pending MUST NOT reset the epoch.

Loading, unknown layout, navigation error, login/checkpoint/consent/captcha, search, or group states MUST NOT trigger fallback. `feed_continuation_unconfirmed` SHALL cause another ordinary gated Facebook Feed scroll and MUST NOT trigger fallback. Non-Facebook `feed_exhausted` behavior SHALL remain the existing refresh path. Once Reels cards are reported, the existing evaluation, read, interaction authorization, pacing, and risk-accounting loop SHALL continue unchanged.

#### Scenario: Scrolling does not reload the same first cards
- **WHEN** the account scrolls a ready Facebook list URL with no blocking state
- **THEN** the reader does not re-navigate to the top and reports only newly appeared cards while the safety front door still runs

#### Scenario: Confirmed empty home is authorized by Cloud
- **WHEN** an active Facebook session reports `cards:[]` with the optional observation identifying a confirmed empty home feed
- **THEN** Cloud sends exactly one existing scroll command carrying the dedicated Reels fallback reason
- **AND** Edge enters Reels only after receiving that authorization

#### Scenario: Unconfirmed zero cards do not switch lists
- **WHEN** Edge reports loading, unknown layout, navigation failure, a blocked page, or merely observes zero cards without explicit empty-state confirmation
- **THEN** Cloud MUST NOT authorize the Reels fallback and Edge MUST remain fail-closed

#### Scenario: Confirmed non-empty Facebook Feed exhaustion is authorized by Cloud
- **WHEN** an active Facebook session reports `action.completed{action:scroll,ok:false,reason:feed_exhausted}` after Edge's bounded terminal-evidence check
- **THEN** Cloud sends exactly one existing scroll command carrying `reason:empty_feed_reels_fallback`
- **AND** Edge enters Reels instead of refreshing the exhausted Facebook Feed

#### Scenario: Duplicate evidence in one fallback epoch remains idempotent
- **WHEN** the same active Facebook session repeats empty or `feed_exhausted` evidence while fallback is pending or confirmed and no authoritative Feed re-entry occurred
- **THEN** Cloud MUST NOT send a second fallback or refresh command
- **AND WHEN** a non-Facebook session reports `feed_exhausted`
- **THEN** Cloud retains the existing refresh behavior and MUST NOT authorize Facebook Reels

#### Scenario: Non-empty Feed re-entry opens a new fallback epoch
- **WHEN** readable Reels cards confirmed a fallback and Edge later reports a non-empty ordinary Feed batch
- **THEN** Cloud resets only the fallback epoch state
- **AND** a later truthful Feed empty/exhausted observation may authorize exactly one new fallback

#### Scenario: Empty, search, group, or pending batches do not reopen fallback
- **WHEN** Edge reports an empty batch, a search/group batch, or a Feed-shaped batch before readable Reels confirmed the pending handshake
- **THEN** Cloud preserves the current fallback epoch and MUST NOT broaden authorization

#### Scenario: Unconfirmed bounded continuation keeps scrolling
- **WHEN** Edge reports `action.completed{action:scroll,ok:false,reason:feed_continuation_unconfirmed}` on the ordinary Facebook Feed
- **THEN** Cloud sends another ordinary scroll only through the existing command, quota, pause, pacing, and session gates
- **AND** Cloud MUST NOT authorize Reels from that receipt

#### Scenario: Existing evaluation and risk chain continues on Reels
- **WHEN** Edge reports an active Reel as a normal card and Cloud later authorizes a like
- **THEN** content evaluation and pacing run through the existing browse loop
- **AND** only a platform-confirmed like receipt is recorded by the existing RiskController path

#### Scenario: Exhausted non-empty list is reported honestly
- **WHEN** a canonical home Feed has previously yielded cards and bounded continued navigation proves stable terminal evidence with no unseen card
- **THEN** Edge returns an exhausted-feed signal instead of silently idling
- **AND** recycled cards are not counted as new
- **AND** Cloud MAY use that honest signal to authorize the platform-specific continuation without changing the Edge exhaustion proof
