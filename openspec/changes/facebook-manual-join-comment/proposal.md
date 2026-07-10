## Why

`facebook-group-join-and-commenting` shipped two BACKGROUND loops on the per-minute content scheduler: an auto group-join loop and a per-account joined-group comment-coverage loop, both default-off. The operator now wants to (a) turn the auto group-join loop ON for real (past shadow-only), and (b) drive the same capability on demand from Feishu, one account at a time, with a human in the loop: type one command and have a named account **join a fresh target group and immediately leave a natural comment inside it** — optionally a contact/lead-gen comment through the existing human-reviewed lane. There is no such on-demand "join a new group and comment there now" command today; the only comment command (`/comment <昵称> [--contact]`) comments inside already-configured / already-joined containers and is itself gated by the unattended Facebook-comment kill switch.

## What Changes

- Turn the Facebook auto group-join loop ON for real on `dev`: `AIDCP_FB_GROUP_JOIN_AUTO=true` (shadow off), with the background join loop running under the content scheduler.
- Add a `--join` flag to the Feishu `/comment <昵称>` command. With `--join`, the named account joins ONE new target group through the EXISTING join scheduler (lazy-claim → observe → fail-closed judge → click once → server-verify → membership ledger) and — only on a judgment-confirmed join (or already-member) — publishes a comment INSIDE that just-joined group.
- Allow `--contact` and `--join` together, in any trailing order (`/comment 昵称 --join --contact` ≡ `--contact --join`). `--join --contact` = join a new group + post a contact/lead-gen comment through the EXISTING human-reviewed approval lane (verbatim contact injection), never the unattended path.
- The manual join-then-comment is human-authorized: its targeted comment (pinned to the just-joined group) MAY post even when the unattended Facebook-comment kill switch (`AIDCP_FB_COMMENT_AUTO`) is off, but MUST still pass all hard validators, server-confirmed verification, the contact human-review lane, the per-account risk quota and daily cap, the persona gate, and single-flight — never a silent fake success.
- Honest combined outcome: one Feishu result card reports the join outcome AND the comment outcome (joined+commented / joined-but-comment-failed / not-joined / approval-gated / no-targets / disabled …). No confirmed join → no comment.

## Capabilities

### New Capabilities

- `facebook-manual-join-comment`: the `/comment <昵称> --join [--contact]` command — order-independent trailing-flag parsing, Facebook-only guard, join-one-new-group-then-comment orchestration reusing the existing join scheduler and Facebook targeted-comment pipeline, contact comments through the human-reviewed lane, honest combined outcomes with no-join→no-comment, and single-flight isolation from the background loops.

### Modified Capabilities

- `facebook-scheduled-comment`: carve out a human-authorized manual join-then-comment path — its targeted comment, pinned to the account's just-joined group (from the membership ledger) with keywords still from the account config, MAY run when the unattended kill switch is off, while preserving all validators, server-confirmed verification, the contact human-review lane, and fail-closed behavior (no keywords → honest no-op).

## Impact

- Affected repos: `aidcp-cloud` (Feishu command parser flag, `CommandActions.comment` wiring, `CommentScheduler` join-then-comment orchestration + targeted-container override, join-scheduler dependency injection) and `aidcp` (this OpenSpec change). NO `aidcp-edge` change — the `group.join` action and the Facebook comment actions already exist. NO protocol v2 change.
- Config / rollout (`dev`): set `AIDCP_FB_GROUP_JOIN_AUTO=true`; confirm `AIDCP_CONTENT_SCHEDULE_AUTO=true` so the background join loop actually fires. Operational preconditions (imported group targets, online Facebook accounts with an active schedule + `join_group` daily cap, per-profile proxy configured manually in AdsPower) are unchanged from `facebook-group-join-and-commenting`.
- Depends on `facebook-group-join-and-commenting` (join scheduler, membership ledger, coverage callbacks, `join_group` risk action) being deployed on the target. No new tables, no new risk actions, no new role.
- Reuse-first: the join reuses `FacebookGroupJoinScheduler.triggerScheduled`; the comment reuses the Facebook targeted-comment pipeline with the container pinned to the just-joined group. Only the parser, the wiring, and a targeted-container/real-mode override on the comment path are new code.
