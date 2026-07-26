## ADDED Requirements

### Requirement: Facebook manual comment fast return
When and only when a manual single-comment task carries the explicit `--feed` switch, the Facebook Edge executor SHALL preserve all pre-submit gates and input verification, dispatch Enter to submit the comment, wait 500 milliseconds, skip the in-place acknowledgement/result-detection loop, and navigate directly to the canonical Facebook home page. The post-submit outcome MUST be `verification_ambiguous`/submitted-unconfirmed rather than confirmed success, so Cloud writes anti-retry deduplication without recording a confirmed comment or retrying the target. A Facebook comment without the switch SHALL retain the existing in-place platform-confirmation lifecycle, including confirmed, rejected, pending-approval, and ambiguous terminal distinctions.

#### Scenario: Facebook fast return after Enter dispatch
- **WHEN** a manual `/comment <nickname> --feed` Facebook task passes all gates and Enter is dispatched in the target post editor
- **THEN** Edge waits 500 milliseconds, navigates to the canonical Facebook home page without polling comment acknowledgement state, and reports the write as submitted but unconfirmed

#### Scenario: Facebook default path retains lifecycle evidence
- **WHEN** a Facebook comment task does not carry the explicit manual `--feed` switch
- **THEN** Edge MUST keep the existing in-place acknowledgement loop and preserve its confirmed, rejected, pending-approval, and ambiguous outcomes
