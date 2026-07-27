## ADDED Requirements

### Requirement: Native typed-result failures SHALL expose bounded decode-path diagnostics

When a typed browser result cannot be produced or decoded, the Native Page Engine SHALL preserve its existing stable error code and static message and SHALL add a bounded, content-free diagnostic identifying the operation stage, decode stage, expected router result kind when applicable, failing typed field path when available, and actual JSON value category. For an evaluated-router exception, it MAY additionally include only a finite exception class/reason, bounded line/column, and an identifier-only token extracted from a recognized engine-generated pattern. The diagnostic MUST NOT include the offending value, raw CDP result, raw exception/parser message, evaluated source, selector, URL, DOM text, cookie, credential, or storage value.

The diagnostic fields SHALL use finite allowlisted stage/category values and bounded paths. An optional diagnostic added to an internal Native IPC protocol-v2 error record MUST remain compatible with clients that do not consume it, and the current TypeScript client SHALL preserve it in the raised Native error detail without changing the stable error code or effect truth. This internal IPC addition MUST NOT change the Edge-Cloud WebSocket protocol.

#### Scenario: Nested typed field is incompatible

- **WHEN** a Facebook router result has the expected wrapper and result kind but one nested typed field carries an incompatible JSON category
- **THEN** the failure retains `cdp_error` and the static bounded message while its diagnostic identifies `typed_value`, the exact bounded field path, expected result kind, and actual JSON category without including the field value

#### Scenario: Wrapper and result-kind failures remain distinguishable

- **WHEN** CDP returns an exception, omits `result.value`, omits the router output value, or returns an unexpected router output kind
- **THEN** the diagnostic reports the corresponding finite decode stage rather than collapsing those cases into an indistinguishable field failure

#### Scenario: Evaluated router exception is classified without raw text

- **WHEN** the browser returns `exceptionDetails` because a router helper reads a property from null during a transient navigation document
- **THEN** the diagnostic identifies `cdp_exception`, its finite error class/reason, bounded location, and safe identifier token without returning the raw exception description or evaluated source

#### Scenario: Diagnostic is safely absent

- **WHEN** an older or unrelated Native failure carries no diagnostic object
- **THEN** the TypeScript client preserves the existing stable error behavior and does not require or fabricate diagnostic fields

#### Scenario: Untrusted content is redacted

- **WHEN** a typed decode failure is caused by a string, object, or array containing page-derived text
- **THEN** serialized stdout, bounded stderr, and the TypeScript error detail contain only its field path and JSON category and contain none of the raw value or parser text

### Requirement: Observation-only group join failures SHALL remain not started

A Native Facebook `group_join` command whose `click` parameter is false SHALL be classified as observation-only. If it fails to navigate, probe, or decode, its effect phase SHALL be `not_started`; it MUST NOT be upgraded to `ambiguous` solely because the command kind can support a separate `click=true` write path. A `click=true` failure MUST retain conservative write-effect truth unless the orchestration has explicit actuation-boundary evidence.

#### Scenario: Observation decode fails

- **WHEN** `group_join(click=false)` fails while decoding a pre-actuation browser result
- **THEN** the error retains its diagnostic and reports `effectPhase=not_started`, not `native_effect_ambiguous`

#### Scenario: Write-capable invocation remains conservative

- **WHEN** `group_join(click=true)` fails and the engine cannot prove whether actuation occurred
- **THEN** it remains ambiguous and MUST NOT be reclassified as not started by the observation-only rule

### Requirement: Group-join action receipts SHALL preserve the structured observation across the Native bridge

When the Rust Native Page Engine returns a group-join action receipt, the Edge TypeScript bridge SHALL forward the group-specific structured observation as the `action.completed.observation` witness even when the serialized generic observation field is JSON `null`. The bridge MUST preserve an existing non-null generic observation, MUST remove the internal group-specific alias before sending the Edge-Cloud payload, and MUST NOT infer success, membership, or actuation from the normalization.

#### Scenario: Rust null option does not discard the group observation

- **WHEN** a Native action receipt contains `observation: null` and a non-null `groupObservation` object
- **THEN** Edge forwards that object as `action.completed.observation` and omits `groupObservation`

#### Scenario: Existing generic observation remains authoritative

- **WHEN** a Native action receipt contains both a non-null generic observation and a group-specific observation
- **THEN** Edge preserves the generic observation as-is and does not replace it

#### Scenario: Both observation forms are absent

- **WHEN** a Native action receipt has neither a non-null generic observation nor a non-null group observation
- **THEN** Edge does not fabricate evidence and Cloud remains able to fail closed
