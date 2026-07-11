## MODIFIED Requirements

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
