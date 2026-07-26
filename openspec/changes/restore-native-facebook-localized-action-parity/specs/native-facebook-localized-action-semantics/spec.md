## ADDED Requirements

### Requirement: Native Facebook localized actions have an executable parity audit

The Edge repository SHALL maintain focused executable evidence comparing each Native Facebook action vocabulary and lifecycle against its retired behavior oracle. The audit MUST identify which Like, Follow, Group Join, Comment, Publish, Consent, and blocker semantics require repair and which remain equivalent. Production changes MUST migrate only evidence-backed semantics, MUST retain capability ownership, and MUST NOT turn an unknown localized state into success.

#### Scenario: Retired action vocabulary is narrower in Native

- **WHEN** an observed or previously tested retired action label or lifecycle state is absent from its Native capability
- **THEN** the capability's focused parity test fails until the exact semantic behavior is restored

#### Scenario: Existing action family is already equivalent

- **WHEN** the current Native Reels Follow, Group Join, Consent/blocker, or retained Comment semantics cover the retired oracle
- **THEN** the audit records retain-only evidence and the implementation is not mechanically rewritten

### Requirement: Native Facebook reaction vocabulary has one shared owner

The Native Facebook router SHALL maintain the observed zh-CN, zh-TW, English, Spanish, and Vietnamese Like/reaction label families in one capability-neutral internal semantics module assembled before Feed Like and Reels. Feed Like and Reels MUST consume that shared vocabulary and positive-state classifier, while the shared module MUST NOT own card identity, active-video association, action-rail geometry, target uniqueness, actuation, or verification choreography. Production TypeScript, caller input, and package resources MUST NOT supply or override the vocabulary.

#### Scenario: Bare simplified-Chinese Reel Like with count is accepted

- **WHEN** the commanded canonical Reel has one active video and exactly one associated right-rail control whose `aria-label` is `赞` and whose rendered body is a numeric reaction count
- **THEN** Reels resolves that control as neutral, freshly activates that same element at most once, and binds verification to the same Reel and marker

#### Scenario: Retained Like locales use the same Reel evidence

- **WHEN** an otherwise identical primary control uses a retained zh-TW, English, Spanish, or Vietnamese Like label
- **THEN** Reels applies the same geometry, uniqueness, commit-count, and same-target verification requirements

#### Scenario: Numeric Feed summary remains a decoy

- **WHEN** a Feed card contains a reaction summary with a supported reaction-word label and numeric body
- **THEN** the summary alone is not classified as the post Like action and receives no click

#### Scenario: Localized Like does not prove selected state

- **WHEN** the resolved Reel control still exposes only its neutral label and numeric count after activation
- **THEN** verification remains unconfirmed until the same marked control exposes an established selected attribute or remove/unlike witness

### Requirement: Native Facebook Publish preserves navigation and composer selection stages

`PublishNavigateEntry` SHALL navigate once to the Facebook home URL and SHALL confirm an interactive or complete home surface with a visible main region or already-open composer within the established bounded navigation window. Its home decision MUST use one Publish-owned snapshot of URL, ready state, visible main, editor, blocking-dialog, and credential-input evidence, and MUST reject a visible non-composer blocking dialog. It MUST NOT click the composer entry. `PublishSelectMode` SHALL validate the canonical personal-timeline option while retaining the retired optional `optionKind` compatibility, preserve the Cloud-provided 40-second Facebook `select_mode` deadline through the TypeScript adapter, Native client, and Rust capability, confirm the home surface, wait at most 20 seconds for a delayed composer entry, freshly resolve and click it at most once, and confirm exactly one composer editor within the caller's remaining absolute command budget. Every successful awaited probe MUST be followed by an absolute-deadline check before reporting success or dispatching a write. Navigation and post-click confirmation MAY treat transient read errors as absent witnesses only while their existing bounded deadline remains; initial target probes and write dispatch MUST NOT be retried.

#### Scenario: Home composer entry renders late

