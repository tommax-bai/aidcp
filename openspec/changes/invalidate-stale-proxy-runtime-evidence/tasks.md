## 1. Contract

- [x] 1.1 Validate the runtime-evidence, preflight-projection, and fleet-console deltas against the existing proxy-state authority boundaries.

## 2. Edge implementation

- [x] 2.1 Add one canonical stale projection that preserves only a bounded generation marker while clearing IPs, timestamps, and session traffic.
- [x] 2.2 Apply invalidation before a no-child replacement start and on confirmed standby, child error, or child close, without clearing on an unconfirmed close request.
- [x] 2.3 Add focused regressions for stopped, failed-preflight, cold-standby, and live-current-generation projections.

## 3. Validation and delivery

- [x] 3.1 Run focused Edge proxy/lifecycle tests and typecheck.
- [x] 3.2 Run the full Edge test suite and strict OpenSpec validation.
- [x] 3.3 Record implementation commits, validation, and the source-only desktop delivery boundary.

<!--
Implementation: aidcp-edge 5541ba8 (canonical stale projection, lifecycle invalidation, and regressions).
Validation: focused proxy/lifecycle tests 34/34; npm run typecheck; full Edge suite 2707 passed, 0 failed, 1 gated skip; openspec validate invalidate-stale-proxy-runtime-evidence --strict.
Delivery: aidcp-edge commit 5541ba8 was pushed to master. Source-only desktop delivery; no installer was built or released, so an already installed 0.3.25 client is unchanged.
Deviation: the first full-suite run had one load-sensitive Native Page Engine engine_timeout; its focused file then passed 13/13 and the final full suite passed with zero failures.
-->
