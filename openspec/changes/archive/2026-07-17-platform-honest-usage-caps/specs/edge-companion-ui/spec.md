## ADDED Requirements

### Requirement: Cloud MUST NOT supply usage caps for actions the platform cannot perform

The cloud MUST NOT supply a client-facing usage cap for an action that the connected account's platform structurally cannot perform. Supplying such a cap presents the account with a daily plan the system can never carry out, which the client then renders as a cap, a percentage, and a progress bar that can never advance — the fabrication this capability already forbids the client from inventing on its own.

This rule is about the cap, not about the surface that carries it: it MUST hold for every cap the cloud supplies toward the client, whatever window it describes and whichever configuration it was read from. A cap that names an action the platform cannot perform is fabricated whether it arrives in the daily projection, in a per-window projection, or in the receipt of some unrelated write.

The determination MUST come from the platform's own support declarations. Because an unsupported action may be declared in either the note-scoped action matrix or the orchestration capability matrix, the projection MUST consult both; consulting only one is a defect, not a scoping choice. Support MUST NOT be encoded numerically — a cap configured to zero MUST NOT be used to mean "unsupported", and the quota configuration MUST NOT be given a platform dimension.

The projection MUST fail open. If the account's platform cannot be resolved, or any support lookup throws, the cloud MUST supply caps exactly as it did before this rule existed. Withholding a cap MUST be caused only by an explicit unsupported declaration, never by a failure to look one up.

Withholding a cap MUST NOT withhold the corresponding total: the client's action rows continue to render every supplied total, and only the cap, its percentage, and its plan-completed state are absent. This requirement changes which caps the cloud supplies; it does not change how many action rows the client renders.

#### Scenario: Facebook is not offered caps for collect or follow

- **WHEN** the cloud projects usage caps for a Facebook account, whose platform declares collect unsupported in the note-scoped action matrix and follow unsupported in the orchestration capability matrix
- **THEN** the supplied caps omit both collect and follow
- **AND** every other supplied cap is unchanged
- **AND** the supplied totals are unchanged, including the collect and follow totals

#### Scenario: Every cap-bearing surface is covered, not just the daily one

- **WHEN** the cloud supplies caps for a Facebook account across more than one surface — the daily projection, the per-window projections including the session window whose caps come from a different, platform-blind configuration, and the receipt returned by an unrelated settings write
- **THEN** none of them offers a cap for collect or follow
- **AND** no surface presents a cap that another surface withholds, because two surfaces disagreeing about the same account is itself the fabrication

#### Scenario: A platform that supports the action still receives its cap

- **WHEN** the cloud projects usage caps for an account whose platform declares every projected action supported
- **THEN** the supplied caps are byte-for-byte the configured quota tier's caps

#### Scenario: Platform resolution fails while projecting caps

- **WHEN** the account's platform cannot be resolved, or a support lookup throws, while the cloud projects usage caps
- **THEN** the cloud supplies the full configured set of caps
- **AND** the client is never left without usage information because a lookup failed

#### Scenario: Client renders the withheld cap honestly

- **WHEN** the client receives a daily usage payload whose totals include an action that has no supplied cap
- **THEN** the client renders that action's total with no cap, no percentage, and no progress bar
- **AND** the client does not treat that action as a plan that can complete

#### Scenario: Withheld caps do not block the day-completed state

- **WHEN** every action that has a supplied cap has reached it, and an action without a supplied cap has not
- **THEN** the client presents the daily plan as completed
- **AND** an action with no supplied cap never prevents the completed state, because an action with no plan cannot be an incomplete plan
