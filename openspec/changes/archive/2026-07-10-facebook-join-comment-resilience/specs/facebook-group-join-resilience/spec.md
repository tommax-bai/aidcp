## ADDED Requirements

### Requirement: Membership state confirmation SHALL recognize all supported locales

The Facebook group-join executor and the cloud pre-click/post-click judge SHALL classify member / pending / questionnaire states using the same multilingual lexicon used to locate the Join control, via normalized (NFKC) contains-match, NOT English/Chinese exact-equality literals or English/Chinese-only regexes. A membership label MUST still positively match a known member/pending/questionnaire term — this requirement never loosens the classifier toward reporting success without a positive signal.

#### Scenario: Successful join on a supported non-EN/ZH group is recognized
- **WHEN** a join click on a supported-locale group flips the control to a localized member label (e.g. Vietnamese "đã tham gia", Spanish "salir del grupo")
- **THEN** the executor reports `already_member`/joined success rather than exhausting the post-click poll and returning `join_failed`

#### Scenario: Already-member non-EN/ZH page is not misread as button-less
- **WHEN** the group page already shows a localized member label at observe time
- **THEN** the executor returns `already_member`, not `no_button`

#### Scenario: Decorated English member label is recognized
- **WHEN** the member control renders as decorated English (e.g. "✓ Joined" or "Joined ⌄")
- **THEN** contains-match recognizes it as a member state rather than failing an exact-equality check

### Requirement: Edge-task-lease failures SHALL be honest, audited, retryable transients

The join orchestration SHALL catch edge-task-lease acquisition and disconnect errors and route them through the retryable-failure classifier with an audit row. A lease failure MUST NOT leave the membership stranded in `joining` with a null cooldown, MUST NOT be re-picked on every scheduler tick with zero backoff, and MUST NOT be counted against the permanent attempt cap. One account's lease failure MUST NOT abort the scheduler heartbeat for other accounts.

#### Scenario: Lease acquire timeout gets cooldown and audit
- **WHEN** acquiring the browser task lease for a join attempt throws (acquire timeout / edge offline / disconnect)
- **THEN** the membership receives a retryable-transient cooldown and an audit row, instead of remaining in `joining` with no cooldown

#### Scenario: Lease failure does not consume the permanent attempt cap
- **WHEN** a join attempt fails on lease acquisition
- **THEN** the permanent attempt counter is not incremented for that lease failure and the group is not driven toward permanent `failed`

### Requirement: Coverage member-left demotion SHALL require confirmation regardless of reason

A join-coverage failure SHALL NOT demote a joined membership to `left` on a single navigation-error signal. The same left-confirmation threshold applied to permission-gated signals MUST apply to navigation errors (or the navigation error MUST route to a transient coverage cooldown that leaves the membership `joined`).

#### Scenario: Single navigation error does not evict a joined member
- **WHEN** one coverage attempt on a joined group returns a navigation error
- **THEN** the membership stays `joined` (its left-confirmation count is incremented) and is not immediately set to the irreversible `left` state

#### Scenario: Repeated confirmations still demote
- **WHEN** the configured number of left-confirmations is reached across attempts
- **THEN** the membership is demoted to `left` as before

### Requirement: Slow-render observations SHALL be retryable, not terminal

When the readiness poll exhausts with the page still below a minimal readiness threshold (document still loading or zero visible action nodes), the edge SHALL report a distinct not-ready outcome carrying readiness diagnostics rather than a terminal absent-button outcome, and the cloud SHALL route the not-ready outcome to a retry tier instead of a terminal failure or a fail-closed model call.

#### Scenario: Ready poll exhausts on a still-loading page
- **WHEN** the join readiness poll reaches its deadline while the document is still loading or no action nodes are visible
- **THEN** the edge reports a not-ready outcome with readiness diagnostics and the cloud schedules a retry rather than recording a terminal failure

#### Scenario: Pre-click model call is gated behind minimal readiness
- **WHEN** the observation is not minimally ready
- **THEN** the cloud does not spend a fail-closed pre-click model call that would produce a terminal skip; it retries instead

### Requirement: Retry backoff SHALL be tiered by transient class

Pure-network transients (observe/confirm timeouts, no-observation, navigation errors, not-ready, lease-unavailable) SHALL receive a short exponential-with-jitter cooldown (minutes scale) and SHALL NOT consume the permanent attempt cap. Account-level states (login-required, captcha/checkpoint) SHALL keep the long cooldown and the account-pause path. Backoff MUST include decorrelated jitter so accounts firing on a shared heartbeat do not retry the same group simultaneously.

#### Scenario: Network transient retries on a minutes scale without burning attempts
- **WHEN** a join attempt fails on a pure-network transient
- **THEN** the group is retried after a short jittered cooldown and the permanent attempt counter is unchanged

#### Scenario: Account-level failure keeps the long backoff
- **WHEN** a join attempt fails with login-required or captcha
- **THEN** the long cooldown and account-pause behavior apply, unchanged

### Requirement: The cloud judge lexicon SHALL be drift-guarded against the edge lexicon

The cloud pre-click judge SHALL recognize member/pending states before applying the join-CTA shortcut so a localized already-member label is not misread as an instant-join, and SHALL cover the same supported locales as the edge Join lexicon. Because the edge and cloud are separate packages, the two lexicon copies MUST be protected by a drift-guard regression test (mirroring the protocol-parity discipline) rather than silently diverging. Fail-closed behavior for genuinely-unknown labels MUST be preserved.

#### Scenario: Localized already-member label is not a false instant-join
- **WHEN** the judge evaluates a group whose control shows a localized already-member label that contains a join substring (e.g. "đã tham gia" containing "tham gia")
- **THEN** the judge classifies it as already-member and does not emit a false `instant_join`

#### Scenario: Lexicon drift is caught by tests
- **WHEN** the edge Join/member/pending lexicon and the cloud judge lexicon diverge
- **THEN** the drift-guard regression test fails

### Requirement: Unrecognized post-click modals MUST NOT be destructively dismissed

The join executor MUST NOT press Escape to dismiss a post-click modal it cannot positively classify as an optional survey. An unclassified or membership-questions modal SHALL be reported honestly (questionnaire-required or ambiguous) rather than closed, so a real join questionnaire is never destroyed.

#### Scenario: Non-EN/ZH membership questionnaire is reported, not closed
- **WHEN** a post-click modal is a membership-questions gate in a supported non-EN/ZH locale
- **THEN** the executor reports `questionnaire_required` and does not press Escape to dismiss it
