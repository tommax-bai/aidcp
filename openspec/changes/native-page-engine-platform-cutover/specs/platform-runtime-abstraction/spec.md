## ADDED Requirements

### Requirement: Facebook capability assembly resolves to Native execution
An Edge environment that declares Facebook browser capabilities SHALL assemble a compatible Native Facebook executor before advertising those capabilities. The existing Cloud capability names and product semantics remain unchanged; capability admission MUST fail honestly when the compatible Native adapter is unavailable.

#### Scenario: Compatible Native Facebook adapter is ready
- **WHEN** the Facebook driver, browser provider, and Native manifest all declare compatible support
- **THEN** Edge advertises the existing Facebook capabilities and routes them to Native execution

#### Scenario: Native Facebook adapter is incompatible
- **WHEN** the driver declares a Facebook capability but the Native manifest/protocol lacks its required command coverage
- **THEN** Edge withholds or rejects that capability rather than routing it to Xiaohongshu or JavaScript
