## ADDED Requirements

### Requirement: Facebook reaction counts are read from a digit-bearing witness and absence is never a measured zero

Every Facebook reaction **count** the Native adapter reports — on a feed card, a Reels card, a group first-post card, and a note detail — MUST be derived from a control whose accessible label or rendered text actually contains a digit **and** whose semantics are a reaction summary. The reaction text carried in an independent action-evidence witness is an attribution observation, not a count: it MUST NOT be consumed as a numeric engagement metric by any party, and this requirement does not make it one. The adapter MUST NOT source a reaction count from the neutral reaction-action control that the like executor actuates, and it MUST NOT change the resolver used to locate that actuation control, so like targeting, Reels like, and the reaction-summary exclusion already required by note-scoped targeting are unaffected. Localized magnitude suffixes MUST be parsed from that same witness text.

When no digit-bearing reaction-summary witness can be resolved on the target, the adapter MUST report the count as **not observed** rather than as zero. The reported card and detail payloads MUST carry an explicit optional not-observed marker; when that marker is present the numeric field MUST NOT be treated as a measurement by any consumer. A sentinel numeric value MUST NOT be used to express absence. When the marker is absent, the numeric field retains today's meaning, so peers that do not send it behave exactly as before.

#### Scenario: Neutral action control is not a count source

- **WHEN** a Facebook card exposes a neutral reaction-action control whose label is exactly a localized "Like" word and no digit anywhere in its label or text
- **THEN** the reported reaction count is marked not observed
- **AND** no count is derived from that neutral control and the like executor's control resolver is unchanged

#### Scenario: Reaction summary with a localized magnitude is read as a real number

- **WHEN** the target card exposes a reaction-summary control whose label or text contains a digit with a localized magnitude suffix
- **THEN** the reported reaction count is that parsed number
- **AND** the not-observed marker is absent

#### Scenario: Absence is distinguishable from a genuine zero

- **WHEN** one Facebook post genuinely has no reactions and another post's summary control cannot be resolved
- **THEN** the first is reported as an observed count of zero without the marker and the second is reported with the not-observed marker
- **AND** neither is reported as a sentinel negative or out-of-range number

### Requirement: Facebook comment actuation opens a collapsed comment entry before declaring the editor missing

When a Facebook comment command cannot resolve the scoped comment editor, the Native adapter MUST, within its existing bounded acquisition budget, consult the comment-entry probe for the commanded target and — if the probe returns exactly one in-scope entry with coordinates — actuate it once with trusted pointer input, then continue re-probing for the editor. The entry actuation MUST occur at most once per command. The adapter MUST NOT report an editor-not-found terminal result without having either actuated one recognized entry or established that no unique in-scope entry exists.

If the entry probe reports an ambiguous target, a target/context mismatch, or a participation-approval gate, the adapter MUST converge on that terminal reason and MUST NOT actuate anything. If the entry actuation succeeds but no editor appears within the remaining budget, the result MUST remain an honest not-started outcome and MUST NOT be reported as a submitted comment.

#### Scenario: Collapsed comment box on an arbitrary post is opened

- **WHEN** a comment command targets a post whose comment box is collapsed and whose comment entry is recognizable by the existing probe
- **THEN** the adapter actuates that entry once with trusted pointer input and then acquires the editor
- **AND** it does not return editor-not-found after scrolling alone

#### Scenario: Ambiguous entry is never actuated

- **WHEN** the comment-entry probe reports more than one candidate entry for the commanded target
- **THEN** the adapter returns the ambiguous-target terminal reason
- **AND** it dispatches no pointer input

#### Scenario: Entry opened but editor never appears

- **WHEN** the entry has been actuated once and no scoped editor is resolvable before the command budget ends
- **THEN** the adapter returns an honest not-started result naming the editor acquisition failure
- **AND** it actuates the entry no further times and reports no comment as submitted

### Requirement: Navigate-purpose Facebook open reads the purpose and never substitutes the current page

The Native Facebook adapter MUST read the note-open purpose field rather than only carrying it. When the purpose is navigate, the adapter MUST resolve a navigable canonical target from the command itself — the canonical post permalink carried as the note identity, or an explicit address when supplied — navigate to it, wait for readiness, and return an action-completed receipt carrying the independent observation and the page-derived canonical post id.

