## Context

The legacy `FacebookBrowseSession` treats a reported card batch as presentation evidence, separately from browser scroll intent. A single-card Reels batch produces `reel_view`; a Feed batch containing exactly one `isVideo:true` card produces `feed_video_view`. Both carry `statsDelta.views=1` for the Electron shell's local fallback, while Cloud remains authoritative whenever `dailyUsage` is present.

`NativeBrowseSession` currently forwards the same `page.cards` payload to Cloud but emits only presence. It emits `note_open` and a fallback view only after `note_detail`, so Native-only browsing is invisible until detail-open and can double-project a card if card projection is restored without matching detail suppression.

## Goals / Non-Goals

**Goals:**

- Restore the legacy evidence boundary in the Native Facebook adapter.
- Use canonical Facebook post identity for session-lifetime activity deduplication.
- Keep Cloud reporting independent from local companion projection.
- Lock Reels, Feed video, malformed identity, duplicate cards, and later-detail behavior with focused Native tests.

**Non-Goals:**

- Change Cloud view accounting, quotas, risk state, or `page.cards` protocol.
- Count ordinary non-video Feed cards or infer video from title, URL, or page shape when `isVideo` is absent.
- Change Native navigation, selectors, likes, follows, dwell timing, packaging, or deployment.

## Decisions

### Project only from accepted `page_cards` output

The adapter will project activity after forwarding Native `page_cards`, using the exact reported cards as evidence. It will not project from `page.scroll` intent, presence, or browser URL because those signals do not prove that a new content identity was presented.

For Reels, eligibility requires `listKind === 'reels'`, exactly one reported card, and a canonical Facebook post identity. For Feed video, eligibility requires `listKind === 'feed'`, exactly one `isVideo:true` card in the batch, no Reel URL shape, and the existing strict canonical Feed-video identity rules. Other non-video cards may coexist in the Feed batch; two or more video cards make the presentation ambiguous and produce no video activity.

Alternative rejected: project every Feed card. Ordinary Feed cards historically count only after a real detail read, and expanding this change would invent a new browsing contract.

### Share the existing formatters and Feed-video identity boundary

Native will reuse `facebookReelViewUiText`, `facebookFeedVideoViewUiText`, and `facebookReadUiText` rather than maintain a second set of clipping and fallback rules. The strict Feed-video identity helper will move to the shared Facebook identity module so legacy and Native adapters use one fail-closed implementation.

Alternative rejected: accept any canonical post with `isVideo:true`. The existing rule intentionally rejects Reel identities, non-Facebook hosts, fragments, and malformed query shapes.

### Keep session-lifetime projection witnesses separate from Cloud delivery

Native will retain canonical identities projected from Reels and Feed video in two session-owned sets. A repeated card payload will still be reported to Cloud as supplied by the Native engine, but will not generate another desktop activity or fallback increment.

A later `note_detail` will always be reported to Cloud. Its local `note_open` projection will be suppressed only when its canonical identity matches either presentation set. Missing or uncanonical detail identity preserves the existing `note_open` fallback.

Alternative rejected: deduplicate by raw URL or title. Facebook exposes multiple URL shapes for one post and metadata can be absent or mutable.

## Risks / Trade-offs

- [Native reports one video among unrelated non-video cards] → Match the legacy oracle: the unique `isVideo:true` card is the only video-presentation witness; multiple videos remain fail-closed.
- [Cloud and local fallback totals differ temporarily] → Preserve the existing authority split; `statsDelta` is only a local fallback and does not replace Cloud `dailyUsage`.
- [Session restart permits the same item to appear again] → Scope witnesses to one Native browse session, matching available in-process evidence without adding persistence or protocol state.
- [Refactoring identity logic changes legacy behavior] → Move the helper without modifying its body and run both Native-focused and legacy Facebook session tests.

## Migration Plan

No data migration is required. Build and restart of the Edge runtime is sufficient after normal integration. Rollback is the paired Edge commit; no durable state or protocol needs reversal.

## Open Questions

None.
