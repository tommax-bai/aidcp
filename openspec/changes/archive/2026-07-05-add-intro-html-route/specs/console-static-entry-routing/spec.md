## ADDED Requirements

### Requirement: Legacy Intro Entry Route

The console SPA SHALL support `/intro.html` as a legacy entry alias for the
authenticated management console. When an unauthenticated operator opens
`/intro.html`, the app MUST route through the normal login flow. When an
authenticated operator opens `/intro.html`, the app SHALL land on the canonical
console home route instead of rendering an application 404. The alias MUST NOT
appear in the top business navigation.

#### Scenario: Unauthenticated intro entry uses login flow

- **WHEN** an unauthenticated operator opens `/intro.html`
- **THEN** the console routes to `/login` using the same authentication guard as other protected routes
- **AND** it does not render an application-level 404

#### Scenario: Authenticated intro entry lands on home

- **WHEN** an authenticated operator opens `/intro.html`
- **THEN** the console redirects to the canonical home route `/`
- **AND** the standard console shell and navigation render

#### Scenario: Intro entry stays hidden from navigation

- **WHEN** the console top navigation is rendered
- **THEN** no visible business navigation item links to `/intro.html`
