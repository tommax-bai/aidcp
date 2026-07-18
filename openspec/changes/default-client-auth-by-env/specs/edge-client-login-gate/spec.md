## MODIFIED Requirements

### Requirement: Edge client login gate activation

The edge desktop client SHALL enable the customer login gate whenever it can
resolve a customer-auth base URL. Explicit full URLs from
`AIDCP_CLIENT_AUTH_URL` or persisted `clientAuthUrl` SHALL take precedence over
baked package metadata. Baked package metadata SHALL take precedence over
environment defaults.

When no explicit or baked customer-auth URL is present, the client SHALL resolve
the default customer-auth URL from the resolved cloud environment key. The
official `dev` and `ol` cloud environments SHALL both have default customer-auth
URLs and therefore SHALL require customer login by default.

#### Scenario: dev starts with customer login by default

- **WHEN** the desktop client starts with the resolved cloud environment `dev`
  and no explicit customer-auth URL override
- **THEN** the client resolves `http://121.89.85.150:8088/capi` as the
  customer-auth base URL
- **AND** the login gate is enabled before the main window can proceed

#### Scenario: ol starts with customer login by default

- **WHEN** the desktop client starts with the resolved cloud environment `ol`
  and no explicit customer-auth URL override
- **THEN** the client resolves `https://aidcp.tommax.cc/capi` as the
  customer-auth base URL
- **AND** the login gate is enabled before the main window can proceed

#### Scenario: explicit customer-auth URL still wins

- **WHEN** the desktop client is started with `AIDCP_CLIENT_AUTH_URL` or a
  persisted full `clientAuthUrl`
- **THEN** that full URL is used as the customer-auth base URL
- **AND** the dev/ol default URL mapping does not override it
