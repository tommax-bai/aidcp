## Context

The Edge Facebook session emits a single-card `page.cards{listKind:'reels'}` only after `FacebookReelsReader` proves a new active Reel identity. Cloud treats that presentation as the authoritative `view` event and suppresses a later `note.detail` from counting the same Reel twice. The desktop activity stream is separate: the cards branch emits only presence, while the detail branch emits `note_open` plus a local fallback view delta. Therefore a Reel can be counted in “今日进展” without appearing in “今天做了这些”.

## Goals / Non-Goals

**Goals:**

- Project every successfully reported new Reel card into exactly one truthful local “读” activity.
- Use card metadata when available and a bounded generic fallback without exposing URLs or ids.
- Keep the local fallback view delta aligned with the same presentation event.
- Suppress a later detail activity for a Reel whose presentation was already projected.

**Non-Goals:**

- Changing Cloud view accounting, Reel navigation, selection, dwell time, or like/follow policy.
- Claiming that the video was watched to completion or deeply read.
- Changing ordinary Feed/detail activity behavior or building an Edge installer.

## Decisions

### 1. Emit activity from the accepted Reel cards branch

The session will emit a structured `reel_view` activity immediately after reporting a `listKind:'reels'` single-card payload. This reuses the exact Edge evidence Cloud already accepts as a view. Emitting from raw scroll intent was rejected because failed navigation or a recycled card would create false activity.

### 2. Give Reel presentation its own UI event type

`reel_view` will map to the existing “读” visual category, but its sentence will use “看了” rather than the detail-specific “打开”. Reusing `note_open` was rejected because it would blur presentation and explicit detail-open semantics and make deduplication harder to audit.

### 3. Suppress detail projection by canonical Reel identity

The session will remember canonical Reel ids for which a presentation activity has been emitted. A later `note.detail` for one of those ids will still be sent to Cloud, but the local `note_open` activity and fallback `views` delta will be skipped. Ordinary Feed details and any detail without a matching prior Reel activity remain unchanged.

### 4. Cloud usage remains authoritative

The `reel_view` event may carry `statsDelta.views=1` only for the existing offline/local fallback path. When Cloud `dailyUsage` is present, the renderer continues to use Cloud totals. No protocol or Cloud counter change is needed.

## Risks / Trade-offs

- [Reel author metadata is absent] → Show a bounded summary-only or generic “看了一个 Reel” sentence; never substitute a URL/id.
- [A later explicit open repeats the same content] → Canonical-id suppression prevents a second activity and second local fallback increment while retaining `note.detail` delivery.
- [UI type is not mapped] → Add renderer and parsing tests so `reel_view` is visibly categorized as “读”, not the generic dot.
- [Installed clients remain unchanged] → Land source and tests only; packaging remains an explicit separate request.

## Migration Plan

1. Add the event formatter and session projection with focused tests.
2. Add renderer classification coverage and run Edge focused/full/typecheck validation.
3. Fast-forward integrate source and OpenSpec records. No Cloud deployment or installer build is required.

Rollback is the Edge commit reversal; Cloud accounting and protocol are unaffected.

## Open Questions

None.
