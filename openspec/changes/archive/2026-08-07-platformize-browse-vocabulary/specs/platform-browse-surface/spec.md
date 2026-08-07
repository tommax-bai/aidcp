## MODIFIED Requirements

### Requirement: Adding a platform must not require changing shared orchestration

Onboarding a new platform MUST NOT change any of: the role-name enumeration, the risk controller or its state machine, the pacing center-value algorithm, or any orchestration role code and the dispatcher event-translation layer. Onboarding SHALL consist of: a registry entry (with the type checker forcing every support and surface cell to be stated), extending the platform id union, implementing the edge driver/session/executors, running real-machine probes, **and declaring the platform's own command set under its platform-segment prefix** — new `MessageType` entries, combination-table rows in the command bridge, edge active-command allowlist entries, and operation-registry descriptors. These command declarations are additive, exhaustively typed against the two protocol copies, and MUST NOT alter any other platform's declarations or any shared-name command semantics.

#### Scenario: A new platform is a registry entry plus an edge driver plus its command declarations

- **WHEN** a new platform is onboarded
- **THEN** the change is limited to a new registry entry, the platform id union, edge driver/session/executor code plus probes, and additive platform-segment command declarations (protocol types, bridge rows, allowlist entries, registry descriptors)
- **AND** no orchestration role code, risk, pacing, or event-translation code is modified, and no other platform's command declarations change

### Requirement: Surface and purpose ride existing messages as optional fields

The protocol MUST carry read surface and open purpose as optional fields on the note-open messages and MUST carry a derived note id and an independent observation packet as optional fields on the action-completed message. The page-cards message MAY additionally carry optional list-kind (`feed` or `reels`) and list-state (`ready` or `empty`) observations; omission MUST default to ready feed behavior.

The **list form a scroll command addresses** is carried by the command name's surface segment (`feed` / `search` / `reels`, e.g. `facebook.reels.scroll`), not by a payload field; the former `targetSurface` payload field MUST NOT be reintroduced. The `feed/detail` Surface union is a distinct concept whose sole meaning remains whether an action leaves the list context; `reels` and `search` are list forms and MUST NOT be added to that union. Loop closure, comment migration, support gating, and risk logic MUST NOT branch on the list-kind observation.

#### Scenario: Reels list form does not become a control-flow surface
- **WHEN** page-cards observes `listKind:reels` while a Facebook note is read in place
- **THEN** note-open still uses `surface:feed`
- **AND** loop closure, comment migration, support gating, and risk logic do not branch on the list-kind observation

#### Scenario: Scroll list form is declared by name, not payload
- **WHEN** the cloud commands scrolling on a Reels or search results list
- **THEN** the list form is expressed by the command name's surface segment
- **AND** no payload field duplicates that dimension

#### Scenario: Empty observation is narrow and optional
- **WHEN** page-cards carries `listKind:feed`, `listState:empty`, and zero cards
- **THEN** only the Facebook empty-home fallback consumer may translate that observation into the existing fallback command
- **AND** old consumers may ignore both optional fields without protocol failure
