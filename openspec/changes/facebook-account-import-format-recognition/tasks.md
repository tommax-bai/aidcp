## 1. Parser Coverage

- [x] 1.1 Add focused tests for `uid|password|2FA|email|cookie|access_token`, including field mapping, embedded Cookie pipes, UID/`c_user` consistency, and omission of ignored secrets. <!-- aidcp-edge: synthetic-only focused coverage added; pre-implementation run passed 8/12 and failed the four new behavior tests as expected -->
- [x] 1.2 Add mixed-batch, unknown/invalid layout, ambiguity/fail-closed, legacy regression, and credential-safe error tests. <!-- aidcp-edge: mixed three-layout, unknown, deterministic ambiguity, mismatch, and secret-safe assertions added -->

## 2. Edge Implementation

- [x] 2.1 Refactor the shared Facebook account parser to evaluate an extensible rule registry and accept only one valid candidate while preserving existing formats. <!-- aidcp-edge: three deterministic rules now return no_match/error/match and the shared selector fails closed unless exactly one candidate matches -->
- [x] 2.2 Add the UID/password/2FA/email/Cookie/Token rule with deterministic field validators, two-ended Cookie extraction, shared normalization, and identity cross-checking. <!-- aidcp-edge: new rule validates numeric UID, email shape, Base32 2FA, non-empty token boundary, reconstructs Cookie from the middle, and reuses c_user equality validation -->
- [x] 2.3 Update the Facebook account import placeholder/help copy to describe automatic recognition, the three supported layouts, and discarded Token fields without promising arbitrary compatibility. <!-- aidcp-edge: renderer copy lists all three layouts and states unknown/ambiguous formats are rejected -->

## 3. Validation

- [x] 3.1 Run focused Facebook account-import and relevant Electron create/write/renderer tests. <!-- aidcp-edge: npx tsx --test over six focused Electron files PASS 119/119; parser-only PASS 12/12 -->
- [x] 3.2 Run the full Edge test suite and `npm run typecheck`; inspect bounded failures rather than inferring success from truncated output. <!-- aidcp-edge: pre-integration npm test PASS 1889/1889, test:acceptance PASS 25/25, typecheck/build PASS; after rebase onto latest origin/master npm test PASS 1900/1900 and typecheck/build PASS -->
- [x] 3.3 Run `openspec validate facebook-account-import-format-recognition --strict` and confirm the Edge/control worktrees contain no pasted real credentials. <!-- control: strict validation PASS; targeted scan of both worktrees found no supplied email-domain, c_user-prefix, or token-prefix fragments -->

## 4. Integration

- [x] 4.1 Commit the Edge implementation with validation evidence, rebase onto the latest `master`, fast-forward integrate it into the clean canonical checkout, and push `origin/master`. <!-- aidcp-edge b0135ffdd1f86734c314fd6c9215bb5a041244f3 on master; origin/master pushed; post-rebase npm test 1900/1900, typecheck/build PASS; no installer built -->
- [ ] 4.2 Record repo/commit/validation/deviation evidence in this task file, commit the OpenSpec change, fast-forward integrate it into control `main`, and push `origin/main`; do not package an installer.
