# Tasks — facebook-manual-join-comment

## 1. Preconditions

- [x] 1.1 Ground on `origin/main` (control) + `origin/master` (cloud); `facebook-group-join-and-commenting` is implemented + deployed dev (join scheduler, membership ledger, `join_group` risk action). Do NOT re-implement it. <!-- aidcp-cloud 4cbdf44 -->
- [x] 1.2 Confirm no edge / protocol change is needed (`group.join` action + Facebook comment actions already exist). <!-- aidcp-cloud 4cbdf44 -->

## 2. aidcp-cloud — command parser (`src/feishu/commands.ts`)

- [x] 2.1 Add `joinGroup?: boolean` to `ParsedCommand`. In the `/comment` branch, consume TRAILING flag tokens (`--join` / `--contact`, case-insensitive) in any order; set `joinGroup` / `injectContact`; remaining leading tokens join as the nickname. Preserve the trailing-only invariant (a mid-nickname flag-looking token is not consumed). <!-- aidcp-cloud 4cbdf44 -->
- [x] 2.2 Thread `joinGroup` through `CommandActions.comment(nickname, { injectContact, joinGroup })` and `CommandRouter.runComment`. Update `HELP_TEXT` with the `--join` / `--join --contact` lines. <!-- aidcp-cloud 4cbdf44 -->

## 3. aidcp-cloud — CommentScheduler orchestration (`src/comment-agent/comment-scheduler.ts`)

- [x] 3.1 Add injected dep `facebookJoinNewGroup?: (accountId) => Promise<{ triggered: boolean; reason?: string; groupUrl?: string; outcome?: string }>`. <!-- aidcp-cloud 4cbdf44 -->
- [x] 3.2 `triggerManual` gains `joinFirst?: boolean`. When set: run existing fast guards (persona, contact fail-closed, single-flight, edge online) first; Facebook-only guard (non-FB → honest unsupported); then fire-and-forget the join-then-comment orchestration under the comment `running` lock. <!-- aidcp-cloud 4cbdf44 -->
- [x] 3.3 Orchestration `runFacebookJoinThenComment`: await `facebookJoinNewGroup(accountId)`; branch on outcome; on `joined`/`already_member` run the pinned targeted comment; post ONE honest combined result card (join + comment) via `postResultCard`. No confirmed join → no comment, honest card. <!-- aidcp-cloud 4cbdf44 -->
- [x] 3.4 `runFacebookTargetedTask` gains `overrideContainerUrl?`: when set, force real mode (bypass `AIDCP_FB_COMMENT_AUTO` / shadow), pin the container to the given URL, take keywords from `facebookConfigFor` (fail-closed no-op if empty), and drive coverage ledger callbacks for that group. Return the terminal outcome so the combined card is honest. Non-override callers unchanged (zero regression). <!-- aidcp-cloud 4cbdf44 -->

## 4. aidcp-cloud — server wiring (`src/server.ts`)

- [x] 4.1 Inject `facebookJoinNewGroup: (accountId) => facebookGroupJoinScheduler.triggerScheduled(accountId)` into the `CommentScheduler` construction. <!-- aidcp-cloud 4cbdf44 -->
- [x] 4.2 In `actions.comment`, thread `joinGroup` and call `commentScheduler.triggerManual(acct, { injectContact, joinFirst: joinGroup })`. <!-- aidcp-cloud 4cbdf44 -->

## 5. aidcp-cloud — tests

- [x] 5.1 Parser unit tests: `--join`/`--contact` in both orders, `--join` alone, no-flag unchanged, mid-nickname flag-looking token not consumed. <!-- aidcp-cloud 4cbdf44 -->
- [x] 5.2 CommentScheduler tests: join `joined` → pinned comment runs on the returned group; non-member join outcome → no comment + honest card; non-FB account → unsupported; `--contact` missing contact → fail-closed before posting; single-flight refuses a second command; override forces real mode even with `AIDCP_FB_COMMENT_AUTO` off but still runs validators/verify. <!-- aidcp-cloud 4cbdf44 -->

## 6. Verification (cloud)

- [x] 6.1 `npm run test:acceptance` → full `npm test` → `npm run typecheck` green (AC-* red lines intact). <!-- aidcp-cloud 4cbdf44: acceptance 47 + full 1730 + typecheck all green -->
- [x] 6.2 Adversarial multi-agent review of the kill-switch carve-out + orchestration for silent-fake-success / TOCTOU / no-join-yet-comment leaks; fix confirmed findings. <!-- aidcp-cloud 239dfd7: 6-lens adversarial workflow (18 agents); 1 confirmed (comment-phase throw dropped closure card) fixed + never-throw wrapper; cross-scheduler edge guards added as rollout safety; raw-URL→placeholder; refuted 2 -->

## 7. Rollout + deploy (dev)

- [ ] 7.1 Land cloud branch to `master` (fetch + rebase + tests) and control change to `main`.
- [ ] 7.2 Deploy cloud to `dev` via the safety sequence (deploy-target check → backup → rsync → restart → healthcheck → rollback-on-fail). NEVER touch same-host isales.
- [ ] 7.3 Enable the auto group-join loop on `dev`: set `AIDCP_FB_GROUP_JOIN_AUTO=true` (shadow off) in `/opt/aidcp/cloud/.env`; confirm `AIDCP_CONTENT_SCHEDULE_AUTO=true` for the background loop; restart; confirm startup log shows join automation enabled.
- [ ] 7.4 Register real-machine acceptance items in `docs/real-machine-acceptance-backlog.md`: (a) `/comment <昵称> --join` joins one new group + comments inside it; (b) `--join --contact` routes through Feishu approval; (c) background auto-join loop fires under quota; (d) honest cards for gated/no-target/disabled outcomes.

## 8. Closeout

- [ ] 8.1 `openspec validate facebook-manual-join-comment --strict`.
- [ ] 8.2 Archive after dev verification.
