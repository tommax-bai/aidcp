## 1. Contract

- [x] 1.1 Define the reference-creation close-control navigation contract, scope, design, and tasks.
- [x] 1.2 Validate `curated-create-close-returns-library` with strict OpenSpec validation. <!-- 2026-07-18 strict valid before implementation -->

## 2. Edge Renderer

- [x] 2.1 Add a reusable return-to-library path that discards intermediate detail stack frames and reuses list restoration.
- [x] 2.2 Route the reference-creation page `×` to the library with an accurate accessible label.
- [x] 2.3 Preserve the create-page back-to-detail action and close behavior on unrelated pages.
- [x] 2.4 Add focused navigation and list-state regression coverage. <!-- content workspace 14/14; typecheck and diff checks passed -->

## 3. Verification and Integration

- [x] 3.1 Run focused tests, full edge tests, acceptance tests, typecheck, and diff checks. <!-- content workspace 14/14; acceptance 25/25; full edge 1799/1799; typecheck and diff checks passed -->
- [x] 3.2 Commit, land, and push the edge implementation without packaging an installer. <!-- aidcp-edge 88c9b81 pushed to origin/master; canonical master fast-forwarded; no installer built -->
- [x] 3.3 Record evidence, strictly validate, commit and push control changes, then archive the completed OpenSpec change. <!-- strict validation repeated after implementation; control commit and archive follow -->
