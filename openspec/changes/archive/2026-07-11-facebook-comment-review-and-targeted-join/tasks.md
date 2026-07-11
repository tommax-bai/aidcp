# Tasks — facebook-comment-review-and-targeted-join

Cloud-only change. No protocol change, no edge change, no console change. Develop in
`../aidcp-cloud.wt/facebook-comment-review-and-targeted-join`; integrate via `scripts/land-change`.

## 1. aidcp-cloud — Feature A: all FB comments require Feishu review (default-on, reversible)

- [x] 1.1 Add optional dep `facebookCommentReviewAll?: () => boolean` to `CommentSchedulerDeps` (default true when absent), right after `facebookShadow`.
- [x] 1.2 Generalize `approveFacebookContactComment` → `approveFacebookComment` with optional `contactInfo`: review text = body-only when no contact (no trailing newline), body+contact when present; return `{text}` or `{text, contactInfo}`; generalize the unwired warn string.
- [x] 1.3 Restructure the FB targeted-comment body: keep `contact_info_missing` fail-closed before the shadow gate; keep the shadow early-return before review; after shadow, gate real submit on `injectContact || facebookCommentReviewAll()` via `approveFacebookComment` (fail closed → `compose_skipped`/`approval_rejected_or_timeout`, no submit, no dedup). Do NOT consult `manualOverride` in the review gate.
- [x] 1.4 Wire `facebookCommentReviewAll: () => readEnvString('AIDCP_FB_COMMENT_REVIEW_ALL') !== 'false'` in `src/server.ts` next to `facebookAutoEnabled`/`facebookShadow`.
- [x] 1.5 Tests: update `fbFlowDeps` to inject an auto-approving approval so existing non-contact happy paths still reach `commented`; update the ~11 non-contact assertions; add (a) default-on unwired → no submit, (b) `REVIEW_ALL=false` → direct submit, (c) `manualOverride` still requires review, (d) non-contact card text = body only. Keep contact test at line ~589 green.
<!-- aidcp-cloud 8062dd5 Feature A: unified FB review gate + generalized approveFacebookComment + AIDCP_FB_COMMENT_REVIEW_ALL default-on. Note: baseDeps already injected an auto-approving approval, so the existing non-contact tests passed unchanged; added 4 new tests instead. -->

## 2. aidcp-cloud — Feature B: /comment --join=<url> targeted group join + comment

- [x] 2.1 `src/feishu/commands.ts`: parse `--join=<url>` (trailing, any order with `--contact`) → `joinGroupUrl`; keep bare `--join`; thread `joinGroupUrl` through `ParsedCommand`, `CommandActions.comment` options, `runComment`; add HELP bullet.
- [x] 2.2 `src/server.ts`: comment action passes `joinGroupUrl` into `commentScheduler.triggerManual`; add `facebookJoinSpecificGroup` dep wired to `facebookGroupJoinScheduler.joinSpecificGroup`.
- [x] 2.3 `src/comment-agent/comment-scheduler.ts`: add `joinGroupUrl` to `triggerManual` + `runFacebookJoinThenComment`; when present require `facebookJoinSpecificGroup` (honest error if unwired, never fall back to next-from-library) and route to it; add `invalid_group_url` / `owned_by_other_account` cases to `joinOnlyReceipt`.
- [x] 2.4 `src/comment-agent/facebook-group-store.ts`: `FacebookGroupTargetStore.ensureTarget(url,{enabled=false})` (FK backing, never upgrades an existing target); `FacebookGroupMembershipStore.claimSpecific(accountId,url)` returning `{row, ownedByOther}` respecting `UNIQUE(group_url)` (fresh insert / this-account reuse / joined fast-path / foreign-owned honest).
- [x] 2.5 `src/comment-agent/facebook-group-join-scheduler.ts`: extract `runAssignedJoin` from `runReal` (behavior-preserving); add public `joinSpecificGroup(accountId,url,{manual})` — canonicalize (invalid_group_url), single-flight, FB/edge/kill-switch gates, skip canJoin/session-budget (operator authority), ensureTarget+claimSpecific, already-member fast path, else runAssignedJoin.
- [x] 2.6 Tests: `feishu-commands` parse matrix (url form, both flags any order, bare --join regression, trailing-only); `facebook-group-join-scheduler` (invalid url, already-member fast path w/o edge, fresh join asserts target not enabled, owned-by-other, kill-switch/non-FB); `comment-scheduler` (routes to specific-join, unwired → honest error no fallback, non-FB reject).
<!-- aidcp-cloud 8062dd5 Feature B: --join=<url> parse + ensureTarget(enabled=false)+claimSpecific (UNIQUE(group_url) scoping) + joinSpecificGroup reusing extracted runAssignedJoin. --join (both forms) still respects AIDCP_FB_GROUP_JOIN_AUTO kill switch per existing contract (on in dev). -->

## 3. aidcp-cloud — Regression gates

- [x] 3.1 `npm run test:acceptance` green (esp. AC-PUB: never submit without authorization — now covers non-contact FB comments).
- [x] 3.2 `npm test` full green.
- [x] 3.3 `npm run typecheck` clean.
<!-- aidcp-cloud 8062dd5: test:acceptance 47 pass; npm test 1797 pass; typecheck clean. -->

## 4. Integration + deploy

- [x] 4.1 Rebase onto latest `origin/master`, `scripts/land-change aidcp-cloud facebook-comment-review-and-targeted-join`, update main checkout.
- [x] 4.2 Deploy dev (backup → rsync → restart → healthcheck), per safety sequence.
- [x] 4.3 Flip dev env: `AIDCP_FB_COMMENT_AUTO=true`, `AIDCP_CONTENT_SCHEDULE_AUTO=true`. `contactCommentEnabled` unchanged.
<!-- aidcp-cloud 8062dd5 landed to origin/master + main checkout fast-forwarded (land-change --yes). Collision analysis: 3 concurrent FB branches already merged; facebook-scheduled-comment untouched region. -->
<!-- 2026-07-11 deployed dev: git-archive HEAD snapshot → backup (/opt/aidcp/cloud.bak.20260711-112014.tar.gz + .env.bak) → rsync (excl .env/node_modules/.git, no --delete) → restart → healthcheck green (active, :8787, PG ready, feishu WSClient onReady, ContentScheduler+CommentScheduler running). 5 changed files md5-match local. -->
<!-- ITEM 6 finding: AIDCP_FB_COMMENT_AUTO / AIDCP_CONTENT_SCHEDULE_AUTO / AIDCP_FB_GROUP_JOIN_AUTO were ALREADY =true on dev — no flip needed. Deploying this code (AIDCP_FB_COMMENT_REVIEW_ALL absent = default ON) is what makes the already-on auto-comments human-reviewed. AIDCP_FB_COMMENT_REVIEW_ALL left absent (default-on); set =false only to restore auto-publish. contactCommentEnabled left untouched per user. -->

## 5. Real-machine acceptance (deferred to backlog)

- [x] 5.1 Register real-machine items in `docs/real-machine-acceptance-backlog.md`: non-contact FB comment shows a review card and only posts after approval; `/comment <昵称> --join=<url>` joins the exact group and comments; already-member fast path; invalid/foreign-owned URL honest cards.
<!-- registered as 簇 48 in docs/real-machine-acceptance-backlog.md (2026-07-11). -->

Not archived yet — pending real-machine acceptance (簇 48). Cloud code fully landed + deployed dev + tests green.
