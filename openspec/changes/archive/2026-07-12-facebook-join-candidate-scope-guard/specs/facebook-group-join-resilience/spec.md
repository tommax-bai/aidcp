## ADDED Requirements

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
