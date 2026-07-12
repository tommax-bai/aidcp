## ADDED Requirements

### Requirement: Facebook account config supports generated or template comment bodies

Each Facebook account's comment configuration SHALL include a comment-body mode. `generated` mode SHALL use the existing Facebook composer after the target post is opened and read. `template` mode SHALL choose from operator-configured account templates and MUST skip LLM comment generation for the body. Both modes SHALL still require configured search keywords, target selection from the account joined-group ledger, deterministic validation, human review when configured/required, edge submit, server-confirmed verification, and honest audit outcomes.

Template mode MUST fail closed when the account has no valid templates; it MUST NOT silently fall back to generated mode. Generated mode MUST NOT require templates. Templates MUST be stored per account, may contain multiple entries, and SHALL be sanitized for empties/duplicates while preserving meaningful internal whitespace.

#### Scenario: Generated mode uses the composer
- **WHEN** a Facebook account is configured for `generated` mode and a target post is opened
- **THEN** the pipeline calls the Facebook composer with the keyword, group label, post text, and discussion sample before validating and reviewing the produced body

#### Scenario: Template mode skips generation
- **WHEN** a Facebook account is configured for `template` mode and has valid templates
- **THEN** the pipeline selects a template body and does not call the Facebook composer for that comment attempt

#### Scenario: Template mode without templates fails closed
- **WHEN** a Facebook account is configured for `template` mode but has no valid templates
- **THEN** the pipeline records/returns an honest no-op or compose-skipped outcome and MUST NOT fall back to generated comments

### Requirement: Template comments use the same safety and contact lanes as generated comments

Template comment bodies SHALL pass the same deterministic body validators before any submit attempt: empty/low-signal, length, URL/bare-domain, contact-info text, `@mention`, spam phrase, and relevance rules where applicable. A rejected template MUST NOT be repaired and posted. Contact-info comments SHALL keep the template/generated body separate from the account contact string: the body is sent as `text`, and the contact string is injected through the existing contact-info lane after human review.

#### Scenario: Template body with contact text is rejected
- **WHEN** a template body contains a phone number, email, WeChat-like contact phrase, or similar contact text
- **THEN** the body validator rejects it before submit, and the contact-info lane is not used to rescue that invalid body

#### Scenario: Contact template comment appends account contact info separately
- **WHEN** a contact comment uses template mode and the account has configured contact info
- **THEN** the review card shows the template body plus the account contact string, and edge receives the body as `text` plus the contact string in the existing `groupChatCode`/contact-info field

## MODIFIED Requirements

### Requirement: Facebook comments trigger through existing comment entry points routed by account platform

Facebook automatic comments SHALL be triggered through the existing schedule-driven comment entry point (per-account comment schedule with its daily cap) and the existing Feishu `/comment` command entry point; a separate Facebook-specific cron MUST NOT be added. Both entry points SHALL resolve the account platform through the account store (`accounts.platform`) and route Facebook accounts to the Facebook targeted-comment pipeline. For each account the pipeline SHALL read an operator-configured keyword list, pick a keyword at random, select a concrete group URL from that account's own joined-group membership ledger, and search ONLY within that selected group, then pick a candidate post from the in-container results (bounded extraction). It MUST NOT perform whole-site Facebook search and MUST NOT comment on posts outside the selected joined group. Missing keywords OR missing eligible joined groups produce an honest no-op result.

#### Scenario: Schedule trigger routes by platform
- **WHEN** the content schedule fires a comment action for an account with `accounts.platform='facebook'`
- **THEN** the comment pipeline uses the Facebook platform profile and the targeted pipeline, not the xhs search loop

#### Scenario: No configured keywords or joined groups yields no-op
- **WHEN** a Facebook account is active but has no configured keywords, or no joined group can be selected for the account
- **THEN** the trigger records/returns a no-targets outcome and does not search whole-site or browse random Facebook surfaces

#### Scenario: Search stays within a selected joined group
- **WHEN** the pipeline picks a random keyword for a Facebook account
- **THEN** it searches only inside one concrete group URL selected from that account's joined-group ledger and never performs a whole-site search

### Requirement: Facebook comments are composed after reading the target post and its discussion

