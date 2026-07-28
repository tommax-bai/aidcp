## MODIFIED Requirements

### Requirement: Unified account automation exposes Facebook rule mode without treating it as a content action

The unified account automation catalog and Facebook-filtered view SHALL expose the account's fixed rule-mode configuration, effective mode, collecting progress, the current round's position in the fixed two-round cycle and latest round summary. The write path SHALL validate Facebook support on the server and return authoritative readback. The rule configuration MUST remain a distinct domain record and MUST NOT be encoded as a `post`, `comment`, `contact_comment` or `join_group` mode, daily cap or hour-cell trigger. The all-platform summary MAY show that rule mode is enabled but MUST NOT expose an unsupported rule editor for other platforms.

The behaviour summary rendered for an account MUST describe the cadence that its stored rule definition actually encodes. It MUST NOT display a cadence taken from compiled-in constants when the stored definition differs.

#### Scenario: Facebook view exposes rule mode
- **WHEN** the operator filters account automation to Facebook
- **THEN** each Facebook row shows the fixed rule-mode toggle, behavior summary, both cadence tiers and authoritative runtime status

#### Scenario: Other platform views have no rule control
- **WHEN** the operator filters account automation to Xiaohongshu or WeChat Channels
- **THEN** no Facebook rule-mode control is rendered and a forged server write remains rejected

#### Scenario: Rule mode is not an hourly content action
- **WHEN** the account reaches the configured number of confirmed rule views outside any content-action hash minute
- **THEN** the rule round may be created from its count trigger without consuming or fabricating an hourly `content_schedule` fire key

#### Scenario: Join-contact frequency is reported as its own tier
- **WHEN** the operator inspects a Facebook account running rule mode
- **THEN** the view distinguishes the view-to-like tier from the round-to-join-contact tier and MUST NOT present a single combined counter
