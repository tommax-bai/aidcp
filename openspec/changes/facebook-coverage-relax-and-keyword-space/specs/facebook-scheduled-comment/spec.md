## ADDED Requirements

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
