## 1. Contract

- [x] 1.1 Define the curated-detail body typography contract, scope, design, and tasks.
- [x] 1.2 Validate `curated-detail-body-typography` with strict OpenSpec validation. <!-- 2026-07-18 strict valid before implementation -->

## 2. Edge Renderer

- [x] 2.1 Apply the approved font stack, `16px` size, and `400` weight to curated detail body text.
- [x] 2.2 Apply the same font stack with `14px` size and `400` weight only to library card body summaries.
- [x] 2.3 Preserve existing line-height, clamping, wrapping, spacing, and independent scrolling.
- [x] 2.4 Add focused style-contract regression coverage. <!-- renderer smoke 62/62; typecheck and diff checks passed -->

## 3. Verification and Integration

- [x] 3.1 Run focused tests, full edge tests, acceptance tests, typecheck, and diff checks. <!-- renderer smoke 62/62; acceptance 24/24; full edge 1776/1776; typecheck and diff checks passed -->
- [x] 3.2 Commit, land, and push the edge implementation without packaging an installer. <!-- aidcp-edge e6ecf04 pushed to origin/master; canonical master fast-forwarded; no installer built -->
- [x] 3.3 Record evidence, strictly validate, commit and push control changes, then archive the completed OpenSpec change. <!-- strict validation repeated after implementation; control commit and archive follow -->