If no navigable canonical target can be resolved, or the landed page's canonical identity does not equal the commanded identity, the adapter MUST return an honest not-started action-completed receipt naming that failure. The adapter MUST NOT synthesize a note detail from whatever page is currently open, and MUST NOT return a detail output for a navigate-purpose command. A purpose value that the adapter does not act on MUST NOT be silently ignored on a path whose contract depends on it.

#### Scenario: Navigate purpose without an explicit address still navigates

- **WHEN** a navigate-purpose open carries only a canonical Facebook post permalink as the note identity
- **THEN** the adapter navigates to that permalink and returns an action-completed receipt with the page-derived canonical id
- **AND** it does not evaluate the current page as if it were the target detail

#### Scenario: Unresolvable navigate target is not disguised as a read

- **WHEN** a navigate-purpose open carries no address and no canonical permalink
- **THEN** the adapter returns a not-started action-completed receipt naming the unresolvable target
- **AND** it returns no note detail and performs no navigation

#### Scenario: Landing on a different post is not accepted

- **WHEN** navigation completes but the landed page's canonical post id differs from the commanded id
- **THEN** the adapter returns a not-started action-completed receipt naming the identity mismatch
- **AND** it does not report the current page as the commanded detail

### Requirement: Facebook list-surface exhaustion is classified per surface and never mislabeled as target-not-found

Bottom confirmation MUST be reachable on every declared Facebook list surface — home feed, search results, and group — using the same set of surfaces the adapter already accepts as the active list. The pre-round guard MUST NOT skip bottom confirmation merely because the current surface is not the home feed, **and the confirmation's own validity predicate MUST NOT invalidate a sample merely for being on a non-home list surface**: reachability requires both, and relaxing only the guard leaves the state unreachable.

Bottom confirmation MUST use exactly five samples at offsets `t=0`, `t=5s`, `t=7.5s`, `t=10s`, and `t=12.5s`, where the probe passed into confirmation is the `t=0` sample. Across all five samples, the document generation and declared list surface MUST remain unchanged, the surface MUST remain non-loading and near-bottom, the height MUST NOT grow past the established noise floor, and the canonical card identity set MUST remain unchanged. `feed_exhausted` MUST be returned only after the fifth sample and only when `explicit_end` is present in all five samples. The adapter MUST NOT return `feed_exhausted` after any earlier sample. If structural evidence is invalidated, the confirmation MUST be cancelled immediately; if structural evidence remains stable through the fifth sample but `explicit_end` was absent from any sample, the result MUST be continuation-unconfirmed. The separate home-empty confirmation stays home-only and keeps its independent timing.

The Facebook browse-scroll and page-scroll command budget MUST be long enough for every bounded confirmation round and MUST be aligned across the Edge request, Edge admission, and Native engine ceiling. The fixed-sample wait MUST remain interruptible by task cancellation and the command deadline; lengthening confirmation MUST NOT make Native task quiescence wait for the full confirmation window.

#### Scenario: Exhaustion requires the complete five-sample sequence

- **WHEN** all bottom evidence, including `explicit_end`, remains valid at `t=0`, `t=5s`, `t=7.5s`, `t=10s`, and `t=12.5s`
- **THEN** the adapter returns `feed_exhausted` only after the `t=12.5s` sample
- **AND** it does not return `feed_exhausted` after any of the first four samples

#### Scenario: One missing explicit-end sample prevents exhaustion

- **WHEN** structural bottom evidence remains valid for all five samples but `explicit_end` is absent from any one sample
- **THEN** the adapter returns continuation-unconfirmed after the fifth sample
- **AND** it does not authorize a Reels transition from that confirmation

When a bounded scroll ends without new canonical cards, the terminal reason MUST be classified by observed evidence, not by home-surface-only conditions: if canonical cards were seen on any declared list surface, the adapter MUST return a non-terminal continuation-unconfirmed reason; a target-not-found reason MUST be reserved for the case where no canonical card was observed at all. Reporting a target-not-found reason for a "this batch is fully seen" state is a prohibited semantic downgrade. Every Facebook scroll receipt MUST carry the observed list surface in its existing optional observation so Cloud can select a surface-appropriate recovery, and a Reels transition MUST NOT be authorized from exhaustion observed on a non-home list surface.

