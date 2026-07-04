## Why

`warned` risk state currently scales conservative quotas by `0.7` with downward rounding.
For low-frequency interaction windows whose baseline is `1`, this produces `0`, so a
temporary `warned` state blocks every like, collect, comment, follow, and comment-like at
the minute window. That is stricter than intended: `warned` should slow and reduce
interactive behavior, not silently turn all interaction categories into hard-zero quotas.

## What Changes

- Change risk quota scaling from downward rounding to upward rounding.
- Preserve hard stop semantics for `restricted` and `frozen`; multiplying by `0` still
  yields `0`.
- Add regression coverage that `warned` keeps low-frequency minute windows at `1` instead
  of collapsing them to `0`.

## Impact

- Affects `aidcp-cloud` risk quota calculation only.
- Does not change protocol, edge routing, account state transitions, or quota config
  storage.
- `warned` accounts remain publish-paused and reduced against conservative quotas, but
  sparse interactions can pass the quota gate again.
