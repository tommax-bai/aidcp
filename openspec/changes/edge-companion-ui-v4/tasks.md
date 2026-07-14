## 1. Contract

- [x] 1.1 Define the visual semantics, hierarchy, responsive boundaries, and non-goals for the Electron UI v4 refresh.
- [x] 1.2 Update the companion UI, fleet console, and runtime guidance capability deltas.

## 2. Edge Implementation

- [x] 2.1 Unify renderer tokens, neutral titlebar surfaces, cards, typography, and interaction colors. <!-- aidcp-edge becc0f6 -->
- [x] 2.2 Move lifecycle controls into the daily progress header and render metrics as one segmented panel. <!-- aidcp-edge becc0f6 -->
- [x] 2.3 Replace collapsed-rail status rings with platform-solid avatars, corner status dots, and one blue selection layer. <!-- aidcp-edge becc0f6 -->
- [x] 2.4 Compact the running value-guidance decoration while preserving honest stage explanations and reduced-motion behavior. <!-- aidcp-edge becc0f6 -->

## 3. Verification

- [x] 3.1 Add DOM and CSS regression coverage for lifecycle-control placement, platform/status separation, and collapsed-rail semantics. <!-- aidcp-edge becc0f6 -->
- [x] 3.2 Reuse the canonical dependency tree and run `electron:dev` from the feature worktree for visual verification. <!-- 2026-07-14: renderer URL confirmed the edge-companion-ui-v4 worktree; expanded and collapsed rail inspected. -->
- [x] 3.3 Run focused Electron UI tests, the complete related UI suite, `npm run typecheck`, `git diff --check`, and strict OpenSpec validation. <!-- 2026-07-14: Electron UI 120/120, typecheck PASS, build PASS, diff check PASS, OpenSpec strict PASS. -->

## 4. Checkpoint

- [x] 4.1 Commit the Edge implementation on the `edge-companion-ui-v4` branch before further visual iteration. <!-- aidcp-edge becc0f6 -->
- [x] 4.2 Record the Edge commit and validation evidence in this task file; keep installer packaging out of scope unless explicitly requested. <!-- No installer built or published. -->