- **WHEN** `select_mode` begins on the confirmed Facebook home surface and a supported composer entry appears after the first probe but within the trigger budget
- **THEN** Native clicks that fresh entry exactly once and returns success only after the composer editor is visible

#### Scenario: Composer is already open

- **WHEN** the canonical composer editor is already open on the Facebook home surface
- **THEN** `select_mode` returns confirmed without another entry click

#### Scenario: Page leaves home before selection

- **WHEN** the current surface stops being the Facebook home surface before the entry click
- **THEN** Native returns a not-started home-state failure and performs no click

#### Scenario: Visible dialog blocks the home composer

- **WHEN** the home snapshot contains a visible dialog that does not contain the composer editor
- **THEN** Native returns a not-started blocked-dialog result and performs no entry click

#### Scenario: Editor does not open after click

- **WHEN** one supported entry click is dispatched but no unique composer editor appears before the absolute command deadline
- **THEN** Native returns an ambiguous non-success result and never clicks the entry again

#### Scenario: Slow probe crosses the absolute deadline

- **WHEN** an editor or submitted-state probe begins before the deadline but returns its positive witness after that deadline
- **THEN** Native does not confirm the expired command; pre-click selection remains not started and post-click selection or submission remains ambiguous

### Requirement: Native Facebook Publish retains the proven localized control families

Publish entry, editor, submit, and submitted-state probes SHALL retain the exact evidence-backed English, zh-CN, zh-TW, Vietnamese, and Spanish label families from the retired Publish executor. Entry matching SHALL include `分享你的新鲜事` inside an otherwise longer accessible label, SHALL exclude comment/reply controls, and SHALL require exactly one canonical visible supported entry without using ranking to discard additional candidates. Submit matching SHALL remain scoped to the open composer and SHALL reject disabled or ambiguous controls. Post-submit verification SHALL confirm either composer closure or one retained submitted-state phrase within a bounded 20-second window capped by the caller's remaining absolute deadline.

#### Scenario: Personalized simplified-Chinese composer entry

- **WHEN** one visible home control has an accessible label such as `Tianxing Bai，分享你的新鲜事吧！`
- **THEN** the Publish entry probe resolves it as the unique composer entry

#### Scenario: Retained localized submit control

- **WHEN** an open composer has one enabled submit control labeled with a retained zh-CN, zh-TW, English, Vietnamese, or Spanish form
- **THEN** Native resolves that composer-scoped control and does not use a document-wide fallback

#### Scenario: Comment text resembles a composer entry

- **WHEN** visible comment or reply controls contain words overlapping the Publish entry vocabulary
- **THEN** they are excluded and receive no Publish click

### Requirement: Native Comment preserves localized pending-approval vetoes

Comment acknowledgement SHALL use the full evidence-backed pending-approval expression from the retired Comment executor, including administrator-review and visible-after-approval variants. The expression MUST apply only to the scoped own comment lifecycle metadata after removing the submitted body, or to the dedicated participation dialog gate. A pending approval state MUST veto confirmed success even if an optimistic row or control set exists.

#### Scenario: Administrator approval is pending

- **WHEN** the scoped own comment row exposes an established Chinese or English administrator-approval or visible-after-approval phrase
- **THEN** Native reports pending approval and does not confirm the comment

#### Scenario: Submitted body contains approval words

- **WHEN** the user's submitted comment text itself contains a pending-approval phrase but the remaining own-row metadata has a valid server acknowledgement
- **THEN** the submitted body does not trigger the veto and the server evidence may confirm the comment

### Requirement: Unknown localized controls have no generic online write fallback

An action label outside the evidence-backed Native vocabulary MUST remain a truthful not-found, unsupported, ambiguous, pending, or unconfirmed result according to its capability. The production main path MUST NOT invoke a TypeScript page executor, `CloudElementSelector`, `LikeStepRunner`, or an LLM-selected click after Native cannot establish the capability witness.

#### Scenario: Unknown locale reaches a write command

- **WHEN** Native cannot establish an exact capability-owned target from the supported vocabulary and structural evidence
- **THEN** no generic selector or LLM authorizes a replacement click and the command remains non-success
