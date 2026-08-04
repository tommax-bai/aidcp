## ADDED Requirements

### Requirement: First-post group-root navigation confirms landing before any probe runs

The first-post comment path SHALL NOT begin probing for a candidate post until it has confirmed that the browser
actually landed on the requested group root. Document readiness alone MUST NOT be accepted as landing evidence:
a navigation that has been dispatched but not yet applied leaves the **previous** document in a ready state,
which satisfies a readiness-only wait instantly and lets every downstream check run against the wrong page.

Landing confirmation SHALL require both document readiness and the current address resolving to the requested
group root, within a bounded window. Failing to confirm landing within that window is a **posture-class** failure:
it SHALL spend one unit of the corrective budget and re-probe, and MUST NOT be reported as a post-identity failure
and MUST NOT terminate the step on its own.

This requirement is the direct guard against acting on a stale page. Any page-posture conjunct that exists only
because landing was never awaited SHALL be justified against this requirement before it is relaxed.

#### Scenario: Stale ready document is not accepted as landing

- **WHEN** navigation to the group root is dispatched while the previous page is still displayed and already reports a ready document
- **THEN** the path does not begin probing, and continues waiting until the address resolves to the requested group root or the bounded window elapses

#### Scenario: Landing timeout is posture-class, not identity-class

- **WHEN** the bounded landing window elapses without the address resolving to the requested group root
- **THEN** the failure spends one unit of the corrective budget and the path re-probes
- **AND** the reported reason distinguishes "did not land on the requested group root" from "post identity could not be confirmed"

#### Scenario: Normal landing is unchanged

- **WHEN** navigation applies and the address resolves to the requested group root within the window
- **THEN** probing begins exactly as before, with no additional delay beyond the confirmation itself

### Requirement: The first-post corrective navigation budget is spent only by failures

The first-post path's corrective re-navigation budget SHALL be a distinct quantity from the record of whether the
preparation phase already navigated. Preparation-phase navigation — the initial jump performed because the starting
page was not already the clean group root — MUST NOT decrement the corrective budget.

Collapsing the two makes the corrective branch statically unreachable in the common case: after joining a group the
starting page is essentially never the clean group root, so preparation always navigates, so a corrective branch
gated on "has not navigated yet" can never fire. The failure mode is silent — no error, no log, simply a recovery
path that never runs.

The corrective budget SHALL start at its full value regardless of what preparation did, SHALL be decremented only
when a probe actually fails, and SHALL be reported as exhausted ("retried N times") rather than as an inability
when it runs out.

#### Scenario: Preparation navigation leaves the corrective budget intact

- **WHEN** the starting page is not the clean group root, so the preparation phase navigates once, and the subsequent probe fails with a posture-class reason
- **THEN** the corrective re-navigation still runs, because the preparation jump did not consume the corrective budget

#### Scenario: Corrective budget is consumed only by failures

- **WHEN** repeated probe failures consume the corrective budget in full
- **THEN** the step terminates with a reason expressed as "retried N times without success", not as "cannot be done"

#### Scenario: Already-correct starting page is unchanged

- **WHEN** the starting page is already the clean group root and preparation performs no navigation
- **THEN** the corrective budget is the same value it would have been had preparation navigated

### Requirement: The requested group address is validated after stripping URL decoration

Validation of the group address supplied by Cloud SHALL strip query string and fragment before comparing, and
SHALL judge the address invalid only when it is not a group-address form at all. A tracking parameter carried on
an otherwise valid group link MUST NOT fail the step.

When the supplied address genuinely is not a group address, the reported reason SHALL name that condition. It
MUST NOT reuse the post-identity reason value: reporting an input-format problem as a page-identity problem sends
the operator to look at the wrong thing, and hides a defect that is trivially fixable at the caller.

#### Scenario: Decorated group link is accepted

- **WHEN** Cloud supplies a valid group address carrying a query string or fragment
- **THEN** validation strips the decoration, accepts the address, and the step proceeds

#### Scenario: Non-group address is rejected under its own reason

- **WHEN** the supplied address is not a group-address form
- **THEN** the step fails with a reason naming an invalid requested group address, distinct from the post-identity reason

## MODIFIED Requirements

### Requirement: First-post scroll continuation is measured and actuated on the element that actually scrolls

The bounded first-post scroll search SHALL move and measure the same scrolling element that the list probe already resolves. When the document itself does not scroll — the document scroll height equals the viewport height and the window scroll position stays at zero while an ancestor container of the feed holds the real scrollbar — the probe MUST NOT report window or document coordinates as its displacement and bottom evidence.

Exhaustion ("did not move and is at the bottom") SHALL be decided from that element's own metrics. The specified scroll budget MUST be spendable in full on such layouts; a layout that never scrolls the document MUST NOT cause the loop to exit after its first round.

The scroll budget SHALL also be spendable in full across **posture-class** probe failures. A probe failure that
describes the page's surroundings rather than the identity of a target — not landed yet, not hydrated yet, region
not resolvable, address decoration — SHALL consume one round and continue probing while rounds remain. Only
**identity-class** failures — candidate binding conflict, evidence changed under a resolved candidate — SHALL
terminate the loop immediately, because continuing past them risks acting on a different post. The two classes
MUST be distinguishable in the returned reason; a single undifferentiated "probe failed" value MUST NOT be used
to decide loop termination.

#### Scenario: Group layout scrolls an inner container, not the document
- **WHEN** the first-post probe scrolls a group discussion stream whose real scrollbar is on an ancestor of the feed
- **THEN** the probe actuates that container and reports its displacement and bottom state
- **AND** the bounded scroll loop continues while that container still moves or is not at its bottom

#### Scenario: Posture-class probe failure consumes one round and continues
- **WHEN** a probe round fails for a posture-class reason and scroll rounds remain
- **THEN** the loop consumes one round and probes again, instead of returning the failure immediately

#### Scenario: Identity-class probe failure terminates immediately
- **WHEN** a probe round fails because a resolved candidate's binding conflicts or its evidence changed
- **THEN** the loop terminates at once without spending further rounds, and the failure is reported under its own identity-class reason

#### Scenario: Ordinary window-scrolling layout is unchanged
- **WHEN** the document itself scrolls
- **THEN** displacement and bottom evidence come from the window as before
- **AND** the observable behaviour of the bounded scroll loop does not change

#### Scenario: Exhaustion is still reported honestly
- **WHEN** the resolved scrolling element neither moves nor has further content after the bounded rounds
- **THEN** the probe reports exhaustion
- **AND** it does not report a candidate it did not find
