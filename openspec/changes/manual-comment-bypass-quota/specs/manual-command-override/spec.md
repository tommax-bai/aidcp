## ADDED Requirements

### Requirement: Manual operator commands bypass pacing and risk quotas

An operator-initiated command (the Feishu `/comment <nickname> [--join] [--contact]`) SHALL be
treated as a full operator override and MUST NOT be blocked by pacing or risk **quotas**. This
includes the per-session group-join budget, the join day/hour/minute rate quota, the comment
day/hour/minute rate quota, the comment daily cap, and the hard risk state (`restricted` /
`frozen`). The override MUST be carried by an explicit signal set only at the manual command
entry point; automatic and scheduled paths (auto-comment loop, hot-lead auto-comment, the
background join loop) MUST NOT carry it and MUST keep respecting every quota. The command MUST
still honor physical-correctness gates: edge online, per-account single-flight, an available
join target, configured keywords, the Facebook-only guard for `--join`, the feature kill switch,
and shadow mode.

#### Scenario: Manual join proceeds despite exhausted quotas

- **WHEN** an operator runs `/comment <acct> --join` for a Facebook account whose session join
  budget is exhausted and whose risk join quota is denied
- **THEN** the join is dispatched (not refused with `session_budget` / `quota_denied`), and on a
  verified join the session-join consumption is still recorded so the ledger stays truthful

#### Scenario: Manual comment proceeds despite comment quota / daily cap

- **WHEN** an operator runs `/comment <acct>` (or the in-group comment after `--join`) for a
  Facebook account whose comment risk quota is denied or whose comment daily cap is reached
- **THEN** the comment stage skips the quota gate and proceeds to a real send (still passing
  compose validation, server-side confirmation, and `--contact` human approval)

#### Scenario: Automatic paths still respect quotas

- **WHEN** the automatic comment loop, the hot-lead auto-comment path, or the background join
  loop reaches a denied quota for an account
- **THEN** it is refused with the honest quota outcome and dispatches nothing (the manual override
  signal is absent on these paths)

#### Scenario: Manual override does not fake success or self-harm

- **WHEN** a manual command bypasses a quota gate but the underlying action cannot honestly
  complete (edge offline, no join target, no keywords, kill switch off, non-member group)
- **THEN** the command returns an honest non-success result card and dispatches no fake success;
  risk counting of a genuinely successful action still flows through the normal
  `interaction.occurred` → `RiskController.record` path (the override skips only the pre-gate)
