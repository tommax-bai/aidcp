## Context

The Edge attaches to an AdsPower page before establishing account identity and opening the Cloud WebSocket. On the reproduced startup, CDP became ready on `about:blank`; `readFacebookIdentity` recovered the numeric id from `c_user`, spent its hydration budget scanning that blank document, and sent hello without a nickname. Only after hello did `FacebookBrowseSession.start()` call `ensureFeed()` and navigate to Facebook.

A live comparison of five simultaneously running AdsPower profiles showed the second failure dimension. Two Chinese-layout profiles exposed a supported `aria-label` suffix and succeeded. Three Vietnamese-layout profiles exposed the correct self anchor and visible names (`Ve Te`, `So La`, `Mi Xu`), but their labels used `Dòng thời gian của <name>`, which the suffix parser did not recognize. Some of those layouts also lacked the current feed/card selectors, so the Cloud `page.cards` nickname enrichment trigger was absent.

Constraints:

- The numeric Facebook id remains authoritative and comes from `c_user` or an id-bearing profile signal; a display name never establishes identity.
- Runtime identity monitoring and `profile.open{direct}` must stay navigation-free.
- A blank or unrelated page is not “ready” merely because `document.readyState === 'complete'`; readiness must be based on the Facebook page context and id-bound self signals.
- No protocol or Cloud schema change is needed because hello already carries an optional verified nickname and Cloud already persists differences.

## Goals / Non-Goals

**Goals:**

- Ensure the Facebook startup identity read happens against a real Facebook consumer page rather than `about:blank`.
- Read localized nicknames without maintaining an unbounded language suffix table.
- Preserve fail-closed id binding, bounded waits, and honest empty nickname results.
- Make successful Facebook startup nickname refresh independent of feed-card extraction.

**Non-Goals:**

- Repair every Facebook feed/article selector in this change.
- Navigate to `/me`, a numeric profile URL, or any author profile to obtain a nickname.
- Change Cloud persistence, protocol payloads, account routing, risk state, or XHS startup behavior.
- Build or publish an Edge installer.

## Decisions

### 1. Model page bootstrap as an explicit startup permission

`readFacebookIdentity` will honor the existing `ReadSelfIdentityOptions.allowNavigate` boundary. If navigation is allowed and the first scan is on an unknown/non-Facebook context such as `about:blank`, it may navigate once to the Facebook consumer home page. It will not navigate when already on a Facebook consumer/login/checkpoint page, and it will never navigate to `/me` or a profile URL.

The startup option selector will enable this only for Facebook initial identity establishment, including AdsPower. XHS AdsPower startup keeps `allowNavigate=false`. Runtime watchers, login polling, and Facebook `profile.open{direct}` pass `allowNavigate=false` explicitly.

Alternative considered: start the browse session before handshake. Rejected because browse orchestration currently depends on an established account/Cloud session and moving it would broaden lifecycle and risk behavior far beyond identity readiness.

### 2. Wait on business context and self signals, not load-complete alone

The identity reader will take an initial signal snapshot. After a permitted home bootstrap, it will use the existing bounded hydration loop to rescan. A Facebook consumer URL plus an id-bound self anchor that yields a name is success; a cookie id without a name remains a best-known identity while the loop continues. If the budget expires, the reader returns the stable id with an empty nickname.

This naturally tolerates redirects and asynchronous React hydration. `document.readyState` is not a success condition because `about:blank` itself legitimately reports `complete`.

### 3. Add id-anchored visible anchor text as a locale-independent source

The DOM scan will retain `{href, ariaLabel, textContent}` for each candidate profile anchor. For an anchor whose href resolves to the established numeric account id (or `/me`), nickname selection will prefer the existing parsed `aria-label`, then use cleaned visible text. Other ids are ignored before either field is considered.

This keeps the strongest safety boundary—the stable self id—while removing the need to know whether a locale expresses “timeline” as a suffix or prefix. Generic shell strings still pass through the existing reject list, extended for observed Vietnamese profile-shell labels.

Alternative considered: add the Vietnamese `aria-label` grammar only. Rejected because it would fix one locale while retaining the same structural instability for the next locale/layout.

### 4. Keep the existing Cloud fallback, but do not depend on it

When startup capture succeeds, hello carries the verified nickname and the existing Cloud difference-write path updates the account. The later first-`page.cards` enrichment remains an in-place secondary attempt for compatible layouts. No empty-card event or protocol change is introduced in this scope.

## Risks / Trade-offs

- [Startup may spend longer waiting for a slow Facebook page] → Use a bounded startup hydration budget and retain the stable cookie id as an honest fallback.
- [Visible anchor text could contain shell copy] → Require exact self-id binding first, normalize/clean the candidate, and reject known generic labels; never use text from an unrelated id.
- [A navigation-enabled caller could unintentionally move an unrelated page] → Navigation occurs only from an unknown/non-Facebook context, only to the Facebook home page, and all runtime/direct callers explicitly disable it.
- [New Facebook feed layouts may still emit no `page.cards`] → Startup hello is the primary successful refresh path; feed selector compatibility is intentionally a separate change.

## Migration Plan

1. Land the Edge code and focused tests without protocol or data migration.
2. Run Facebook identity/session tests, acceptance, the full Edge test suite, and typecheck.
3. Roll back by reverting the Edge commit; Cloud and stored account data remain compatible because message shapes do not change.

## Open Questions

None for this scope. Feed-card selector modernization should be investigated separately with its own captured layouts and behavioral contract.
