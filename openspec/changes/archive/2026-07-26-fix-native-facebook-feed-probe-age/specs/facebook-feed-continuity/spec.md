## ADDED Requirements

### Requirement: Native Feed probe timing is decodable across the browser-to-Rust boundary

The Facebook browser router SHALL emit `documentAgeMs` as a finite, non-negative integer that the strict Rust Native Feed probe model can decode. A real browser's fractional high-resolution time origin MUST NOT terminate initial or resumed automatic browsing before the existing bounded Feed settle flow begins. Rust SHALL continue to reject malformed or undeclared probe fields rather than coercing arbitrary values or bypassing the Native-only boundary.

#### Scenario: Fractional Chrome time origin starts the bounded Feed flow

- **WHEN** the Facebook Feed probe computes document age from a Chrome `performance.timeOrigin` containing a fractional millisecond component
- **THEN** the router emits a non-negative integer `documentAgeMs`, Rust decodes the bounded probe, and the session proceeds into the existing Feed settle and continuation flow

#### Scenario: Strict bounded-result validation remains fail-closed

- **WHEN** a Facebook Feed probe contains an undeclared field or a value that does not satisfy the declared bounded shape
- **THEN** Rust rejects the probe and reports an honest Native failure without fabricating cards or activating a JavaScript fallback
