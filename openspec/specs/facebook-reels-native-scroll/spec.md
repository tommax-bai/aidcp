# facebook-reels-native-scroll Specification

## Purpose
TBD - created by archiving change repair-native-facebook-reels-scroll. Update Purpose after archive.
## Requirements
### Requirement: Native Facebook Reels scrolling uses a surface-specific trusted actuator

When the Native-only Facebook runtime receives `page.scroll` while the observed list surface is Reels, the Edge SHALL resolve exactly one active video independently from canonical Reel identity and SHALL resolve exactly one structural navigation axis before dispatch. A vertical layout SHALL use bounded trusted CDP input in this order: ArrowDown, one small wheel over the freshly active video, then one geometrically constrained vertical next-button click. A horizontal layout SHALL use ArrowRight and then one geometrically constrained horizontal next-button click. It MUST NOT use document `window.scrollBy`, a horizontal wheel guess, or both keyboard axes in one command. Before each fallback write, the Edge MUST freshly re-probe the active video and axis so late movement suppresses the next input.

#### Scenario: Anonymous landing Reel advances vertically

- **WHEN** `/reel/` has one active video without `noteId`, a vertical rail is uniquely resolved, and trusted ArrowDown changes to a different active video with canonical identity
- **THEN** the Edge reports the newly active Reel and does not dispatch wheel or button input

#### Scenario: Identified Reel advances horizontally

- **WHEN** one identified active Reel and a horizontal rail are uniquely resolved and trusted ArrowRight changes its stable identity
- **THEN** the Edge reports the newly active Reel and does not dispatch wheel or button input

#### Scenario: Vertical keyboard is unchanged and wheel advances

- **WHEN** ArrowDown leaves the vertical Reel unchanged but one wheel over the freshly resolved active video changes its stable identity
- **THEN** the Edge reports the newly active Reel and does not click the next button

#### Scenario: Late movement suppresses a fallback write

- **WHEN** the active video changes after a prior attempt but before the next fallback input is committed
- **THEN** the fresh pre-commit probe accepts that transition, verifies canonical identity, and does not dispatch the fallback input

### Requirement: Reels progress requires stable identity change

The Edge SHALL structurally identify the active Reels target by a unique visible `videoKey`; a canonical `noteId + videoKey` pair is required before that target may be reported as a Reel card or used for any interaction. For an anonymous pre-state, navigation success requires both a different active `videoKey` and a canonical post-state `noteId`. For an identified pre-state, success requires a canonical post-state whose `noteId` or `videoKey` differs. Document `scrollY`, command receipt, input dispatch, route hydration onto an unchanged anonymous video, and unchanged cards MUST NOT independently prove progress.

#### Scenario: Anonymous active video is targetable but not reportable

- **WHEN** `/reel/` has exactly one visible active video and no canonical Reel permalink or route id
- **THEN** Edge may bind navigation to its session-local `videoKey` and rectangle
- **AND** Edge MUST NOT emit a card, count a view, or authorize an interaction for it

#### Scenario: Anonymous route gains id without changing video

- **WHEN** an anonymous pre-state gains a canonical route id but retains the same active `videoKey`
- **THEN** Edge MUST NOT claim that the requested forward navigation succeeded

#### Scenario: Document scroll position changes without Reel identity movement

- **WHEN** a Reels input changes document scroll position but the active video identity remains unchanged
- **THEN** the Edge does not report new `page.cards`

#### Scenario: Active video and canonical identity change

- **WHEN** the freshly probed active Reel satisfies the applicable anonymous or identified transition rule
- **THEN** the Edge reports one fresh Reels card batch derived from the moved-to active Reel

#### Scenario: Route identity has no matching permalink-bearing article

- **WHEN** a `/reel/<id>` page has one active video whose bounded container contains only repeated `/reel/hashtag/` navigation links and no `article` or current-Reel permalink
- **THEN** the Edge binds the canonical route `noteId` to that active-video container, excludes the hashtag routes as post identities, and reports exactly one current Reels card

### Requirement: Reels no-change terminates honestly

If the Reels surface has no unique active video or no unambiguous navigation axis, the Edge SHALL fail before input with `effectPhase:not_started` and SHALL NOT emit a normal `page.cards` result. If any trusted input was dispatched but all permitted methods complete without a canonical post-transition Reel, the Edge SHALL emit one failed scroll receipt with an ambiguous effect phase and SHALL NOT emit normal cards. Either terminal MUST stop the current decision cycle instead of triggering an unbounded high-rate scroll loop.

#### Scenario: Active Reel is missing or ambiguous

- **WHEN** zero or multiple videos are equally eligible as the active Reel
- **THEN** the Edge fails closed before input with `not_started/no_target` and emits no fabricated progress

#### Scenario: Navigation axis is ambiguous

- **WHEN** one active video exists but vertical and horizontal control evidence is absent or ambiguous
- **THEN** the Edge dispatches no input and returns one pre-dispatch failure

#### Scenario: All axis-specific methods leave the Reel unchanged

- **WHEN** the driver dispatches all permitted methods for the resolved axis and no canonical post-transition Reel is proven
- **THEN** the Edge emits one failed `action.completed{action:'scroll'}` with an ambiguous effect phase and emits no `page.cards`

#### Scenario: Video changes but canonical identity remains absent

- **WHEN** a trusted input changes the active `videoKey` but no canonical `noteId` appears within the bounded verification window
- **THEN** the Edge emits one ambiguous `reels_identity_unresolved` scroll receipt and dispatches no further input

### Requirement: Ordinary Facebook Feed scrolling remains separate

When the observed Facebook list surface is not Reels, the Edge SHALL keep the existing Feed scroll implementation and MUST NOT run the Reels trusted-input fallback chain.

#### Scenario: Feed scroll uses the existing path

- **WHEN** `page.scroll` arrives on the Facebook home Feed
- **THEN** the Edge executes the existing Feed document-scroll behavior and does not probe or click a Reels next control

