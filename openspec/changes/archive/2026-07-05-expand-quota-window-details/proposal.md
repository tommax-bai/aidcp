## Why

The current Electron quota strip only exposes the worst action for each quota window. Operators can read it as missing data: session appears to contain only likes, minute appears to contain only views, and hour appears similarly partial.

The companion should keep the default card focused on the authoritative daily summary, then reveal complete per-window detail on demand.

## What Changes

- Keep the default "today usage" card focused on the account daily totals for view, like, collect, comment, follow, and publish.
- Make the daily summary card expandable; the expanded area shows session, minute, hour, and day as peer quota windows.
- In the expanded area, each supplied window shows all six actions, not only the worst action.
- Cloud fills the session window with all six action totals where data exists: interaction actions from the active session budget and view/publish from account activity since the session started. Session quotas remain honest: actions without a session cap do not get fabricated caps.
- Cloud supplies window timing metadata for rolling windows, and Electron expires stale minute/hour quota windows locally when no fresher cloud snapshot has arrived.
- Preserve the existing backward-compatible day aliases and old daily-only behavior.

## Impact

- Protocol: no breaking field rename; window payloads become more complete.
- Cloud: session window aggregation reads current-session view/publish counts in addition to interaction budget usage.
- Edge/Electron: daily summary becomes a compact expandable disclosure with a complete quota detail matrix.
- Release: cloud requires ECS deployment; Electron Windows installer should be rebuilt after edge change.
