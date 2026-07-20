## ADDED Requirements

### Requirement: Manual comment fast return to feed
The Feishu manual command `/comment <nickname> --feed` SHALL accept `--feed` as a trailing switch composable with the other recognized trailing comment switches in any order. The switch SHALL apply only to a legacy/manual single-comment task and SHALL NOT be inferred for automatic, scheduled, curated, or plain `/comment` runs.

All existing pre-submit requirements SHALL remain in force, including account resolution, target selection, deduplication unless separately overridden by `--force`, human review, current-target validation, content safety, captcha checks, editor readback, and the final pre-submit cancellation checkpoint. Only after the Edge has dispatched the irreversible comment submit action SHALL it skip platform-result detection and waiting, delay 500 milliseconds, issue direct navigation to the platform home page, and release the comment operation.

Because no platform result was observed, the Edge and Cloud MUST classify the outcome as submitted but unconfirmed, MUST NOT present it as platform-confirmed success, MUST write the existing anti-retry deduplication record, and MUST NOT automatically retry the comment. Commands without `--feed` SHALL preserve the existing confirmation behavior.

#### Scenario: Operator requests fast return
- **WHEN** an operator sends `/comment <nickname> --feed`, the task passes review and safety gates, and Edge dispatches the comment submit action
- **THEN** Edge waits 500 milliseconds, does not run the platform-result confirmation loop, directly navigates to the platform home page, and reports a submitted-but-unconfirmed outcome that is deduplicated and not retried

#### Scenario: Submit is blocked before dispatch
- **WHEN** a `/comment <nickname> --feed` task fails any target, approval, safety, captcha, editor, or pre-submit cancellation gate before the submit action is dispatched
- **THEN** the system MUST report the existing not-dispatched failure, MUST NOT use the fast-return submitted outcome, and MUST NOT navigate as though a comment was submitted

#### Scenario: Plain command keeps confirmation
- **WHEN** an operator sends `/comment <nickname>` without `--feed`, or an automatic/scheduled comment task runs
- **THEN** the system MUST retain the existing platform-result confirmation and terminal classification behavior
