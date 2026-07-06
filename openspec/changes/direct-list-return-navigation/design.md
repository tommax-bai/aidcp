## Context

`navigation.back` is the cloud-to-edge contract for returning from a note, profile, or notification excursion. The edge implementation currently decides whether to call browser `history.back()` based on current list URL and note-modal visibility, then falls back to `Page.navigate(exploreUrl)` if the landing page is unhealthy.

Recent incidents show that any path that touches a stale Xiaohongshu detail history entry can surface an `access-modal` with "当前笔记暂时无法浏览 / 请打开小红书App扫码查看". That modal is page-level note access gating, not an account captcha. Treating it as `unknown` blocks the command loop and can escalate account risk incorrectly.

## Goals / Non-Goals

**Goals:**

- Prefer forward navigation to a known healthy source list over browser history.
- Preserve the `navigation.back` protocol and `action.completed{action:'back', ok:true}` completion contract.
- Preserve search-origin returns by recording the search result URL before opening a note.
- Keep note access-limit modals out of captcha/unknown account-risk reporting.

**Non-Goals:**

- Do not change cloud role topology or introduce a new protocol message.
- Do not investigate or change account credentials, login state, or Xiaohongshu account settings.
- Do not solve every Xiaohongshu access-denied cause; only recover the browse loop honestly.

## Decisions

1. Keep `navigation.back` as the protocol name, but change edge return semantics to "return to source list".

   The cloud contract already means "get back to the list so browsing can continue"; using browser history is an implementation detail. Keeping the message avoids cloud/protocol churn and limits the blast radius.

2. Record the source list URL on the edge immediately before `note.open`.

   Feed-origin notes can always return to configured `exploreUrl`. Search-origin notes need the actual `search_result` URL because `SessionContext` currently stores only `sourcePageType`, not the search URL. Edge is the only component that can cheaply read the exact current URL before opening the detail.

3. Use direct `Page.navigate` by default for feed-origin returns.

   This loses feed scroll position, but it avoids stale detail history entries and access-limit modals. The trade-off is acceptable because repeated history incidents are worse than re-ranking or duplicate card exposure.

4. Treat Xiaohongshu `access-modal` / `access-limit-app` as a recoverable non-account overlay.

   The modal text and classes identify a note-specific Web access limitation. It must not be reported as captcha/unknown account blocking. Returning to the list should clear it; if it persists, subsequent health checks still prevent silent success.

## Risks / Trade-offs

- Feed scroll position is lost more often -> mitigate with visited/recent note IDs and existing page.cards evaluation.
- Search result URLs may be unavailable after edge restart or direct detail startup -> fall back to existing health-checked return behavior rather than inventing a search URL.
- Access-limit modal classification may miss a future Xiaohongshu class rename -> keep text-based signals in tests alongside class-based signals.
