## Why

The Facebook Native cutover preserved command names but did not preserve all localized control semantics or capability state machines discovered by the retired TypeScript executors. DEV evidence on 2026-07-26 proves three user-visible failure modes: a uniquely associated Reel control with `aria-label="赞"` is rejected as `like_button_not_found`; the personal-timeline composer text `Tianxing Bai，分享你的新鲜事吧！` was initially rejected as `composer_entry_not_found`; and, after restoring that phrase, publish record `195` still failed because one composer region and its one nested composer button were counted as two targets and rejected as `ambiguous_target`. Source comparison also finds a narrower Native comment pending-approval vocabulary.

## What Changes

- Audit every retired Facebook action vocabulary against the current Native Feed Like, Reels Like/Follow, Group Join, Comment, Publish, Consent, and blocker implementations, recording both gaps and verified-equivalent boundaries.
- Introduce one capability-neutral, Native-only reaction-semantics router module for the observed zh-CN, zh-TW, English, Spanish, and Vietnamese Like/reaction vocabulary used by Feed Like and Reels.
- Restore Reels recognition of a unique active-video right-rail bare Like label with numeric text without weakening Feed summary, comment, off-rail, or ambiguity guards.
- Restore the retired Publish stage contract: `navigate_entry` navigates to and validates the Facebook home surface; `select_mode` validates the target, waits for delayed composer entry rendering, performs one fresh trusted click, and verifies the editor opened within the one command budget.
- Preserve the existing 40-second Facebook `select_mode` deadline end to end, while keeping its trigger window at 20 seconds and leaving other Publish commands at their existing ceilings.
- Restore the retired Publish entry/editor/submit/submitted-state label families, including `分享你的新鲜事`, without adding unobserved fuzzy matches.
- Canonicalize a matching non-actionable Publish container to its matching actionable descendant controls, deduplicating one region/button representation while preserving ambiguity when more than one real control remains.
- Restore the retired Comment pending-approval veto vocabulary so localized approval states cannot be mistaken for confirmed publication.
- Preserve equivalent Join, Consent, blocker, editor, comment lifecycle, and author-bound Reels Follow semantics without mechanically rewriting them.
- Keep unknown and ambiguous labels fail-closed; do not assemble `CloudElementSelector`, `LikeStepRunner`, an online LLM click fallback, or any TypeScript page executor.

## Capabilities

### New Capabilities

- `native-facebook-localized-action-semantics`: Defines evidence-backed localized control semantics and capability-owned lifecycle requirements for Native Facebook Like, Comment, and Publish actions, plus parity audit gates for unchanged action families.

### Modified Capabilities

None.

## Impact

- Edge Native Facebook router assembly, Publish Rust capability, parity ledger, and focused router/Rust/boundary tests.
- Retired TypeScript Facebook executors remain behavior oracles only and are not reintroduced into production routing or package inputs.
- No Cloud policy, like probability, risk, quota, protocol, database, Console, installer, signing, OL deployment, or real-account write is included.
- This change implements the Native parity portion of the active `facebook-composer-open-deadline` contract; that change's pending live composer probe and real Publish acceptance remain unsatisfied delivery gates.
