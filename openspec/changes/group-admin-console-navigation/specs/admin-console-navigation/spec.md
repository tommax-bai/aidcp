## ADDED Requirements

### Requirement: Admin destinations SHALL be organized into stable business groups
The admin console SHALL present the existing visible destinations under six ordered groups: Overview contains Data; Accounts contains Accounts, WeChat Strategy, and Facebook Groups; Content contains Content, Curated, and Schedule; Interaction contains Interaction Contacts and Notification Routes; AI Configuration contains Persona and Roles; System contains Safety, Usage, and Client Users.

#### Scenario: Desktop operator scans the primary navigation
- **WHEN** an authenticated operator views the console at desktop width
- **THEN** the first header row presents the six labelled groups instead of fourteen flat destination buttons

#### Scenario: Operator selects a group
- **WHEN** the operator opens or navigates to a destination in a group
- **THEN** the second header row presents every labelled destination in that group

### Requirement: Navigation context SHALL follow the current route
The console SHALL visibly identify both the owning group and visible destination for exact and nested routes, using path-boundary matching so similar prefixes do not activate multiple destinations.

#### Scenario: Direct destination URL loads
- **WHEN** the operator opens an existing destination URL directly
- **THEN** its owning primary group and its secondary destination are active

#### Scenario: Nested destination URL loads
- **WHEN** the operator opens a nested path below a visible destination
- **THEN** the owning group and destination remain active

#### Scenario: Similar route prefixes are present
- **WHEN** the current path is `/content-schedule`
- **THEN** Schedule is active and Content is not active

#### Scenario: Settings route loads
- **WHEN** the operator opens `/settings`
- **THEN** the independent Settings action is active and the System group remains the navigation context

### Requirement: Narrow navigation SHALL keep every destination readable and reachable
Below the narrow layout breakpoint, the console SHALL replace the desktop group and destination rows with a labelled grouped navigation trigger. The opened menu MUST expose every visible destination with text under its owning group; it MUST NOT rely on an icon-only strip.

#### Scenario: Header enters narrow layout
- **WHEN** the available width crosses below the narrow breakpoint
- **THEN** the desktop navigation rows are hidden and a labelled current-location trigger is visible

#### Scenario: Operator opens the narrow menu
- **WHEN** the operator activates the narrow navigation trigger
- **THEN** all fourteen destination labels are reachable under the six group headings

### Requirement: Existing routes and independent actions SHALL remain stable
The navigation redesign SHALL NOT change existing destination URLs. Download, Settings, and User actions SHALL remain independent header actions, and route definitions plus all navigation surfaces SHALL continue to derive from shared route metadata.

#### Scenario: Operator follows an existing bookmark
- **WHEN** an operator follows any existing admin destination URL after deployment
- **THEN** the same page loads without a navigation migration or redirect introduced by this change

#### Scenario: Operator uses a header action
- **WHEN** the operator uses Download, Settings, or User controls
- **THEN** the control remains available outside the grouped business navigation

#### Scenario: A visible route is registered
- **WHEN** the navigation catalog is validated
- **THEN** every visible route belongs to exactly one known group and appears in the derived desktop and narrow navigation models
