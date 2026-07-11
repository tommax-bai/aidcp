# facebook-scheduled-comment Specification

## Purpose
TBD - created by archiving change facebook-scheduled-comment. Update Purpose after archive.
## Requirements
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

**Operator `--force` override (change manual-comment-force-flag)**: only when the Feishu manual command carries `--force`, the **relevance** check (`weak_relevance`) SHALL be skipped for that run (implemented by passing an empty relevance context so the relevance branch is a no-op). The `--force` override MUST NOT relax any **content-safety** validator: URLs/bare domains, contact info, `@mention`, length violations, spam phrases, and empty/low-signal text MUST still reject with `compose_skipped`, and the system MUST still not auto-fix then post. `--force` is carried only from the manual command entry point; automatic/scheduled/shadow paths MUST keep enforcing `weak_relevance`.

#### Scenario: URL is rejected
- **WHEN** the composed Facebook comment contains a URL or bare domain
- **THEN** validators reject it with `compose_skipped`, and no submit occurs

#### Scenario: Validator reject is not repaired into post
- **WHEN** a validator rejects the LLM output
- **THEN** the system does not call another fixer that can still post in the same attempt

#### Scenario: `--force` skips relevance but not content-safety
- **WHEN** an operator runs `/comment <acct> --force` for a Facebook account and the composed comment has zero keyword overlap with the target post but contains a URL or contact info
- **THEN** the `weak_relevance` check is skipped, but the comment MUST still be rejected with `compose_skipped` for the URL/contact violation (content-safety validators are not overridden)

#### Scenario: Automatic path still enforces relevance
- **WHEN** the automatic/scheduled Facebook comment path composes a comment with zero relevance overlap (no `--force` present)
- **THEN** validators MUST reject it with `weak_relevance` → `compose_skipped` (the override signal is absent on automatic paths)

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

### Requirement: Facebook coverage mode is gated by a global switch for all accounts

Facebook joined-group coverage commenting SHALL be enabled by a single global switch that, when on, applies to EVERY Facebook account (no per-account allowlist required). The switch MUST default off in code so a fresh environment does not silently enable coverage for all accounts; it is turned on explicitly per environment. A legacy per-account allowlist MAY still narrow coverage to specific accounts when the global switch is off (backward-compatible), but MUST NOT be required when the global switch is on. When neither the global switch nor the allowlist selects an account, that account MUST NOT use coverage mode (it falls back to operator-configured containers), preserving prior behavior. The global switch MUST be reversible (turning it off returns to allowlist-only, or fully off).

#### Scenario: Global switch on enables coverage for every account
- **WHEN** the global coverage switch is on and a Facebook account is not in any allowlist
- **THEN** that account's scheduled comments use joined-group coverage selection (subject to the daily cap and the always-on human review)

#### Scenario: Global switch off preserves prior gating
- **WHEN** the global coverage switch is off
- **THEN** only accounts in the legacy allowlist use coverage mode, and all other accounts fall back to operator-configured containers exactly as before this change

### Requirement: Coverage-mode comment target selection relaxes timing as a review-gated fallback

When Facebook coverage mode is enabled for an account (the account is in the coverage allowlist), the comment pipeline SHALL first attempt to pick a joined group under the normal timing constraints — warmup (minimum join age) AND cooldown (minimum time since last comment) — from a least-recently-commented window, at random. When NO joined group satisfies these timing constraints, the pipeline SHALL, by default, fall back to a RELAXED selection that ignores the warmup and cooldown timing (still restricted to `status='joined'` groups, still ordered least-recently-commented, still random within the window) instead of skipping the account. A relaxed pick MUST be flagged so the human-review approval card visibly marks that the timing window was not met, for the operator to confirm or reject. The relaxed fallback MUST still enforce the per-account daily cap and every other gate — it relaxes ONLY the per-group timing, never the per-account comment volume, and never the always-on human review. The relaxed fallback MUST be reversible via an environment kill switch that restores the strict behavior (no eligible group → honest no-op skip). When the account has zero joined groups at all, the result MUST still be an honest no-op, relaxed or not.

#### Scenario: All joined groups within cooldown fall back to a flagged relaxed pick
- **WHEN** coverage mode is enabled for an account whose every joined group is still inside warmup or cooldown, and the relaxed fallback is enabled (default)
- **THEN** the pipeline picks the least-recently-commented joined group anyway and the resulting Feishu human-review card is annotated that the timing constraints were not met, so the operator decides

#### Scenario: Relaxed fallback still respects the daily cap
- **WHEN** an account has already reached its Facebook comment daily cap
- **THEN** no relaxed pick is submitted — the daily cap denies the run exactly as it does for a normal pick (the relaxed fallback never raises per-account volume)

#### Scenario: Kill switch restores strict skip
- **WHEN** the relaxed-fallback kill switch is disabled and no joined group satisfies the timing constraints
- **THEN** the pipeline produces an honest no-targets no-op and does not comment, exactly as before this change

#### Scenario: Zero joined groups is still an honest no-op
- **WHEN** a coverage account has no joined groups at all
- **THEN** both the normal and the relaxed selection return empty and the pipeline records an honest no-op — it never fabricates a target or blindly posts

### Requirement: Operator search keywords preserve internal whitespace as a single term

An operator-configured Facebook comment search keyword that contains internal whitespace (a multi-word phrase) SHALL be stored and used as ONE keyword/search term end-to-end. The console keyword input MUST NOT split a term on spaces into multiple keywords; only leading/trailing whitespace is trimmed. Comma-separation between distinct keywords SHALL still be supported.

#### Scenario: Multi-word phrase stays one keyword
- **WHEN** an operator enters the search term `手冲 咖啡` in the console keyword field
- **THEN** it is stored and searched as the single keyword `手冲 咖啡`, not as two keywords `手冲` and `咖啡`

#### Scenario: Comma still separates keywords
- **WHEN** an operator enters `手冲 咖啡, 烘焙`
- **THEN** it is stored as two keywords, `手冲 咖啡` and `烘焙`

