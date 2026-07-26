## MODIFIED Requirements

### Requirement: Surface and purpose ride existing messages as optional fields

The protocol MUST carry read surface and open purpose as optional fields on the existing note-open message and MUST carry a derived note id and an independent observation packet as optional fields on the existing action-completed message. The existing page-cards message MAY additionally carry optional list-kind (`feed` or `reels`) and list-state (`ready` or `empty`) observations; omission MUST default to today's ready feed behavior. `reels` is a list form and MUST NOT be added to the `feed/detail` Surface union, whose sole meaning remains whether an action leaves the list context. No new message type may be introduced and the active-command allowlist MUST NOT change.

#### Scenario: Old edge and old cloud are unchanged
- **WHEN** note-open, action-completed, and page-cards omit all new optional fields
- **THEN** behavior is identical to before this change
- **AND** the message-type count, active-command allowlist, and `feed/detail` Surface union are unchanged

#### Scenario: Reels list form does not become a control-flow surface
- **WHEN** page-cards observes `listKind:reels` while a Facebook note is read in place
- **THEN** note-open still uses `surface:feed`
- **AND** loop closure, comment migration, support gating, and risk logic do not branch on the list-kind observation

#### Scenario: Empty observation is narrow and optional
- **WHEN** page-cards carries `listKind:feed`, `listState:empty`, and zero cards
- **THEN** only the Facebook empty-home fallback consumer may translate that observation into the existing fallback command
- **AND** old consumers may ignore both optional fields without protocol failure
