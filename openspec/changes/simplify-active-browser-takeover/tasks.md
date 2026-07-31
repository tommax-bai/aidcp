## 1. Active Takeover and Proxy Preparation

- [x] 1.1 Add a race-safe Active-only startup path that bypasses Cloud authority, GOST, and preflight while refusing to fresh-start if Active disappears
- [x] 1.2 Remove expected/browser public-egress plumbing and make the AdsPower provider attach directly to every Active profile
- [x] 1.3 Reduce Facebook proxy preflight to bounded target reachability for Inactive fresh starts while preserving authority revision, cache, `no_proxy`, and double-hop behavior

## 2. Observation and UI

- [x] 2.1 Replace public-egress runtime observation with generation-scoped receive-traffic aggregation
- [x] 2.2 Remove browser/direct public-egress fields and verification conclusions from the Facebook proxy status UI
- [x] 2.3 Remove the obsolete Active-proxy takeover error classifier, terminal lifecycle branch, and associated status copy

## 3. Regression Coverage

- [x] 3.1 Update provider, preflight, Electron lifecycle, and startup-order tests for direct Active takeover and race-safe fresh-start protection
- [x] 3.2 Update traffic aggregation and renderer tests to prove no public-egress probing or display remains

## 4. Validation and Delivery

- [x] 4.1 Run focused Edge tests, full Edge tests, typecheck, and diff checks
- [x] 4.2 Run strict OpenSpec validation and record Edge commit, validation results, release boundary, and deviations

<!--
Implementation: aidcp-edge@0fda134, pushed to origin/master.
Validation: 94 focused tests passed; full Edge suite passed 2850 with 0 failures and 1 gated skip; typecheck, CJS syntax checks, diff checks, and strict OpenSpec validation passed.
Delivery: source only; no installer was built and no installed client was changed.
Deviation: an Active-takeover core refuses cold standby so a later Inactive relaunch cannot bypass the normal proxy preparation path.
-->
