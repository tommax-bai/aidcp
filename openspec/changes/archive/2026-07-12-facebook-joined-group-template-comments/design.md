## Context

Current Facebook comment configuration stores `keywords` and `containers`. The scheduler fails closed unless both are non-empty, chooses a configured container URL, and sends that URL to edge as `search.execute.container`. Edge is intentionally scoped: a missing Facebook container returns `permission_gated` and never becomes whole-site search.

Joined-group coverage already maintains the safer runtime source the operator now wants: each account's own `facebook_group_membership` rows with `status='joined'`, warmup/cooldown, least-recently-commented ordering, and a relaxed fallback that still only chooses joined groups and marks the approval card.

The desired change is therefore a cloud/console configuration change, not an edge search expansion. Edge should keep receiving one concrete group URL per attempt.

## Goals / Non-Goals

**Goals:**

- Make account FB configuration account-centric: keywords, comment mode, and templates.
- Remove operator-facing group/container editing from the account FB configuration modal.
- Use the joined-group coverage selector as the normal Facebook comment container source for unpinned comment runs.
- Keep the existing relaxed fallback: if warmup/cooldown produce no candidate, choose from joined groups by least-recently-commented and flag review.
- Add template comments that skip LLM generation but still run the same target search/open, hard validation, review, submit, verification, and ledger bookkeeping.
- Preserve separated contact injection (`text` plus contact info) for generated and template comments.

**Non-Goals:**

- No Facebook whole-site search.
- No edge protocol rewrite if `search.execute.container` remains the selected group URL.
- No desktop installer/package release unless explicitly requested.
- No migration that drops legacy `containers` data immediately; old rows should remain harmless and readable during rollback.

## Decisions

### D1. Joined groups are the normal source, not a secondary fallback to configured containers

Normal unpinned Facebook comments will call the joined-group selector for every account. The account config `containers` list will no longer be required for `enabled=true`, and the console will stop editing it.

Alternatives considered:

- Keep `containers` and add a "use joined groups" toggle: rejected because the operator wants group configuration removed, and dual source modes create ambiguous no-op/fallback behavior.
- Let edge search Facebook without `container`: rejected because it violates the existing edge safety model and would broaden scope beyond joined groups.

### D2. Keep the coverage selector's two-stage pick

The selector first applies `status='joined'`, `joined_at` warmup, `cooldown_until`, and `last_commented_at` cooldown, ordered least-recently-commented. If none are eligible and relaxed fallback is enabled, it chooses from `status='joined'` groups by least-recently-commented and returns a `relaxed` marker for the review card.

This reuses the mechanism already implemented for joined-group coverage and avoids adding a second selection policy.

### D3. Template mode only replaces composition

The pipeline still searches a selected joined group, opens the candidate post, reads the post/discussion, and then chooses content:

- `generated`: call the existing Facebook composer.
- `template`: pick one configured template and skip the composer.

Both modes run deterministic validation on the body before shadow/review/submit. Contact info stays outside the body and is appended only through the existing contact-info lane after review.

Alternatives considered:

- Submit a template without opening/reading the target: rejected because it would remove target validation, human review context, and existing failure observability.
- Allow templates to include contact info directly: rejected because it would bypass the current body/contact separation and validator carve-out.

### D4. Backward-compatible storage

Additive fields should be used for `commentMode` and `commentTemplates`. The legacy `containers` column can remain in `account_facebook_comment_config` for compatibility and rollback, but runtime normal selection should not depend on it.

The effective config should be enabled when keywords exist and the selected content mode is configured correctly:

- generated: at least one keyword.
- template: at least one keyword and at least one valid template.

The target group is resolved separately at run time from the membership ledger.

## Risks / Trade-offs

- [Template repetition fingerprint] → Keep daily caps, per-group cooldown, least-recently-commented rotation, hard validators, and human review. First implementation should not add multi-group retries in one attempt.
- [Old rows have containers but no keywords] → Keywords remain the explicit account intent gate; no keywords stays an honest no-op.
- [No joined groups after removing manual containers] → The result is an honest no-targets no-op; no whole-site search and no fallback to legacy containers.
- [Template mode with no templates] → Fail closed with a distinct compose/config reason and do not silently switch to generated comments.
- [Legacy coverage env switches still exist] → The source selector should be refactored so normal comments no longer require the old coverage source switch. The comment automation kill switch and review/cap gates remain unchanged.

## Migration Plan

1. Add cloud config fields and default existing rows to `commentMode='generated'`, `commentTemplates=[]`.
2. Update the scheduler to decouple "config enabled" from target group availability and always obtain the runtime group through joined-group selection for normal unpinned runs.
3. Update console FB configuration UI and mirrored types to remove containers and expose mode/templates.
4. Keep legacy `containers` persisted but unused by normal FB config; rollback can still use old code against the retained column.
5. Validate with focused cloud/console tests and `openspec validate facebook-joined-group-template-comments --strict`.
