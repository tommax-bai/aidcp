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

### Requirement: Coverage member-left demotion SHALL require confirmation regardless of reason

A join-coverage failure SHALL NOT demote a joined membership to `left` on a single navigation-error signal. The same left-confirmation threshold applied to permission-gated signals MUST apply to navigation errors (or the navigation error MUST route to a transient coverage cooldown that leaves the membership `joined`).

#### Scenario: Single navigation error does not evict a joined member
- **WHEN** one coverage attempt on a joined group returns a navigation error
- **THEN** the membership stays `joined` (its left-confirmation count is incremented) and is not immediately set to the irreversible `left` state

#### Scenario: Repeated confirmations still demote
- **WHEN** the configured number of left-confirmations is reached across attempts
- **THEN** the membership is demoted to `left` as before

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

### Requirement: Join candidate collection and clicking SHALL be scoped to the target group's own action region, excluding cross-group (suggestion-rail) candidates

Facebook group-join candidate collection and clicking SHALL be scoped to the target group's own action region, and MUST NOT select a Join control that belongs to a different group. Facebook group pages render a "discover more groups" suggestion rail whose Join controls belong to **other** groups and, because UI chrome language follows the account (not the group), carry a literal label **identical** to the target group's own Join control (e.g. 「加入小组」/"Join group"). These rail controls do not carry the `banner`/`navigation`/`complementary` roles and therefore survive the existing region exclusion. Selecting a Join control page-wide (document-order first) can thus click a **different group's** Join whenever the target group's own control is not Join-classified — already-member, already-pending, or a late-rendering header Join — joining a group the cloud never adjudicated (a reckless wrong-target action).

Concretely, join-candidate collection and clicking MUST be scoped to the target group's own action region by a **fail-closed positive-containment** rule (candidates default OUT of scope; only those positively contained in the target group's own region are in scope):

