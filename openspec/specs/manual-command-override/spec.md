# manual-command-override Specification

## Purpose
TBD - created by archiving change manual-comment-bypass-quota. Update Purpose after archive.
## Requirements
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

### Requirement: The `--force` flag is an operator override of relevance and per-target dedup

The Feishu manual comment command SHALL accept an optional trailing switch `--force` that, for the
**manual command path only**, overrides the two **soft screening** gates: (1) topical relevance
(the xhs strong-relevance target picker and the Facebook `weak_relevance` validator) and (2)
per-note / per-post dedup (the "already-commented" skip). `--force` is a single operator switch
that relaxes both. It MUST be carried only from the manual command entry point (the same explicit
signal discipline as the quota override); automatic and scheduled paths (auto-comment loop,
hot-lead auto-comment, panel targeted comment, background paths) MUST NOT carry it and MUST keep
enforcing relevance and dedup. `--force` MUST compose with `--contact` and `--join[=<url>]` in any
order.

`--force` is a **relevance/dedup** override and is **independent** of the pacing/risk **quota**
override (which is already applied to every manual `/comment`): the two are separate signals with
separate scopes. `--force` MUST NOT relax any of the hard gates: the Feishu human-approval gate
(未授权/超时一律不发), the Facebook content-safety validators (URLs/bare domains, phone/email/IM
contact, `@mention`, spam phrases, length/low-signal), the edge honesty gates (search-keyword
consistency, on-search-page, in-place detail-page noteId re-check before submit, Facebook
membership state), and per-account isolation (PII). When `--force` cannot honestly complete an
action it MUST still return an honest non-success result, never a faked success.

#### Scenario: `--force` comments even when nothing is strongly relevant (xhs)

- **WHEN** an operator runs `/comment <acct> --force` for an xhs account and no searched candidate
  is judged strongly relevant to the persona
- **THEN** the task MUST NOT stop at `no_strong_candidate`; it selects the highest-collect candidate
  overall and proceeds to open → compose → human review → post (still gated by human approval)

#### Scenario: `--force` re-comments an already-commented target

- **WHEN** an operator runs `/comment <acct> --force` and the only available target is a note/post
  this account already commented on
- **THEN** the per-note/per-post dedup skip MUST be relaxed so the target is eligible again (a fresh
  comment may be composed and, after human approval, posted)

#### Scenario: `--force` skips relevance but keeps content-safety validators (Facebook)

- **WHEN** an operator runs `/comment <acct> --force` for a Facebook account
- **THEN** the `weak_relevance` relevance check is skipped, but a draft containing a URL, contact
  info, `@mention`, or a spam phrase MUST still be rejected (`compose_skipped`), and the comment MUST
  still pass human approval before any send

#### Scenario: `--force` never bypasses human review

- **WHEN** `/comment <acct> --force` produces a draft
- **THEN** it MUST still go through Feishu human approval; not approved / timed out MUST NOT post
  (`--force` relaxes only relevance and dedup, never the human brake)

#### Scenario: Automatic paths ignore `--force`

- **WHEN** the auto-comment loop, hot-lead auto-comment, or panel targeted comment runs for an
  account
- **THEN** it MUST keep enforcing relevance and dedup (the `--force` signal is absent on these paths)

#### Scenario: `--force` composes with existing switches

- **WHEN** an operator runs `/comment <acct> --join --contact --force` (any order)
- **THEN** all three switches take effect together: join a new group, inject the account's contact
  info, and relax relevance/dedup — while human review and content-safety validators still apply

### Requirement: Manual override 不得扩散到批量或异步委托

manual override SHALL 只适用于既有单次、操作员在线等待的人工命令。DelegatedTask 的批量评论、跨账号动作、定时/下一安全空档执行和任何异步剩余部分 MUST 使用自动化风险额度并向下游传 `manualOverride=false`；系统 MUST NOT 把一个 N 条任务拆成 N 次人工 override 来绕过配额。

#### Scenario: 五条评论任务遇到日配额
- **WHEN** 自动化额度只允许再完成 2 条评论而委托目标为 5 条
- **THEN** 最多执行额度允许的部分并等待/部分完成
- **AND** MUST NOT 通过五次 manual override 达成表面 5/5

