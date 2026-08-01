## MODIFIED Requirements

### Requirement: Native page writes MUST be validated against the acted-upon target

Every Native command that writes to the page MUST verify, after dispatch, that the intended business result actually occurred on the same target instance it acted on. The absence of that evidence MUST be reported as an honest non-success outcome that distinguishes "never started" from "dispatched but unconfirmed"; it MUST NOT be promoted to success, and a plain "the call returned without an exception" MUST NOT be accepted as validation. Where post-action validation is impossible for a specific command surface, that surface MUST be recorded explicitly as unvalidated rather than defaulting to a success result.

Whether a command satisfies this is a property of its own post-condition, not of which module it is written in: a shared resolve–act–validate orchestration exists and is wired to a first real command, but a command with its own honest post-condition is equally compliant. Which side of that line each command sits on MUST be recorded in a per-surface inventory, and that inventory MUST be mechanically held to the engine's own set of writing commands — every write command appears exactly once, so that adding one without classifying it fails rather than passing silently. **An unlisted surface reads as covered**, which is why completeness is enforced rather than reviewed.

The inventory MUST distinguish "meets the bar" from three things that are **not** the same as having validation: a check that exists but falls short of the strength bar (recorded with where it falls short), a surface with no readable business result at all (recorded with why, and explicitly not therefore defaulting to success), and a surface nobody has read yet.

**Both non-compliant categories MUST be monotone budgets, not only the unread one.** Each budget MUST equal the actual count of its category so that trimming it leaves no headroom for new entries to refill — a ratchet with slack is not a ratchet. Constraining only the unread category is insufficient and MUST NOT be treated as satisfying this: reclassifying a surface from unread to falls-short lowers the unread budget and passes every check while the surface's risk of reporting a false success is unchanged. A ratchet with a second, unguarded exit is not a ratchet either.

Every falls-short entry MUST additionally carry a named disposition: either the action that will close it, or an explicitly named exception stating the reason, the prerequisite, and who resolves it. Recording only where the check falls short is insufficient, because without a disposition a falls-short entry differs from a compliant one only in the reader's memory — and eliminating reliance on memory is the entire reason the inventory exists.

A newly added write command MUST NOT default into the unread category. Once the unread budget reaches zero it MUST remain zero; raising it again is not permitted, because that would restore the default this rule exists to forbid.

Until a surface is recorded as meeting the bar, this guarantee MUST NOT be cited for it.

#### Scenario: Dispatched write without observed effect is not success

- **WHEN** a Native write command dispatches its input and the post-action read does not show the intended state change on the bound target
- **THEN** the command reports an unconfirmed outcome
- **AND** it does not report success and does not fabricate an effect count

#### Scenario: Target lost after dispatch stays indeterminate

- **WHEN** the bound target disappears or changes identity between dispatch and validation
- **THEN** the command reports an indeterminate outcome rather than success or a retryable not-started result

#### Scenario: Reclassifying unread as falls-short does not launder the ratchet

- **WHEN** a surface is moved from the unread category to the falls-short category without its post-condition changing
- **THEN** the falls-short budget must be raised to accommodate it, which the gate refuses
- **AND** the inventory check fails rather than passing on the lowered unread budget alone

#### Scenario: Falls-short entry without a disposition is rejected

- **WHEN** an entry is recorded as falls-short with a description of the shortfall but no closing action and no named exception
- **THEN** the inventory check fails

#### Scenario: Named exception is traceable

- **WHEN** a falls-short entry cannot be closed because it depends on a prerequisite outside the current work
- **THEN** its disposition names the reason, the prerequisite, and who resolves it
- **AND** where the prerequisite is a real-machine measurement, it points at the specific tracked item rather than at real-machine work in general

#### Scenario: Unread budget stays at zero once reached

- **WHEN** the unread budget has reached zero and a new write command is added
- **THEN** that command must be classified on introduction
- **AND** raising the unread budget to accommodate it is refused
