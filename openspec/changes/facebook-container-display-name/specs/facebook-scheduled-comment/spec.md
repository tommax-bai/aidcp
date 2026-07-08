## ADDED Requirements

### Requirement: Facebook comment containers are identified to humans by group name, never by id

A Facebook comment container SHALL store a functional key (the group/page URL, which contains the numeric id) AND a human-readable name. The name SHALL be the container's real group/page name, auto-resolved by the edge from the container page (reported back to cloud, which persists it against the matching URL). Every human-facing surface (management console, audit rows, Feishu receipts) SHALL display the group name; when a name has not yet been resolved it SHALL show a neutral placeholder (e.g. "待识别"). Surfaces MUST NOT display the raw group id / URL to humans. When the edge cannot read a name it MUST return no name (honest), and cloud MUST NOT fabricate a name from the id. Legacy bare-URL container configuration MUST be accepted (coerced to a URL with an unresolved name) for backward compatibility.

#### Scenario: Group id is never shown to humans
- **WHEN** an operator views a configured Facebook container in the console (or an audit row / Feishu receipt references it) and the container's real name has been resolved
- **THEN** the surface shows the group name (e.g. "Puerto Rico Y Sus Encantos e Historia") and never the raw group id or URL

#### Scenario: Name auto-resolves from the container page
- **WHEN** a Facebook comment run searches inside a configured container and the edge reads the container's real name from the group page
- **THEN** the edge reports the name with its `page.cards`, and cloud persists it against the matching container URL so subsequent human-facing surfaces show the group name

#### Scenario: Unresolved name shows a placeholder, never the id
- **WHEN** a container has been configured (URL pasted) but its real name has not yet been resolved
- **THEN** human-facing surfaces show a neutral placeholder ("待识别"), not the group id / URL

#### Scenario: Unreadable name is honest, never fabricated
- **WHEN** the edge cannot read a container's real name from the page
- **THEN** it returns no name and cloud leaves the stored name unresolved (never derives a display name from the id)
