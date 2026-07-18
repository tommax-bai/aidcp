## ADDED Requirements

### Requirement: Authoritative assigned environments default into the client roster

When customer authentication is enabled, the official client SHALL treat the intersection of the logged-in customer's authoritative assigned environments and the complete local physical environment list as the default running roster. Default roster enrollment MUST remain subordinate to authoritative ownership, MUST persist without starting an environment, and MUST preserve a customer-controlled manual exclusion. The client MUST scope the exclusion to the current customer, MUST NOT carry it across customer identities, and MUST fail closed without changing roster or exclusion state when the authoritative or physical list is incomplete or untrusted.

#### Scenario: Assigned local environments become visible by default
- **WHEN** an authenticated customer has multiple authoritatively assigned environments that exist in the complete local physical list
- **THEN** every non-excluded environment is persisted into the running roster and becomes visible as an offline row without being started

#### Scenario: Manual exclusion cannot expand tenant scope
- **WHEN** the renderer saves manual exclusions while customer authentication is enabled
- **THEN** the main process accepts only envKeys in the current authoritative assigned set and MUST NOT let the renderer store another customer's envKey

#### Scenario: Different customer does not inherit exclusions
- **WHEN** a different customer logs in on the same client installation
- **THEN** the new customer starts with no exclusions inherited from the previous customer and their assigned local environments follow the default enrollment rule

#### Scenario: Incomplete truth preserves prior state
- **WHEN** ownership refresh fails, the local profile result is truncated or empty, or the session becomes invalid
- **THEN** the client does not default-enroll, remove, or clear exclusions based on that result and MUST NOT fall back to another customer's or the full local environment set

