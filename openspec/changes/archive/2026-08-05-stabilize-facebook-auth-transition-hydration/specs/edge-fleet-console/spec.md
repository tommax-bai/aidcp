## ADDED Requirements

### Requirement: Fleet login state SHALL not demand attention during bounded authentication hydration

The client SHALL keep a managed Facebook environment in the existing starting/login projection while saved-credential filling remains inside its 25-second window or an authentication checkpoint remains inside its 15-second structural hydration window. It MUST NOT emit or project `credential_fill_unavailable`, `unsupported_facebook_checkpoint`, `需要登录`, or terminal `异常` solely because the in-window document is incomplete. This state MUST NOT be promoted to `运行中` before stable identity and ordinary execution evidence exist.

#### Scenario: Credential fill is still pending
- **WHEN** the freshly started Facebook login document has empty fields but remains inside the 25-second managed credential-fill window
- **THEN** the environment SHALL remain in `启动中` and MUST NOT appear under `需要处理`

#### Scenario: Post-TOTP checkpoint is still hydrating
- **WHEN** a confirmed automatic TOTP submission is followed by an incomplete checkpoint inside the 15-second hydration window
- **THEN** the environment SHALL remain `启动中 · 登录中` without showing `异常` or requiring user intervention

#### Scenario: Bounded wait ends without recovery
- **WHEN** the relevant 25-second credential or 15-second checkpoint window expires and the coordinator reports the existing structured manual or terminal reason
- **THEN** the client SHALL project the existing `需要处理` state with that safe reason
- **AND** it MUST NOT report successful login, running work, or stable identity
