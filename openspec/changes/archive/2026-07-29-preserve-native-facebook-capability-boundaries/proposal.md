## Why

Facebook platform behavior is a core product asset discovered through real-page exploration, but the Native cutover preserved command envelopes more reliably than the capability-specific state machines behind them. The current Feed Like, Reels interaction, and Group Join repairs restore individual behaviors while continuing to overlap one large Rust engine and one browser router, so integration must preserve those fixes without recreating the same maintenance and parity risk.

## What Changes

- Integrate the independently developed Feed Like, Reels Like/Follow, and Group Join parity changes through one serialized Edge integration boundary.
- Make each supported Native Facebook capability own its complete page-operation choreography: exact target resolution, fresh pre-commit validation, platform-specific actuation, same-target verification, terminal reason semantics, and one bounded command budget.
- Split Facebook session state and capability workflows out of the generic Native engine into platform-owned modules; keep the shared engine responsible only for session supervision, command lifecycle, CDP transport, cancellation, and typed result delivery.
- Restore the proven Facebook Join, Comment, and Publish commit-window contract through a bounded local Native-to-host handshake, so the task coordinator knows when an irreversible write is protected and never preempts it as if no write had started.
- Split the embedded Facebook browser logic by stable capability responsibility and assemble it into the existing encoded Native router artifact without exposing selectors or executable page rules to TypeScript or package resources.
- Add a behavior-parity ledger and regression gates derived from the retired Facebook executors for every Native-supported Facebook command; commands without a complete capability implementation remain `capability_unsupported`.
- Preserve the current Cloud/Edge protocol, Cloud policy, risk ownership, capability names, and Native-only/no-JavaScript-fallback boundary; the commit-window handshake is confined to the supervised local Edge/Native lifecycle protocol.

## Capabilities

### New Capabilities

- `native-facebook-capability-runtime`: Defines capability-owned Native Facebook execution boundaries, behavior-oracle preservation, action-specific actuation, unified deadlines, and regression gates.

### Modified Capabilities

<!-- No baseline capability semantics change; the existing Feed Like, Reel interaction, and Group Join changes remain the owners of their platform behavior deltas. -->

## Impact

- `aidcp-edge/native/page-engine/src/engine.rs` becomes a platform-neutral dispatcher for Facebook operations rather than the owner of Facebook capability state machines.
- New Native Facebook Rust modules own session/feed, Feed Like, Reels interaction, Group Join, comment, publish, and shared Facebook result helpers.
- The local Native process protocol gains a correlated commit-window request/ack lifecycle used by the existing Edge `CommitWindowGuard`; no Cloud message changes.
- The embedded Facebook router is assembled from capability-owned source modules while remaining one encoded build artifact.
- Native router, Rust, facade, acceptance, full Edge, typecheck, build-artifact, and strict OpenSpec validation are required after serialized integration.
- No Cloud protocol, database, Console, installer, signing, OL deployment, or real-account write is included; real Facebook acceptance remains a separate explicitly authorized runtime gate.
