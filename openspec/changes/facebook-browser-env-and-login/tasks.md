## 1. Preconditions and Scope

- [x] 1.1 Confirm `platform-abstraction-layer` is implemented, validated, and archived before starting Facebook runtime code.
  <!-- done 2026-07-06: platform-abstraction-layer was validated, deployed to dev, and archived in aidcp commit 6c0b170 before Facebook runtime code began. -->
- [x] 1.2 Open same-name worktree for `aidcp-edge`; open `aidcp-cloud` only if probe reporting or platform validation requires cloud changes.
  <!-- done 2026-07-06: edge worktree /Users/baitianxing/codes/aidcp-edge.wt/facebook-browser-env-and-login on branch codex/facebook-browser-env-and-login. Cloud worktree not opened because this tranche only added edge probes/driver metadata. -->
- [ ] 1.3 Prepare a disposable Facebook AdsPower profile and test target; do not use production accounts for gated post probes.
  <!-- partial 2026-07-06: created AdsPower profile k1ebny3j in group aidcp-probe, name "FB Probe - 2026-07-06", status unverified, no proxy configured. Test URL matrix captured in probe-plan.md; gated submit target still requires operator-created disposable post URL after manual login. -->
  <!-- partial 2026-07-06: created additional logged-out F2-only AdsPower profile k1ecc0b2 in group aidcp-probe, name "FB F2 Logged-out Probe - 2026-07-06". It is for login-wall/checkpoint detection only. Gated F1 submit target is still missing. -->

## 2. Facebook Startup and Identity

- [x] 2.1 Add Facebook platform startup target descriptor with Facebook start URL and allowed tab predicates.
  <!-- done 2026-07-06: edge commit 3a5ea7a adds FACEBOOK_TARGET, platform URL allow-listing, and CDP targetPredicate selection for AdsPower attach. -->
- [x] 2.2 Implement minimal Facebook driver skeleton with `platform='facebook'`, capability metadata, `readIdentity`, and `detectOverlay`.
  <!-- done 2026-07-06: edge commit 3a5ea7a registers facebookPlatformDriver with identity/overlay only; browse/comment/publish are intentionally not advertised. -->
- [x] 2.3 Add identity probe logic that returns a stable id or fails honestly; reject display-name-only and conflicting candidates.
  <!-- partial 2026-07-06: post-challenge probe found logged-in candidate signals and profile-link/account-menu candidates, but did not persist a raw stable Facebook id. Identity is not considered passed yet. See post-challenge-logged-in-probe-findings.md. -->
  <!-- done 2026-07-06: edge commit 3a5ea7a implements numeric-id-only derivation; display-name-only and conflicting candidates fail honestly. Live stable-id confirmation still belongs to the Phase-0 gates. -->
- [x] 2.4 Add tests for Facebook identity success, no-id failure, display-name-only rejection, and conflicting-candidate rejection.
  <!-- done 2026-07-06: test/facebook/identity.test.ts covers stable success, display-name-only failure, conflicting candidates, invalid JSON, and readFacebookIdentity success. -->

## 3. Storage-Safe and Fingerprint Probes

- [x] 3.1 Add storage summary probe for cookies/localStorage/sessionStorage/IndexedDB/cache presence with value redaction by construction.
  <!-- partial 2026-07-06: post-challenge probe recorded storage counts only: localStorage 11-12, sessionStorage 1-3, IndexedDB 22, Cache 0. No raw values were saved. -->
  <!-- done 2026-07-06: edge commit 3a5ea7a adds collectFacebookStorageSummary; cookie values are immediately bucketed by length, and storage probes read keys/counts only. -->
  <!-- done 2026-07-06: live baseline proved raw storage key/name strings can contain account-scoped or HMAC-like fragments. Edge runner now outputs key/name hash, length bucket, contains-digit, and token-like flags only; no raw storage keys/names. -->
- [x] 3.2 Add fingerprint/provider sanity probe for AdsPower Facebook profiles using safe non-secret fields.
  <!-- done 2026-07-06: edge commit 3a5ea7a adds collectFacebookFingerprintSummary for viewport/language/timezone/webdriver/plugins plus providerKind/stealth metadata. -->
- [x] 3.3 Add tests or snapshot checks proving probe output does not include raw storage values, tokens, cookie values, or credentials.
  <!-- done 2026-07-06: test/facebook/probes.test.ts verifies raw cookie values and synthetic session token values are absent from serialized probe output. -->
  <!-- done 2026-07-06: test/facebook/probes.test.ts also verifies raw storage key/name sentinel strings are absent after key/name hash redaction. -->

