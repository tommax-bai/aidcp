## Context

The retired TypeScript Facebook session called `ensureFeed()` before its first scan. The Native-only session facade now sends `browse_scroll{reason:'initial_scan'}` directly to the Rust page engine, whose Facebook router reads the currently attached page without first establishing a Feed surface. AdsPower persists the last browser page, so a previous Reel, profile, group, search, or detail page can become the next automation session's accidental baseline.

The Cloud remains the authority that decides when a Feed session may move to Reels or another excursion. The Edge must therefore establish a deterministic Feed starting point without adding a new Cloud command or reviving the retired TypeScript page reader.

## Goals / Non-Goals

**Goals:**

- Make every Facebook automatic browse start or resume establish `https://www.facebook.com/` before the first card scan.
- Keep the navigation and post-navigation page reading inside the Native Facebook adapter.
- Fail honestly if the Feed page cannot be reached or inspected.
- Preserve all non-Facebook startup behavior and existing Cloud transition authority.

**Non-Goals:**

- Changing Feed selection, Reels fallback policy, pacing, quotas, risk state, or browser persistence.
- Returning to a pre-task scroll position after an automatic browse session resumes.
- Adding configuration, retries, compatibility branches, protocol messages, or JavaScript fallback.
- Packaging or releasing an installer.

## Decisions

### Reuse the existing Native `initial_scan` command

`NativeBrowseSession.start()` already emits `browse_scroll{reason:'initial_scan'}` for every initial start and browse resume. The Rust Facebook adapter will give that existing command a platform-specific meaning: navigate to the canonical Facebook home URL, wait for the new document to become ready, then run the existing bounded card projection.

Adding a new protocol command was rejected because this is an Edge-local page baseline, not a new Cloud orchestration decision. Navigating in the TypeScript facade was rejected because page structure and navigation policy belong to the Native-only adapter.

### Establish Feed unconditionally for a new browse generation

The adapter will not trust the persisted page even when it resembles a list surface. A new automatic browse generation deliberately resets to the canonical home Feed, so stale Reels/search/detail state and stale DOM cursors cannot leak across sessions. Ordinary Feed scrolling after startup remains idempotent and does not repeatedly navigate home.

### Treat failed baseline establishment as startup failure

If trusted CDP navigation, readiness probing, or the resulting Feed projection fails, the Native command must surface that failure. It must not fall back to scanning or reporting cards from the pre-navigation persisted page.

## Risks / Trade-offs

- [Starting automation reloads an already-open Feed] → This is limited to a new/resumed browse generation and intentionally creates a deterministic session boundary; ordinary subsequent scrolling remains continuous.
- [Facebook redirects home navigation to login/checkpoint] → Existing Native blocker classification reports the real state; the old persisted page is never accepted as Feed.
- [A task releases while its page is still visible] → Task quiescence already precedes browse resume; returning to Feed is the desired ownership handoff.
- [Other platforms regress] → The special branch exists only in the Rust Facebook adapter and tests assert the shared TypeScript startup command remains unchanged.

## Migration Plan

1. Land the OpenSpec delta and Edge implementation.
2. Run focused Native tests, Native build/verification, acceptance, full Edge tests, and typecheck.
3. Fast-forward into the default branches and rebuild the local development Native binary.
4. Do not claim installed-client delivery until a separately authorized installer is packaged and installed.

Rollback is a normal revert of the Edge commit; there is no protocol or data migration.

## Open Questions

None.
