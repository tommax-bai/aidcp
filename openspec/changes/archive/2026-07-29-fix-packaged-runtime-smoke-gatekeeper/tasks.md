## 1. Gatekeeper-safe packaged smoke

- [x] 1.1 Resolve and verify the trusted development Electron runner for same-architecture macOS packaging
- [x] 1.2 Execute the final packaged ASAR smoke with the trusted runner while preserving existing static and cross-architecture gates
- [x] 1.3 Surface bounded, actionable child-process failure evidence

## 2. Regression coverage

- [x] 2.1 Add contract tests for macOS trusted-runner selection, signature verification, and non-macOS/cross-architecture behavior
- [x] 2.2 Run focused packaging tests and Edge typecheck
  <!-- Edge validation: 15 focused tests passed; `npm run typecheck` passed. -->
- [x] 2.3 Build an arm64 OL directory artifact and confirm the packaged smoke passes without a Gatekeeper block
  <!-- `electron:build:mac -- --arm64 --dir --publish never` passed with OL metadata (`http://123.56.253.183:8088/capi`); dynamic ASAR smoke loaded jsdom, tough-cookie, and ws. -->

## 3. Delivery record

- [x] 3.1 Run strict OpenSpec validation and record Edge commit/validation results
  <!-- Edge: 62b979c. Validation: 15 focused tests, typecheck, and arm64 OL directory packaging passed. OpenSpec strict validation passed before control commit. -->
