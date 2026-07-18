## 1. Contract

- [x] 1.1 Complete proposal, design, tasks, and `edge-companion-ui` delta for independent curated-detail scrolling.
- [x] 1.2 Validate the change with `openspec validate curated-detail-independent-scroll --strict`. <!-- 2026-07-18 strict valid before implementation -->

## 2. Edge Renderer

- [x] 2.1 Give each wide-layout detail column its own native scroll position without wheel coordination.
- [x] 2.2 Constrain the wide detail viewport, add bounded trailing space, contain column overscroll, and preserve the existing narrow single-column fallback.
- [x] 2.3 Ensure page changes and rerenders reset detail scroll positions without custom wheel listeners.
- [x] 2.4 Make the curated-detail header compact and sticky while retaining visible back and close controls.

## 3. Verification

- [x] 3.1 Add focused renderer tests for isolated column positions, unhandled native wheel input, and narrow-layout fallback.
- [x] 3.2 Run focused content-workspace tests, the full edge test suite, and `npm run typecheck`. <!-- final integration: acceptance 24/24, full edge 1770/1770, typecheck passed -->
- [x] 3.3 Record the edge implementation commit and validation evidence in this task file. <!-- aidcp-edge: 11c28ae independent column scroll; bf15d60 platform-aware POSIX mode test; b4c33d1 compact sticky detail header after rebase -->
- [x] 3.4 Add focused assertions for sticky compact header styling and the visible accessible close control. <!-- focused content-workspace + renderer 76/76; close remains visible with aria-label -->

## 4. Integration

- [x] 4.1 Rebase the edge worktree onto current `origin/master`, rerun required validation, and fast-forward the change to `master`. <!-- rebased onto b8c9b83; acceptance 24/24, full 1770/1770, typecheck passed -->
- [x] 4.2 Push the edge default branch and record integration evidence; do not package a desktop installer unless explicitly requested. <!-- origin/master b4c33d1; canonical master fast-forwarded; no installer built -->
- [ ] 4.3 Update the OpenSpec task evidence, re-run strict validation, commit and push the control-repo change, then archive only when all required work is complete.
