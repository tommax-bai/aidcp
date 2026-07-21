## 1. Edge Reel activity projection

- [x] 1.1 Add a structured `reel_view` companion event and truthful author/summary formatter with generic fallback.
- [x] 1.2 Emit one `reel_view` plus one local fallback view delta for each accepted new Reel card, and suppress a later duplicate `note_open` projection for the same canonical Reel.
- [x] 1.3 Map `reel_view` to the existing “读” activity-stream visual category without changing other event families.

## 2. Focused behavior coverage

- [x] 2.1 Add formatter tests for author+summary, partial metadata, bounded text, and machine-identifier-free fallback.
- [x] 2.2 Add Facebook session tests proving first/next Reel activity, failed-navigation silence, exact-detail deduplication, and unchanged ordinary Feed detail activity.
- [x] 2.3 Add renderer coverage proving `reel_view` appears with the “读” marker.

## 3. Validation and delivery

- [x] 3.1 Run focused Facebook/UI tests, the Edge full suite, and `npm run typecheck` in the isolated worktree.
  <!-- Edge validation before integration: focused Facebook/session/renderer tests 128 passed; formatter boundary tests 3 passed; full suite 2159 passed, 0 failed/skipped; npm run typecheck passed. -->
- [x] 3.2 Run `openspec validate facebook-reels-read-activity --strict` and record validation plus Edge commit evidence here.
  <!-- Edge commit after final rebase: aidcp-edge ab470ec. Post-final-rebase focused tests: 129 passed; npm run typecheck passed. OpenSpec strict validation passed after rebasing onto origin/main. -->
- [ ] 3.3 Fetch/rebase, rerun required validation, fast-forward push Edge and control default branches, and record that no installer was built.
