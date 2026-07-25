## 1. Native Facebook startup baseline

- [x] 1.1 Route Facebook `browse_scroll{reason:'initial_scan'}` through trusted navigation to `https://www.facebook.com/` before card projection.
- [x] 1.2 Preserve honest failure semantics so navigation/readiness failure cannot report cards from the persisted page.

## 2. Regression coverage

- [x] 2.1 Add fake-CDP Rust coverage that starts from a persisted non-Feed Facebook page, proves home navigation precedes the first card evaluation, and rejects stale-page reads after navigation failure.
- [x] 2.2 Keep the shared Native session startup command and non-Facebook behavior unchanged under focused TypeScript tests.

## 3. Validation and delivery

- [x] 3.1 Run focused TypeScript and Rust tests, Rust all-targets, Native build/verification, Edge acceptance, full tests, and typecheck.
- [x] 3.2 Run `openspec validate facebook-startup-feed-baseline --strict` and record validation, commits, delivery boundary, and deviations.
  <!-- Validation: focused TypeScript 25/25; Rust all-targets 62/62; focused startup failure/success 2/2 after rebase; Clippy -D warnings; Edge acceptance 30/30; Edge full tests 2295/2295; typecheck; Native release build and encoded-rule verification; OpenSpec strict validation. Edge commit: bb7d41c. Deviations: none. -->
- [x] 3.3 Commit, rebase, fast-forward integrate, and push Edge and control changes; rebuild the canonical local Native binary without packaging an installer.
  <!-- Delivery: Edge master was fast-forwarded and pushed; the canonical local darwin-arm64 Native development binary was rebuilt and verified. No installer/package or live-account acceptance was performed; a running Edge process must restart to load the rebuilt binary. -->