- A candidate is **in scope only if** it is a descendant of the target group's **own header/action region** — the block containing the group's primary name heading (`<h1>` / `[role="heading"][aria-level="1"]` bearing the group name) together with the group's primary action controls. The block's upper bound is set by walking up from the heading and stopping before any ancestor that contains a **different-group navigation reference** (see next bullet for how a reference is detected). Any candidate not positively contained in that block — including a suggestion-rail Join rendered as a **bare `div[role=button]` sibling of the suggested group's name link (carrying NO different-group `href` ancestor)** — is **out of scope by default**. This positive-containment default is the load-bearing safety rule: its failure mode when the region is under-resolved to the safe (narrow) side is safe (the target's own Join is missed → honest no-click + retry), never a wrong-group click. **NOTE (fail-closed is conditional on reference detectability):** because the block's upper bound relies on detecting a different-group reference, a suggestion rail whose different-group id is encoded ONLY in an undetectable form (neither an `a[href]`, nor a `[role="link"]`, nor any element attribute value — e.g. only in a JS closure) can cause the block to over-expand (fail-open); real-machine calibration MUST validate a non-anchor rail before this behavior is trusted for landing, and the member-contradiction guard below closes the membership-fabrication direction independently.
- A different-group **navigation reference** is detected from ANY element (its `href` OR any of its attribute values) carrying a `/groups/<id>` substring whose id **differs** from the current page's target group id (parsed from `location.pathname`; numeric-id and vanity-slug both compared) — covering anchors, `[role="link"]`, and non-anchor client-routed cards that encode the id in `data-*`/similar.
- **The header/action region MUST be positively identified as the TARGET group's, not merely free of foreign references.** A "suggested groups" card can be laid out so its group-name heading + Join sit in a sub-region (e.g. a content column) that is itself free of any `/groups/<id>` link (the card's foreign link living in a sibling column); such a foreign-free fragment MUST NOT be accepted as the target's header region. The edge MUST choose among candidate group-name headings the one that positively belongs to the target group's own top-level region (e.g. a heading whose region is bounded by the group's main content root rather than by an intermediate card that references a different group), and MUST fail closed (retryable) when no heading positively resolves to the target's region — it MUST NOT fall back to the first heading on the page.
- On top of positive containment, two **corroborating exclusions** further narrow scope (they may only remove candidates, never re-admit them): (E1) a candidate whose nearest-ancestor navigation reference (as defined above) resolves to a different group is excluded; (E2) a candidate falling within a "discover more groups / suggested groups" carousel container is excluded. A blacklist built from these exclusions alone MUST NOT be the load-bearing rule, because a bare-`div` rail Join carries no different-group anchor and would escape it.
- **A membership signal MUST NOT establish `already_member` while an in-scope Join control is present.** A group that shows its own Join CTA cannot be one the account has already joined; a co-occurring "already joined" signal therefore indicates cross-group pollution (e.g. an opaque suggestion rail that escaped scoping) and MUST NOT fabricate `already_member` — the target's own Join is acted on instead.
- **Fail-closed scope outcomes MUST be reported as a retryable transient, not a permanent no-button failure**, so that a group whose scope is momentarily unresolvable (re-navigation race / late header render) is retried rather than permanently dropped from the join pool.
- The click pass MUST select the Join control **only among in-scope candidates**. It MUST NOT fall back to page-wide "document-order first Join" — that fallback is exactly the path that clicks a suggestion-rail (different-group) Join.
- **Fail-closed on scope ambiguity**: when the target group id cannot be parsed from the URL **or the target group's own header/action region cannot be resolved**, the click pass MUST report honestly (`scope_unresolved`) and MUST NOT click any Join page-wide. When no in-scope candidate is Join-classified (target is member/pending/late-render), the click pass MUST report honestly (`no_target_in_scope`) and MUST NOT reach outside the scope for a Join.
- The observe pass MUST annotate each candidate with whether it belongs to the target group's own action region and MUST select the group's primary CTA (`mainCta`/`joinButton`) **only among in-scope candidates**, so a suggestion-rail Join never impersonates the group's own CTA. **Membership-signal reading MUST likewise be scoped to the target group's own region** — a suggestion-rail "already joined" signal for a different group MUST NOT enter the reported membership signals nor let the post-click membership check fabricate success on the wrong group. The observe pass MUST still report the full candidate list (including out-of-scope candidates) to the cloud judge — it MUST NOT silently drop candidates (the cloud, not the edge, owns the fail-closed decision and needs the full picture).
- When an in-scope control exists but is classified as none of join/member/pending, the edge MUST report it honestly (with its original text and scope flag) and MUST NOT substitute an out-of-scope Join to fabricate success.

#### Scenario: A suggestion-rail Join for a different group is never clicked
- **WHEN** the page shows the target group's own control as non-Join (e.g. a pending "取消请求") and a suggestion-rail Join for a different group carries the identical literal 「加入小组」, and the cloud has instructed a click
- **THEN** the click pass finds no in-scope Join, reports honestly (`no_target_in_scope`), and never clicks the different group's Join

#### Scenario: A bare-div suggestion-rail Join carrying no different-group anchor is still out of scope
- **WHEN** the target group's own control is non-Join and a suggestion-rail Join for a different group is a bare `div[role=button]` sibling of the suggested group's name link, carrying NO `a[href]` ancestor resolving to a different group
- **THEN** positive containment (not the E1 anchor exclusion) keeps it out of the target group's own region, so the click pass finds no in-scope Join and reports `no_target_in_scope`, never clicking it

#### Scenario: A non-anchor suggestion-rail Join (role=link / attribute-encoded group id) is still out of scope
- **WHEN** the target group's own control is non-Join and a suggestion-rail card navigates to a different group via a non-anchor element (a `div[role="link"]` or a card whose different-group `/groups/<id>` is encoded only in an attribute value such as `data-*`, with no `a[href]`)
- **THEN** the different-group reference is still detected from `[role="link"]`/attribute values, the header block is bounded to exclude the rail, the rail Join is out of scope, and it is never clicked

#### Scenario: A two-column suggested-group card (foreign link in a sibling column) does not impersonate the target header
- **WHEN** a "groups you may like" card places the different-group `/groups/<id>` link in one column (e.g. a thumbnail) and the group-name heading + Join in a sibling content column that itself contains no `/groups/<id>` link, and that card's heading appears before the target group's own heading in document order
- **THEN** the card's content column is NOT accepted as the target's header region (its heading is rejected because its region is bounded by the card, which references a different group), the card's Join is out of scope and never clicked, and the card's member CTA never fabricates `already_member` for the target; the target's own heading is used instead (or, if none positively resolves, the edge fails closed retryably)

#### Scenario: Ambiguous target header (two symmetric candidate regions) fails closed
- **WHEN** the page presents more than one candidate group-name heading region that each positively resolves to the target (e.g. a different-group link floats outside a suggested card so both the target header and the card look like equally-valid target regions) and the edge cannot determine which belongs to the target
- **THEN** the edge fails closed (retryable) and clicks nothing, rather than guessing and risking a wrong-group click

#### Scenario: A membership signal with an in-scope Join present does not fabricate already_member
- **WHEN** the target group's own in-scope control is a Join AND an out-of-scope suggestion-rail card for a different group shows an "already joined" signal that (in a degenerate opaque-rail case) reaches the membership signals
- **THEN** `already_member` is NOT reported (a group showing a Join CTA cannot already be joined) and the target's own Join is acted on

#### Scenario: A fail-closed scope outcome is retryable, not a permanent failure
- **WHEN** the scope cannot be resolved (target group id unparseable, or the header/action region cannot be resolved, or no in-scope Join candidate exists) on a click attempt
- **THEN** the outcome is reported as a retryable transient (so the group is retried), not a permanent no-button failure that drops the group from the join pool

#### Scenario: A suggestion-rail "already joined" signal never fabricates target membership
- **WHEN** a suggestion-rail card for a different group shows an "already joined" membership signal outside the target group's own header/action region
- **THEN** that signal is not included in the reported membership signals and the post-click membership check does not treat it as the target group having been joined

#### Scenario: The target group's own Join is clicked normally
- **WHEN** the target group is joinable and its own Join control (not wrapped in a link to a different group) is present in scope
- **THEN** the click pass clicks that in-scope Join and reports its coordinates, unaffected by any suggestion-rail candidates

#### Scenario: Unparseable target group id fails closed
- **WHEN** the target group id cannot be parsed from `location.pathname`
- **THEN** the click pass reports `scope_unresolved` and clicks nothing page-wide

#### Scenario: The target's own control belongs to a link to the SAME group and is not mis-excluded
- **WHEN** the target group's own Join control is wrapped in an anchor resolving to the current page's own `/groups/<id>`
- **THEN** the candidate is in scope (same id) and remains eligible for selection

#### Scenario: Observe pass selects the group's own CTA, not a rail candidate, but still reports all candidates
- **WHEN** the observe pass sees both the target group's own CTA and suggestion-rail Join candidates
- **THEN** it selects `mainCta`/`joinButton` only from in-scope candidates, annotates each candidate's scope, and still includes the out-of-scope rail candidates in the reported list

### Requirement: Edge-task-lease failures SHALL be honest, audited terminal attempt failures

The join orchestration SHALL catch edge-task-lease acquisition and disconnect errors, mark the current membership `failed`, and write an audit row with the original lease failure reason. A lease failure MUST NOT leave the membership in `assigned` or `joining`, MUST NOT write a retry cooldown, and MUST NOT cause the next invocation to report `no_targets` while other scoped targets remain available. One account's lease failure MUST NOT abort the scheduler heartbeat for other accounts.

#### Scenario: Lease acquire timeout fails the current target immediately
- **WHEN** acquiring the browser task lease for a join attempt throws an acquire timeout, edge-offline, or disconnect error after a target was claimed
- **THEN** that membership becomes `failed` with the lease reason and an audit row, without a cooldown or hidden retry

#### Scenario: A failed lease does not block the next target
- **WHEN** the account invokes group join again after the previous target failed on lease acquisition and another scoped target is available
- **THEN** the scheduler may claim the other target and MUST NOT return `no_targets` because of the terminal failed row

### Requirement: Native Facebook group join SHALL preserve the established scoped actuation and bounded verification contract

For current-group scope, React-compatible actuation, readiness, hydration, post-click verification, and honest outcome classification, the Native-only Facebook adapter SHALL apply the established Facebook group-join executor semantics. This requirement does not assert parity with the legacy coordinator-visible 18.5-second commit window, because the current host-to-Native lifecycle does not expose the engine's internal click boundary. The adapter MUST NOT treat a command being dispatched, a click being attempted, cancellation, or a timeout expiring as proof that the account joined the group.

The adapter SHALL positively resolve the target group's own heading/action region from the current `/groups/<id>` page and SHALL classify Join, member, and pending controls only within that region. It SHALL retain bounded out-of-scope candidate evidence but MUST NOT use a recommendation control to establish the target group's state or to actuate a join. Unresolved or ambiguous scope MUST fail closed without a click.

Immediately before actuation, the adapter SHALL re-resolve exactly one enabled in-scope Join control and invoke that current React-owned element's in-page click behavior. It MUST NOT rely on coordinates captured by an earlier readiness probe as the join actuation.

The join command SHALL permit the established bounded sequence of up to 30 seconds readiness polling, a 2-second pre-click hydration settle, a 1.5-second immediate post-click settle, and up to 45 seconds durable verification. This longer budget SHALL apply only to Native Facebook `group.join`; ordinary Native commands SHALL retain their existing deadline.

The Native join SHALL honor cancellation during readiness and hydration and immediately before actuation as a not-started result. Once the in-page click has been invoked, cancellation SHALL stop bounded verification with `clicked=true` and an ambiguous `preempted_by_task` result; it MUST NOT report joined or replay the click.

#### Scenario: Unique current-group React control is re-resolved and joined state is confirmed

- **WHEN** the target group page resolves one enabled in-scope Join control and its React handler changes the page to a positive member state
- **THEN** the Native adapter re-resolves that element at the actuation boundary, invokes its in-page click behavior, and reports joined only after the member state is observed

#### Scenario: Recommended-group Join is excluded

- **WHEN** the current target group is pending or otherwise has no in-scope Join control while a recommendation region contains an identically labelled Join control for another group
- **THEN** the Native adapter reports the current group's pending or no-target state, records the recommendation as out of scope, and never clicks it

#### Scenario: Ambiguous target region fails closed

- **WHEN** more than one heading/action region can plausibly resolve as the target group or more than one in-scope Join control remains
- **THEN** the Native adapter reports a retryable not-ready/ambiguous no-click outcome and MUST NOT select by document order

#### Scenario: Existing terminal state short-circuits before actuation

- **WHEN** the scoped pre-click observation positively establishes already-member, pending, or questionnaire-required state
- **THEN** the Native adapter returns that honest outcome without invoking any Join control

#### Scenario: Slow hydration and durable state remain inside the join budget

- **WHEN** the Join control appears near the end of the 30-second readiness window and Facebook needs the established hydration and post-click verification windows before rendering a durable state
- **THEN** the host and Native session allow the bounded join sequence to complete instead of truncating it at the ordinary 30-second command deadline

#### Scenario: Dispatched click without durable proof is ambiguous

- **WHEN** the in-scope Join control was invoked but no member, pending, questionnaire, or structural membership transition can be proven within the bounded post-click window
- **THEN** the Native adapter reports `join_verification_ambiguous` with a dispatched/ambiguous effect and MUST NOT report joined

#### Scenario: Cancellation before actuation is not started

- **WHEN** takeover cancellation arrives before the in-page Join invocation
- **THEN** the Native adapter returns a not-started cancellation and clicks nothing

#### Scenario: Cancellation after actuation is ambiguous

- **WHEN** takeover cancellation arrives after the Join invocation but before durable verification
- **THEN** the Native adapter returns `preempted_by_task` with `clicked=true` and an ambiguous effect, without replay or claimed membership

### Requirement: Native Facebook group join SHALL repair only observed bounded-result faults

The Native Facebook group-join router and Rust consumer SHALL produce and decode every bounded result used by the complete group-join path. Before changing a producer field, router helper, or consumer type in response to an `invalid bounded result`, the implementation MUST capture the real failure's operation stage and decode stage plus its field path/JSON category or safely classified exception evidence with the diagnostic-only build. It MUST repair the observed boundary and add that exact condition to a regression fixture; it MUST NOT add broad coercion or compatibility fallbacks for unobserved shapes.

#### Scenario: Real diagnostic identifies the repair

- **WHEN** the diagnostic-only Native binary runs the full observation-only join path against the exact failing browser page
- **THEN** the captured typed path/category or safely classified exception condition is recorded before the producer/consumer boundary is changed, and the regression test uses that observed condition

#### Scenario: Sampled probes do not substitute for the full command

- **WHEN** isolated consent or join probes decode successfully but the full group-join command still fails
- **THEN** the repair follows the full command's diagnostic stage and MUST NOT guess a field from the isolated samples

#### Scenario: Transient null document body does not throw

- **WHEN** the readiness join probe runs while Facebook navigation has no `document.body` and therefore no main action root
- **THEN** the router reports no composer and unresolved/not-ready scope as bounded data, allowing the existing readiness loop to continue, rather than throwing before a result exists

### Requirement: Target group header membership SHALL be recognized without widening actuation scope

The Native Facebook group-join scope resolver SHALL include the target group's real primary header action region when it is positively related to the unique current-group heading, including layouts where the heading and action controls are siblings inside a common target-owned header container. A member-classified control such as `已加入` in that region SHALL contribute a positive current-group membership signal.

The resolver MUST continue to exclude controls owned by a different-group navigation reference or recommendation/suggestion card, MUST keep candidates out of scope by default when target ownership is unresolved or ambiguous, and MUST never use the expanded membership scope as a page-wide Join fallback. An in-scope Join control SHALL continue to contradict and prevent an `already_member` verdict.

#### Scenario: Real current-group header reports already member

- **WHEN** the exact target page has one positively resolved group heading and its sibling primary header control is member-classified as `已加入`
- **THEN** that control is in target scope and the observation-only command reports the target as already a member without clicking

#### Scenario: Suggested-group member control remains excluded

- **WHEN** a recommendation card contains a member-classified control for another group
- **THEN** that control remains out of target scope and cannot establish membership for the current group

#### Scenario: Suggested-group Join remains ineligible

- **WHEN** the target header relation is expanded to cover a sibling action region and the page also contains Join controls in recommendation cards
- **THEN** only a uniquely target-owned in-scope Join can be eligible for actuation and no recommendation Join is admitted by the expansion

#### Scenario: Ambiguous target ownership still fails closed

- **WHEN** more than one heading/action region can plausibly own the current group's controls
- **THEN** the resolver reports unresolved or ambiguous scope and clicks nothing rather than choosing by document order

### Requirement: Slow-render observations SHALL receive one bounded no-click recovery before terminal failure

When the first readiness observation ends with a no-click `not_ready` or `nav_error`, the scheduler SHALL run exactly one fresh observe leg within the same logical join invocation. The recovery observe SHALL navigate the canonical group URL again, SHALL be audited as a non-terminal recovery, and SHALL NOT write a retry cooldown or retain a database assignment between invocations. If the recovery produces a minimally ready observation, the existing judge and click flow proceeds. If it produces another execution failure, the cloud SHALL mark the current membership `failed` with the final concrete reason. The system MUST NOT call the fail-closed model on an unready observation.

#### Scenario: Slow first render recovers on a fresh observe
- **WHEN** the first observe reaches its readiness deadline with `clicked=false` and `reason=not_ready`, and a second canonical observe becomes minimally ready
- **THEN** the scheduler audits one recovery, evaluates only the ready observation, and may continue to the existing click leg without writing a cooldown

#### Scenario: Repeated slow render is terminal without target-pool blockage
- **WHEN** both the first and bounded recovery observes return `not_ready`
- **THEN** the membership becomes `failed` with the final not-ready reason, no cooldown is written, and another scoped target remains claimable on a later invocation

#### Scenario: Pre-click model call remains gated behind minimal readiness
- **WHEN** an observation is not minimally ready and the bounded recovery has not produced a ready observation
- **THEN** the cloud does not spend a fail-closed pre-click model call and returns the honest final current-attempt failure

### Requirement: Join execution failures SHALL fail after bounded no-click recovery while account-level blockers retain pause

Pure execution failures before confirmed membership—including observe/confirm timeouts, no-observation, navigation errors, not-ready, lease-unavailable, and post-confirmation slow render—SHALL retain the original reason in audit and SHALL write no retry cooldown. Only a no-click `not_ready` or `nav_error` receives the single in-invocation recovery defined above. After that recovery is exhausted, or for every other execution failure, the current membership SHALL immediately become `failed` and stop occupying the account's unfinished-assignment slot so a later invocation can select another scoped target. Account-level login-required and captcha/checkpoint states SHALL retain their existing account pause, long backoff, and bounded-attempt behavior. Already-joined coverage cooldowns SHALL remain unchanged.

#### Scenario: Repeated navigation failure is terminal for this target
- **WHEN** opening the claimed group page returns `nav_error` and the one fresh observe recovery also returns `nav_error`
- **THEN** the membership becomes `failed`, the result reports the final `nav_error`, no cooldown is written, and the command does not comment

#### Scenario: Next invocation selects another target
- **WHEN** a previous target is terminal `failed` after its bounded no-click recovery and the account still has another eligible scoped group
- **THEN** the next invocation can claim the other group without waiting for a retry timer

#### Scenario: Clicked ambiguity is never replayed
- **WHEN** a join result reports `clicked=true` but membership verification remains slow or ambiguous
- **THEN** the scheduler MUST NOT run the no-click observe recovery or issue another Join click, and MUST preserve an honest non-success outcome

#### Scenario: Lease failure keeps current fail-fast behavior
- **WHEN** a join attempt cannot acquire or retain its Edge task lease
- **THEN** the membership becomes `failed` with the concrete lease reason, without a cooldown or hidden retry

#### Scenario: Account-level failure keeps the long backoff
- **WHEN** a join attempt encounters login-required or captcha
- **THEN** the account pause and long cooldown behavior apply unchanged rather than treating the account-wide blocker as one target's ordinary failure

#### Scenario: Joined coverage behavior is unchanged
- **WHEN** navigation fails while checking comment coverage for a membership already recorded `joined`
- **THEN** the existing left-confirmation/cooldown protection remains in force and the joined fact is not demoted by this change

### Requirement: Native Facebook task release SHALL preserve the current page until deliberate navigation

After an exclusive Facebook page task releases, the Native host SHALL unblock command handling and resume passive page observation without issuing an autonomous home/feed navigation. The current group page MUST remain available to the next join or comment leg. A later deliberate feed command SHALL remain responsible for validating and restoring the retained active feed/search list before it scrolls.

#### Scenario: Observe release does not navigate home before click
- **WHEN** a Facebook group observe leg finishes on the canonical target group page and releases its task lease
- **THEN** Native resume performs no `initial_scan` navigation, and the following click leg can reuse that exact group page

#### Scenario: Deliberate feed work still restores the active list
- **WHEN** a task leaves Facebook on a group or post page and the next authorized command is a feed scroll
- **THEN** the feed command validates the current surface against the retained active list and navigates to that list if required before scrolling

