## ADDED Requirements

### Requirement: Migrated platforms share selector-free Native supervision
The browser-independent Edge core SHALL supervise the Native process and typed sessions for every migrated platform while retaining ownership of browser-provider launch, Cloud connectivity, task admission, lifecycle, and receipt forwarding. Platform facades in JavaScript SHALL be selector-free and MUST NOT attach to or actuate a migrated page target directly.

#### Scenario: Facebook browser is launched
- **WHEN** the provider returns a loopback DevTools endpoint for an admitted Facebook task
- **THEN** Edge opens a Facebook Native session with the endpoint and typed task identity
- **AND** the Facebook facade performs page work only through Native

#### Scenario: WeChat API runtime does not need browser inspection
- **WHEN** the WeChat runtime can continue with a valid stored API session
- **THEN** ordinary API orchestration remains independent of Native page execution and no browser session is opened merely for encapsulation
