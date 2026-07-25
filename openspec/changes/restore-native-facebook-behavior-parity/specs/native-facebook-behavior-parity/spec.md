## ADDED Requirements

### Requirement: Native-only Facebook preserves the established platform command boundary

The Facebook Native-only adapter SHALL implement only commands covered by the Facebook platform contract. Supported behavior SHALL include identity and page probes, Feed/Reels browse, search, note detail, exact-target like, Reel follow, comment, group join, and the existing Facebook publish atom subset. Facebook collect, comment-like, carousel browse, comment scroll, notifications, and author-profile browse MUST return `capability_unsupported` before any page actuation. A generic cross-platform command name MUST NOT create an implicit Facebook capability.

#### Scenario: Unsupported generic command does not touch the page

- **WHEN** a Facebook Native session receives `interaction.like_comment`, `note.browse_images`, `note.scroll_comments`, a notification command, `interaction.collect`, or `profile.open`
- **THEN** Edge returns `capability_unsupported` without router evaluation, navigation, scrolling, clicking, typing, or risk accounting

#### Scenario: Supported command stays Native-only

- **WHEN** a supported Facebook command is executed
- **THEN** the Rust Native Page Engine owns CDP inspection, actuation, and verification, and Edge MUST NOT invoke the retired TypeScript Facebook page executor or a JavaScript fallback process

### Requirement: Native Feed scanning preserves stateful continuation truth

The Native Facebook session SHALL distinguish canonical cards, visible unreportable articles, loading, explicit empty, and exhausted Feed states. It SHALL use loading-aware card-set settling, continue downward for up to the established bounded rounds when visible articles lack trusted permalinks, filter canonical identities already reported by that session, and report `feed_exhausted` only after the established no-growth, near-bottom, consecutive-confirmation evidence. It MUST NOT authorize or perform a Reels transition merely because the current viewport has no reportable permalink.

#### Scenario: Visible unreportable first viewport continues in Feed

- **WHEN** the initial Facebook Feed viewport contains visible hydrated articles but no trusted canonical permalink and a later bounded viewport contains a canonical card
- **THEN** Native scrolls within Feed, reports the later card, and does not emit explicit empty or navigate to Reels

#### Scenario: Loading zero-card viewport is not empty

- **WHEN** no canonical card is currently extractable and the Feed has an accessibility loading signal
- **THEN** Native waits within the bounded settle budget and, if still loading at the deadline, returns a retryable loading/no-target result rather than an empty card batch

#### Scenario: Recycled cards are not reported as new

- **WHEN** virtualized Feed scrolling renders canonical post identities already reported in the same Native session
- **THEN** Native filters those identities and continues the bounded search for new cards

#### Scenario: Exhaustion requires bounded structural evidence

- **WHEN** a scroll command finds no new canonical cards
- **THEN** Native reports `feed_exhausted` only after document height stops growing, the page is near the bottom, and that state is confirmed in consecutive rounds

### Requirement: Native navigation preserves the active Facebook list surface

The Native Facebook session SHALL establish Feed on startup, retain the current home or search list URL, return from detail to that originating list surface, and refresh home Feed through a bounded SPA home action with a changed non-empty top-card postcondition. A raw reload MUST NOT be the primary refresh path and SHALL obey the existing three-minute fallback floor.

#### Scenario: Persisted non-Feed page is not accepted as startup baseline

- **WHEN** AdsPower opens on a Reel, profile, group, search, or detail page
- **THEN** Native establishes Facebook home Feed before reporting initial Feed cards

#### Scenario: Search detail returns to search

- **WHEN** a note is opened from a Facebook search result and navigation back is requested
- **THEN** Native returns to the same search result URL and does not reset to home

#### Scenario: Refresh proves a new batch

- **WHEN** Feed refresh is requested
- **THEN** Native reports success only after the home SPA action yields a non-empty top canonical identity different from the pre-action identity, or otherwise returns an honest bounded failure

### Requirement: Native blocker and consent gates match Facebook safety policy

