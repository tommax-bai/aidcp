## ADDED Requirements

### Requirement: Facebook unattended comment validators reject unsafe generated text

For Facebook scheduled comments, generated text SHALL pass deterministic validators before any browser submit. Validator failures are final for that attempt: the system MUST return a skipped outcome and MUST NOT silently substitute templates, placeholders, or auto-fixed text for posting.

#### Scenario: Contact information is rejected
- **WHEN** generated Facebook comment text contains phone/email/WeChat-like contact information
- **THEN** validators reject it and no comment is submitted

#### Scenario: Empty LLM output is skipped
- **WHEN** the LLM produces empty or unparsable comment text
- **THEN** the attempt is skipped honestly, with no template fallback and no submit
