## 1. Control contract

- [x] 1.1 Extend the WeChat Channels customer API schema with strict per-channel `syncFreshness` evidence and update list/detail fixtures for distinct, null and current timestamps.
  <!-- repo=aidcp commit=pending validation=customer schema fixtures pass deploy=n/a deviation=none -->
- [x] 1.2 Validate the contract metaschemas/fixtures and confirm no WS v2, protocol routing or risk-state contract changed.
  <!-- repo=aidcp commit=pending validation=check-jsonschema metaschema and customer fixtures pass deploy=n/a deviation=no ws/protocol/risk files changed -->

## 2. Cloud evidence and projection

- [x] 2.1 Add typed `SyncFreshness` store projection scoped by account/env/channel and return it from customer interaction list/detail without reusing `meta.asOf`.
  <!-- repo=aidcp-cloud commit=0e8dbd1 validation=focused store and customer API tests plus typecheck pass deploy=pending deviation=none -->
- [x] 2.2 Make a later `observedAt` for the same idempotent batch advance only sync evidence/cursor success time, while equal/older replays remain time-idempotent and business rows/jobs stay deduplicated.
  <!-- repo=aidcp-cloud commit=0e8dbd1 validation=unit replay cases pass; PostgreSQL integration case added but local test DB not configured deploy=pending deviation=none -->
- [x] 2.3 Add focused store/API tests for never-synced channels, different channel times, unchanged/empty later observations, equal/older replays, pagination snapshot separation and authorization non-enumeration.
  <!-- repo=aidcp-cloud commit=0e8dbd1 validation=4 pass 0 fail 3 PostgreSQL tests skipped for missing dedicated DB deploy=pending deviation=none -->

## 3. Edge honest display

- [x] 3.1 Consume strict `syncFreshness` in InteractionWorkspace, remove `meta.asOf` as data/health state, and render per-channel unknown, last-success, stale and clock-skew states without cross-environment leakage.
  <!-- repo=aidcp-edge commit=1a71428 validation=renderer honesty focus 6 pass and full renderer 24 pass deploy=n/a deviation=none -->
- [x] 3.2 Gate true empty states on target-channel sync evidence and distinguish sync request accepted from completion by comparing the post-request `receivedAt` with the captured env/channel baseline.
  <!-- repo=aidcp-edge commit=1a71428 validation=accepted/unadvanced/advanced empty refresh cases pass deploy=n/a deviation=none -->
- [x] 3.3 Update Edge fixtures and renderer tests for missing legacy fields, one-channel-only evidence, stopped historical time, Cloud offline, empty successful refresh, unadvanced accepted requests and late responses from another environment.
  <!-- repo=aidcp-edge commit=1a71428 validation=full interaction-workspace 24 pass 0 fail plus typecheck pass deploy=n/a deviation=none -->

## 4. Validation and delivery

- [ ] 4.1 Run focused Cloud interaction tests and `npm run typecheck`; run focused Edge Electron tests and `npm run typecheck`, retaining bounded pass/failure evidence.
- [ ] 4.2 Run `openspec validate wechat-sync-timestamp-honesty --strict`, then record repo, commit SHA, validation, deployment and deviations in this task ledger.
- [ ] 4.3 Rebase/integrate and push the control, Cloud and Edge default branches without force; deploy Cloud runtime changes to `dev` only after `scripts/deploy-target dev --check`, then verify documented service/listener/health/log/database boundaries. Do not build an Edge installer.
