## 1. aidcp-cloud — coverage relaxed-timing fallback + review-card note

- [x] 1.1 Add a `relaxed?: boolean` option to `FacebookGroupCoverageCandidateOptions` and make `coverageCandidates` run a relaxed query when set: drop the warmup / cooldown / `cooldown_until` gates, keep only `status='joined' AND joined_at IS NOT NULL`, keep the least-recently-commented ordering and the pick-window LIMIT. Store-level unit test (fake pool captures SQL): normal query keeps the timing gates; relaxed query omits them.
  <!-- aidcp-cloud d2df859: relaxed branch in coverageCandidates (shared SELECT cols), 2 store SQL-capture tests (normal keeps 3 gates, relaxed omits them, still status=joined + LRU order). -->
- [x] 1.2 In `facebookCoverageConfigFor` (server bootstrap dep) implement the two-tier pick: try the normal constrained candidates first; if empty AND the relaxed-fallback env switch is on (`AIDCP_FB_GROUP_COVERAGE_RELAX` !== 'false', default on), retry with `{ relaxed: true }`; set `relaxed: true` on the returned coverage config only when the fallback actually supplied the chosen group. Zero joined groups → chosen stays null → honest no-op unchanged.
  <!-- aidcp-cloud d2df859: two-tier pick in server.ts facebookCoverageConfigFor; AIDCP_FB_GROUP_COVERAGE_RELAX default-on kill switch; relaxed flag only when fallback supplied chosen. -->
- [x] 1.3 Thread the `relaxed` flag: add `relaxed?: boolean` to `FacebookCoverageCommentConfig`; in the Facebook targeted body pass `coverageRelaxed` into `approveFacebookComment` only when `usingCoverage` and the coverage config is relaxed (manual pinned-group path never sets it); in `approveFacebookComment` append a "未满足冷却/预热期，已放开时限选群，请人工确认" note to the review-card title when `coverageRelaxed` is set. No change to the shared approval port / XHS card.
  <!-- aidcp-cloud d2df859: FacebookCoverageCommentConfig.relaxed; review gate passes coverageRelaxed when usingCoverage && coverageCfg?.relaxed; approveFacebookComment builds warning title. Manual pin path (coverageCfg undefined) never annotates. Shared port/card untouched. -->
- [x] 1.4 Scheduler unit test: coverage config with `relaxed:true` produces a review card whose title carries the warning; `relaxed:false`/absent produces the plain title; the daily-cap gate still denies a relaxed pick over cap.
  <!-- aidcp-cloud d2df859: 3 scheduler tests — relaxed→title warning, absent→plain title, relaxed over daily-cap→quota_denied/daily_cap and no card emitted. -->
- [x] 1.5 `npm run test:acceptance` (AC red lines green) → full `npm test` → `npm run typecheck`, all pass.
  <!-- aidcp-cloud d2df859: acceptance 47 pass, full npm test 1802 pass (0 fail, +5 new), typecheck clean. -->

## 2. aidcp-console — keyword input preserves internal spaces

- [x] 2.1 In `FacebookSearchConfig.tsx` remove the space `' '` from the keyword tags input `tokenSeparators` (leave comma) so a multi-word phrase stays one keyword; update the field help text so it no longer advertises "空格添加". Leave the container (URL) input's separators unchanged (URLs never contain spaces; splitting aids bulk paste).
  <!-- aidcp-console 6704e99: keyword Select tokenSeparators=[','] (space removed); help text updated to explain multi-word phrase stays one keyword; container Select unchanged. -->
- [x] 2.2 `npm run build` (or `tsc` typecheck) + existing console tests pass.
  <!-- aidcp-console 6704e99: typecheck clean, vitest 91 pass + 1 skipped (pre-existing), production build ok. Note: the multi-word-keyword behavior itself is not unit-tested — AntD tags CJK tokenization is not reliably reproducible under jsdom via fireEvent; deferred to real-machine (簇 51). -->

## 3. Integration, deploy, verification

- [x] 3.1 Land cloud + console branches to their `master` (rebase onto latest, resolve hot-file drift with concurrent Facebook changes, ff-merge), push.
  <!-- aidcp-cloud master d2df859 (ff from 8062dd5, no drift), aidcp-console master 6704e99 (ff from f3cd239). Both via scripts/land-change --yes: rebase + acceptance/test/typecheck + ff-push + main-checkout sync + worktree cleanup. -->
- [x] 3.2 Deploy cloud to dev (backup → rsync src → restart → healthcheck) per the deploy safety sequence; deploy console to dev (rsync build to nginx root, no `--delete`).
  <!-- deployed dev 2026-07-11. cloud: git-archive snapshot d2df859; ECS verified at base 8062dd5 (3-file md5 match, no concurrent intermediate); backup /opt/aidcp/cloud.bak.20260711-115545.tar.gz + .env.bak.20260711; rsync src (exclude .env/node_modules/.git); restart aidcp-cloud.service; healthcheck active, 8787+8090 listening, Feishu WSClient onReady, CommentScheduler+ContentScheduler running, PG select 1 ok, NRestarts=0, no errors, COVERAGE_RELAX marker live. console: build 6704e99; backup /opt/aidcp/console.bak.20260711-115739.tar.gz; rsync dist→/opt/aidcp/console (no --delete); pruned orphan asset index-DC8wBKyL.js (keep-set from index.html grep); backups trimmed to 10; nginx 8088 smoke index.html/new JS 200, /api/health 200. isales never touched. -->
- [x] 3.3 Register the real-machine acceptance items (relaxed pick surfaces a flagged review card in a coverage-enabled account; multi-word keyword saved from console reaches the edge as one search term) in `docs/real-machine-acceptance-backlog.md`.
  <!-- registered 簇 51 (2026-07-11). -->
- [ ] 3.4 After real-machine verification, `openspec validate facebook-coverage-relax-and-keyword-space --strict` and archive.
