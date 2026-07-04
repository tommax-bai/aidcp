## Why

The Electron companion currently shows the "today" summary from local shell log deltas. That can drift from the actual account-scoped daily counters stored in cloud, especially after reconnects, multi-edge activity, or publish records that are not represented by the local four interaction counters.

Operators need the companion to answer three questions at a glance:

- how much this account has done today,
- whether follow and publish are also included,
- whether any visible action has reached the current quota level's daily limit.

## What Changes

- Add an optional account daily usage projection to `ui.snapshot`.
- Build the projection in cloud from account-scoped risk counters, account-scoped publish history, and the active risk quota level.
- Convert the projection into structured `[ui-event]` lines for the Electron shell.
- Render six compact daily metrics in Electron: views, likes, collects, comments, follows, publishes.
- Show quota caps, progress bars, and saturated states when cloud supplies limits, while keeping local log deltas as a fallback before the first snapshot arrives.

## Impact

- Protocol: backward-compatible optional field on `ui.snapshot`.
- Cloud: reads per-account daily counters and quota metadata.
- Edge: consumes a new structured UI event and keeps old log-derived counters working.
- Electron UI: visual redesign of the summary strip, preserving the existing light, polished companion design language.
