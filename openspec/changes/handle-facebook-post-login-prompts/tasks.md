## 1. Capture live prompt contracts

- [x] 1.1 Record redacted fixtures for the exact ad-data introduction, successor choice, temporary loading shell, and same-label Feed card negative case. <!-- aidcp-edge test/native-page-engine/facebook-auth-router.test.ts; live text/route shapes only, no account data -->
- [x] 1.2 Add a regression fixture for a Remember Password modal that appears after the first authenticated observation. <!-- aidcp-edge test/native-page-engine/facebook-auth.test.ts -->

## 2. Extend Native Facebook prompt recognition and actions

- [x] 2.1 Add the document-bound `ad_data_review_get_started` signal and exact route/content/target guards to the Facebook auth router. <!-- aidcp-edge native/page-engine/src/facebook-router/06-auth.js -->
- [x] 2.2 Add `facebook_auth_start_ad_data_review` to Native command types, capability parity, TypeScript client mapping, and one-signal/one-action execution. <!-- aidcp-edge Native command/capability/auth plus TypeScript client/coordinator -->
- [x] 2.3 Implement the 30-second successor verifier so loading/disabled/target disappearance are observed but only the exact successor choice confirms success; preserve no-replay ambiguity. <!-- aidcp-edge exact successor fixture and Rust duration assertion -->
- [x] 2.4 Verify existing Remember Password `OK` uses the Native move-before-press/release path and does not confirm from loading or disabled state alone. <!-- aidcp-edge shared dispatch_pointer_click plus loading/disabled postcondition regressions -->

## 3. Hold startup through late prompts and manual choice

- [x] 3.1 Add a 15-second authenticated quiet window to the serial Facebook startup coordinator and reset it after supported prompt actions. <!-- aidcp-edge coordinator plus production assembly test -->
- [x] 3.2 Classify the exact successor as enumerated `facebook_ad_data_choice_required` without automatically selecting or confirming any privacy/ad option. <!-- aidcp-edge exact router state; no choice command added -->
- [x] 3.3 Add retained-wait identity-read deferral while the manual choice remains unresolved, then resume stable identity in the same generation after a new quiet window. <!-- aidcp-edge self-identity defer preflight and main assembly -->
- [x] 3.4 Project the enumerated manual-choice reason as “需要处理” and preserve existing confirmed pause/close handling. <!-- aidcp-edge Electron enumerated reason regression -->

## 4. Validate and deliver

- [x] 4.1 Run focused router/coordinator/identity-wait/Electron lifecycle tests and Edge typecheck. <!-- 81 focused tests passed; npm run typecheck passed -->
- [x] 4.2 Run Native formatting, clippy, focused Facebook tests, and proportionate full Native tests serially where needed. <!-- fmt/clippy passed; Rust library 187/187 plus all integration/doc tests passed with RUST_TEST_THREADS=1 -->
- [x] 4.3 Run `openspec validate handle-facebook-post-login-prompts --strict` and `git diff --check` in both repositories. <!-- strict validation and both diff checks passed -->
- [x] 4.4 Commit the isolated Edge and control changes, integrate by fast-forward onto current defaults, push, and record validation plus the no-package/no-install boundary. <!-- Edge dfb57f1; control delivered by this containing commit; no package/build/install/deploy performed -->
