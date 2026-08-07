# platform-browse-surface Specification

## Purpose
TBD - created by archiving change platform-registry-shape. Update Purpose after archive.
## Requirements
### Requirement: Note-scoped action support is declared per platform and gated at one point

The cloud registry MUST declare, for every platform, whether each note-scoped action (`read_content`, `like`, `collect`, `comment`, `comment_like`, `browse_images`, `scroll_comments`) is supported, as a fully-covered mapping so the type checker forces every cell to be stated. Every unsupported action MUST carry a non-empty reason. A single dispatch wrapper MUST be the only place that **gates dispatch** on this support: when an action is unsupported for the connected platform, the command MUST NOT be dispatched and the refusal MUST be audited with its reason. Support MUST NOT be inferred from numeric coincidence (for example a metric that happens to be zero).

Additional consumers MAY read the declaration **only for non-gating purposes** — for example projecting what the client is told it may do. Such a consumer MUST NOT dispatch, refuse, or cancel any command, MUST NOT be relied on as an enforcement point, and MUST NOT be the reason any refusal goes unaudited. Every non-gating consumer MUST fail open: a platform-resolution miss or a lookup exception MUST fall back to the behaviour that existed before that consumer was added, so a supported platform never loses capability because a read-only consumer's lookup failed.

#### Scenario: Facebook collect is refused explicitly, not by coincidence

- **WHEN** the interaction appraiser requests both a like and a collect for a Facebook note
- **THEN** the like is dispatched and the collect is refused at the single dispatch gate with its declared reason
- **AND** the refusal does not depend on Facebook's collect metric being zero

#### Scenario: Unsupported deep-read actions are not dispatched

- **WHEN** the platform declares `browse_images` or `scroll_comments` unsupported
- **THEN** those commands are never dispatched to the edge
- **AND** no round-trip or model call is spent producing a command that the edge would only reject

#### Scenario: A non-gating consumer reads the declaration without becoming a second gate

- **WHEN** a read-only consumer such as the client usage-cap projection reads note-scoped action support
- **THEN** it MAY shape what it reports to the client
- **AND** it MUST NOT dispatch, refuse, or cancel any command
- **AND** the single dispatch wrapper remains the only audited refusal point

#### Scenario: A non-gating consumer's lookup fails

- **WHEN** a non-gating consumer's platform resolution or support lookup misses or throws
- **THEN** it MUST fall back to the behaviour that existed before that consumer was added
- **AND** a supported platform never loses capability because a read-only lookup failed

### Requirement: Surface is a declared platform fact meaning whether an action leaves the list

The registry MUST declare, per platform, the surface (`feed` or `detail`) on which `read_content`, `like`, and `comment` are performed, where surface means whether orchestration must leave the list context. Surface MUST NOT encode page form (dialog, drawer, modal, overlay, profile are driver-internal details and MUST NOT be added to the surface set). Surface MUST be declared only for those three actions; actions that are unsupported or that ride on an already-opened detail reading chain MUST NOT be given a surface. A single pure resolver MUST be the only reader of these surface declarations.

#### Scenario: Xiaohongshu reads, likes, and comments all on detail

- **WHEN** the platform is Xiaohongshu
- **THEN** the surface resolver returns `detail` for read, like, and comment
- **AND** loop closure and comment-migration decisions read this static value

### Requirement: Loop closure and comment migration are driven by the static table, not runtime inference

The decision to return to the list with a back command versus continuing with a scroll, and the decision to trigger a comment migration, MUST be computed from the static surface resolver plus a per-note migration flag that the cloud sets when it emits a migration command. The observed-surface echo MUST be audit-only and MUST NOT drive any control-flow branch. Because Xiaohongshu declares read on detail and its comment surface equals its read surface, its loop closure MUST always be a back command and a comment migration MUST be structurally unreachable, independent of the order in which edge reports arrive.

#### Scenario: Xiaohongshu loop closure is order-independent

- **WHEN** a `page.cards` report interleaves between a Xiaohongshu `note.detail` and the next `feed.entered`
- **THEN** the closure command is still a back command
- **AND** the outcome does not depend on which report arrived first

### Requirement: Deep-read short-circuit is injected, fail-open, and honest

Roles MUST learn platform support only through injected closures, never by importing the registry or branching on a platform literal. When a deep-read sub-action is unsupported, the role MUST take its existing else branch and report the truthful outcome (for example zero images browsed with a reason), never fabricating success. The injected closures MUST fail open: when the registry lookup is missing or throws, the closure MUST return true so the platform behaves as it does today, never silently disabling a supported platform.

#### Scenario: Registry miss does not disable a supported platform

- **WHEN** the deep-read support closure cannot resolve a registry entry or throws
- **THEN** it returns true and the deep-read command is still dispatched as today
- **AND** no platform is silently downgraded

#### Scenario: Unsupported deep-read is reported honestly

- **WHEN** `browse_images` is unsupported for the connected platform
- **THEN** the role emits its images-done event with zero images browsed and a reason
- **AND** it does not call the model or claim images were viewed

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

### Requirement: Action receipts derive their note id from the acted-upon DOM

An action-completed receipt's note id MUST be derived from the actual acted-upon article's DOM as a canonical post id, and MUST NOT be copied from the command payload. When the receipt carries no note id, a detail-context receipt falls back to the session's current note id (today's behavior), while a feed-surface receipt with no note id MUST be refused for accounting rather than attributed to the current note. A navigate-purpose open MUST NOT report a decision note.detail and MUST NOT overwrite real reaction counts with zero.

