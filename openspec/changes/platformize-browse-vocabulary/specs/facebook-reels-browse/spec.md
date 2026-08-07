## MODIFIED Requirements

### Requirement: Reels re-entry MUST NOT require a non-empty ordinary feed as its only unlock

An account whose ordinary home feed produces nothing SHALL still be able to be re-authorized onto the Reels surface. Re-authorization MUST NOT depend solely on a non-empty ordinary feed returning, because an account is on Reels precisely when its ordinary feed produced nothing — that unlock can never fire for the accounts that need it.

Cloud MUST NOT use a long-lived `confirmed` flag as evidence of the current page. It SHALL retain only a bounded in-flight Reels redrive attempt and per-session recovery count. Edge SHALL probe the live page for every `facebook.reels.scroll{reason:'resume_redrive'}` and either report the canonical Reel already active or enter Reels through the verified entry path.

Re-entry SHALL be bounded per session. Once the bound is spent, the browse loop MUST reach a terminal state rather than alternating between two surfaces that both yield nothing.

#### Scenario: Reels session returns to an ordinary feed or task page
- **WHEN** a Reels-targeted session is currently on an ordinary feed, group, detail, or other non-Reels page and receives a unified Reels redrive
- **THEN** Edge reconciles the live page to Reels without requiring a non-empty Feed report first
- **AND** Cloud does not consult a past `confirmed` state

#### Scenario: Already on Reels
- **WHEN** Edge receives a unified Reels redrive while a canonical active Reel is already present
- **THEN** Edge reports the current canonical Reel without redundant navigation or input
- **AND** the normal evidence-driven browse loop continues from that fresh card report

#### Scenario: Duplicate evidence during an in-flight entry
- **WHEN** repeated Feed-empty or no-target evidence arrives while one Reels redrive attempt is in flight
- **THEN** Cloud does not issue a parallel entry command
- **AND** a canonical Reel card clears only the transient attempt

#### Scenario: Re-entry is bounded
- **WHEN** Reels redrive recovery has already been used its allowed number of times in one session
- **THEN** further no-target receipts do not create unbounded retries
- **AND** the session reaches a terminal state instead of alternating indefinitely

### Requirement: Configured Reels primary reuses the verified Reels entry path
When a Facebook session pins Reels as its primary surface, Cloud SHALL authorize entry with `facebook.reels.scroll{reason:'facebook_reels_primary'}` and Edge SHALL route that command to the existing Reels entry executor. Edge SHALL first use bounded observation to report a canonical active Reel without input when available. If the observation ends on an exact keyboard-safe Reels surface without a reportable card, Edge SHALL continue the same command through the one-key probe boundary; active-video or axis recognition MUST NOT terminate entry before that probe. Route navigation or input delivery alone MUST NOT count as entry success.

#### Scenario: Configured primary reaches a reportable Reel without input
- **WHEN** Cloud authorizes `facebook_reels_primary` and bounded entry observation verifies one canonical active Reel
- **THEN** Edge SHALL report that Reel through the existing Reels card contract and perform no navigation input

#### Scenario: Reels route is safe but has no reportable card
- **WHEN** bounded entry observation reaches an exact keyboard-safe Reels route but cannot resolve one canonical active Reel
- **THEN** Edge SHALL dispatch exactly one preferred key through the shared navigation actuator
- **AND** it SHALL report a card only if bounded post-observation then verifies canonical progress

#### Scenario: Reels entry remains unresolved after the probe
- **WHEN** the one entry probe is delivered but no canonical active Reel appears within the bounded post-observation window
- **THEN** Edge SHALL return the existing honest ambiguous result and neither Edge nor Cloud SHALL fabricate a view or start content evaluation

### Requirement: Ineffective Reels entry receives one exact-target foreground recovery

For `facebook.reels.scroll{reason:'facebook_reels_primary'}` and `facebook.reels.scroll{reason:'empty_feed_reels_fallback'}`, Edge SHALL keep the first navigation to the Reels route background-first and SHALL prove that the exact bound page reached a ready Reels route/surface before deciding whether entry took effect. If bounded readback proves that the exact bound target remained outside a ready Reels surface, Edge MAY call `Page.bringToFront` on that same target at most once for the command, SHALL re-probe before another write, and MAY issue at most one fresh Reels navigation retry. Reaching the Reels surface MUST suppress foreground activation even when canonical video cards are still hydrating or unavailable; that later card condition SHALL terminate honestly without reclassifying the navigation as ineffective. A late successful entry observed after activation MUST suppress the retry. Target drift, blocker state, or `Page.bringToFront` acknowledgement alone MUST NOT count as entry success.

#### Scenario: First background entry succeeds

- **WHEN** the initial Reels navigation reaches a ready Reels surface
- **THEN** Edge never calls `Page.bringToFront` for that command and separately reports the canonical Reel or an honest hydration/no-target outcome

#### Scenario: Ineffective entry foregrounds and retries once

- **WHEN** the initial navigation completes but bounded same-target readback proves that the eligible Facebook page did not enter a ready Reels surface
- **THEN** Edge calls `Page.bringToFront` once, re-probes the exact target, and issues at most one fresh Reels navigation retry

#### Scenario: Entry completes after activation but before retry

- **WHEN** the post-activation re-probe observes a ready Reels surface
- **THEN** Edge accepts that entry and does not send another `Page.navigate`

#### Scenario: Foreground recovery still cannot confirm entry

- **WHEN** the one foreground recovery and optional fresh navigation retry do not produce a canonical active Reel
- **THEN** Edge returns the existing honest pending, no-target, or ambiguous result and does not fabricate a Reel view

#### Scenario: Blocker or target drift suppresses recovery

- **WHEN** the initial entry readback observes login, challenge, consent, another blocker, or a different target/document context
- **THEN** Edge does not foreground or retry navigation through this recovery path and returns the applicable honest outcome
