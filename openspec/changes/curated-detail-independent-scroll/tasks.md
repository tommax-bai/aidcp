## 1. Contract

- [x] 1.1 Complete proposal, design, tasks, and `edge-companion-ui` delta for independent curated-detail scrolling.
- [x] 1.2 Validate the change with `openspec validate curated-detail-independent-scroll --strict`. <!-- 2026-07-18 strict valid before implementation -->

## 2. Edge Renderer

- [x] 2.1 Add wide-layout scroll coordination that advances both detail columns and clamps each at its own boundary.
- [x] 2.2 Constrain the wide detail viewport, add bounded trailing space, contain column overscroll, and preserve the existing narrow single-column fallback.
- [x] 2.3 Ensure page changes and rerenders reset detail scroll positions without leaking event listeners.

## 3. Verification

- [x] 3.1 Add focused renderer tests for either column reaching bottom first, reverse scrolling, pointer-over-finished-column continuation, and narrow-layout bypass.
- [x] 3.2 Run focused content-workspace tests, the full edge test suite, and `npm run typecheck`. <!-- focused renderer: 74 pass; typecheck passed; full suite: 1748 pass / 1 pre-existing Windows-only POSIX mode assertion failure, reproduced unchanged in canonical master at customer-auth-security.test.ts:67 -->
- [x] 3.3 Record the edge implementation commit and validation evidence in this task file. <!-- aidcp-edge 1946acf pushed to origin/curated-detail-independent-scroll: four renderer/test files, focused 74 pass, typecheck pass -->

## 4. Integration

- [ ] 4.1 Rebase the edge worktree onto current `origin/master`, rerun required validation, and fast-forward the change to `master`.
- [ ] 4.2 Push the edge default branch and record integration evidence; do not package a desktop installer unless explicitly requested.
- [ ] 4.3 Update the OpenSpec task evidence, re-run strict validation, commit and push the control-repo change, then archive only when all required work is complete.

<!-- 2026-07-18 integration attempt: rebase onto origin/master was current; acceptance 24/24 passed; full suite 1748/1749 passed. land-change correctly stopped before push because the Windows host reports 0666 for the pre-existing POSIX 0600 assertion in test/electron/customer-auth-security.test.ts:67. The same failure reproduces on untouched canonical master. No bypass or default-branch push was performed. -->
