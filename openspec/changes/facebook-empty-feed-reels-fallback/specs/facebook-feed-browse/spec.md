## MODIFIED Requirements

### Requirement: Facebook feed stays continuous instead of reloading to top

The Facebook list reader MUST make navigation idempotent. A ready Facebook home MUST remain in place even when it has no hydrated cards or feed container, while search and group lists MUST retain their existing list-container readiness rule. Every path MUST still run login, checkpoint, consent, captcha, and blocking-overlay checks. Card scanning MUST report only newly appeared top-level hydrated cards keyed by a session-level canonical-id cursor. A zero-card home MUST NOT be treated as exhausted or empty unless the explicit loading-aware empty-state contract in `facebook-feed-continuity` confirms it.

When the Edge reports an explicitly confirmed empty Facebook home through the existing optional `page.cards` observation fields, or honestly reports `feed_exhausted` after a non-empty Facebook list has yielded real cards and bounded navigation has found no unseen card, the Cloud SHALL authorize the fallback by sending the existing scroll command with the deployed `empty_feed_reels_fallback` compatibility reason. Only that Cloud authorization MAY switch the Edge session to Reels. The authorization SHALL be idempotent per active session. Loading, unknown layout, navigation error, login/checkpoint/consent/captcha, search, or group states MUST NOT trigger the fallback. Non-Facebook `feed_exhausted` behavior SHALL remain the existing refresh path. Once Reels cards are reported, the existing evaluation, read, interaction authorization, pacing, and risk-accounting loop SHALL continue unchanged.

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
- **WHEN** an active Facebook session reports `action.completed{action:scroll,ok:false,reason:feed_exhausted}` after Edge's bounded loading-aware exhaustion check
- **THEN** Cloud sends exactly one existing scroll command carrying `reason:empty_feed_reels_fallback`
- **AND** Edge enters Reels instead of refreshing the exhausted Facebook Feed

#### Scenario: Duplicate exhaustion and other platforms preserve safe behavior
- **WHEN** the same active Facebook session repeats `feed_exhausted` after Reels fallback was already authorized
- **THEN** Cloud MUST NOT send a second fallback or refresh command
- **AND WHEN** a non-Facebook session reports `feed_exhausted`
- **THEN** Cloud retains the existing refresh behavior and MUST NOT authorize Facebook Reels

#### Scenario: Existing evaluation and risk chain continues on Reels
- **WHEN** Edge reports an active Reel as a normal card and Cloud later authorizes a like
- **THEN** content evaluation and pacing run through the existing browse loop
- **AND** only a platform-confirmed like receipt is recorded by the existing RiskController path

#### Scenario: Exhausted non-empty list is reported honestly
- **WHEN** a list has previously yielded cards and bounded continued navigation surfaces no unseen card
- **THEN** Edge returns an exhausted-feed signal instead of silently idling
- **AND** recycled cards are not counted as new
- **AND** Cloud MAY use that honest signal to authorize the platform-specific continuation without changing the Edge exhaustion proof
