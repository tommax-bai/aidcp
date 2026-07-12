## Context

Current persona editing treats empty text as invalid. Both console and cloud block it as `persona_required`, so an operator cannot intentionally clear a stale or wrong persona from the admin page. Runtime gates already understand `source=none` / unbound accounts and fail closed, so the missing piece is an explicit unbind write path.

Current nickname persistence is conservative: startup/handshake capture is mainly used to fill a missing nickname and Facebook handshake persistence explicitly avoids overwriting an existing nickname. That leaves stale system nicknames after an operator or platform account changes the displayed name.

## Goals / Non-Goals

**Goals:**

- Let an operator clear the persona editor and save to unbind that account.
- Return the real post-write persona state (`source=none`, empty identity summary) after unbind.
- Detect verified XHS and Facebook nicknames on each startup identity check where the platform exposes one.
- Update stored nicknames when the verified platform nickname differs from the current stored nickname.
- Preserve stable account id as the only identity/routing key.

**Non-Goals:**

- Do not introduce default/fallback persona behavior.
- Do not use nicknames as account identity or route keys.
- Do not force navigation solely for Facebook nickname capture beyond its existing id-anchored startup reader.
- Do not build or release the Electron desktop installer unless separately requested.

## Decisions

1. **Empty persona save maps to delete/unbind, not an empty row.**

   The persona store should remove the `persona_config` row or otherwise make `isPersonaBound(accountId)` false. This reuses existing session-start, publish, and comment gates without adding a third "blank override" state.

2. **Console allows empty submit and labels it as unbind.**

   Client-side required validation must be removed or scoped to non-empty saves. The write remains non-optimistic: the UI refreshes from the API response and shows the returned `source=none` state.

3. **Nickname write policy becomes "verified non-empty difference updates".**

   Cloud should compare the verified platform nickname with the stored nickname. If stored is empty or different, persist the verified nickname. Empty or unverified values remain ignored.

4. **XHS uses the existing login nickname capture path, but arms it on startup even when a nickname exists.**

   The current XHS capture path is already separated from browsing and can update account metadata without performing account-scoped actions. Changing the arm condition from "missing nickname" to "startup capture requested" keeps the work in the login guidance path.

5. **Facebook uses handshake `accountNickname` as the verified startup nickname.**

   Edge already derives Facebook nickname only after stable numeric id resolution. Cloud can safely accept a non-empty `accountNickname` after platform validation and update if it differs.

## Risks / Trade-offs

- **[Risk] Clearing the editor accidentally unbinds an account.**  
  Mitigation: console copy should make the save action and post-save state clear; runtime gates already block unbound accounts honestly.

- **[Risk] Nickname churn from transient bad reads.**  
  Mitigation: only non-empty, existing verified startup nickname sources are accepted; Facebook keeps id-anchored generic-name filtering, and XHS keeps the existing profile detail capture path.

- **[Risk] Nickname-based Feishu commands may break if a nickname changes.**  
  Mitigation: this is intentional because commands should use the current human-visible nickname. Stable account id remains unchanged.

## Migration Plan

- Deploy cloud after tests so API semantics and nickname write policy are active.
- Deploy console static bundle after tests so the admin page permits clear-and-save unbind.
- Edge source changes, if any, are committed and pushed; desktop installer packaging is not automatic under current release policy.
- Rollback is straightforward: restore the previous cloud/console commits. Existing unbound accounts remain unbound until operators save a valid persona again.
