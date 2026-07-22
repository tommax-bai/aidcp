## 1. Edge activity projection

- [x] 1.1 Add a bounded Feed-video activity formatter and distinct `feed_video_view` companion-event type.
- [x] 1.2 Emit one Feed-video read activity and local fallback view for an eligible single-video Feed batch, using session-wide Feed-specific canonical deduplication and suppressing a later duplicate detail activity.
- [x] 1.3 Map `feed_video_view` to the existing “读” marker without changing other activity families.

## 2. Focused behavior coverage

- [x] 2.1 Add formatter tests for full, partial, generic, clipped, and machine-identifier-free wording.
- [x] 2.2 Add Facebook session tests for eligible Feed-video activity, duplicate presentation/detail idempotence, and silent non-video, multi-video, malformed, and Reel-shaped Feed batches.
- [x] 2.3 Add renderer coverage proving `feed_video_view` uses the “读” marker and remains environment-routed like existing activities.

## 3. Validation and delivery

- [x] 3.1 Install isolated worktree dependencies with `npm ci --prefer-offline`, then run focused Facebook/UI tests, Edge acceptance, the full suite, and `npm run typecheck`.
  <!-- Edge validation: formatter 6/6, Facebook session 53/53, renderer 81/81, acceptance 29/29, full 2190/2190, typecheck passed. The first full run exposed a macOS path-trust failure for the worktree Electron dependency; after restoring the physical dependency and ad-hoc signing that isolated copy, the focused Electron test passed 5/5 and the full rerun passed. -->
- [ ] 3.2 Run `openspec validate facebook-feed-video-read-activity --strict` and record Edge/control commit SHAs, validation totals, deviations, and the no-Cloud/no-installer boundary in this file.
- [ ] 3.3 Rebase onto the latest default branches, rerun required gates after conflict resolution, fast-forward push Edge and control defaults serially, and preserve the concurrent Reel-follow worktree.
- [ ] 3.4 Verify the development-runtime loading boundary after integration; restart the current development client only if it can be done without overwriting settings or forcing a synthetic Facebook action, and report any remaining live-acceptance limitation honestly.
