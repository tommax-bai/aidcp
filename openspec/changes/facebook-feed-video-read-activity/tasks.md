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
  <!-- Final post-rebase Edge validation: formatter 6/6, Facebook session 53/53, renderer 81/81, acceptance 29/29, full 2191/2191, typecheck passed. Validation-only deviations: macOS killed the new worktree path's otherwise identical Electron bundle until the isolated physical copy received an ad-hoc signature; an unrelated interaction-workspace timing assertion failed once under full-suite load, passed its exact rerun, and the final full retry passed. No product-behavior deviations. -->
- [x] 3.2 Run `openspec validate facebook-feed-video-read-activity --strict` and record Edge/control commit SHAs, validation totals, deviations, and the no-Cloud/no-installer boundary in this file.
  <!-- Strict OpenSpec validation passed. Edge implementation/integration commit: d88e490f659285e524329dd4cf0c732189103046. Control artifact commit after rebase: 9b015ffe50255fe662048e89596f7afbf3feb8dc. Scope boundary: Edge source plus control contract only; no Cloud/Console/protocol/database change, no ECS deployment, and no Edge installer build. -->
- [ ] 3.3 Rebase onto the latest default branches, rerun required gates after conflict resolution, fast-forward push Edge and control defaults serially, and preserve the concurrent Reel-follow worktree.
- [x] 3.4 Verify the development-runtime loading boundary after integration; restart the current development client only if it can be done without overwriting settings or forcing a synthetic Facebook action, and report any remaining live-acceptance limitation honestly.
  <!-- The running development Electron process started at 2026-07-22 11:30:51 +08:00 from the canonical checkout before d88e490 was integrated, so it has not loaded this behavior. It was not restarted: the active Facebook automation could resume real platform actions, and the canonical Edge master also acquired an independent local-only signing commit (4432206) during integration. Remote origin/master is safely updated; live acceptance requires a later controlled restart after that concurrent commit is reconciled. -->
