## ADDED Requirements

### Requirement: Electron client prompts when the active account lacks persona
The Electron companion SHALL actively surface persona setup when the selected environment is logged in, connected to cloud, and the bound account has no persona. It MUST open the account persona dialog and emit a desktop notification once per unresolved environment/account condition. It MUST NOT repeatedly reopen the dialog on every status tick, and it MUST stop prompting once the account is bound or the environment changes.

#### Scenario: Unbound logged-in account opens persona dialog
- **WHEN** a selected environment reports `auth='logged in'`, `cloud='connected'`, and no `personaBound`
- **THEN** the client opens the account persona dialog for that environment and sends a desktop notification telling the operator to set the account persona

#### Scenario: Status ticks do not spam prompts
- **WHEN** the same unresolved environment/account continues to report unbound persona across repeated status updates
- **THEN** the client keeps at most one active prompt/notification for that unresolved condition

#### Scenario: Bound account suppresses setup prompt
- **WHEN** the selected environment reports `personaBound=true` or the user successfully persists a persona locally
- **THEN** the client closes the unresolved prompt state for that environment/account and MUST NOT auto-open the setup dialog

### Requirement: Persona wizard uses tone and content-preference panels
The Electron persona wizard SHALL present exactly two operator-facing selection panels before generation: `语气调性` first, followed by `内容偏好`. `语气调性` SHALL be the first panel in the scroll order. `内容偏好` SHALL group second-level interests under industry/category titles, using the category title as the section title and interest buttons as selectable options.

#### Scenario: Tone panel appears first
- **WHEN** the persona wizard is visible for an unbound ready account
- **THEN** the first selection panel is titled `语气调性`
- **AND** the content-preference panel appears below it

#### Scenario: Content preferences are grouped by industry
- **WHEN** the persona wizard renders content preferences
- **THEN** each industry/category title is rendered as a group header
- **AND** its second-level interests are rendered as selectable buttons under that title

#### Scenario: Recruitment category is first
- **WHEN** the content-preference panel renders
- **THEN** the first category is `招聘求职`
- **AND** it includes `骑手外卖`, `蓝领零工`, `数据标注`, `自有兼职`, and `在校实习`

### Requirement: Content-preference groups allow custom interests
Each content-preference group SHALL expose a `+` custom action. Activating it SHALL allow the operator to add one or more custom interests for that group. Custom interests MUST be visible as selectable chips in the same group, MUST participate in keyword collection for `persona.generate`, and MUST be bounded by the same input limits as other client-entered persona keywords.

#### Scenario: Add custom interest to a category
- **WHEN** the operator clicks `+` beside a content-preference group and enters a valid custom interest
- **THEN** that custom interest appears in that group as a selected preference
- **AND** generating persona includes the custom interest in `keywordSelections`

#### Scenario: Empty custom interest is ignored
- **WHEN** the operator opens a custom input but submits an empty or whitespace-only value
- **THEN** no custom chip is added and the existing selections remain unchanged

### Requirement: Browser permission prompts are handled honestly
The Electron shell SHALL install a permission request handler for browser permission prompts in the app window. Sensitive permissions that are not required for AIDCP automation, including geolocation, camera, microphone, MIDI/HID/serial/Bluetooth-style device access, SHALL be denied by default. The client SHALL surface a visible message or desktop notification when it denies such a permission, and MUST NOT report the page as successfully authorized.

#### Scenario: Geolocation request is denied and surfaced
- **WHEN** a loaded browser page requests geolocation permission through Electron
- **THEN** the app denies the request
- **AND** the operator receives a notification or visible message explaining that the permission was blocked

#### Scenario: Unknown sensitive permission fails closed
- **WHEN** a page requests an unrecognized permission not explicitly allowed by the client
- **THEN** the app denies the request rather than granting it silently
