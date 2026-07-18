## 1. Contract

- [x] 1.1 Define the scrollbar-visibility contract, design, and implementation tasks.
- [x] 1.2 Validate `hide-curated-detail-scrollbars` with strict OpenSpec validation. <!-- 2026-07-18 strict valid before implementation -->

## 2. Edge Renderer

- [x] 2.1 Hide standard and Chromium scrollbars only for the two curated-detail columns.
- [x] 2.2 Remove reserved scrollbar gutters while preserving `overflow-y: auto`, overscroll containment, and narrow fallback.
- [x] 2.3 Add focused style-contract assertions.
- [x] 2.4 Reduce the sticky detail header to a single row with only back, title, and close controls.
- [x] 2.5 Verify the sticky header keeps normal layout space and does not overlap detail content.

## 3. Verification and Integration

- [x] 3.1 Run focused renderer tests, full edge tests, acceptance tests, and typecheck. <!-- focused 76/76; acceptance 24/24; full edge 1770/1770; typecheck passed -->
- [x] 3.2 Commit the edge implementation, rebase, fast-forward to `master`, and push without packaging an installer. <!-- aidcp-edge 3ad6639 pushed to origin/master; canonical master fast-forwarded; no installer built -->
- [ ] 3.3 Record evidence, strictly validate, commit and push control changes, then archive the completed OpenSpec change.
