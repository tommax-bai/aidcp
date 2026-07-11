## ADDED Requirements

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
