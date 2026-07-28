## MODIFIED Requirements

### Requirement: Facebook rule mode is an explicit account-scoped fixed definition

The system SHALL provide a Facebook-only rule mode with the fixed versioned definition `facebook_browse_5_like_1_join_contact_every_2@2`, expressing a two-tier cadence: every five durable unique confirmed reads open one rule round that attempts one like, and every second round additionally attempts one join-contact. It SHALL be persisted with the **environment** as its authoritative key. The only operator choice SHALL be enabled or disabled; operators MUST NOT supply scripts, prompts, thresholds, cadence numbers, action lists or other free-form execution logic. Missing configuration SHALL mean disabled. Writes MUST validate the target environment's authoritative normalized platform, persist atomically with audit fields and return server readback; unsupported, unknown or non-Facebook environments MUST be rejected without a partial write. Configuration MUST be writable and readable for an environment that currently has no bound account.

Configuration readback SHALL report the definition identity persisted in the authoritative row. Cloud MUST NOT substitute the compiled-in definition constants for a stored row whose definition identity differs; a mismatch SHALL be surfaced as a named projection problem rather than silently rendered as the current definition.

Runtime resolution SHALL read the configuration of the environment that currently binds the executing account. When that reverse resolution yields no unique environment — binding unknown, binding conflict, cross-customer contention or an unreadable environment registry — the system MUST fail closed to "rule mode not enabled" with a named blocker and MUST NOT infer enablement from any account-keyed legacy value.

#### Scenario: Facebook environment enables the fixed rule
- **WHEN** an operator enables rule mode for an authoritative Facebook environment
- **THEN** Cloud persists the fixed definition version against that environment and returns the write-after-read truth with `updatedAt` and `updatedBy`

#### Scenario: Non-Facebook environment is rejected
- **WHEN** an operator attempts to enable Facebook rule mode for a Xiaohongshu, WeChat Channels or unknown-platform environment
- **THEN** the full write is rejected and no rule configuration or runtime progress is created

#### Scenario: Missing configuration is safely off
- **WHEN** a Facebook environment has no rule-mode configuration row
- **THEN** reads report rule mode disabled and MUST NOT create a row or start rule execution

#### Scenario: Stored definition mismatch is not disguised as the current definition
- **WHEN** a stored rule configuration row carries a definition identity other than the current one
- **THEN** readback names the mismatch and MUST NOT report that row as configured for the current definition

#### Scenario: Unbound environment can be preconfigured
- **WHEN** an owner enables rule mode for an owned Facebook environment that has no bound account yet
- **THEN** Cloud persists the environment configuration and reports it as configured but not currently executing, MUST NOT fabricate an account, progress or effective mode

#### Scenario: Rebinding carries configuration to the new account
- **WHEN** an environment with rule mode enabled changes its bound account from A to B
- **THEN** the environment configuration stays byte-for-byte unchanged and account B is admitted under it, while account A is no longer governed by it, MUST NOT require a restart

#### Scenario: Ambiguous reverse resolution fails closed
- **WHEN** the executing account resolves to zero or more than one environment, or the environment registry is unreadable
- **THEN** rule mode does not start or advance and the named blocker is exposed, MUST NOT fall back to any account-keyed legacy configuration

## ADDED Requirements

### Requirement: Rule progress, view dedupe and batch outcomes remain account-keyed

Rule collecting progress, unique-view dedupe facts and batch terminal states SHALL continue to be persisted and deduplicated per account, execution target and rule definition version. They MUST NOT be migrated to, mirrored onto, or resolved through the environment key. When an environment's bound account changes, the new account SHALL start collecting from zero and SHALL NOT inherit the previous account's visited-content set or in-flight batch.

#### Scenario: New account starts from zero after rebinding
- **WHEN** an environment with rule mode enabled rebinds from account A at `7/10` to account B
- **THEN** account B begins at `0/10` with an empty visited-content set and MUST NOT skip content solely because account A had already viewed it

#### Scenario: In-flight batch does not survive rebinding
- **WHEN** account A has an open rule batch at the moment its environment rebinds to account B
- **THEN** account A's batch settles under its own account key with a truthful terminal state and MUST NOT be continued, reassigned or reported under account B

#### Scenario: Progress is not resolved through the environment
- **WHEN** progress or dedupe is read for an executing account
- **THEN** the lookup uses the account key directly and MUST NOT depend on environment reverse resolution succeeding