## 4. Page Structure and Editor Probes

- [x] 4.1 Add read-only Page/Group/post structure probe that records post container, permalink/id, author/text, comments region, expand controls, and virtualization observations.
  <!-- partial 2026-07-06: post-challenge read-only probe recorded Page, Page permalink, and Group post structure counts. Page permalink is the best next editor probe target. Group post still showed a visible join control and must be permission-gated. -->
  <!-- partial 2026-07-06: Group/search/post access probe recorded slug and numeric group entry, group internal search, global search, permalink extraction, and search-result post access. See group-search-post-probe-findings.md. -->
  <!-- partial 2026-07-06: narrow layout probe at 430x932 and 768x900 confirmed URL-first Group/search/post routes remain usable. See narrow-layout-probe-findings.md. -->
  <!-- done 2026-07-06: edge commit 224b196 adds collectFacebookPageStructure with surface classification, permalink normalization, article/editor/comment/expand counts, membership signals, and virtualization metadata. Probe output records structure, not raw post body text. -->
  <!-- done 2026-07-06: edge follow-up strips nonessential Facebook tracking/context query params from permalink candidates and drops raw internal permalinkHrefs from final output. -->
- [x] 4.2 Add read-only comment editor probe that tests focus, controlled input, send-button enablement, and clearing without submitting.
  <!-- partial 2026-07-06: observed Facebook comment editors as div[contenteditable="true"][role="textbox"] with aria-label "写评论…" on Page surfaces. Group sample used "输入回答…" and is not submit-ready until membership is proven. -->
  <!-- partial 2026-07-06: Page permalink editor probe passed focus/type/control-observe/clear without submitting. Marker was accepted by controlled editor, "发布评论" control appeared, keyboard clear left final text length 0. See editor-probe-findings.md. -->
  <!-- partial 2026-07-06: Group post/editor surfaces still showed join signals; do not run Group editor input/submit until membership classifier proves permissions. -->
  <!-- partial 2026-07-06: Page permalink editor focus/type/clear also passed under 430x932 and 768x900 viewport overrides; locator should avoid desktop-only geometry. -->
  <!-- done 2026-07-06: edge commit 224b196 adds probeFacebookCommentEditorReadOnly. It focuses semantic contenteditable textbox, inserts a synthetic marker, observes submit-control enablement, clears with keyboard, returns marker hash only, and never submits. Group-like/join-visible editors fail as permission_gated before typing. -->
- [x] 4.3 Add gated submit probe requiring explicit env flag, disposable account, and target URL; default must refuse to post.
  <!-- done 2026-07-06: edge commit 224b196 adds facebookGatedSubmitPreflight. Default disabled, missing disposable confirmation, missing target URL, non-Facebook URL, target mismatch, and overlay blocking all refuse before any submit implementation. Actual F1 submit remains a gated real-machine Phase-0 task. -->

## 5. Checkpoint/Login Detection

- [x] 5.1 Extend overlay detection with Facebook URL/location classifiers for checkpoint, login, account recovery, and temporarily blocked pages.
  <!-- partial 2026-07-06: ran logged-out AdsPower probe with profile k1ebny3j. Findings recorded in logged-out-probe-findings.md. Pure login, public-content-with-login-overlay, login redirect with next, and direct checkpoint normalization are now understood for first classifier design. -->
  <!-- partial 2026-07-06: manual login triggered Meta human verification under /two_step_verification/authentication/ with fbsbx captcha and google recaptcha frames. Findings recorded in login-challenge-findings.md; classifier must fail closed before further navigation. -->
  <!-- done 2026-07-06: edge commit 3a5ea7a adds classifyFacebookOverlay and FacebookOverlayMonitor; checkpoint/two_step_verification/captcha frames classify as captcha, login/recover as login, temporary block/help states as unknown. -->
- [x] 5.2 Run blocking-state detection before any gated submit attempt.
  <!-- done 2026-07-06: edge commit 224b196 runs classifyFacebookOverlay in facebookGatedSubmitPreflight and refuses with blocked_by_login / blocked_by_captcha / blocked_by_unknown before submit readiness. -->
