## 1. Contract

- [x] 1.1 Define the curated-list title and status-label hierarchy, isolation, design, and tasks.
- [x] 1.2 Validate `curated-list-card-typography` with strict OpenSpec validation. <!-- 2026-07-18 strict valid before implementation -->

## 2. Edge Renderer

- [x] 2.1 Set curated list card titles to the approved font stack at `16px / 700` while preserving single-line ellipsis.
- [x] 2.2 Set list card creation-state labels to the same font stack at `11px / 700`.
- [x] 2.3 Keep curated detail badges at `9.5px` and preserve existing card layout behavior.
- [x] 2.4 Add focused style-contract regression coverage. <!-- renderer smoke 62/62; typecheck and diff checks passed -->

## 3. Verification and Integration

- [x] 3.1 Run focused tests, full edge tests, acceptance tests, typecheck, and diff checks. <!-- renderer smoke 62/62; acceptance 24/24; full edge 1779/1779; typecheck and diff checks passed -->
- [x] 3.2 Commit, land, and push the edge implementation without packaging an installer. <!-- aidcp-edge 9d8be1d pushed to origin/master; canonical master fast-forwarded; no installer built -->
- [x] 3.3 Record evidence, strictly validate, commit and push control changes, then archive the completed OpenSpec change. <!-- strict validation repeated after implementation; control commit and archive follow -->
