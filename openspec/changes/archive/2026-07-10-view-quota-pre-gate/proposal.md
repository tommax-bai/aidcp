## Why

`view` quotas are currently enforced only when a note detail has already arrived and
cloud records `interaction.occurred{action:'view'}`. If the account enters `warned`
mid-window, the effective view quota can shrink below the already-recorded count; the
next opened note is then rejected by `RiskController.record('view')` after the browser
has already viewed it. The UI count stops increasing, but the safety gate is too late.

This showed up on 2026-07-04 for the `工程师大白` account: an unknown blocking overlay
caused `warned` behavior while the current hour already had more views than the warned
hour cap. Subsequent view attempts hit pacing saturation after the page was opened.

## What Changes

- Add a cloud-side pre-gate before dispatching `open_note`: check
  `RiskController.explain('view')` for the connection's real account.
- If the gate rejects, do not dispatch `open_note`; put only the browse loop into
  view-quota sleep, then re-check when the sliding quota window releases.
- Do not block session start / auto-resume on temporary minute/hour view quota
  exhaustion. The session may stay alive, but no new note opens while sleeping.
- Keep manual and scheduled note creation/publish independent from view-quota sleep;
  publish generation/approval/dispatch does not require a preceding browse action.

## Impact

- Affects `aidcp-cloud` browse orchestration and risk quota explanations only.
- No protocol changes and no edge changes.
- Does not change how `view` is counted: successful note detail reports still append
  `risk_counters`; rejected pre-gate attempts append nothing because no note is opened.
- Likes/collects/follows/comments are naturally suppressed during view-quota sleep
  because they require an opened note/profile path.
