## ADDED Requirements

### Requirement: Facebook scheduled comments are disabled by default and fail closed

Facebook scheduled commenting SHALL be controlled by a global kill switch that defaults off. When disabled, missing, invalid, or explicitly false, no trigger path (scheduled or Feishu-command) MUST post, record risk/cooldown, or claim work occurred. Per-account `accounts.status` and platform matching MUST also gate work.

#### Scenario: Default off prevents posting
- **WHEN** the cloud process starts without enabling the Facebook comment automation switch
- **THEN** no Facebook scheduled comment is posted or risk-recorded, even if Facebook accounts and targets exist

#### Scenario: Paused account is skipped
- **WHEN** a Facebook account has `accounts.status='paused'`
- **THEN** the scheduled trigger skips it and does not dispatch browse/comment work

### Requirement: Facebook comments trigger through existing comment entry points routed by account platform

Facebook automatic comments SHALL be triggered through the existing schedule-driven comment entry point (per-account comment schedule with its daily cap) and the existing Feishu `/comment` command entry point; a separate Facebook-specific cron MUST NOT be added. Both entry points SHALL resolve the account platform through the account store (`accounts.platform`) and route Facebook accounts to the Facebook targeted-comment pipeline, which SHALL load operator-configured target URLs for the account. V1 SHALL only browse configured targets; it MUST NOT perform whole-site Facebook search. Missing targets produce an honest no-op result.

#### Scenario: Schedule trigger routes by platform
- **WHEN** the content schedule fires a comment action for an account with `accounts.platform='facebook'`
- **THEN** the comment pipeline uses the Facebook platform profile and the targeted pipeline, not the xhs search loop

#### Scenario: No configured targets yields no-op
- **WHEN** a Facebook account is active but has no configured target Pages/Groups/posts
- **THEN** the trigger records/returns a no-targets outcome and does not browse random Facebook surfaces

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
