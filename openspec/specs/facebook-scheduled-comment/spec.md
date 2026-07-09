# facebook-scheduled-comment Specification

## Purpose
TBD - created by archiving change facebook-scheduled-comment. Update Purpose after archive.
## Requirements
### Requirement: Facebook scheduled comments are disabled by default and fail closed

Facebook scheduled commenting SHALL be controlled by a global kill switch that defaults off. When disabled, missing, invalid, or explicitly false, no trigger path (scheduled or Feishu-command) MUST post, record risk/cooldown, or claim work occurred. Per-account `accounts.status` and platform matching MUST also gate work.

#### Scenario: Default off prevents posting
- **WHEN** the cloud process starts without enabling the Facebook comment automation switch
- **THEN** no Facebook scheduled comment is posted or risk-recorded, even if Facebook accounts and targets exist

#### Scenario: Paused account is skipped
- **WHEN** a Facebook account has `accounts.status='paused'`
- **THEN** the scheduled trigger skips it and does not dispatch browse/comment work

### Requirement: Facebook comments trigger through existing comment entry points routed by account platform

Facebook automatic comments SHALL be triggered through the existing schedule-driven comment entry point (per-account comment schedule with its daily cap) and the existing Feishu `/comment` command entry point; a separate Facebook-specific cron MUST NOT be added. Both entry points SHALL resolve the account platform through the account store (`accounts.platform`) and route Facebook accounts to the Facebook targeted-comment pipeline. For each account the pipeline SHALL read an operator-configured keyword list and an operator-configured container list (the operator's own / joined Pages and Groups), pick a keyword at random, and search ONLY within one configured container, then pick a candidate post from the in-container results (bounded extraction). It MUST NOT perform whole-site Facebook search and MUST NOT comment on posts outside the configured containers. Missing keywords OR missing containers produce an honest no-op result.

#### Scenario: Schedule trigger routes by platform
- **WHEN** the content schedule fires a comment action for an account with `accounts.platform='facebook'`
- **THEN** the comment pipeline uses the Facebook platform profile and the targeted pipeline, not the xhs search loop

#### Scenario: No configured keywords or containers yields no-op
- **WHEN** a Facebook account is active but has no configured keywords, or no configured containers (Pages/Groups)
- **THEN** the trigger records/returns a no-targets outcome and does not search whole-site or browse random Facebook surfaces

#### Scenario: Search stays within configured containers
- **WHEN** the pipeline picks a random keyword for a Facebook account
- **THEN** it searches only inside one of the operator-configured containers and never performs a whole-site search, and any candidate post outside the configured containers is not commented on

### Requirement: Shadow mode runs to validation without posting or recording

Shadow mode SHALL execute target selection, composition, and deterministic validation, but MUST NOT submit the comment, mark cooldown, record risk, dedupe as posted, or report `commented`. Shadow output SHALL be logged/auditable without secrets.

#### Scenario: Shadow candidate does not post
- **WHEN** shadow mode produces a valid candidate comment
- **THEN** the system logs the target/text/validator result safely and does not call the edge submit capability or record risk

### Requirement: Unattended Facebook composition uses hard validators

Facebook scheduled comments SHALL run deterministic validators after LLM composition and before any submit attempt. Validators MUST reject URLs/bare domains, phone/email/WeChat-like contact info, `@mention`, platform-specific length violations, spammy English phrases, empty/low-signal text, and weak target relevance. Rejected text MUST produce `compose_skipped`; the system MUST NOT auto-fix then post.

#### Scenario: URL is rejected
- **WHEN** the composed Facebook comment contains a URL or bare domain
- **THEN** validators reject it with `compose_skipped`, and no submit occurs

#### Scenario: Validator reject is not repaired into post
- **WHEN** a validator rejects the LLM output
- **THEN** the system does not call another fixer that can still post in the same attempt

### Requirement: Facebook post success requires server-confirmed verification

Facebook comment execution SHALL report success only when it can verify a server-confirmed comment on the intended target post, scoped by own identity and text fragment. Acceptable confirmation includes a comment permalink/id or delayed reload/requery proof that the comment remains on the target post. Editor clearing, local optimistic row insertion, or comment-count changes alone MUST NOT count as success. Ambiguous or missing confirmation returns a non-success reason.

#### Scenario: Optimistic DOM alone is not success
- **WHEN** Facebook locally renders a new comment row immediately after submit but no server-confirmed id/permalink or delayed persistence is verified
- **THEN** edge MUST NOT report `ok:true`; it reports an honest non-success outcome such as `state_unchanged` or `verification_ambiguous`

#### Scenario: Verified server comment reports success
- **WHEN** the submitted comment is confirmed by permalink/id or delayed requery on the target post matching own identity and text
- **THEN** edge reports `ok:true` and cloud may record risk/cooldown

### Requirement: Every Facebook failure point has an honest non-commented outcome

Facebook scheduled commenting SHALL distinguish and surface non-success outcomes including kill switch off, account paused, platform mismatch, no targets, login required, checkpoint/blocked, no strong candidate, validator rejection, quota denied, cooldown denied, submit no target, and verification ambiguous. None of these outcomes may be recorded as `commented`.

#### Scenario: Login required is not no candidate
- **WHEN** a Facebook profile is logged out when a scheduled comment attempt runs
- **THEN** the result is login-required/blocking, not `no_strong_candidate` or `commented`

#### Scenario: Verification ambiguous is not success
- **WHEN** the comment submit cannot be verified after bounded attempts
- **THEN** the result is non-success and no risk/cooldown success record is written

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

### Requirement: Facebook comments are composed after reading the target post and its discussion

Facebook automatic comment composition SHALL happen AFTER the target post is opened, using the post's caption (when present) and a bounded sample of other people's comments as context. The composer MUST write in the same language as the post/comment content (the local content language), and MUST NOT default to the interface language when it differs. The comment SHALL respond to the actual discussion rather than being written blind from a keyword alone. The edge MUST report the caption and comment samples honestly (empty when a photo post has no caption; never fabricated). The deterministic relevance check SHALL treat the keyword plus the post caption and comments as the relevance context.

#### Scenario: Comment matches the content language, not the UI language
- **WHEN** a target post and its comments are in a non-Chinese language (e.g. Spanish) while the account's Facebook interface language is Chinese
- **THEN** the composed comment is written in the content language (Spanish), not Chinese

#### Scenario: Compose reads the post before writing
- **WHEN** an automatic Facebook comment is composed
- **THEN** the post is opened and its caption + other-people comments are read first, and the composer receives them as context (it is not written blind from the keyword alone)

#### Scenario: Photo post with no caption still composes from the discussion
- **WHEN** the target is a photo post with no text caption
- **THEN** the edge reports an empty caption (never fabricated) and the composer grounds the comment in the other-people comments and persona

### Requirement: Shadow mode is a read-only browse that never submits

Shadow mode SHALL perform the read-only steps needed to compose (search and open the target post to read its caption and comments) and run composition + validators, but MUST NOT submit a comment, record risk/cooldown, dedupe as posted, or report `commented`. It MUST NOT dispatch the comment-submit command.

#### Scenario: Shadow browses read-only but never submits
- **WHEN** shadow mode runs for a Facebook account
- **THEN** it may dispatch search and open (read-only) to read the post, composes and validates a candidate, and audits `shadow_ok` — but never dispatches the comment-submit command and never records success

