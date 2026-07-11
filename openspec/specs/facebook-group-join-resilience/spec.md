# facebook-group-join-resilience Specification

## Purpose
TBD - created by archiving change facebook-join-comment-resilience. Update Purpose after archive.
## Requirements
### Requirement: Membership state confirmation SHALL recognize all supported locales

The Facebook group-join **post-click** confirmation SHALL primarily use a **language-independent structural signal** for the truth of "did the account get in", with the multilingual member / pending / questionnaire lexicon (NFKC contains-match, shared edge↔cloud) **retained as a positive-only supplement**. The load-bearing structural signal MUST be a **click-attributable transition**, NOT a lexicon-derived predicate:

- **Composer transition (load-bearing, language-independent)**: joined confirmation SHALL require that a focusable post/comment composer in the group body was **absent in the pre-click observation and present in the post-click observation** of the **same `click=true` navigation** (the pre-click observation captured just before the click, the post-click observation after it). This transition does NOT depend on any lexicon, so it holds in locales the Join/member lexicon does not cover. A non-member public group that renders a composer to non-members has the composer **present pre-click** → no transition → not confirmed.
- **Corroborating only (NOT load-bearing)**: "no visible Join CTA post-click" (`joinCtaPresent` false) and "document not loading" MAY corroborate but MUST NOT be the sole positive. Rationale (adversarial-review finding): `joinCtaPresent` is derived from the **Join lexicon** (a Join control is only recognized when its label matches the lexicon), so in an uncovered locale a non-member's Join button is missed and `joinCtaPresent` fails **open** — using it as the sole guard would falsely confirm membership for a non-member. The transition is the guard that does not fail open.
- **Post-click only — no observe/pre-click structural verdict**: the edge/judge MUST NOT conclude `already_member` (or joined) from structure at observe time / pre-click, where no click has occurred. A no-click structural `already_member` would mark the membership joined without ever joining (ledger corruption + a comment in a group the account never joined). Observe-time / pre-click `already_member` is decided only by a positive **lexicon** member match.
- **Ordering**: pending / questionnaire detection SHALL be evaluated **before** the structural joined verdict, so a Join→Pending flip that also renders a composer is classified as pending, never joined.
- **Cloud is the joined authority**: the judge SHALL be given the structural fields (composer-present, Join-CTA-present) for both the same-navigation pre and post observations (they ride the loosely-typed observation channel; the scheduler threads the pre-click observation). A localized member/pending lexicon match MAY corroborate, but its **absence MUST NOT veto** a transition-confirmed join, and the lexicon MUST NOT be the sole gate that turns a real join into `join_failed`.
- This requirement never loosens toward success without a positive signal: when neither the composer transition **nor** a positive member-lexicon match is present, the executor/judge MUST NOT report joined (no silent assume-joined).

#### Scenario: Localized join is confirmed by the composer transition, not the lexicon
- **WHEN** a join click on a supported-locale group yields a composer that was absent in the same-navigation pre-click observation and present post-click, but the control's member label is in a locale the lexicon does not cover
- **THEN** the executor/judge reports joined success on the transition, rather than exhausting the poll and returning `join_failed` (killing the repeat-join false-negative), without relying on the lexicon

#### Scenario: Non-member public group with a composer present pre-click is never fake-joined
- **WHEN** the group renders a focusable composer to a non-member **already at pre-click** (and in an uncovered locale where `joinCtaPresent` is false), and the post-click observation still shows a composer
- **THEN** there is no composer transition (composer present pre-click), so the joined verdict MUST NOT fire — the executor reports `join_failed`, never a false joined (the lexicon-derived `joinCtaPresent` is NOT trusted as the sole guard)

#### Scenario: Observe-time / pre-click never concludes already_member from structure
- **WHEN** at observe time (no click) a non-member page shows a main-scoped composer and a Join control whose label is not in the lexicon (so `joinCtaPresent` is false)
- **THEN** the system MUST NOT report `already_member` from structure (no no-click markJoined); observe-time `already_member` requires a positive lexicon member match

#### Scenario: Join→Pending flip with a composer is classified pending, not joined
- **WHEN** the post-click observation is a Pending/questionnaire state that also renders a composer
- **THEN** pending/questionnaire detection (evaluated before the structural joined verdict) classifies it as pending, not joined

#### Scenario: Successful join is still corroborated by lexicon supplement
- **WHEN** a join click flips the control to a localized member label the lexicon covers (e.g. Vietnamese "đã tham gia", Spanish "salir del grupo")
- **THEN** the executor reports `already_member`/joined success — the lexicon match positively confirms membership

#### Scenario: Decorated English member label is recognized
- **WHEN** the member control renders as decorated English (e.g. "✓ Joined" or "Joined ⌄")
- **THEN** the retained lexicon contains-match recognizes it as a member state rather than failing an exact-equality check

#### Scenario: No positive signal is still an honest failure
- **WHEN** after the post-click poll there is neither a composer transition nor any positive member/pending lexicon match
- **THEN** the executor/judge MUST NOT report joined success; it reports the honest not-joined / retry outcome (no assume-joined)

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

