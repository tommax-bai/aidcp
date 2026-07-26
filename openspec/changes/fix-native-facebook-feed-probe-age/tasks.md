## 1. Native Feed probe contract

- [x] 1.1 Normalize Facebook `documentAgeMs` to a finite, non-negative integer at the embedded browser-router boundary.
  <!-- aidcp-edge 20245e8: browser router now emits a safe non-negative integer -->
- [x] 1.2 Add JavaScript producer and Rust consumer regression tests for a realistic fractional Chrome time origin and strict bounded-result decoding.
  <!-- aidcp-edge 20245e8; focused evidence: router contract 27/27; Rust targeted decode 1/1 -->

## 2. Validation

- [x] 2.1 Run focused router/Rust tests, Native build and verification, Edge acceptance, full tests, and typecheck.
  <!-- aidcp-edge 20245e8. Passed: router 27/27; targeted Rust decode 1/1; Rust unit 51/51; cargo fmt; acceptance 30/30; Edge full exit 0; typecheck; desktop build input; Native build/verify sha256 0026f176151b5edf0a47a8ee44a62381c409da3927661e6c08e882e85dc47286. Baseline deviations reproduced unchanged on Edge master: contract_fixtures explore_feed expects omitted optional fields but receives blockingKind/blockingText null; Rust 1.97 Clippy reports two pre-existing collapsible_if findings in engine.rs. -->
- [x] 2.2 Run `openspec validate fix-native-facebook-feed-probe-age --strict` and record validation results and deviations.
  <!-- Control worktree strict validation passed; runtime/test deviations are recorded under 2.1. -->

## 3. Integration and development delivery

- [ ] 3.1 Commit the isolated Edge and control changes with explicit pathspecs, then integrate and push both default branches through the documented fast-forward flow.
- [x] 3.2 Rebuild and verify the canonical local development Native artifact; keep installer, OL deployment, and real-account write acceptance explicitly out of scope.
  <!-- Canonical aidcp-edge master rebuilt and verified darwin-arm64 sha256 95ebc1709249ecac555a10392a1086439f1074aa3639a709e7af3c92dd80ea78. No Edge process remained running, so no resident old binary required restart. No installer/package, OL deployment, or real-account write acceptance was performed. -->
