## Why

Facebook ordinary Feed videos are already counted as real `view` facts when Edge proves that one strict primary video is presented, but the desktop activity stream emits a readable entry only for Reels or a later detail open. This makes “今日进展” increase while “今天做了这些” omits the same-session Feed-video browse facts, as confirmed on Mi Xu.

## What Changes

- Emit one truthful “读” activity when Edge reports a newly presented ordinary Facebook Feed video that qualifies for Cloud view accounting.
- Use the reported card’s real caption and author when available, with a bounded generic fallback that exposes no URL or machine id.
- Deduplicate repeated presentation of the same canonical Feed-video identity and suppress a later detail activity for an already-projected video while still forwarding the detail to Cloud.
- Keep Cloud `dailyUsage` authoritative; the local activity event carries only the existing immediate fallback view increment.
- Classify the new Feed-video activity under the existing “读” marker and add focused session, formatter, and renderer regression coverage.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `edge-companion-ui`: Require every Cloud-countable ordinary Facebook Feed-video presentation to appear exactly once in “今天做了这些” without double-counting a later detail read.

## Impact

- `aidcp-edge`: Facebook session activity projection, companion-event wording/type, renderer activity classification, and focused tests.
- Control/OpenSpec: behavior contract, design, tasks, validation, and delivery evidence.
- No Cloud logic, protocol shape, database schema, Console code, ECS deployment, or Edge installer is required. A running development client must restart after source integration to load the new Edge behavior.
