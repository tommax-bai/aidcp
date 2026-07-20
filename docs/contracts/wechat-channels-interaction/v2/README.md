# WeChat Channels interaction contract v2

v2 is an additive overlay for group/default reply-configuration management. The v1 Edge protocol, runtime-controls and interaction DTOs remain unchanged.

New internal routes:

```text
GET|POST /api/interaction-reply-config-scopes
GET      /api/interaction-reply-config-scopes/:scopeId
POST     /api/interaction-reply-config-scopes/:scopeId/initialize
PUT      /api/interaction-reply-config-scopes/:scopeId/policy
POST|PUT|DELETE /api/interaction-reply-config-scopes/:scopeId/templates[/templateId]
POST|PUT|DELETE /api/interaction-reply-config-scopes/:scopeId/rules[/ruleId]
PUT      /api/interaction-reply-config-scopes/:scopeId/profiles
POST     /api/interaction-reply-config-scopes/:scopeId/preview
POST     /api/interaction-reply-config-scopes/:scopeId/publish
GET      /api/interaction-reply-config-scopes/:scopeId/audit
GET      /api/accounts/:accountId/effective-reply-config
```

The effective resolution order is exact: non-empty `accounts.group_label` selects only its group scope; null selects only the singleton default scope. A grouped account never falls back to default. Runtime controls and all risk/auth/capability gates stay account-scoped.

Account-scoped reply configuration and migration-inventory routes are retired. The resolver mode is always `scoped`; historical jobs without `configScopeId` fail closed instead of loading legacy account snapshots.

Validate the overlay fixtures from this directory:

```bash
check-jsonschema --check-metaschema schemas/*.schema.json
check-jsonschema --schemafile schemas/internal-api.schema.json fixtures/internal-api/*.json
check-jsonschema --schemafile schemas/customer-auth-api.schema.json fixtures/customer-api/*.json
```
