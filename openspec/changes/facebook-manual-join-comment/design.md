# Design — facebook-manual-join-comment

## Context

Two background loops already exist on the per-minute `ContentScheduler` (change `facebook-group-join-and-commenting`, deployed dev):

- Join loop → `FacebookGroupJoinScheduler.triggerScheduled(accountId)`: lazy-claim next target → observe → LLM judge (fail-closed; never clicks an approval-gated group) → click Join once → observe → judge → write the membership ledger + audit. Gated by `AIDCP_FB_GROUP_JOIN_AUTO` (default off) and `AIDCP_FB_GROUP_JOIN_SHADOW`. Returns `{ triggered, reason?, groupUrl?, outcome? }` with `outcome ∈ {joined, already_member, gated_skip, pending, ambiguous_skip, join_failed, nav_error, …}`.
- Coverage comment loop → `CommentScheduler` FB targeted-comment pipeline (`runFacebookTargetedTask`): pick keyword + container → search-in-container → open post → compose (read-first) → deterministic validators → (contact → human-review approval) → submit → server-verify. Container source is either the operator config list or, for allowlisted accounts, the joined-group ledger. Gated by `AIDCP_FB_COMMENT_AUTO` / `AIDCP_FB_COMMENT_SHADOW`.

The Feishu `/comment <昵称> [--contact]` command already routes Facebook accounts into that targeted-comment pipeline (`CommentScheduler.triggerManual`). Flags are parsed trailing-only in `src/feishu/commands.ts`.

The user wants a single on-demand command that does join-then-comment for one account, and to turn the join loop on for real.

## Goals / Non-goals

- Goal: `/comment <昵称> --join [--contact]` joins ONE new group and comments inside it, human-authorized, honest outcomes.
- Goal: turn the background auto group-join loop ON (real) on dev.
- Non-goal: no edge change, no protocol change, no new table/role/risk-action. No change to the background loops' own gating.
- Non-goal: no bulk manual joins — exactly one join per command invocation (human-paced).

## Key decisions

### D1 — Reuse `triggerScheduled` for the join; the manual command shares the join kill switch

The manual `--join` calls `FacebookGroupJoinScheduler.triggerScheduled(accountId)` unchanged. `triggerScheduled` honors `AIDCP_FB_GROUP_JOIN_AUTO`, so the manual command REQUIRES group-join automation to be enabled (which this change enables on dev). When it is off, the command honestly reports "group-join is off" instead of doing a real join.

Rationale: a SINGLE kill switch governs ALL real joins — background loop and manual command alike. This keeps the safety story simple, and means the join scheduler is NOT modified (zero collision with concurrent changes `add-join-group-session-limit` / `facebook-group-target-filters` that also touch it). `triggerScheduled` also already resolves `currentAssignment ?? claimNext`, so it finishes any stuck assignment before claiming a fresh group (no leaked claims), and enforces the `join_group` risk quota + per-session join budget + single-flight.

### D2 — The comment is pinned to the just-joined group

On a confirmed join, the orchestrator runs the Facebook targeted-comment pipeline with the container PINNED to the returned `groupUrl` (an `overrideContainerUrl`), not chosen from the config list or the LRU coverage window. Keywords still come from the account's Facebook comment config; if the account has no keywords configured, the comment step fails closed with an honest `no_targets` (never whole-site search, never a blind post). Ledger coverage callbacks (`markCoverageCommented` / left-signal) fire for that group, exactly as the coverage loop would.

### D3 — The manual targeted comment forces real mode (human authorization), still fully validated

When `overrideContainerUrl` is set (manual join-comment only), the comment path forces real mode: it bypasses the unattended `AIDCP_FB_COMMENT_AUTO` kill switch and `AIDCP_FB_COMMENT_SHADOW`. This is required to avoid a silent fake success — a confirmed join followed by a silently-skipped comment would violate the "no silent fake success" red line. The bypass is scoped to this one human-authorized, group-pinned path; a plain `/comment <昵称>` (no `--join`) is unchanged and still no-ops under the off switch.

The forced-real comment STILL enforces: hard validators, server-confirmed verification, per-account `canDo('comment')` + daily cap, the contact human-review approval lane when `--contact` is present (contact fail-closed if missing), persona gate, and single-flight. Only the auto/shadow gate is bypassed.

### D4 — Orchestration lives in `CommentScheduler`, one combined result card

`CommentScheduler` gains an injected `facebookJoinNewGroup?(accountId)` dependency (wired in `server.ts` to `facebookGroupJoinScheduler.triggerScheduled`). `triggerManual` gains a `joinFirst` option. When set, after the existing fast guards (persona, contact fail-closed, single-flight, edge online, Facebook-only), it runs a fire-and-forget orchestration under the comment scheduler's `running` lock: await the join → branch on outcome → on `joined`/`already_member` run the pinned targeted comment → post ONE honest combined result card via `postResultCard`.

The two schedulers keep separate `running` sets and run strictly sequentially (join fully completes before the comment starts), so there is no double-drive of one account; physical edge access is serialized by the shared edge task leases regardless.

### D5 — Order-independent trailing-flag parsing

The parser consumes trailing tokens while each matches a known flag (`--join` / `--contact`, case-insensitive), setting `joinGroup` / `injectContact`, and joins the remainder as the nickname. This preserves the existing trailing-only invariant (a flag-looking token in the MIDDLE of a nickname is not consumed and stays part of the nickname), and accepts the flags in either order.

## Join-outcome → command behavior

| join outcome | comment? | result card |
| --- | --- | --- |
| `joined` (fresh) | yes, pinned to the group | join + comment outcome |
| `already_member` | yes, pinned to the group | join(already member) + comment outcome |
| `gated_skip` / `pending` | no | honest: approval-gated, request state, no comment |
| `ambiguous_skip` / `join_failed` / `nav_error` / `no_button` | no | honest join failure, no comment |
| not triggered: `disabled` | no | honest: group-join automation is off |
| not triggered: `edge_offline` / `running` / `quota_denied` / `session_budget` / `no_targets` / `not_facebook_account` | no | honest reason, no comment |

## Alternatives considered

- Orchestrate in `server.ts` and post two cards (join card + comment card): rejected — two cards is noisier, and threading the comment's final outcome back for a card is cleaner inside the scheduler that already owns `runFacebookTargetedTask`.
- A dedicated manual-join method on the join scheduler that bypasses `AIDCP_FB_GROUP_JOIN_AUTO`: rejected for now (D1) — keeps one kill switch and avoids touching a hot, concurrently-edited file.

## Risks

- Turning on real joins skips the design's shadow-accuracy gate (tasks 9.1–9.5 of `facebook-group-join-and-commenting`). Mitigation: the join judge is fail-closed (never clicks an approval-gated group → no permanent dangling request from an auto click), joins are rate-limited (day/hour/minute + session budget), and the manual path is one human-paced join at a time. Accepted per operator decision (2026-07-10).
- Bypassing the FB-comment kill switch for the manual path widens what can post while the unattended switch is off. Mitigation: scoped to a human-issued command, one specific just-joined group, still fully validated + verified + (contact) human-reviewed.
