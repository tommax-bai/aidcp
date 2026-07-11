## MODIFIED Requirements

### Requirement: Membership state confirmation SHALL recognize all supported locales

The Facebook group-join post-click confirmation SHALL primarily use a **language-independent structural signal** for the truth of "did the account get in", with the multilingual member / pending / questionnaire lexicon (NFKC contains-match, shared edge↔cloud) **retained as a positive-only supplement**. To avoid a NEW false-positive on public groups that render a composer to non-members, the joined verdict MUST rest on a **post-only membership fact plus a same-navigation transition**, never on bare composer presence:

- **Post-only membership fact (load-bearing)**: joined confirmation SHALL require that the **post-click observation shows a focusable post/comment composer in the group body AND shows no visible Join CTA in the group body**. "No visible Join CTA post-click" is a single-observation fact (not a cross-navigation "disappeared"), robust to the two-invocation architecture — a non-member on a public group retains a visible Join CTA, so it fails this fact.
- **Same-navigation transition (corroborating)**: the composer SHALL be evaluated as a transition using the **within-invocation pre/post observation pair from the same `click=true` navigation** (the pre-click observation captured just before the click and the post-click observation after it), NOT a separate earlier observe-only invocation on a different navigation. A late-rendering non-member composer that produces a spurious absent→present transition is still rejected by the post-only "no visible Join CTA" fact.
- **Ordering**: pending / questionnaire detection SHALL be evaluated **before** the joined verdict, so a Join→Pending flip that also renders a composer is classified as pending, never joined.
- The joined authority (cloud judge) SHALL be given the structural fields (composer-present, Join-CTA-present, Leave-affordance-present) for both the within-invocation pre and post observations; a localized member/pending lexicon match MAY corroborate, but its **absence MUST NOT veto** a structurally-confirmed join, and the lexicon MUST NOT be the sole gate that turns a real join into `join_failed`.
- This requirement never loosens toward success without a positive signal: when the post-only membership fact is not met **and** no positive member-lexicon match is present, the executor/judge MUST NOT report joined (no silent assume-joined).
- At observe time (no click performed), a **bare composer presence MUST NOT** flip a never-joined group to `already_member`; observe-time `already_member` still requires a positive member signal — a lexicon member match, or a composer present **with no visible Join CTA** in the group body.

#### Scenario: Localized already-member is confirmed by composer + no-visible-Join-CTA post-click
- **WHEN** a join click on a supported-locale group yields a post-click observation with a focusable composer and no visible Join CTA in the group body (composer absent in the same-navigation pre-click observation), but the control's member label is in a locale the lexicon does not cover
- **THEN** the executor/judge reports joined success on the structural fact + transition, rather than exhausting the poll and returning `join_failed` (killing the repeat-join false-negative)

#### Scenario: Public group that shows a composer to non-members is not fake-joined
- **WHEN** the group renders a focusable composer to a non-member while a Join CTA remains visible in the group body
- **THEN** the joined verdict fails the post-only "no visible Join CTA" fact, so the executor MUST NOT report joined; it proceeds to attempt Join (and at observe time MUST NOT report `already_member`)

#### Scenario: Join→Pending flip with a composer is classified pending, not joined
- **WHEN** the post-click observation is a Pending/questionnaire state that also happens to render a composer
- **THEN** pending/questionnaire detection (evaluated before the joined verdict) classifies it as pending, not joined

#### Scenario: Successful join is still corroborated by lexicon supplement
- **WHEN** a join click flips the control to a localized member label the lexicon covers (e.g. Vietnamese "đã tham gia", Spanish "salir del grupo")
- **THEN** the executor reports `already_member`/joined success — the lexicon match positively corroborates the structural fact

#### Scenario: Decorated English member label is recognized
- **WHEN** the member control renders as decorated English (e.g. "✓ Joined" or "Joined ⌄")
- **THEN** the retained lexicon contains-match recognizes it as a member state rather than failing an exact-equality check

#### Scenario: No positive signal is still an honest failure
- **WHEN** after the post-click poll there is neither the post-only membership fact (composer + no visible Join CTA) nor any positive member/pending lexicon match
- **THEN** the executor/judge MUST NOT report joined success; it reports the honest not-joined / retry outcome (no assume-joined)
