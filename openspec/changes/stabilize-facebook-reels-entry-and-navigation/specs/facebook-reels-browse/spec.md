## ADDED Requirements

### Requirement: Ineffective Reels entry receives one exact-target foreground recovery

For `page.scroll{reason:'facebook_reels_primary'}` and `page.scroll{reason:'empty_feed_reels_fallback'}`, Edge SHALL keep the first navigation to the Reels route background-first and SHALL prove that the exact bound page reached a ready Reels route/surface before deciding whether entry took effect. If bounded readback proves that the exact bound target remained outside a ready Reels surface, Edge MAY call `Page.bringToFront` on that same target at most once for the command, SHALL re-probe before another write, and MAY issue at most one fresh Reels navigation retry. Reaching the Reels surface MUST suppress foreground activation even when canonical video cards are still hydrating or unavailable; that later card condition SHALL terminate honestly without reclassifying the navigation as ineffective. A late successful entry observed after activation MUST suppress the retry. Target drift, blocker state, or `Page.bringToFront` acknowledgement alone MUST NOT count as entry success.

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
