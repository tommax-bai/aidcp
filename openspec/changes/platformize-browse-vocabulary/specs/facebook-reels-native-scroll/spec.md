## MODIFIED Requirements

### Requirement: Native Facebook Reels scrolling uses a surface-specific trusted actuator

When the Native-only Facebook runtime receives `facebook.reels.scroll` and verifies it is on an exact Reels surface, Edge SHALL freshly verify explicit keyboard safety plus cancellation and deadline gates, then dispatch exactly one trusted CDP key selected by a non-blocking session preference. A new session SHALL prefer ArrowRight. After a delivered key lacks canonical progress, the next normally admitted command SHALL prefer the other key; after canonical progress, the successful key SHALL remain preferred. Active-video uniqueness, canonical pre-identity, next-control structure, disabled or occluded controls, and a resolved navigation axis MUST NOT be prerequisites for this reversible probe. Edge MUST NOT dispatch wheel input, click a navigation control, try both keys, or perform a second write within the command.

Reels-entry reasons (`resume_redrive` and the empty-feed / primary-surface entry reasons) SHALL navigate to the Reels surface first, as today. A non-entry `facebook.reels.scroll` arriving while the observed surface is not Reels SHALL fail honestly with the observed surface reported, and MUST NOT execute the Feed scroll path instead.

#### Scenario: Axisless live shape receives the first probe
- **WHEN** an exact `/reel/` page is explicitly keyboard-safe but a disabled `Next items` control and an active `Next Card` overlay do not yield one structural axis
- **THEN** a new session SHALL dispatch exactly one ArrowRight gesture and no wheel or pointer input

#### Scenario: Unconfirmed first probe selects the other key later
- **WHEN** the first delivered ArrowRight does not produce canonical progress and Cloud later admits another scroll command normally
- **THEN** Edge SHALL dispatch exactly one ArrowDown gesture for the later command

#### Scenario: Confirmed direction remains preferred
- **WHEN** a delivered probe produces a canonically confirmed next Reel
- **THEN** Edge SHALL retain that probe key as the preference for a later normally admitted scroll

#### Scenario: Missing active-video structure does not veto a probe
- **WHEN** the exact Reels surface is keyboard-safe but zero or multiple videos satisfy the active-card heuristic
- **THEN** Edge SHALL still dispatch the one preferred key and SHALL report no card unless bounded post-observation resolves one canonical active Reel

#### Scenario: Stable safety gate blocks all input
- **WHEN** focus is editable, login/captcha/consent evidence is present, the route is not Reels, the command is cancelled, or its deadline cannot contain the trusted input
- **THEN** Edge SHALL dispatch no keyboard, wheel, or pointer input

#### Scenario: Declared Reels intent does not silently scroll the Feed
- **WHEN** a non-entry `facebook.reels.scroll` arrives while the observed surface is the home Feed
- **THEN** Edge SHALL fail the command honestly, reporting the observed surface
- **AND** MUST NOT run the Feed document-scroll behavior under the Reels command name

### Requirement: Ordinary Facebook Feed scrolling remains separate

Feed scrolling is commanded as `facebook.feed.scroll` and SHALL keep the existing Feed scroll implementation; the Reels trusted-input chain is reachable only via `facebook.reels.scroll`. A `facebook.feed.scroll` arriving while the observed surface is Reels SHALL fail honestly with the observed surface reported, and MUST NOT run the Reels probe instead.

#### Scenario: Feed scroll uses the existing path

- **WHEN** `facebook.feed.scroll` arrives on the Facebook home Feed
- **THEN** the Edge executes the existing Feed document-scroll behavior and does not probe or click a Reels next control

#### Scenario: Declared Feed intent does not silently probe Reels

- **WHEN** `facebook.feed.scroll` arrives while the observed surface is an exact Reels page
- **THEN** Edge SHALL fail the command honestly, reporting the observed surface
- **AND** MUST NOT dispatch a Reels trusted-key probe under the Feed command name
