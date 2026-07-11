## ADDED Requirements

### Requirement: Join candidate collection and clicking SHALL be scoped to the target group's own action region, excluding cross-group (suggestion-rail) candidates

Facebook group-join candidate collection and clicking SHALL be scoped to the target group's own action region, and MUST NOT select a Join control that belongs to a different group. Facebook group pages render a "discover more groups" suggestion rail whose Join controls belong to **other** groups and, because UI chrome language follows the account (not the group), carry a literal label **identical** to the target group's own Join control (e.g. 「加入小组」/"Join group"). These rail controls do not carry the `banner`/`navigation`/`complementary` roles and therefore survive the existing region exclusion. Selecting a Join control page-wide (document-order first) can thus click a **different group's** Join whenever the target group's own control is not Join-classified — already-member, already-pending, or a late-rendering header Join — joining a group the cloud never adjudicated (a reckless wrong-target action).

Concretely, join-candidate collection and clicking MUST be scoped to the target group's own action region by a **fail-closed positive-containment** rule (candidates default OUT of scope; only those positively contained in the target group's own region are in scope):

- A candidate is **in scope only if** it is a descendant of the target group's **own header/action region** — the block containing the group's primary name heading (`<h1>` / `[role="heading"][aria-level="1"]` bearing the group name) together with the group's primary action controls. Any candidate not positively contained in that block — including a suggestion-rail Join rendered as a **bare `div[role=button]` sibling of the suggested group's name link (carrying NO different-group `href` ancestor)** — is **out of scope by default**. This positive-containment default is the load-bearing, fail-closed safety rule: its failure mode when the region is under-resolved is safe (the target's own Join is missed → honest no-click + retry), never a wrong-group click.
- On top of positive containment, two **corroborating exclusions** further narrow scope (they may only remove candidates, never re-admit them): (E1) a candidate whose nearest-ancestor `closest('a[href]')` (or own `href`) resolves to a `/groups/<id>` whose id **differs** from the current page's target group id (parsed from `location.pathname`) is excluded; (E2) a candidate falling within a "discover more groups / suggested groups" carousel container is excluded. A blacklist built from these exclusions alone MUST NOT be the load-bearing rule, because a bare-`div` rail Join carries no different-group anchor and would escape it.
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