Facebook generated-comment composition SHALL happen AFTER the target post is opened, using the post's caption (when present) and a bounded sample of other people's comments as context. The generated composer MUST write in the same language as the post/comment content (the local content language), and MUST NOT default to the interface language when it differs. The generated comment SHALL respond to the actual discussion rather than being written blind from a keyword alone. Template-comment mode SHALL still open the target post and read the caption/comment sample before choosing and validating the template body, but it MUST NOT call the generated composer or rewrite the template based on the post content. The edge MUST report the caption and comment samples honestly (empty when a photo post has no caption; never fabricated). The deterministic relevance check SHALL treat the keyword plus the post caption and comments as the relevance context when relevance validation is enabled.

#### Scenario: Generated comment matches the content language, not the UI language
- **WHEN** a target post and its comments are in a non-Chinese language (e.g. Spanish) while the account's Facebook interface language is Chinese
- **THEN** the generated comment is written in the content language (Spanish), not Chinese

#### Scenario: Generated compose reads the post before writing
- **WHEN** an automatic Facebook comment is composed in generated mode
- **THEN** the post is opened and its caption + other-people comments are read first, and the composer receives them as context (it is not written blind from the keyword alone)

#### Scenario: Photo post with no caption still composes from the discussion
- **WHEN** the target is a photo post with no text caption
- **THEN** the edge reports an empty caption (never fabricated) and the generated composer grounds the comment in the other-people comments and persona

#### Scenario: Template mode reads target context but skips composer
- **WHEN** an automatic Facebook comment is prepared in template mode
- **THEN** the post is opened and context is read for validation/review/audit, but the body comes from a configured template rather than LLM generation

### Requirement: Coverage-mode comment target selection relaxes timing as a review-gated fallback

When the Facebook comment pipeline selects a joined group for an account, it SHALL first attempt to pick a joined group under the normal timing constraints — warmup (minimum join age) AND cooldown (minimum time since last comment) — from a least-recently-commented window, at random. When NO joined group satisfies these timing constraints, the pipeline SHALL, by default, fall back to a RELAXED selection that ignores the warmup and cooldown timing (still restricted to `status='joined'` groups, still ordered least-recently-commented, still random within the window) instead of skipping the account. A relaxed pick MUST be flagged so the human-review approval card visibly marks that the timing window was not met, for the operator to confirm or reject. The relaxed fallback MUST still enforce the per-account daily cap and every other gate — it relaxes ONLY the per-group timing, never the per-account comment volume, and never the always-on human review. The relaxed fallback MUST be reversible via an environment kill switch that restores the strict behavior (no eligible group → honest no-op skip). When the account has zero joined groups at all, the result MUST still be an honest no-op, relaxed or not.

#### Scenario: All joined groups within cooldown fall back to a flagged relaxed pick
- **WHEN** a Facebook account's every joined group is still inside warmup or cooldown, and the relaxed fallback is enabled (default)
- **THEN** the pipeline picks the least-recently-commented joined group anyway and the resulting Feishu human-review card is annotated that the timing constraints were not met, so the operator decides

#### Scenario: Relaxed fallback still respects the daily cap
- **WHEN** an account has already reached its Facebook comment daily cap
- **THEN** no relaxed pick is submitted — the daily cap denies the run exactly as it does for a normal pick (the relaxed fallback never raises per-account volume)

#### Scenario: Kill switch restores strict skip
- **WHEN** the relaxed-fallback kill switch is disabled and no joined group satisfies the timing constraints
- **THEN** the pipeline produces an honest no-targets no-op and does not comment, exactly as before this change

#### Scenario: Zero joined groups is still an honest no-op
- **WHEN** a Facebook account has no joined groups at all
- **THEN** both the normal and the relaxed selection return empty and the pipeline records an honest no-op — it never fabricates a target or blindly posts

## REMOVED Requirements

### Requirement: Facebook coverage mode is gated by a global switch for all accounts

**Reason**: Joined-group selection is no longer a secondary coverage source that competes with operator-configured containers. It is the normal container source for Facebook comment attempts after this change, still protected by the existing Facebook comment kill switch, per-account schedule caps, risk gates, single-flight, and human review.

**Migration**: Keep any legacy environment switches harmless during rollout, but normal Facebook comment target selection MUST NOT require the old coverage source switch to be enabled.

### Requirement: The joined-group ledger is an allowed comment-container source under a per-account gate

**Reason**: The joined-group ledger is no longer merely an optional source under a per-account gate; it is the normal source for unpinned Facebook comments. Manual join-then-comment remains pinned to the just-joined group.

**Migration**: Continue using the existing membership ledger and coverage selector. Remove fallback to operator-configured containers for normal unpinned comment runs.
