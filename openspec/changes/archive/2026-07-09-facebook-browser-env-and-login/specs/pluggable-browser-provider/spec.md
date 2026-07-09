## ADDED Requirements

### Requirement: browser provider startup and tab selection are platform-aware

The browser provider and edge startup flow SHALL accept a platform target descriptor that supplies start URL, allowed URL/domain predicates, and tab selection rules. For `facebook`, the startup flow MUST select or open Facebook URLs rather than requiring xhs-specific `urlIncludes` matches. Provider responsibilities remain limited to lifecycle/CDP endpoint delivery; downstream platform driver logic handles page-specific behavior.

#### Scenario: Facebook startup does not require xhs tab
- **WHEN** `AIDCP_PLATFORM=facebook` and the AdsPower profile has no `xiaohongshu.com` tab
- **THEN** edge still starts by selecting/opening an allowed Facebook tab and does not fail because an xhs URL is absent

#### Scenario: Provider boundary remains unchanged
- **WHEN** a Facebook profile is launched through AdsPower
- **THEN** AdsPower still only supplies browser lifecycle/CDP endpoint information; locating, identity, overlay detection, and page operations remain outside provider code

### Requirement: Facebook AdsPower fingerprint sanity probe runs before automation

For Facebook profiles, the system SHALL provide a read-only fingerprint sanity probe that records safe, non-secret signals such as viewport, timezone/language consistency, provider mode, stealth setting, and whether obvious automation flags are exposed. The probe MUST NOT attempt to bypass or solve platform defenses; it only verifies that configured provider state is not obviously inconsistent.

#### Scenario: Sanity probe reports non-secret fingerprint summary
- **WHEN** the Facebook fingerprint sanity probe runs
- **THEN** it reports safe summary fields and flags obvious misconfiguration, without dumping cookies, tokens, proxy credentials, or fingerprint raw internals
