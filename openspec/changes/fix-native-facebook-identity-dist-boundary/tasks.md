## 1. Separate the production-safe identity boundary

- [x] 1.1 Move canonical Facebook post identity and Native presentation classifiers into a pure module with no page-rule imports.
- [x] 1.2 Preserve the existing mixed-module exports for development consumers and route Native browse orchestration directly to the pure module.

## 2. Guard the production graph

- [x] 2.1 Add focused coverage for the pure helper compatibility and Native import boundary.
- [x] 2.2 Prove the production `dist` build rejects retired page-rule reachability and succeeds after the split.

## 3. Validate and integrate

- [x] 3.1 Run focused tests, full Edge tests, typecheck, desktop build-input verification, and production-dist verification.
- [ ] 3.2 Run strict OpenSpec validation and record Edge/control commits, validation, and artifact/live-account boundaries.
