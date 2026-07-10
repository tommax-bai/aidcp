# Manual `/comment` command bypasses pacing/risk quotas

## Why

The Feishu `/comment <nickname> [--join] [--contact]` command is an operator-initiated
(human-in-the-loop) action, yet it was routed through the **same** pacing/risk quota gates
that exist to pace the **automatic** background loops:

- The `--join` group-join stage reused the auto join scheduler, so it was blocked by the
  per-session join budget (`session_budget`) and the risk day/hour/minute join quota
  (`quota_denied`). A real operator command surfaced "本场会话加群额度已用尽；未加群也未评论".
- The comment stage (both plain `/comment` and the in-group comment after `--join`) was gated by
  the comment risk quota (`canDo('comment')`) and the comment daily cap.

By contrast, the manual XHS `/comment` path has **no** quota gates at all — manual XHS comments
always execute. So the behavior was inconsistent: Facebook manual commands inherited the
auto-loop pacing, Xiaohongshu manual commands did not.

Operator decision (2026-07-10): a manual command is a full operator override. It MUST bypass all
pacing quotas (session budget + join rate quota + comment rate quota + comment daily cap) **and**
the hard risk state (`restricted` / `frozen`). Only physical-correctness gates remain.

## What Changes

- Introduce an explicit `manualOverride` signal, set **only** at the single Feishu `/comment`
  handler. Automatic paths (ContentScheduler auto-comment, hot-lead auto-comment, the auto join
  loop) never carry it and keep respecting quotas — no regression to 养号 pacing.
- When the manual override is present, the group-join stage skips both quota gates
  (`canUseSessionJoin`, `canJoin`) and the comment stage skips both quota gates
  (`facebookCanComment`, comment daily cap). A verified manual join still records session-join
  consumption so the ledger stays truthful.
- Preserved even for manual commands: kill switch (`AIDCP_FB_*_AUTO`), shadow mode, edge-offline
  honest refusal, per-account single-flight, no-targets / no-keywords honest no-op, and the
  Facebook-only guard for `--join`.

## Impact

- Affected specs: `interaction-risk-gating` (adds a manual-command carve-out).
- Affected code (aidcp-cloud): `src/comment-agent/comment-scheduler.ts`,
  `src/comment-agent/facebook-group-join-scheduler.ts`, `src/server.ts`.
- No protocol change; no edge change. Automatic pacing behavior is unchanged.
