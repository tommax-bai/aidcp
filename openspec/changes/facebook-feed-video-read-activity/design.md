## Context

Cloud already treats a Facebook ordinary-Feed batch containing exactly one strict `isVideo:true` card with a canonical non-Reel identity as a real presentation view. The Edge session reports the same `page.cards` payload but emits a local activity only for `listKind:'reels'`; ordinary Feed cards fall through to a presence-only event. On Mi Xu this produced ten Cloud-confirmed views and zero matching read activities in one uninterrupted client session.

The existing Reel activity path establishes the required honesty boundary: project a readable activity from an accepted card presentation, carry an immediate local fallback count, and suppress a later duplicate detail activity. The Feed-video path should reuse that pattern without changing Cloud accounting or broadening which cards count as views.

## Goals / Non-Goals

**Goals:**

- Project every Edge-reported ordinary Feed-video presentation that matches the existing Cloud-countable single-video shape into one readable local activity.
- Bind the activity to the card’s canonical post identity and actual caption/author metadata.
- Keep duplicate presentation and later detail reporting idempotent in the activity stream and local fallback count.
- Preserve Cloud customer-auth `dailyUsage` as the authoritative total.

**Non-Goals:**

- Changing Feed card qualification, Cloud `interaction.occurred` accounting, quota policy, or the 25% like policy.
- Adding a new protocol field, persisted activity-history API, database table, or Console surface.
- Claiming video completion, deep reading, or content understanding beyond presentation.
- Building or releasing an Edge installer.

## Decisions

### 1. Emit from the accepted Feed cards boundary

`FacebookBrowseSession.emit()` SHALL inspect the same outgoing Feed batch immediately after reporting it to Cloud. Exactly one `isVideo:true` card with a canonical non-Reel Facebook post identity is eligible; zero, multiple, malformed, or Reel-shaped candidates remain silent. Emitting from scroll intent was rejected because a failed scroll or unreportable DOM card is not a proven view.

### 2. Use a distinct `feed_video_view` activity type

The new event SHALL use the existing “读” marker but retain a distinct machine-readable type from `reel_view` and `note_open`. This keeps presentation surfaces auditable and avoids labeling an inline Feed presentation as a Reel or explicit detail open.

### 3. Keep Feed-video presentation deduplication session-wide and surface-aligned

The session SHALL maintain a Feed-video set of canonical post ids already projected as presentations. It SHALL live for the full `FacebookBrowseSession` instance and MUST NOT be cleared by Feed cursor resets, search changes, refreshes, or returns. A repeated Feed cards batch or later `note.detail` for the same id still reaches Cloud but SHALL NOT emit a second activity or fallback `views` increment.

The existing Reel activity set remains separate because its reset and Cloud accounting semantics are surface-specific. Reusing its pattern but not its storage keeps the new Feed projection aligned with Cloud’s session-wide `countedFacebookFeedVideoViewKeys` behavior and avoids changing already-delivered Reel behavior.

### 4. Reuse bounded human-readable metadata and local fallback semantics

The formatter SHALL prefer the reported caption/title and author, clip both to the existing activity widths, and fall back to “看了一个视频” without exposing URL, noteId, or other machine identifiers. The event carries `statsDelta.views=1` only for the existing immediate/offline fallback; the next Cloud customer-auth refresh remains authoritative and may replace it.

### 5. Integrate after rebasing the concurrent Reel-follow work

Another active Edge change modifies adjacent Facebook session, companion-event, renderer, and test code. This change remains isolated in its own worktree and SHALL be rebased onto the latest `origin/master` immediately before serial integration; all affected focused tests, acceptance, full tests, and typecheck SHALL be rerun after any conflict resolution.

## Risks / Trade-offs

- [Feed card shape drifts from the Cloud predicate] → Require the existing internal `isVideo` witness, exactly one video card, a canonical identity, and explicit non-Reel shape; keep focused invalid/multiple/Reel-shaped tests.
- [The same Feed video is re-reported after return, search, or refresh] → Deduplicate by canonical post id in a Feed-specific set that is not cleared with the browsing cursor.
- [A later detail open duplicates the presentation] → Reuse the presentation-id set to suppress only the local activity/count while still forwarding detail data.
- [Caption or author is absent] → Use bounded partial or generic wording and never substitute machine identifiers.
- [Concurrent Edge work changes adjacent lines] → Rebase and rerun all required validation before fast-forward integration; never overwrite the other worktree.

## Migration Plan

1. Add the Feed-video formatter, event type, presentation projection, shared deduplication, and read-marker mapping with focused tests.
2. Run focused Facebook/UI tests, acceptance, the full Edge suite, and typecheck in the isolated worktree.
3. Rebase onto the latest Edge default branch, rerun required gates, fast-forward push, then integrate and validate the control OpenSpec evidence.
4. Verify the development-runtime loading boundary. Restart the currently running client only when doing so cannot overwrite settings or trigger an unapproved Facebook action; otherwise report the restart requirement as a remaining live-acceptance limitation. No ECS deployment applies because Cloud code is unchanged; no installer is built.

Rollback is the Edge commit reversal plus a development-client restart. Cloud view accounting remains unchanged throughout.

## Open Questions

None.
