## Why

Two operator-facing gaps in the current Facebook comment path:

1. **Unattended non-contact FB comments auto-publish without human review.** Today only contact-info comments go through the Feishu approval gate; a plain (no-contact) Facebook comment is composed, passes deterministic validators, and is submitted directly with no human in the loop. Before turning on `AIDCP_FB_COMMENT_AUTO` at scale, the operator wants **every** Facebook comment reviewed, not just the ones carrying a contact method. The human is the brake.

2. **`/comment --join` can only join the next group from the shared target library.** There is no way to tell an account "join *this specific* group and comment in it." Operators need `/comment <昵称> --join=<群链接>` to target one exact group URL, join it if not already a member (or comment directly if already a member), scoped to that one account without turning the URL into a broadly auto-joinable target for everyone.

## What Changes

- **Feature A — all Facebook comments require Feishu review (default-on, reversible).** Generalize the existing Facebook contact-comment approval into a single review gate that covers contact AND non-contact Facebook comments, behind a new default-ON env flag `AIDCP_FB_COMMENT_REVIEW_ALL`. Setting it to the literal string `false` restores today's behavior (non-contact FB comments submit after validation). Contact comments are unchanged (they were always reviewed). Shadow/dry-run still short-circuits before any review and never submits. `manualOverride` (Feishu `/comment`) still bypasses only quota/risk gates, **never** the human review.

- **Feature B — `/comment <昵称> --join=<url>` targeted group join + comment.** Parse the URL form of `--join`; join that specific group scoped to this account (create a per-account membership row backed by a target row inserted with `enabled=false`, so the shared auto-join sweep never hands the URL to other accounts). If already a member, skip the join and comment directly. Honest outcomes for invalid URL and for a group already owned by a different account — never impersonate membership.

## Capabilities

### Modified Capabilities

- `comment-interaction`: Facebook comments (contact and non-contact) SHALL route through the Feishu human-review gate by default; the gate is reversible via `AIDCP_FB_COMMENT_REVIEW_ALL=false`. Shadow still skips review+submit; `manualOverride` never bypasses review.
- `comment-search-command`: `/comment <昵称> --join=<url>` SHALL join a specific group URL scoped to the account then comment in it; already-member fast-path; honest failure for invalid/foreign-owned URLs; MUST NOT create a shared auto-joinable target and MUST NOT silently fall back to next-from-library when the URL form is used.

## Impact

- Affected repos: `aidcp-cloud` only. No protocol change, no `aidcp-edge` change (reuses existing `group.join` + in-container search/comment messages and the existing approval-card mechanism), no `aidcp-console` change.
- Cloud areas: `src/feishu/commands.ts` (parse `--join=<url>`), `src/comment-agent/comment-scheduler.ts` (unified review gate + join-specific routing), `src/comment-agent/facebook-group-join-scheduler.ts` (specific-URL join path), `src/comment-agent/facebook-group-store.ts` (per-account membership + `enabled=false` target upsert), `src/server.ts` (env-flag + new dep wiring, disjoint from concurrent `facebook-scheduled-comment` server.ts edits).
- Operational: `AIDCP_FB_COMMENT_REVIEW_ALL` defaults ON — after this lands, non-contact FB comments (including auto-scheduled ones) will require a Feishu approval click. Deploy this BEFORE flipping `AIDCP_FB_COMMENT_AUTO` on, so auto-comments never go out unreviewed. `--join=<url>` requires the existing join capability enabled (`AIDCP_FB_GROUP_JOIN_AUTO`, already on in dev).
- Red lines held: MUST NOT silent false-success (review-rejected/timeout/unwired ⇒ honest `compose_skipped`, no submit, no dedup); shadow never submits; `manualOverride` never skips review; targeted join MUST NOT create a shared target or downgrade to a random library group.
