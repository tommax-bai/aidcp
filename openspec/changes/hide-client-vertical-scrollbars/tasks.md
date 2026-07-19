## 1. Contract

- [x] 1.1 Define the vertical-only scrollbar visibility contract, design, and implementation tasks.
- [x] 1.2 Validate `hide-client-vertical-scrollbars` with strict OpenSpec validation. <!-- 2026-07-19 strict valid before implementation -->

## 2. Edge Renderer

- [x] 2.1 Hide only the vertical Chromium scrollbars for the document root, activity stream, and developer log.
- [x] 2.2 Preserve native scrolling, existing overflow rules, and all horizontal scrollbar behavior.
- [x] 2.3 Add focused style-contract assertions for scope and axis isolation.

## 3. Verification and Integration

- [x] 3.1 Run focused renderer tests and typecheck. <!-- renderer-smoke 63/63; typecheck passed -->
- [x] 3.2 Commit the edge implementation, rebase, land to `master`, and push without packaging an installer. <!-- aidcp-edge 319ef31 pushed to origin/master; acceptance 25/25; full 1836/1836; typecheck passed; no installer built -->
- [ ] 3.3 Record evidence, strictly validate, commit and push control changes, then archive the completed OpenSpec change.
