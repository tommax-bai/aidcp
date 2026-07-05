## Context

Manual billing price refresh currently builds T-1/T-2 provider/model/day targets from local token usage, fetches provider billing detail, and derives an effective price only when a billing line text contains the exact internal model id. A production dry-run on 2026-07-05 found 10 targets and valid billing credentials, but every target skipped with `no_billing_sample`.

The sample shows two distinct cases:

- Aliyun billing returned no DashScope token billing rows for the checked days, so cloud must keep skipping those models honestly.
- Volcengine returned Ark/Doubao token rows, but their billing labels were names like `Doubao-Seed-2.0-pro` and `Doubao-Seed-Character`, while runtime model ids were `doubao-seed-2-0-pro-260215` and `doubao-seed-character-260628`. Exact substring matching therefore missed valid token rows.
- Volcengine detail rows used `Count` with `Unit=千tokens` for token quantity, and rounded tiny `PretaxAmount` values to `0.00` while retaining same-row `Price` / `PriceUnit=千tokens`.

The console currently collapses all skip details into `跳过 N 个模型日`, hiding the reason returned by cloud.

## Goals / Non-Goals

**Goals:**

- Match provider billing rows to internal model ids when the provider uses deterministic billing labels rather than exact runtime ids.
- Keep price derivation billing-derived only: no public price table, no guessed fallback price, and no success if billing rows do not contain amount and token usage.
- Surface refresh skip reason counts in the usage page so operators can distinguish configuration issues from absent billing samples.
- Keep the API response shape compatible.

**Non-Goals:**

- No scheduled billing sync or background worker.
- No schema migration.
- No manual mapping database or operator-editable pricing table in this change.
- No attempt to infer DashScope prices when Aliyun billing details are absent.

## Decisions

1. **Use deterministic provider-specific model normalization.**

   Billing matching stays exact after normalization. Cloud will preserve the current full-id substring check, then add provider-specific aliases for known safe cases. For Volcengine, runtime ids that end with a release-date suffix can be normalized by removing the suffix and canonicalizing separators, so `doubao-seed-2-0-pro-260215` matches billing text containing `Doubao_Seed_2.0_pro_32k_infer_input...`.

   Alternative considered: fuzzy string similarity. Rejected because it can cross-match nearby model families and silently pollute price snapshots.

2. **Only match sufficiently specific aliases.**

   Aliases must retain the model family and concrete variant. Generic fragments such as only `doubao` or `seed` are not acceptable match keys. Endpoint-style ids without enough semantic tokens remain unmatched unless billing text contains the exact id.

   Alternative considered: strip every numeric suffix from every provider model. Rejected because non-Volcengine providers may encode materially different variants in numeric suffixes.

3. **Keep no-sample semantics honest.**

   If Aliyun billing returns no DashScope rows, or a billing row lacks token quantity or bill amount, refresh returns `no_billing_sample`. Existing latest-price fallback in `/api/llm-usage` continues to cover models that already have historical snapshots.

4. **Use same-row unit price only when billed amount is rounded away.**

   Cloud may derive the effective amount as `Price × token quantity in the price unit` when the same provider billing row has token units, a non-negative rounded bill amount, and a token-denominated `PriceUnit`. This remains billing-derived and avoids a public price table or guessed fallback. Non-token units such as image counts are ignored by token price refresh.

5. **Report skip reasons in the console, not only skip counts.**

   The response already includes `skipped[].reason`. The console will aggregate those reasons into operator-facing labels. A refresh with zero writes and skips should use warning-level copy instead of a green-only "updated" impression.

## Risks / Trade-offs

- [Overmatching Volcengine variants] -> Keep aliases provider-specific, require concrete normalized variant strings, and cover observed pro/character samples in tests.
- [DashScope remains pending] -> This is correct if the billing account/API has no DashScope token rows; the UI will now say `无账单样本` instead of hiding the cause.
- [Provider billing fields drift] -> Row normalization accepts token quantities from observed `Count` / `Unit` and standard usage fields. New tests should pin the observed `ConfigName` / `ChargeItemCode` / `PriceUnit` Volcengine format.
- [Message gets too long] -> Show reason counts in the toast and keep full per-model detail in the API response for later richer UI if needed.

## Migration Plan

1. Implement and test cloud matching in the aidcp-cloud worktree.
2. Implement and test console skip-reason messaging in the aidcp-console worktree.
3. Validate the OpenSpec change strictly.
4. Deploy cloud and publish console through the existing ECS/static release path after tests pass.

Rollback is code-only: redeploy the previous cloud/console snapshots. No data migration or secret change is involved.
