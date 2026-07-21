## 1. Edge proxy password data path

- [x] 1.1 Keep the all-profile projection non-sensitive and reuse the exact-profile proxy reader for password-bearing configuration.
- [x] 1.2 Add a customer-scoped exact proxy-read IPC and update the existing-environment editor to load, display, and preserve the returned password for the selected target only.

## 2. Regression coverage and security boundaries

- [x] 2.1 Update normalization and IPC-scope tests for exact returned/absent passwords, including proof that the all-profile projection and environment summary remain non-sensitive.
- [x] 2.2 Add renderer coverage proving the target password is loaded on demand, visibly prefilled, and submitted unchanged when another proxy field is edited.
- [x] 2.3 Run focused Electron proxy/renderer tests and Edge typecheck; confirm write-body allowlisting, customer scope, and redaction tests remain green. <!-- aidcp-edge d725385 on top of b7c6dda + version 0063e4c; after physical `npm ci`, seven focused Electron files PASS including proxy preflight, customer scope, renderer and lifecycle; `npm run typecheck` PASS. Read-only local AdsPower probe: 30 profiles, 13 password fields, 12 non-empty; no values emitted. -->

## 3. Closeout

- [x] 3.1 Run `openspec validate preserve-client-proxy-password --strict` and record Edge commit and validation evidence in this task list. <!-- Strict validation PASS after exact-target design update; Edge commits b7c6dda, 0063e4c, d725385. -->
- [x] 3.2 Integrate the validated control and Edge commits onto their default branches and push; do not package or deploy a desktop installer unless separately requested. <!-- User separately authorized merge and deployment on 2026-07-21. Edge `master` fast-forwarded and pushed at d725385; control `main` fast-forwarded through 4468dac before this evidence update. -->
- [ ] 3.3 Build signed and notarized macOS `0.3.24` installers from merged Edge `master` with `dev` defaults, publish only to the dev downloads directory, and verify packaged code, baked target, hashes, sizes, and HTTP availability.
