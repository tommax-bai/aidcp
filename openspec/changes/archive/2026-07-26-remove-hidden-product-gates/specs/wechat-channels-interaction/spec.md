## ADDED Requirements

### Requirement: 视频号产品写能力不得依赖本机隐藏授权

Edge SHALL derive comment and DM text-write capabilities from the scoped Cloud runtime controls, active matching identity, successful corresponding read-path evidence, and current endpoint circuit state. It MUST NOT require a local account grant, local channel enable, local write kill switch state, operator-recorded write-probe approval environment variable, or unpackaged-client bypass token as an additional product authorization.

The first and every subsequent real write MUST still pass Cloud policy, runtime controls, risk, interaction rate limits, CAS, idempotency and single-flight, and Edge exact-target/post-action validation. Missing read evidence, identity mismatch, open circuit, or disabled Cloud control MUST keep the capability closed.

#### Scenario: Packaged client gains configured comment write capability
- **WHEN** a packaged client has active matching identity, successful comment read evidence, healthy endpoints, and scoped Cloud controls enable comment reading and replying
- **THEN** Edge reports comment reply capability without requiring `AIDCP_WECHAT_COMMENT_WRITE_PROBE_VERIFIED` or another local grant

#### Scenario: Cloud channel off remains authoritative
- **WHEN** stale local environment values imply writes are enabled but scoped Cloud controls disable DM text send
- **THEN** Edge reports DM text send unavailable and MUST NOT execute a DM write

#### Scenario: Read evidence or circuit failure remains fail closed
- **WHEN** the corresponding read probe has not succeeded or a required write endpoint circuit is open
- **THEN** Edge keeps the write capability closed regardless of the Cloud channel toggle