- [x] 5.3 Add tests for checkpoint URL, login wall, temporarily blocked text, and clean Facebook page classification.
  <!-- partial 2026-07-06: test fixtures should include Simplified Chinese login labels and the public-content-with-login-overlay state so visible articles are not misclassified as logged-in readiness. -->
  <!-- partial 2026-07-06: test fixtures should include /two_step_verification/, fbsbx captcha frames, google recaptcha frames, and Simplified Chinese "进行人机身份验证" text. -->
  <!-- done 2026-07-06: test/facebook/overlay.test.ts covers checkpoint/human verification, login/recovery, temporary block, clean page, invalid JSON fail-closed, and sticky monitor errors. -->

## 6. Phase-0 Real-Machine Gates

- [ ] 6.1 Run F1 gated post probe on disposable account/test target and record whether server-confirmed comment verification is possible.
- [x] 6.2 Run F2 checkpoint/login URL detection probe and record honest stop outcomes.
  <!-- partial 2026-07-06: observed and manually handled captcha/login challenge during login. This is evidence for F2 detection design, but F2 is not passed until implemented classifier proves honest stop behavior. -->
  <!-- done 2026-07-06: live Phase-0 runner recorded logged-in and logged-out F2 outcomes in phase0-live-probe-findings.md. Logged-out / and /login classify as login; logged-out /checkpoint normalizes to / but still classifies login; /two_step_verification/authentication classifies captcha. No credential/checkpoint solving attempted. -->
- [ ] 6.3 Run F3 low-frequency AdsPower profile stability observation for several days and record result without secrets.
  <!-- partial 2026-07-06: short single-run startup/attach samples passed for k1ebny3j and k1ecc0b2 without immediate new checkpoint, but this is not multi-day low-frequency evidence. -->

## 7. Validation and Closeout

- [x] 7.1 Run relevant edge focused tests, then `npm test`, `npm run test:acceptance` where applicable, and `npm run typecheck`.
  <!-- done 2026-07-06: in edge worktree, git diff --check PASS; npm run typecheck PASS; focused tsx suite PASS 67/67; npm run test:acceptance PASS 13/13; npm test PASS 658/658. Rerun after any later edge changes. -->
  <!-- done 2026-07-06: after edge commit 224b196, git diff --check PASS; npm run typecheck PASS; focused Facebook/platform/CDP suite PASS 33/33; npm run test:acceptance PASS 13/13; npm test PASS 668/668. -->
  <!-- done 2026-07-06: after redaction/F2 runner changes, git diff --check PASS; npm run typecheck PASS; focused Facebook/platform/CDP suite PASS 35/35; npm run test:acceptance PASS 13/13; npm test PASS 670/670. -->
- [x] 7.2 If cloud code changed, run relevant cloud focused tests, acceptance, `npm test`, and `npm run typecheck`.
  <!-- done 2026-07-06: no cloud code changed in this tranche; cloud validation not applicable. -->
- [ ] 7.3 Record repo commit SHAs, probe outcomes, and validation notes in this `tasks.md`.
  <!-- partial 2026-07-06: edge commit 3a5ea7a records startup/identity/storage/fingerprint/overlay probe implementation and tests. Remaining probe outcomes: 4.x page/editor/gated submit code, F1 disposable submit, F2 implemented honest-stop real-machine run, F3 multi-day stability. -->
  <!-- partial 2026-07-06: edge commit 224b196 records Page/Group/post structure probe, read-only editor focus/type/clear probe, and gated submit preflight. Remaining probe outcomes: disposable AdsPower test target, F1 server-confirmed comment verification, F2 real-machine honest-stop run, and F3 multi-day stability. -->
  <!-- partial 2026-07-06: live F2 outcomes and redaction correction are recorded in phase0-live-probe-findings.md. Remaining probe outcomes: F1 server-confirmed comment verification on an operator-owned disposable post and F3 multi-day stability. -->
  <!-- partial 2026-07-06: edge commit 54e07cd adds the reusable Phase-0 manual probe runner and storage/permalink redaction hardening; control commit 7f18ba1 records live F2 findings and spec/design redaction corrections. Remaining probe outcomes: F1 server-confirmed comment verification on an operator-owned disposable post and F3 multi-day stability. -->
- [x] 7.4 Run `openspec validate facebook-browser-env-and-login --strict`.
  <!-- done 2026-07-06: PASS. Rerun after later 4.x/F-gate work changes artifacts. -->
  <!-- done 2026-07-06: PASS after storage key/name redaction spec update and F2 live probe findings. -->
- [ ] 7.5 Do not start `facebook-scheduled-comment` until F1/F2/F3 are all recorded as passed or the design is revised.