#### Scenario: Feed-surface receipt without a derived note id is refused

- **WHEN** the connected edge declares feed-surface targeting and returns an action receipt with no derived note id
- **THEN** the cloud refuses to account the action and audits it
- **AND** it does not attribute the action to the session's current note

### Requirement: Interaction attribution is arbitrated by independent witness

The cloud MUST arbitrate interaction attribution by comparing the receipt's independent observation (author, leading text, reaction text) against the selected feed card field by field, not by comparing a note id to itself. A witness mismatch MUST yield a target-mismatch outcome that refuses to write interaction lineage and increments a grayscale rollback counter, while risk still counts the real occurrence. A stale no-target MUST be treated as an expired snapshot: the post id leaves the session candidates and cards are rescanned and reselected, and it MUST NOT be counted as an interaction-quota failure.

#### Scenario: Independent witness catches a wrong-card like in shadow

- **WHEN** a shadow like receipt's observed author and leading text do not match the selected card
- **THEN** the cloud records target-mismatch and refuses to write lineage
- **AND** it does not treat a returned note id equal to the command as proof of correctness

### Requirement: Comment migration is receipt-driven and fail-closed

When the comment surface differs from the read surface, the cloud MUST migrate to detail in two receipt-driven steps: emit a navigate-purpose open, wait for its action-completed with a detail-surface observation and matching note id, and only then emit the comment. If the navigate step fails, the cloud MUST NOT emit the comment and MUST report the approved-not-delivered comment to the operator. When the comment surface equals the read surface, migration MUST be structurally unreachable and no extra open is emitted.

#### Scenario: Navigate failure does not send the approved comment elsewhere

- **WHEN** the navigate-purpose open for an approved comment fails to land on the target detail
- **THEN** the comment is not emitted on the current page
- **AND** the approved-not-delivered comment is reported to the operator

### Requirement: Exhausted feed self-heals and approvals do not scroll the account away

An exhausted-feed receipt MUST be mapped immediately to a refresh so the session does not fall idle into the watchdog nudge loop. While a human approval is in flight, idle nudges MUST be suppressed by a session flag set by the approval gate and gated in the dispatcher's idle-nudge translation, without reusing the pause-clock mechanism, so the account is not scrolled off the target while waiting.

#### Scenario: In-flight approval is not nudged off target

- **WHEN** an idle nudge fires while a comment approval is awaiting the operator
- **THEN** the nudge is not translated into a scroll
- **AND** the account remains on the target rather than being scrolled away

### Requirement: Orchestration capability words gate role registration and fail open

The orchestration capability matrix MUST include `follow`, `profile_visit`, `patrol`, `notification`, and `group_join`. No capability word may remain declared without a wired consumer.

For `follow`, `profile_visit`, `patrol`, and `notification` the consumer is **gating**: role registration in the dispatcher setup MUST be gated by these capabilities so a platform that does not support patrol or notification does not register the patrol roles, and a platform that does not support follow or profile visits does not register the author-evaluation and follow roles. That gate MUST fail open: only an explicit unsupported declaration skips registration, while a missing entry or a lookup exception registers as today, so a supported platform's patrol is never silently dropped on a lookup failure.

A capability word MAY instead have a **non-gating** consumer — a read-only projection of what the client is told about the account, such as which usage metrics it is shown. `group_join` is such a word: it is read only to decide whether the account is shown a group-join metric, and joining itself continues to be actuated and gated on its own dedicated path. A non-gating consumer MUST NOT dispatch, refuse, or cancel any command, MUST NOT be relied on as an enforcement point, and MUST NOT be the reason any refusal goes unaudited. Declaring a word whose only consumer is non-gating MUST NOT introduce a second gate on that action.

A non-gating consumer MUST preserve the status quo when it cannot decide, and the direction of that fail-safe depends on what the status quo is. Where the consumer's behaviour today is to act, a lookup miss or exception MUST act as today. Where the consumer's behaviour today is not to act — as for a capability word introduced together with the surface that reads it — only an explicit supported declaration may cause it to act, and a lookup miss or exception MUST NOT. Reusing a fail-open-to-supported lookup for such a word is a defect: it would let an unresolvable platform be granted a capability it does not have.

#### Scenario: Facebook does not register patrol roles

- **WHEN** a Facebook session starts and Facebook declares patrol and notification unsupported
- **THEN** the patrol roles are not registered for that connection
- **AND** the capability words are actually read, not merely declared

#### Scenario: Xiaohongshu still registers all patrol roles

- **WHEN** a Xiaohongshu session starts
- **THEN** all patrol roles and the author-evaluation and follow roles register as before
- **AND** a capability lookup miss or exception still registers them rather than dropping them

#### Scenario: The group-join word is read but gates nothing

- **WHEN** the client usage projection reads `group_join` for a Facebook account and finds it supported
- **THEN** the account is shown a group-join metric
- **AND** no command is dispatched, refused, or cancelled on account of that read
- **AND** the join scheduler's own path remains the only place that decides whether a join is actuated

#### Scenario: An unresolvable platform is not granted group joining

- **WHEN** the client usage projection cannot resolve an account's platform, or the `group_join` lookup throws
- **THEN** the account is not shown a group-join metric
- **AND** the projection does not fall back to treating the capability as supported, because a platform that cannot be identified has not declared that it has groups