Before Facebook page actuation, Native SHALL distinguish login, positive captcha, generic checkpoint/security blocking, Facebook soft throttle, and cookie consent. Captcha SHALL require positive captcha evidence; generic checkpoint and throttle SHALL be reported as unknown blockers with same-source bounded evidence. Cookie consent SHALL honor `accept_all` versus `necessary_only`, use the matching unique button, verify disappearance, and stop after the established bounded attempts.

#### Scenario: Generic checkpoint is unknown, not captcha

- **WHEN** the page is on a checkpoint/security route without positive captcha controls or semantics
- **THEN** Native blocks actuation and reports an unknown blocking incident rather than claiming a captcha

#### Scenario: Facebook throttle copy is reported with evidence

- **WHEN** a recognized Facebook soft-throttle message is visible
- **THEN** Native blocks the action and reports the unknown blocker with bounded text from the same scan that caused classification

#### Scenario: Necessary-only policy never clicks accept-all

- **WHEN** cookie consent is visible and the configured policy is `necessary_only`
- **THEN** Native clicks only the unique necessary-only control and returns `blocked_by_consent` if that control is unavailable or the dialog remains after bounded attempts

### Requirement: Native note-scoped actions never fall back to DOM order

A Facebook action carrying a canonical `noteId` SHALL resolve exactly one matching top-level post or active Reel, scroll that target into view, and bind pre- and post-action evidence to the same identity. Missing, recycled, duplicated, or ambiguous targets MUST fail without clicking, typing, or selecting the first available article.

#### Scenario: Missing target does not like the first card

- **WHEN** the commanded `noteId` is absent but another likeable post is visible
- **THEN** Native returns `target_not_found` and does not actuate any reaction control

#### Scenario: Comment uses only the requested post editor

- **WHEN** multiple post editors exist on the page
- **THEN** Native types and submits only in the unique top-level article matching the commanded `noteId`, or fails before submission

### Requirement: Native write actions use trusted actuation and preserve terminal truth

Facebook like, follow, comment, join, and publish writes SHALL use trusted CDP input for the committing interaction, re-probe the same scoped target, and distinguish not-started, confirmed, already-complete, pending/rejected, and ambiguous outcomes. Synthetic DOM keyboard events, direct content mutation, visibility disappearance alone, or a single short observation MUST NOT be treated as confirmed external effect.

#### Scenario: Ambiguous comment is not retryable failure

- **WHEN** a comment submit was dispatched but no server comment identity, same-account acknowledgement, pending-review signal, or explicit rejection can be established within the bounded verification window
- **THEN** Edge returns `verification_ambiguous` with an ambiguous effect phase so Cloud does not automatically retry the uncertain write

#### Scenario: Pending group comment is distinct from public confirmation

- **WHEN** Facebook acknowledges a submitted group comment as pending review
- **THEN** Edge returns `pending_group_approval` and MUST NOT claim a publicly confirmed comment

#### Scenario: Join waits for a durable post-click state

- **WHEN** a unique in-scope Join control is actuated
- **THEN** Native polls within the established bounded window and returns joined, pending, questionnaire-required, explicit failure, or ambiguous truth based on durable post-click evidence

#### Scenario: Publish submit requires commit and verification evidence

- **WHEN** the Facebook composer submit atom is executed
- **THEN** Native verifies full input readback before trusted submit and reports confirmed success only from the established composer/post evidence; a dispatched but unverified submit remains ambiguous

### Requirement: Native parity is protected by behavior-level regression tests

The Edge repository SHALL contain focused Native tests derived from the established Facebook TypeScript behavior cases for Feed settling and continuation, blocker/consent classification, exact target selection, comment terminal classification, join readiness, publish integrity, and unsupported command routing. Tests MUST assert externally meaningful state and reason codes rather than only checking that a selector exists or a router branch returns.

#### Scenario: Native cutover regression is rejected

- **WHEN** a Native implementation again treats loading/unreportable Feed as empty, falls back to the first post, uses a non-equivalent ambiguous reason, or actuates an unsupported Facebook command
- **THEN** a focused parity test fails before integration
