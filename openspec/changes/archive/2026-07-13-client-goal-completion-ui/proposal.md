## Why

The Electron companion currently presents healthy pacing completion with quota terminology, red backgrounds, and warning styling. Users interpret a planned pause as a restriction or failure instead of understanding the progress already made and what will happen next.

## What Changes

- Reframe the daily usage surface as "今日进展" and present reached pacing caps as completed session, stage, or daily plans.
- Explain quota-driven waiting with a value-oriented next-step message and an honest estimated continuation time.
- Use success styling for completed plans, calm styling for waiting, amber styling for states that need user assistance, and reserve red styling for genuine system failures.
- Keep exact action totals, caps, timing metadata, and developer-facing diagnostics available without changing the cloud snapshot or protocol.
- Keep this change independent from the pending mascot redesign.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `edge-companion-ui`: Change the user-facing semantics and visual severity of daily progress, quota-driven pauses, assistance states, and genuine errors.

## Impact

- Affects the Electron renderer HTML, view logic, styling, and companion UI tests in `aidcp-edge`.
- Does not change cloud behavior, protocol fields, quota calculation, risk state, or persistence.
