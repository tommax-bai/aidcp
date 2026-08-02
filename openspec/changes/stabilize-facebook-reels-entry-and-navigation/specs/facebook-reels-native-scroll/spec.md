## MODIFIED Requirements

### Requirement: Native Facebook Reels scrolling uses a surface-specific trusted actuator

When the Native-only Facebook runtime receives `page.scroll` while the observed list surface is Reels, the Edge SHALL resolve exactly one active video independently from canonical Reel identity before dispatch. Structural navigation axis evidence SHALL be an ordering hint and pointer-fallback constraint, not a prerequisite for keyboard input. The router and Native strict decoder SHALL preserve the fresh `reel_next_target.inputSafe` observation, and Native SHALL require it to remain safe before entering keyboard probing. Native SHALL attempt each supported keyboard direction at most once per command in a deterministic order, SHALL observe active-Reel identity after every attempt, and SHALL freshly re-probe the same Reel before any later write. The first verified `ArrowRight` or `ArrowDown` transition SHALL both identify the working actuator and complete the requested scroll; no later key, wheel, or pointer input may follow it. If both keys leave the same Reel unchanged, a vertical layout MAY use one small trusted wheel and then one geometrically constrained vertical next-button click, while a horizontal layout MAY use one geometrically constrained horizontal next-button click. Missing, ambiguous, disabled, or occluded controls MUST block pointer fallback but MUST NOT by themselves block bounded keyboard probing against one safe active Reel. The Edge MUST NOT use document `window.scrollBy`, a horizontal wheel guess, an unbounded retry, or two keyboard directions without a bounded same-Reel re-probe between them.

#### Scenario: Unknown layout advances with ArrowRight

- **WHEN** one safe active Reel is resolved, structural controls do not yield a unique axis, and `ArrowRight` changes to a different active video with canonical identity
- **THEN** the Edge reports the newly active Reel, records `ArrowRight` as the session-local working-key preference, and dispatches no later input

#### Scenario: Unknown layout advances with ArrowDown after a right-key miss

- **WHEN** `ArrowRight` leaves the original active Reel unchanged, a fresh pre-commit probe proves the same Reel remains active and safe, and `ArrowDown` changes to a canonically identified Reel
- **THEN** the Edge reports the newly active Reel and records `ArrowDown` as the working-key preference

#### Scenario: Structural hint orders but does not authorize the result

- **WHEN** fresh structure hints horizontal or vertical navigation
- **THEN** the Edge MAY try the corresponding key first but reports success only after active-video and canonical identity transition are proven

#### Scenario: Late first-key movement suppresses the second key

- **WHEN** the first key appears unchanged during its initial observation but the fresh pre-commit probe observes an active-video transition
- **THEN** the Edge suppresses the other key and every later fallback while it verifies canonical identity

#### Scenario: Unsafe page focus blocks active probing

- **WHEN** a text editor, dialog, blocker, or ambiguous active video makes page-level direction input unsafe
- **THEN** the Edge returns a pre-dispatch failure and emits no keyboard, wheel, or pointer input

#### Scenario: Real safe next-target shape reaches keyboard probing

- **WHEN** the router returns the same active video with `inputSafe:true` and no structural axis
- **THEN** Native decodes the complete result and begins the bounded `ArrowRight` then `ArrowDown` discovery order instead of returning an invalid-result error

#### Scenario: Focus becomes unsafe during the fresh next-target probe

- **WHEN** the initial active Reel was safe but `reel_next_target` returns `inputSafe:false`
- **THEN** Native fails before input and dispatches neither direction key

#### Scenario: Both keys unchanged and a vertical wheel advances

- **WHEN** both bounded keyboard attempts leave the same Reel unchanged, a fresh structural probe proves a vertical layout, and one wheel over the active video changes its stable identity
- **THEN** the Edge reports the newly active Reel and does not click the next button

### Requirement: Reels no-change terminates honestly

If the Reels surface has no unique safe active video, the Edge SHALL fail before input with `effectPhase:not_started` and SHALL NOT emit a normal `page.cards` result. Missing or ambiguous structural axis evidence SHALL NOT alone cause a pre-dispatch `no_target`; Native SHALL use the bounded keyboard-probing contract. If any trusted input was dispatched but every permitted method completes without a canonical post-transition Reel, the Edge SHALL emit one failed scroll receipt with an ambiguous effect phase and SHALL NOT emit normal cards. Either terminal MUST stop the current decision cycle instead of triggering an unbounded high-rate scroll loop.

#### Scenario: Active Reel is missing or ambiguous

- **WHEN** zero or multiple videos are equally eligible as the active Reel
- **THEN** the Edge fails closed before input with `not_started/no_target` and emits no fabricated progress

#### Scenario: Navigation axis is structurally ambiguous

- **WHEN** one safe active video exists but vertical and horizontal control evidence is absent or ambiguous
- **THEN** the Edge uses bounded verified keyboard probing instead of returning a pre-dispatch axis failure

#### Scenario: Both keyboard directions leave the Reel unchanged

- **WHEN** Native dispatches each permitted direction once with a fresh same-Reel re-probe between them and no canonical post-transition Reel is proven
- **THEN** the Edge emits one failed `action.completed{action:'scroll'}` with an ambiguous effect phase unless a freshly proven safe structural fallback remains

#### Scenario: All permitted methods leave the Reel unchanged

- **WHEN** all bounded keyboard and structurally authorized fallback methods leave the original Reel unchanged
- **THEN** the Edge emits one ambiguous `reels_navigation_unconfirmed` receipt and no `page.cards`

#### Scenario: Video changes but canonical identity remains absent

- **WHEN** a trusted input changes the active `videoKey` but no canonical `noteId` appears within the bounded verification window
- **THEN** the Edge emits one ambiguous `reels_identity_unresolved` scroll receipt and dispatches no further input
