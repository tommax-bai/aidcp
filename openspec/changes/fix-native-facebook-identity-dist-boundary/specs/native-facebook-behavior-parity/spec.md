## ADDED Requirements

### Requirement: Native Facebook production dependencies exclude retired page-rule modules

The Edge production distribution SHALL keep Native Facebook orchestration dependencies separate from retired TypeScript Facebook page executors and injected JavaScript page-rule bundles. Shared pure helpers, including canonical post-identity parsing and presentation classification, MUST be provided from a module whose transitive dependency graph does not import those retired page-rule modules. Compatibility exports for development-only consumers MUST NOT make the mixed legacy façade reachable from Native production orchestration.

#### Scenario: Native orchestration shares post identity without shipping legacy rules

- **WHEN** the production Edge TypeScript distribution is built after Native Facebook browse orchestration imports canonical Reel or Feed-video identity helpers
- **THEN** the build succeeds with the helper behavior preserved and the production graph contains none of the forbidden migrated Facebook page-rule JavaScript modules

#### Scenario: A pure helper import reintroduces a legacy dependency

- **WHEN** a Native production module transitively imports a retired Facebook page executor or injected JavaScript rule bundle through a shared helper
- **THEN** production distribution verification fails instead of allowlisting or silently shipping that dependency
