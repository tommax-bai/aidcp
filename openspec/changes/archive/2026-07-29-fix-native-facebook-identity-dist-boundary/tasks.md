## 1. Separate the production-safe identity boundary

- [x] 1.1 Move canonical Facebook post identity and Native presentation classifiers into a pure module with no page-rule imports.
- [x] 1.2 Preserve the existing mixed-module exports for development consumers and route Native browse orchestration directly to the pure module.

## 2. Guard the production graph

- [x] 2.1 Add focused coverage for the pure helper compatibility and Native import boundary.
- [x] 2.2 Prove the production `dist` build rejects retired page-rule reachability and succeeds after the split.

## 3. Validate and integrate

- [x] 3.1 Run focused tests, full Edge tests, typecheck, desktop build-input verification, and production-dist verification.
- [x] 3.2 Run strict OpenSpec validation and record Edge/control commits, validation, and artifact/live-account boundaries.
  <!-- Edge fe6023d + 9388df2: focused 34/34, acceptance 30/30, full 2346/2346, typecheck pass, desktop build-input pass, and production dist reachable=79 removed=63 legacy_page_rules=absent source_maps=absent. Control artifacts 9080ec5; strict OpenSpec validation passed. This change does not alter Rust, package/sign an installer, deploy a client, or perform real-account Facebook writes. -->
