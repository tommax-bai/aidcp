## 1. aidcp-cloud — coverage relaxed-timing fallback + review-card note

- [ ] 1.1 Add a `relaxed?: boolean` option to `FacebookGroupCoverageCandidateOptions` and make `coverageCandidates` run a relaxed query when set: drop the warmup / cooldown / `cooldown_until` gates, keep only `status='joined' AND joined_at IS NOT NULL`, keep the least-recently-commented ordering and the pick-window LIMIT. Store-level unit test (fake pool captures SQL): normal query keeps the timing gates; relaxed query omits them.
- [ ] 1.2 In `facebookCoverageConfigFor` (server bootstrap dep) implement the two-tier pick: try the normal constrained candidates first; if empty AND the relaxed-fallback env switch is on (`AIDCP_FB_GROUP_COVERAGE_RELAX` !== 'false', default on), retry with `{ relaxed: true }`; set `relaxed: true` on the returned coverage config only when the fallback actually supplied the chosen group. Zero joined groups → chosen stays null → honest no-op unchanged.
- [ ] 1.3 Thread the `relaxed` flag: add `relaxed?: boolean` to `FacebookCoverageCommentConfig`; in the Facebook targeted body pass `coverageRelaxed` into `approveFacebookComment` only when `usingCoverage` and the coverage config is relaxed (manual pinned-group path never sets it); in `approveFacebookComment` append a "未满足冷却/预热期，已放开时限选群，请人工确认" note to the review-card title when `coverageRelaxed` is set. No change to the shared approval port / XHS card.
- [ ] 1.4 Scheduler unit test: coverage config with `relaxed:true` produces a review card whose title carries the warning; `relaxed:false`/absent produces the plain title; the daily-cap gate still denies a relaxed pick over cap.
- [ ] 1.5 `npm run test:acceptance` (AC red lines green) → full `npm test` → `npm run typecheck`, all pass.

## 2. aidcp-console — keyword input preserves internal spaces

- [ ] 2.1 In `FacebookSearchConfig.tsx` remove the space `' '` from the keyword tags input `tokenSeparators` (leave comma) so a multi-word phrase stays one keyword; update the field help text so it no longer advertises "空格添加". Leave the container (URL) input's separators unchanged (URLs never contain spaces; splitting aids bulk paste).
- [ ] 2.2 `npm run build` (or `tsc` typecheck) + existing console tests pass.

## 3. Integration, deploy, verification

- [ ] 3.1 Land cloud + console branches to their `master` (rebase onto latest, resolve hot-file drift with concurrent Facebook changes, ff-merge), push.
- [ ] 3.2 Deploy cloud to dev (backup → rsync src → restart → healthcheck) per the deploy safety sequence; deploy console to dev (rsync build to nginx root, no `--delete`).
- [ ] 3.3 Register the real-machine acceptance items (relaxed pick surfaces a flagged review card in a coverage-enabled account; multi-word keyword saved from console reaches the edge as one search term) in `docs/real-machine-acceptance-backlog.md`.
- [ ] 3.4 After real-machine verification, `openspec validate facebook-coverage-relax-and-keyword-space --strict` and archive.
