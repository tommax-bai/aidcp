## ADDED Requirements

### Requirement: Native Facebook Reels scrolling uses a surface-specific trusted actuator

When the Native-only Facebook runtime receives `page.scroll` while the observed list surface is Reels, the Edge SHALL resolve exactly one active Reel and SHALL attempt forward navigation with bounded trusted CDP input in this order: ArrowDown, one small wheel over the active video, then one geometrically constrained next-button click. It MUST NOT use document `window.scrollBy` as a Reels actuator. Before each fallback write, the Edge MUST freshly re-probe the active Reel so a late movement suppresses the next input.

#### Scenario: ArrowDown advances the active Reel

- **WHEN** one active Reel is resolved and trusted ArrowDown changes its stable identity
- **THEN** the Edge reports the newly active Reel and does not dispatch wheel or button input

#### Scenario: Keyboard is unchanged and wheel advances

- **WHEN** ArrowDown leaves the active Reel unchanged but one wheel over the freshly resolved active video changes its stable identity
- **THEN** the Edge reports the newly active Reel and does not click the next button

#### Scenario: Late movement suppresses a fallback write

- **WHEN** the active Reel changes after a prior attempt but before the next fallback input is committed
- **THEN** the fresh pre-commit probe accepts that movement and the Edge does not dispatch the fallback input

### Requirement: Reels progress requires stable identity change

The Edge SHALL identify the active Reel by the pair `noteId + videoKey`, where the active video is the unique visible video with the greatest viewport intersection. A Reels scroll SHALL report `page.cards{listKind:'reels'}` only after that identity differs from the pre-action identity. Document `scrollY`, command receipt, input dispatch, and unchanged cards MUST NOT independently prove progress.

#### Scenario: Document scroll position changes without Reel identity movement

- **WHEN** a Reels input changes document scroll position but the active `noteId + videoKey` remains unchanged
- **THEN** the Edge does not report new `page.cards`

#### Scenario: Active video identity changes

- **WHEN** the freshly probed active Reel has a different `noteId` or `videoKey`
- **THEN** the Edge reports one fresh Reels card batch derived from the moved-to active Reel

#### Scenario: Route identity has no matching permalink-bearing article

- **WHEN** a `/reel/<id>` page has one active video whose bounded container contains only repeated `/reel/hashtag/` navigation links and no `article` or current-Reel permalink
- **THEN** the Edge binds the canonical route `noteId` to that active-video container, excludes the hashtag routes as post identities, and reports exactly one current Reels card

### Requirement: Reels no-change terminates honestly

If all bounded Reels navigation methods complete without a provable active identity change, or the Reels route has no unique active video, the Edge SHALL emit one failed scroll action receipt and SHALL NOT emit a normal `page.cards` result. This terminal MUST stop the current decision cycle instead of triggering an unbounded high-rate scroll loop.

#### Scenario: All navigation methods leave the Reel unchanged

- **WHEN** ArrowDown, wheel, and the constrained next-button attempt all finish without changing `noteId + videoKey`
- **THEN** the Edge emits `action.completed{action:'scroll', ok:false, reason:'no_target'}` exactly once and emits no `page.cards`

#### Scenario: Active Reel is ambiguous

- **WHEN** two visible videos are equally eligible as the active Reel
- **THEN** the Edge fails closed without dispatching a navigation input and emits no fabricated progress

### Requirement: Ordinary Facebook Feed scrolling remains separate

When the observed Facebook list surface is not Reels, the Edge SHALL keep the existing Feed scroll implementation and MUST NOT run the Reels trusted-input fallback chain.

#### Scenario: Feed scroll uses the existing path

- **WHEN** `page.scroll` arrives on the Facebook home Feed
- **THEN** the Edge executes the existing Feed document-scroll behavior and does not probe or click a Reels next control
