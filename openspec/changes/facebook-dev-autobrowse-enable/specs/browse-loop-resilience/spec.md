## ADDED Requirements

### Requirement: Facebook deep-read failures retain canonical recovery semantics

When a Facebook browse session receives a cloud-dispatchable deep-read, interaction, refresh, or notification command that it cannot execute, it SHALL return `action.completed` with the canonical orchestration action name and `ok:false` with an honest reason. The cloud ingress SHALL normalize legacy protocol-message action names before publishing the completion to session roles. A failed `browse_images` or `scroll_comments` completion SHALL advance the corresponding reader stage rather than being treated as an unknown failure.

#### Scenario: Unsupported image browse exits the detail flow
- **WHEN** the cloud sends `note.browse_images` to a Facebook edge that does not implement image browsing
- **THEN** the edge reports `action.completed { action: 'browse_images', ok: false, reason: 'capability_unsupported' }`
- **AND** DeepReader advances with zero images browsed so the normal return-to-list path can run

#### Scenario: Legacy dotted completion remains safe
- **WHEN** an older edge reports `action.completed { action: 'note.scroll_comments', ok: false }`
- **THEN** cloud normalizes the action to `scroll_comments` before session roles consume it
- **AND** the dispatcher does not issue a fallback feed scroll from the current detail page

### Requirement: Facebook scroll verifies the active list context

Before Facebook edge executes a feed scroll, it SHALL ensure the currently remembered list context is active. The remembered context SHALL be the main feed after normal entry/return and the search-results URL after a browse search. If it cannot restore that context, it SHALL report an honest failed scroll and SHALL NOT report page cards from a detail page.

#### Scenario: Detail-page recovery returns to search results
- **WHEN** a browse search opened a detail page and cloud subsequently asks for `page.scroll`
- **THEN** the edge restores that search-results URL before scanning or scrolling
- **AND** it does not redirect the search browse session to the homepage
