## 1. aidcp-edge — Feed continuity (no flag; verify a round on its own)

- [ ] 1.1 `feed-reader.ts` `ensureFeed`: skip the `Page.navigate` only when `URL==activeFeedUrl && hydrated && no blocking overlay`; keep running `blockingReason()` every scroll (cookie consent / login+captcha recheck must not degrade from per-scroll to per-session).
- [ ] 1.2 `scanCards` / `FEED_SCAN_JS`: report only newly-appeared top-level non-nested hydrated cards (exclude nested comment articles; take noteId from the card-header timestamp link, not the first permalink); keep a session-level postId-set cursor (not a DOM-order watermark).
- [ ] 1.3 Zero-new-cards this scan ⇒ bounded continued scroll; still zero ⇒ honestly return `feed_exhausted` (recycled top cards reappearing must not be misread as new).
- [ ] 1.4 Implement FB `feed.refresh` = controlled re-navigation of the feed URL + clear cursor + return to top (matches C1a `feed_refresh.supported=true`).

## 2. aidcp-edge — Inline reader (flag-gated)

- [ ] 2.1 New `src/facebook/inline-reader.ts`: lock the top-level article by command postId (reuse C0 `canonicalPostId` + three-stage); shortcut when message `textContent.length >> innerText.length` (full text already in DOM, do not click); else click an anchored, `<a>`-excluded, in-message expand control via `el.click()`.
- [ ] 2.2 Verify `location.href` + dialog count + target card index unchanged around expansion; any change ⇒ abort in-place, fall back to detail navigation, report `note.detail{surface:'detail'}` honestly.
- [ ] 2.3 Post-check: re-measure the article `innerText.length`; unchanged ⇒ `expand_no_effect` (not success); a short post with no expand control ⇒ normal success (not `no_target`). Report `note.detail{noteId=page-derived, content=full text}`.

## 3. aidcp-edge — note.open routing + independent witness

- [ ] 3.1 `facebook-session.ts` note.open branches on `surface`/`purpose`: `surface:'feed'` ⇒ inline-reader; `purpose:'navigate'` onOpen MUST skip `reportNoteDetail`, returning `action.completed{observation, page-derived noteId}` only.
- [ ] 3.2 Populate `action.completed.observation` from measurement: author/textPreviewHead/reactionText/articleIndex/listKey/surface + page-derived canonical postId.

## 4. aidcp-edge — Target volatility + inline dwell + comments + XHS refusal

- [ ] 4.1 Target gone from DOM ⇒ `no_target(stale)` with no rollback search; only scroll into view when still in DOM but off-screen.
- [ ] 4.2 Inline read dwell = edge-local read floor (content length × dispatched tempo, anchor `inlineReadStartedAt`, max with feed-scroll dwell, never summed) + disconnect fallback.
- [ ] 4.3 Best-effort capture of a feed card's visible comments into `note.detail.comments[]` (protocol field already exists).
- [ ] 4.4 `browse-session.ts` (XHS): receiving `note.open{surface:'feed'}` ⇒ `capability_unsupported`, never silently fall back to detail.

## 5. Real-machine probes + ghost-doc fix

- [ ] 5.1 Run probes P0–P7 on the desktop-UA test env; land the probe findings into this change directory and fix the three comment references to the non-existent probe doc (`a9df78d`) in `cta-labels.ts` / `feed-reader.ts` / `post-reader.ts` (re-sample on real machine first, then write the doc).

## 6. Verification

- [ ] 6.1 Edge unit tests (jsdom/FakeCdp): expand shortcut (`textContent>>innerText` ⇒ no click, content=textContent); `expand_no_effect` when length unchanged; expand control outside message / is an `<a>` ⇒ not clicked; abort-to-detail when location/dialog/index change; cursor (scan reports only new top-level cards, recycled reappearance not misread, zero-new ⇒ bounded scroll ⇒ `feed_exhausted`); ensureFeed guard (skip navigate only when URL==activeFeedUrl && hydrated && no blocking, but `blockingReason()` still called); `purpose:'navigate'` does not report note.detail; observation witness from acted-upon article; XHS honest refusal on `surface:'feed'`; AC-PROTO green.
- [ ] 6.2 Run `npm run test:acceptance`, full `npm test`, `npm run typecheck`.
- [ ] 6.3 Rebase on `origin/master` (coordinate with `facebook-dev-autobrowse-enable` browse-loop-resilience overlap), integrate, push edge to `master`.

## 7. Grayscale (cloud flags; after probes)

- [ ] 7.1 Stage 2: land feed continuity (no flag), verify a real-machine round (cluster 66): no reload-to-top, page.cards only new top-level cards, front door still runs each scroll, depth threshold ⇒ controlled refresh, zero-new ⇒ bounded scroll ⇒ feed_exhausted, taken-over-to-group-page ⇒ listKey mismatch not adopted + recovery.
- [ ] 7.2 Stage 3: land inline code with all flags off (zero behavior).
- [ ] 7.3 Stage 4: dev `AIDCP_FB_INLINE_LIKE` shadow — inline lock runs, not clicked; cloud compares independent witness vs selected card; sample P4 (already-liked state) on dev + test account (authorized).
- [ ] 7.4 Stage 5: enable real like — hard precondition P0+P3+P4 pass + shadow witness 100% match + no_target rate <10%; remove FB like from `RETRIABLE_INTERACTION_REASONS`.
- [ ] 7.5 Stage 6: enable inline read `AIDCP_FB_INLINE_READ` — hard precondition P1+P2; observe expand_no_effect rate / content completeness / feed navigation → 0 / view rate / like-view ratio.

## 8. Change Record

- [ ] 8.1 Update this task record with commits, validation, probes, and grayscale; `openspec validate facebook-feed-inline-browse --strict`; register clusters 66/67/68 in `docs/real-machine-acceptance-backlog.md`.
