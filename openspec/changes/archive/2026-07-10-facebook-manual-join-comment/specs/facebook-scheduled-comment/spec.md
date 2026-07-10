## MODIFIED Requirements

### Requirement: Facebook scheduled comments are disabled by default and fail closed

Facebook scheduled commenting SHALL be controlled by a global kill switch that defaults off. When disabled, missing, invalid, or explicitly false, no UNATTENDED trigger path (the background content schedule, or a plain `/comment <昵称>` command without `--join`) MUST post, record risk/cooldown, or claim work occurred.

The SINGLE exception is a human-authorized manual join-then-comment (`/comment <昵称> --join`), whose comment is PINNED to the account's own just-joined group (from the membership ledger): it MAY compose, submit, and record a comment on that pinned group while the unattended kill switch is off, because the operator's command is the explicit authorization. This exception MUST still enforce every other gate — hard validators, server-confirmed verification, the contact human-review approval lane when `--contact` is present, the per-account risk quota and daily cap, the persona gate, and single-flight — and MUST NOT silently claim success. The exception is scoped ONLY to the group just joined by that command; it MUST NOT enable unattended commenting on operator-configured or other joined containers.

Per-account `accounts.status` and platform matching MUST also gate work.

#### Scenario: Default off prevents posting
- **WHEN** the cloud process starts without enabling the Facebook comment automation switch
- **THEN** no Facebook scheduled comment is posted or risk-recorded, even if Facebook accounts and targets exist

#### Scenario: Paused account is skipped
- **WHEN** a Facebook account has `accounts.status='paused'`
- **THEN** the scheduled trigger skips it and does not dispatch browse/comment work

#### Scenario: Human-authorized manual join-comment may post while the unattended switch is off
- **WHEN** the unattended Facebook-comment kill switch is off, an operator issues `/comment <昵称> --join` from a management chat, and the account confirms a join into new group G
- **THEN** the pinned comment on group G MAY be composed, validated, submitted, and server-verified
- **AND** a plain `/comment <昵称>` (no `--join`) for the same account still no-ops under the off switch, and no OTHER container becomes eligible for unattended commenting

## ADDED Requirements

### Requirement: A pinned just-joined group is a valid comment container with keywords from account config

The Facebook comment pipeline SHALL accept, for a human-authorized manual join-then-comment, a container PINNED to a single just-joined group URL supplied by the caller, in place of choosing from the operator-configured container list or the LRU coverage window. Keywords SHALL still come from the account's Facebook comment configuration; if the account has no configured keywords the pinned path MUST fail closed with an honest no-targets outcome (never whole-site search, never a blind post). The pinned path SHALL update the membership ledger's coverage bookkeeping for that group (mark-commented on verified success; the existing left/inaccessible signal on the relevant failures), exactly as the coverage loop does.

#### Scenario: Pinned container overrides config selection
- **WHEN** a manual join-then-comment supplies just-joined group G as the pinned container
- **THEN** the pipeline searches inside G (not a config-listed or LRU-selected container) and runs the unchanged compose/validate/server-verify path

#### Scenario: Pinned path with no keywords is an honest no-op
- **WHEN** the account has no configured Facebook keywords
- **THEN** the pinned comment step returns an honest no-targets outcome and does not search whole-site or post a blind comment

#### Scenario: Verified pinned comment updates the ledger
- **WHEN** a pinned comment on group G is server-confirmed as posted
- **THEN** the membership row for (account, G) records the coverage timestamp/count, consistent with the background coverage loop
