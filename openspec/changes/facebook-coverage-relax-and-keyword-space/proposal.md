## Why

Two operator-facing usability gaps in the Facebook comment pipeline surfaced after `facebook-comment-review-and-targeted-join` made every Facebook comment human-reviewed:

1. **Coverage mode goes idle when all joined groups are within their timing windows.** In coverage mode the pipeline picks a joined group only if it has cleared warmup (min join age, default 24h) AND cooldown (min hours since last comment, default 72h). When no joined group satisfies both, the pick is empty and the account does nothing that cycle — no comment, no card, just a `no_targets` audit row. For an account with a small set of joined groups, this can mean the account stays idle even though the operator wants it commenting. Now that a human reviews every Facebook comment before it posts, the timing windows can safely degrade from a hard skip into a soft, review-gated fallback: pick the least-recently-commented joined group anyway and let the reviewer decide, with the card flagging that the timing window was not met.

2. **The console splits a keyword on spaces.** The Facebook comment search-keyword input in the console is an AntD tags field whose `tokenSeparators` includes a space, so a multi-word search phrase (e.g. `手冲 咖啡`) is tokenized into two separate keywords before it is ever saved. The cloud already preserves internal spaces (it only trims the ends), so the bug is purely in the console input layer. Operators cannot configure multi-word search terms today.

## What Changes

- **Coverage-mode relaxed fallback (cloud):** When coverage-mode target selection finds no joined group satisfying warmup/cooldown, fall back (by default) to a relaxed pick that ignores the warmup and cooldown timing — still restricted to `status='joined'` groups, still ordered least-recently-commented, still random within the window — instead of skipping the account. Flag the relaxed pick so the Feishu human-review card visibly marks "未满足冷却/预热期，已放开时限选群，请人工确认". The relaxed fallback still enforces the per-account daily cap and every other gate (it relaxes only per-group timing, never per-account volume, never the human review). It is reversible via an env kill switch that restores the strict "no eligible group → skip" behavior. Accounts with zero joined groups still produce an honest no-op.
- **Keyword space preservation (console):** Remove the space character from the keyword tags input's `tokenSeparators` so a search term with internal spaces stays a single keyword, and update the field help text. The container (URL) input keeps space as a separator (URLs never contain spaces; splitting helps bulk paste). The cloud needs no change — it already preserves internal spaces.

## Capabilities

### Modified Capabilities

- `facebook-scheduled-comment`: Coverage-mode target selection gains a review-gated relaxed-timing fallback so a fully-in-cooldown account is not silently idle; operator search keywords preserve internal whitespace as a single term end-to-end.

## Impact

- Affected repos: `aidcp-cloud` (coverage selection + review card note), `aidcp-console` (keyword tags input).
- Cloud areas: coverage candidate query (relaxed variant), coverage config resolver (two-tier pick + relaxed flag), Facebook comment review card title annotation. No protocol, edge, or DB-schema change.
- Console areas: one Facebook config form component (`tokenSeparators` + help text).
- Operational impact: the relaxed fallback only takes effect for accounts in the coverage allowlist (`AIDCP_FB_GROUP_COVERAGE_ACCOUNTS`), which is currently empty on dev — so on dev this is latent until coverage mode is enabled. Default-on behavior (relaxed fallback active) is reversible with `AIDCP_FB_GROUP_COVERAGE_RELAX=false`. No change to the per-account daily cap or the always-on human-review gate.
- Red lines preserved: never a silent false-success — a relaxed pick is a real, honestly-flagged, human-reviewed comment; a zero-joined-group account still returns an honest no-op; the human-review gate is never bypassed.
