## MODIFIED Requirements

### Requirement: Admin destinations SHALL be organized into stable business groups

The admin console SHALL present every route whose shared metadata has `showInNav=true` under six ordered groups: Overview contains Data; Accounts contains Accounts, Environments, WeChat Strategy, and Facebook Groups; Content contains Content, Publish Queue, Curated, and Schedule; Interaction contains Interaction Contacts and Notification Routes; AI Configuration contains Persona and Roles; System contains Safety, Mode Policies, Usage, and Client Users. Mode Policies SHALL route to `/mode-policies` and SHALL be the only global numeric editor for Facebook rule mode and slow start. Adding this destination MUST NOT remove, hide or relocate an existing visible destination.

#### Scenario: Desktop operator scans the primary navigation

- **WHEN** an authenticated operator views the console at desktop width
- **THEN** the first header row presents the six labelled groups instead of a flat destination strip

#### Scenario: Operator selects a group

- **WHEN** the operator hovers over or activates a multi-destination group
- **THEN** a compact floating menu presents every labelled destination in that group without changing the header height or moving page content

#### Scenario: Operator uses the single-destination Overview group

- **WHEN** the operator activates Overview
- **THEN** the console navigates directly to Data without opening a redundant one-item menu

#### Scenario: Operator opens mode policies

- **WHEN** the operator selects Mode Policies from System
- **THEN** the console opens `/mode-policies` and exposes only the internal global numeric policy workflow

### Requirement: Narrow navigation SHALL keep every destination readable and reachable

Below the narrow layout breakpoint, the console SHALL replace the desktop group strip with a labelled grouped navigation trigger. The opened menu MUST expose every shared route whose metadata has `showInNav=true` with text under its owning group; it MUST NOT rely on an icon-only strip or a separately maintained fixed-count list.

#### Scenario: Header enters narrow layout

- **WHEN** the available width crosses below the narrow breakpoint
- **THEN** the desktop group navigation is hidden and a labelled current-location trigger is visible

#### Scenario: Operator opens the narrow menu

- **WHEN** the operator activates the narrow navigation trigger
- **THEN** every current `showInNav=true` destination, including Environments, Publish Queue and Mode Policies, is reachable under the six group headings