Making bottom confirmation reachable on non-home surfaces newly enables both terminal reasons to originate there, so the surface-aware Cloud handling MUST land in the same integration as the adapter change. Every terminal scroll reason the adapter can emit on a declared list surface MUST resolve to a bounded, observable Cloud outcome: either a recovery command or an explicit recorded terminal for that surface. A reason that reaches Cloud and matches no handler — producing neither a command nor a recorded terminal, leaving the session to idle until the watchdog — is a prohibited silent stall, and shipping the adapter's reachability change without the matching Cloud handling is a regression rather than a partial improvement.

#### Scenario: Group surface bottom is confirmable

- **WHEN** a Facebook scroll on a group surface reaches a near-bottom, non-growing state
- **THEN** the adapter runs the same bottom-confirmation evidence path it runs on the home feed
- **AND** it does not unconditionally continue to the next round because the surface is not home

#### Scenario: Fully seen search results are not target-not-found

- **WHEN** a scroll on a search-results surface saw canonical cards but produced no new ones within the bound
- **THEN** the adapter returns a continuation-unconfirmed reason
- **AND** it does not return a target-not-found reason

#### Scenario: Scroll receipt names its list surface

- **WHEN** any Facebook scroll command ends in a non-successful terminal reason
- **THEN** the receipt's observation carries the observed list surface
- **AND** Cloud does not authorize a Reels transition from exhaustion observed on a non-home list surface

#### Scenario: Non-home terminal reason is not left unhandled

- **WHEN** a scroll on a group or search-results surface returns a continuation-unconfirmed or exhausted terminal reason
- **THEN** Cloud produces a bounded recovery command or records an explicit terminal for that surface
- **AND** the session is not left with no command and no recorded terminal, waiting for the idle watchdog

### Requirement: Facebook commands the platform does not implement are refused before page actuation

The Native Facebook adapter MUST hold a per-platform support decision for every command kind it can be routed, and MUST refuse a command kind declared unimplemented for Facebook with the established capability-unsupported pre-actuation result — before the injected page rules are evaluated, before any navigation, input, or click, and before any commit window or write deadline is opened. The Facebook publish command kinds that the retired Facebook publish executor also did not implement — cover selection, candidate-image append, option setting, schedule setting, and both scheduled-publish reconciliation steps — MUST be covered by this refusal instead of returning an in-page not-implemented error.

The behavior-parity ledger MUST record such command kinds as explicitly unsupported with a reason, and MUST NOT claim a behavior oracle, target witness, pre-commit gate, commit primitive, verification witness, or terminal semantics for them. A retired executor MUST NOT be named as the oracle for behavior that executor never implemented.

#### Scenario: Facebook scheduled-publish reconciliation does not reach the page

- **WHEN** a Facebook session receives the scheduled-publish capture or reconciliation command
- **THEN** Edge returns capability-unsupported without evaluating page rules, navigating, clicking, typing, or opening a commit window
- **AND** no in-page not-implemented error is produced

#### Scenario: Ledger does not claim an absent oracle

- **WHEN** the parity ledger is checked against the per-platform support decision
- **THEN** every command kind declared unsupported for Facebook carries an unsupported reason and no oracle, witness, or commit primitive
- **AND** a completeness check fails if any unsupported kind still declares behavior evidence

### Requirement: Facebook write-text acceptance uses one declared predicate per write kind

Each supported Facebook write command kind MUST declare, in the behavior-parity ledger, the single text-acceptance predicate it uses. All pre-commit text checks of one write kind MUST share that one predicate; the Facebook comment path's editor readback, its pre-dispatch re-read, and its focus re-check MUST NOT use three independently written comparisons.

