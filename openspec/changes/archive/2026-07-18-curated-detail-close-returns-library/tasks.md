## 1. Contract

- [x] 1.1 Define the curated-detail-only navigation contract, design, and implementation tasks.
- [x] 1.2 Validate `curated-detail-close-returns-library` with strict OpenSpec validation. <!-- 2026-07-18 strict valid before implementation -->

## 2. Edge Renderer

- [x] 2.1 Hide the left back control only in curated article detail and collapse its reserved header column.
- [x] 2.2 Route the detail `×` to the inspiration library while preserving list state; keep close behavior elsewhere.
- [x] 2.3 Set page-accurate accessible labels and add focused behavior/style regression coverage. <!-- focused renderer tests 76/76; typecheck passed -->

## 3. Verification and Integration

- [x] 3.1 Run focused renderer tests, full edge tests, acceptance tests, typecheck, and diff checks. <!-- focused 76/76; acceptance 24/24; full edge 1776/1776; typecheck and diff checks passed -->
- [x] 3.2 Commit the edge implementation, land it on the default branch, and push without packaging an installer. <!-- aidcp-edge dffa113 pushed to origin/master; canonical master fast-forwarded; no installer built -->
- [x] 3.3 Record evidence, strictly validate, commit and push control changes, then archive the completed OpenSpec change. <!-- strict validation repeated after implementation; control commit and archive follow -->
