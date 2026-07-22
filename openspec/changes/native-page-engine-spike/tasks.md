## 1. Native crate and protocol foundation

- [x] 1.1 Create the isolated `aidcp-edge` worktree and add a pinned Rust 2024 crate, toolchain file, release profile, and Cargo lockfile for `native/page-engine`.
- [x] 1.2 Implement protocol-v1 request/ready/response/error types, loopback endpoint validation, bounded request deadlines, and stdout/stderr separation.

## 2. Read-only CDP and page understanding

- [x] 2.1 Implement DevTools `/json` discovery and native Xiaohongshu target selection without accepting arbitrary WebSocket URLs or selectors from IPC.
- [x] 2.2 Implement the minimal correlated CDP WebSocket client with an internal allowlist limited to `Runtime.enable` and the constant read-only probe.
- [x] 2.3 Implement content-free Xiaohongshu structural signals and honest page-kind classification for `home`, `explore`, `search`, `note_detail`, `profile`, `login`, and `unknown`.
- [x] 2.4 Add deterministic Rust tests for protocol parsing, endpoint validation, target selection, allowlist enforcement, CDP response/error/timeout handling, and page classification.

## 3. Edge development integration and staging

- [x] 3.1 Add a TypeScript `NativePageEngineClient` that launches an explicitly supplied binary, verifies readiness/protocol, correlates one probe response, enforces timeout/kill, and maps process failures honestly.
- [x] 3.2 Add an explicit read-only development probe CLI; keep `src/main.ts` and all production browse/publish handlers free of Native Page Engine routing.
- [x] 3.3 Add an opt-in host release build/staging command that uses Cargo `--locked`, writes the binary outside ASAR under a deterministic platform/architecture directory, and records/verifies SHA-256.
- [x] 3.4 Add focused TypeScript tests for IPC success/failure/timeout and build/packaging isolation, including proof that ordinary Edge builds do not require Rust or the native artifact.

## 4. Validation and evidence

- [x] 4.1 Run Rust formatting, tests, lint/checks, and host release build; inspect the staged binary and record exact commands/results.
  <!-- aidcp-edge worktree: `cargo fmt --all -- --check`; `cargo test --locked` = 18 passed; `cargo clippy --locked --all-targets -- -D warnings`; `AIDCP_CARGO_BIN=/opt/homebrew/opt/rustup/bin/cargo npm run build:native-page-engine`; `npm run verify:native-page-engine` = darwin-arm64 unsigned host artifact SHA-256 6de8c09bf908d933214257f9722267df63ad8813b685382e5cdf1eda704a30ea. Build verification rejects cleartext page-script/selectors and write-operation markers. -->
- [x] 4.2 Install an independent worktree dependency tree, then run focused Edge tests, typecheck, and the ordinary TypeScript build without invoking Cargo.
  <!-- aidcp-edge worktree: physical `npm ci --prefer-offline`; native-focused tests 7/7; `npm run typecheck`; `npm run build:dist`; full `test/**/*.test.ts` suite exit 0. The worktree-local downloaded Electron.app was path-blocked by macOS provenance, so the Electron-embedded-Node test used official `ELECTRON_OVERRIDE_DIST_PATH` pointing at the canonical checkout's byte-identical Electron 31.7.7 arm64 runtime; focused test 5/5 and full suite passed. npm audit reported pre-existing 10 dependency advisories (1 low, 8 high, 1 critical); no dependency versions were changed. -->
- [x] 4.3 If an authorized local AdsPower Xiaohongshu page is available, run one read-only live probe and record visible-page parity; otherwise record the missing live precondition without claiming live validation.
  <!-- No live Xiaohongshu DevTools target was present. A read-only probe against the only current AdsPower endpoint (Douyin) fetched `/json` and returned `no_matching_target` in 0.54s, proving fail-closed target selection; no WebSocket attach or page action occurred. Xiaohongshu DOM/classification parity remains unvalidated. -->
- [x] 4.4 Run `openspec validate native-page-engine-spike --strict`, update this task record with repository commits, validation, packaging/deployment boundaries, and deviations, then integrate through the documented fast-forward workflow if every required gate passes.
  <!-- aidcp-edge commit `37843b0ccd397537c8ec6c02c338ecc0e9386711` was rebased onto the latest remote master, then landed by `scripts/land-change aidcp-edge native-page-engine-spike --yes` and pushed fast-forward to `origin/master`. Landing gates passed: acceptance 29/29, full Edge tests 2198/2198, and typecheck. The canonical aidcp-edge checkout was intentionally not forced to synchronize because it contains two separate local commits and now reports ahead 2/behind 1; the remote integration is complete. `openspec validate native-page-engine-spike --strict` passed. No installer was built, no artifact was signed or added to Electron `extraResources`, and nothing was deployed or released to customers. The missing live Xiaohongshu target is the only validation deviation. -->