The comment predicate MUST accept the commanded text when the normalized editor value contains the normalized commanded text and exceeds it by no more than a declared bounded number of extra characters, restoring the containment oracle of the retired comment executor. It MUST still refuse when the commanded text is absent, truncated, or exceeded beyond the declared allowance, and every refusal MUST clear the editor and remain a not-started outcome. Any remaining asymmetry between write kinds' predicates MUST be recorded in the ledger together with its reason; an undocumented asymmetry is a ledger completeness failure.

#### Scenario: Editor-side additions do not block an approved comment

- **WHEN** the comment editor's normalized value contains the full approved text plus fewer extra characters than the declared allowance
- **THEN** the predicate accepts the readback and the comment proceeds to its trusted submit
- **AND** the same predicate is used by the pre-dispatch re-read and the focus re-check

#### Scenario: Truncated or replaced text is still refused

- **WHEN** the comment editor's normalized value does not contain the full approved text, or exceeds it beyond the declared allowance
- **THEN** the adapter clears the editor and returns a not-started result
- **AND** it does not dispatch a submit

#### Scenario: Undocumented predicate asymmetry fails the ledger check

- **WHEN** two Facebook write kinds use different text-acceptance predicates and the ledger records no reason for the difference
- **THEN** the parity completeness check fails
- **AND** the difference cannot be integrated without a recorded reason

#### Scenario: Comment body plus appended contact block is accepted as one whole

- **WHEN** a comment carries an appended contact block, the body and the block are typed as one string, and the editor accepted only the body
- **THEN** the shared predicate refuses, the editor is cleared, and the outcome stays not-started with nothing reported as submitted
- **AND** the ledger records that this write kind no longer verifies the body and the contact block as two separately accepted segments, together with the reason and the diagnostic granularity that is given up

### Requirement: Lazy-load height growth is judged against a declared noise floor

The adapter's "the page is still growing" judgement MUST compare scroll height against a **declared named noise-floor constant**, not against an arbitrarily small epsilon. A one-pixel epsilon makes any reflow count as growth, which keeps the scroll loop in its continue branch forever and leaves bottom confirmation unreachable on every list surface — including the home feed — even after the surface predicates are relaxed. The constant MUST be the retired implementation's noise floor unless a sampled Native-layout value replaces it, and the same constant MUST back both the pre-round guard and the no-growth element of the termination-evidence chain, because a single helper serves both.

Relaxing the epsilon MUST NOT change the meaning of the judgement: the adapter MUST still continue scrolling while the page is genuinely growing and MUST NOT declare a bottom while it is. Every other evidence predicate MUST remain unchanged; the sampling schedule is governed independently by the five-sample requirement above.

#### Scenario: A reflow smaller than the noise floor is not growth

- **WHEN** two consecutive probes differ in scroll height by less than the declared noise floor and the surface is near bottom with no new cards
- **THEN** the adapter treats the page as not growing and proceeds to bottom confirmation
- **AND** it does not continue to the next round on the strength of that difference

#### Scenario: A real lazy-load batch is still growth

- **WHEN** two consecutive probes differ in scroll height by at least the declared noise floor
- **THEN** the adapter treats the page as still growing and continues scrolling
- **AND** it does not declare the list exhausted

### Requirement: The new reaction-count witness normalizes labels before matching

The newly added reaction-count witness resolver MUST apply diacritic-folding normalization to accessible labels and rendered text **before** matching them against its own vocabulary, reusing the normalization transform that already exists in the same rule bundle rather than writing a second one. A decomposed-form label and its precomposed equivalent MUST yield the same verdict from this resolver.

This requirement is scoped to the newly written count witness. It MUST NOT be read as changing the existing reaction-action resolver or its vocabulary, whose diacritic blind spot is a pre-existing condition shared by both generations and is registered as an outstanding gap rather than fixed here.

#### Scenario: Decomposed and precomposed labels agree

- **WHEN** a reaction-summary control's label carries a Vietnamese word in decomposed Unicode form and an otherwise identical control carries it in precomposed form
- **THEN** the count witness resolves both to the same number
- **AND** neither is reported as not observed on account of its Unicode form

#### Scenario: Existing actuation vocabulary is untouched

- **WHEN** the count witness is added with its normalization step
- **THEN** the reaction-action resolver and its label vocabulary are byte-for-byte unchanged
- **AND** like actuation continues to select the same control it selects today
