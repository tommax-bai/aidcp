## 1. Specification

- [x] Add OpenSpec delta for account-scoped daily usage and quota saturation in the Electron companion.
- [x] Validate the OpenSpec change with `openspec validate edge-account-daily-quota-summary --strict`.

## 2. Cloud

- [x] Add account-scoped today publish count read support.
- [x] Extend `ui.snapshot` to include daily usage totals, current quota level, daily quotas, and saturated actions.
- [x] Add or update cloud tests for the new snapshot payload.
<!-- aidcp-cloud cc3afb8: ui.snapshot.dailyUsage built from risk counters, publish log, effective daily quotas, and covered by ui-snapshot tests. -->

## 3. Edge And Electron

- [x] Sync protocol definitions and convert `ui.snapshot.dailyUsage` into structured UI event lines.
- [x] Update Electron main-process status handling to replace local counters with authoritative daily usage when supplied.
- [x] Keep local log deltas for views/likes/collects/comments/follows as a live fallback.
- [x] Redesign the Electron summary strip with six metrics, quota progress, and saturated visual states.
- [x] Add or update edge/Electron tests.
<!-- aidcp-edge a2a0b62+c422586: protocol mirror, ui-event dailyUsage forwarding, Electron status/rendering, six-metric quota UI, explicit quota-status chip, polished summary header, and renderer/event tests. -->

## 4. Documentation And Validation

- [x] Update protocol documentation.
- [x] Run targeted edge and cloud tests/typechecks relevant to protocol, snapshot, and Electron UI.

Validation:

- `openspec validate edge-account-daily-quota-summary --strict`
- `aidcp-cloud`: `npm run typecheck`; `npx tsx --test test/comm/ui-snapshot.test.ts`
- `aidcp-edge`: `npm run typecheck`; `npx tsx --test test/flows/ui-event-lines.test.ts test/electron/ui-events.test.ts test/electron/companion-ui.test.ts`
