## 1. Contract

- [x] 1.1 Capture the local-only browser inspection boundary, status hierarchy, ownership checks, and non-authoritative auth semantics in OpenSpec.

## 2. Edge desktop implementation

- [x] 2.1 Add the narrow, serialized AdsPower `browser/start` method for trusted manual inspection.
- [x] 2.2 Add a named local-open IPC with current-customer WeChat environment validation and no Cloud or engine lifecycle dependency.
- [x] 2.3 Update the interaction workspace to prioritize engine/auth status and move browser state/opening into a secondary manual-inspection area.

## 3. Validation and integration

- [x] 3.1 Add focused AdsPower, IPC security, and interaction workspace tests.
- [x] 3.2 Run focused tests and `npm run typecheck` in `aidcp-edge`.
- [x] 3.3 Run `openspec validate wechat-local-browser-inspection-control --strict`.
- [ ] 3.4 Commit, integrate, and push `aidcp-edge` master and `aidcp` main; record commit SHAs and validation evidence.

<!-- Validation: aidcp-edge focused interaction/IPC/AdsPower tests 62 passed; renderer smoke tests 61 passed; npm run typecheck passed. OpenSpec strict validation passed. -->
