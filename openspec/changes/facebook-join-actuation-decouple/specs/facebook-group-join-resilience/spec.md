## ADDED Requirements

### Requirement: Join actuation SHALL target the cloud-approved candidate by exact-literal-equality, self-harm-safe across locales

Facebook group-join uses two edge invocations: an observe-only pass, then — after the cloud judges the observation safe — a `click=true` pass that **re-navigates to a fresh page** and re-observes before clicking. Because the fresh page invalidates any DOM handle minted during the observe pass, and because a lexicon/structural "Join-kind re-confirm" **cannot** simultaneously admit an unknown-locale Join label and reject a same-structure Leave control, the actuation-targeting and anti-self-harm mechanism MUST be **exact-literal-equality to the cloud-approved candidate text**:

- The cloud instruction SHALL reference the approved candidate by its **exact original text** (`clickTarget`), a navigation-resilient literal key — NOT a page-local DOM handle, NOT a lexicon classification, NOT a bare positional index.
- The edge SHALL report every observed Join/candidate control's **original text unconditionally** in the observe pass (it MUST NOT drop a candidate because its label is in an unrecognized locale), and on the `click=true` pass SHALL rebuild the candidate list with the **same unconditional reporting**.
- **Exact-literal-equality is the sole hard anti-self-harm gate.** On the `click=true` pass the edge SHALL click a control **only if** its freshly-observed original text is **literally equal** (after an identically-pinned normalization applied on both the observe-capture side and the click-compare side) to the cloud-approved `clickTarget` text. Because Join and Leave (and Cancel) are distinct literals in every locale, a Leave/Cancel control **never** equals the approved Join literal and thus is **never** clicked — this is what makes the mechanism both language-agnostic and self-harm-safe.
- **Ordinal is only a tie-breaker among literal-equal candidates**, never a positional fallback: when two or more freshly-observed candidates have text literally equal to `clickTarget`, the approved ordinal disambiguates; the edge MUST NOT click "whatever sits at index N" when no literal-equal candidate exists.
- **Empty-literal guard**: a `clickTarget` whose normalized value is empty/whitespace-only MUST be treated as absent (fall back to lexicon), and the edge MUST NOT match an empty-text control by literal equality — this prevents an icon-only Leave/Cancel control (empty captured text) from colliding with an empty key.
- **Source-field parity**: the literal SOURCE FIELD used to build the candidate text (e.g. `text || aria-label`) MUST be pinned **identically** on both the observe-capture side and the `click=true` compare side, alongside the normalization form, so the compare side can never be more collapsing/permissive than the capture side.
- When no freshly-observed candidate is literally equal to `clickTarget` (page changed / text drifted), the edge MUST report honestly (`stale_target` / `no_button`) and MUST NOT blind-click.
- When `clickTarget` is absent (legacy cloud), the edge SHALL fall back to its existing lexicon-based Join-location behavior without regression.
- The `clickTarget` field is an additive change to `GroupJoinPayload` and MUST keep the two `protocol.ts` copies byte-identical; because optional-field drift is NOT caught by the `Record<MessageType,true>` typecheck, a dedicated edge+cloud `AC-PROTO` round-trip assertion MUST guard `clickTarget` encode/decode parity.

#### Scenario: Edge clicks the cloud-approved candidate by exact-literal-equality on the fresh page
- **WHEN** the `click=true` pass re-navigates and re-observes, and a freshly-observed candidate's normalized text is literally equal to the cloud-approved `clickTarget`
- **THEN** the edge clicks that candidate, without re-selecting a Join button via its own lexicon

#### Scenario: A Leave/Cancel control is never clicked because its literal never equals the approved Join text (anti-self-harm)
- **WHEN** on the `click=true` pass the position/structure that the approved candidate occupied now hosts a Leave/Cancel control (different literal text) — e.g. the account is already a member
- **THEN** no freshly-observed candidate is literally equal to the approved Join literal, so the edge clicks nothing and reports honestly (`stale_target`), never actuating Leave/Cancel

#### Scenario: Ordinal disambiguates only among literal-equal candidates, never positional
- **WHEN** the fresh page has no candidate whose text is literally equal to `clickTarget` (but has other buttons at various indices)
- **THEN** the edge MUST NOT click any button by position/ordinal; it reports `stale_target` / `no_button`

#### Scenario: Empty-text (icon-only) control is never matched by literal equality
- **WHEN** the approved `clickTarget` normalizes to empty/whitespace, or a freshly-observed candidate has empty captured text (icon-only control)
- **THEN** the edge treats an empty `clickTarget` as absent (lexicon fallback) and never matches an empty-text control by literal equality (an icon-only Leave/Cancel is never clicked via an empty key)

#### Scenario: Candidate text is reported regardless of locale
- **WHEN** the observe pass sees a Join/candidate control whose label is in a locale the edge lexicon does not recognize
- **THEN** the edge still reports that candidate's original text in the observation, so the cloud can approve it as a `clickTarget`

#### Scenario: Missing clickTarget falls back without regression
- **WHEN** a `click=true` command arrives without a `clickTarget` (legacy cloud)
- **THEN** the edge uses its existing lexicon-based Join-location behavior and the join flow does not regress
