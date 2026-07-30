## MODIFIED Requirements

### Requirement: Unified account automation exposes Facebook rule mode without treating it as a content action

The unified account automation catalog and Facebook-filtered view SHALL expose the environment's rule-mode enablement, API owner current published numeric policy revision, execution-target applied current revision/cursor/lag, the account's adopted immutable revision, effective mode, collecting progress, adopted `viewThreshold` and `joinEveryNRounds`, current cadence position and latest round summary as distinct server-authoritative facts. The account schedule surface SHALL keep policy values read-only and SHALL direct global policy management to the corresponding management surface; it MUST NOT provide a second rule-policy editor, customer override or environment override. The rule configuration MUST remain a distinct domain record and MUST NOT be encoded as a `post`, `comment`, `contact_comment` or `join_group` mode, daily cap or hour-cell trigger. The all-platform summary MAY show that rule mode is enabled but MUST NOT expose an unsupported rule control for other platforms.

The behaviour summary rendered for an account MUST describe the immutable policy revision and numeric snapshots that its current progress or round actually adopted. A newer owner current that has not reached the target SHALL be displayed as propagation pending; a newer target applied current SHALL separately be displayed as pending the next safe collecting boundary. Neither state may recalculate current progress, change current cadence position or be presented as already adopted. The surface MUST NOT display compiled-in numeric constants when the referenced revision differs, and a missing, stale, unpublished, structurally invalid or incompatible owner/applied/adopted fact MUST be rendered as unavailable with its named blocker rather than as a legacy cadence.

#### Scenario: Facebook view exposes authoritative policy and runtime
- **WHEN** the operator filters account automation to Facebook
- **THEN** each Facebook row shows environment enablement, owner current, target applied current/cursor/lag, account-adopted revision, both numeric tiers and authoritative runtime status without exposing a policy editor

#### Scenario: Other platform views have no rule control
- **WHEN** the operator filters account automation to Xiaohongshu or WeChat Channels
- **THEN** no Facebook rule-mode control is rendered and a forged server write remains rejected

#### Scenario: Rule mode is not an hourly content action
- **WHEN** the account reaches its adopted `viewThreshold` outside any content-action hash minute
- **THEN** the rule round may be created from its count trigger without consuming or fabricating an hourly `content_schedule` fire key

#### Scenario: Join-contact frequency is reported as its own tier
- **WHEN** the operator inspects a Facebook account running rule mode
- **THEN** the view distinguishes adopted view-to-like threshold from adopted round-to-join-contact cadence and MUST NOT present a single combined counter

#### Scenario: Current propagation and adoption do not rewrite in-flight progress
- **WHEN** owner or target-applied current revision changes while an account has nonzero collecting progress or an active round
- **THEN** the account view continues to render the adopted revision and snapshots for current work, marks owner-to-target propagation and applied-to-adopted safe-boundary waits separately

#### Scenario: Unknown revision is not replaced by compiled defaults
- **WHEN** the schedule projection cannot resolve the exact owner current, target applied current or adopted policy snapshot
- **THEN** the affected policy/runtime facts are unavailable with a named blocker and no compiled threshold or cadence is shown
