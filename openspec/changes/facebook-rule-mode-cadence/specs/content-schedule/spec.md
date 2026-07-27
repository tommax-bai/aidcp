## ADDED Requirements

### Requirement: Unified account automation exposes Facebook rule mode without treating it as a content action

The unified account automation catalog and Facebook-filtered view SHALL expose the account's fixed rule-mode configuration, effective mode, collecting progress and latest batch summary. The write path SHALL validate Facebook support on the server and return authoritative readback. The rule configuration MUST remain a distinct domain record and MUST NOT be encoded as a `post`, `comment`, `contact_comment` or `join_group` mode, daily cap or hour-cell trigger. The all-platform summary MAY show that rule mode is enabled but MUST NOT expose an unsupported rule editor for other platforms.

#### Scenario: Facebook view exposes rule mode
- **WHEN** the operator filters account automation to Facebook
- **THEN** each Facebook row shows the fixed rule-mode toggle, behavior summary and authoritative runtime status

#### Scenario: Other platform views have no rule control
- **WHEN** the operator filters account automation to Xiaohongshu or WeChat Channels
- **THEN** no Facebook rule-mode control is rendered and a forged server write remains rejected

#### Scenario: Rule mode is not an hourly content action
- **WHEN** the account reaches ten confirmed rule views outside any content-action hash minute
- **THEN** the rule batch may be created from its count trigger without consuming or fabricating an hourly `content_schedule` fire key

### Requirement: Facebook rule mode inherits only the effective weekly active window

Rule-mode session start, resume and safe stop SHALL use the same account-effective weekly active window as normal browsing. Rule mode MUST NOT require the content-active mask, a content action mode, daily content cap or per-action hash-minute offset. Slow-start precedence, account pause and all runtime gates remain additional independent conditions.

#### Scenario: Active browse cell permits counting
- **WHEN** a Facebook account has rule mode enabled, slow start is not active and its effective weekly active cell is active
- **THEN** the account may start or resume rule browsing subject to the remaining admission gates

#### Scenario: Content mask does not authorize sleeping browse
- **WHEN** a content-active cell is set but the account's effective weekly active cell is sleeping
- **THEN** rule mode does not start or count views

#### Scenario: Content action off does not disable rule mode
- **WHEN** all scheduled `post`, `comment`, `contact_comment` and `join_group` modes are off but the Facebook rule and weekly active cell are enabled
- **THEN** rule browsing may run because its count trigger is independent of content action scheduling
