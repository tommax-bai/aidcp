## 1. aidcp-edge — Canonical post identity

- [ ] 1.1 Upgrade `src/facebook/probes/page-structure.ts` `sanitizeFacebookPermalinkHref` into `canonicalPostId(href): string | null` — derive `fb:<container>:<postId>` from `posts/<id>` / `story_fbid` / `multi_permalinks` / `pfbid`, add container, exclude `comment_id` / nested-article / share-subtree links, and return `null` (not `''`) on failure.
- [ ] 1.2 Replace the divergent local `postKey` in `src/facebook/like-executor.ts` with the shared `canonicalPostId` derivation so like matching, comment matching, and dedup all key off one identity.

## 2. aidcp-edge — Three-stage target resolution (never DOM-order)

- [ ] 2.1 Parameterize `like-executor.ts` `currentArticleRoot` into `articleRootFor(targetPostId)` fed by `canonicalPostId(payload.noteId)`, falling back to `location.href` derivation only when the command carries no noteId (old-cloud compatibility).
- [ ] 2.2 Implement three-stage resolution (scope: last-opened visible dialog > `div[role=feed]`; top-level non-nested candidate; identity match on the card-header canonical link) and **delete the `document` fallback** in `searchRoots`; extend fail-closed (0 → `no_target`, >1 same-level → `ambiguous_target`) from the permalink branch to the feed context.
- [ ] 2.3 Make `facebook-session.ts` `likeCurrent` read `payload.noteId` (drop the `_payload` discard).

## 3. aidcp-edge — Bound the like to one card

- [ ] 3.1 Merge LOCATE + CLICK + VERIFY into a single in-page eval that tags the clicked article with `data-aidcp-target="<runId>"`; VERIFY reads only the tagged node and re-derives its postId == command postId; tagged node missing before verify → `verify_indeterminate` (not retriable).
- [ ] 3.2 Replace the unconditional `scrollIntoView({block:'center'})` with a bounded, humanized scroll that brings the target article into view before locating.
- [ ] 3.3 Structure `clusterHasComment` so a post-level react must share the action bar with a "comment/share" sibling and must not live inside a nested `[role=article]`; keep the reaction-count numeric guard (`赞：N位用户` is not a toggle).

## 4. aidcp-edge — Scope the comment editor

- [ ] 4.1 Narrow `comment-executor.ts` `fbEditors()` and every `eds[0]` consumer to the target article subtree (reuse the existing `targetPath` template); 0 editors in scope → `editor_not_found`, never fall back to `eds[0]`.

## 5. Verification

- [ ] 5.1 Edge unit tests (jsdom / FakeCdp): multi-article feed with target = Nth card ⇒ only the Nth react button flips, cards 1..N-1 untouched; postId not present ⇒ `no_target` and the DOM-first card is untouched; same-group two `multi_permalinks` posts ⇒ distinct postIds (collide today); garbage/`javascript:` href ⇒ `no_target` (canonicalPostId returns null); three-stage ambiguity ⇒ dialog main post + per-comment article + background feed card sharing a key resolves to the main post only, real same-level >1 ⇒ `ambiguous_target`; multi-editor page ⇒ focus the target article editor, 0-in-scope ⇒ `editor_not_found`; `verify_indeterminate` when the tagged node disappears; numeric guard non-regression.
- [ ] 5.2 Run `npm run test:acceptance`, full `npm test`, and `npm run typecheck`; AC-PROTO stays green (no protocol change).
- [ ] 5.3 Rebase on `origin/master`, integrate, push edge to `master`; record real-machine acceptance under cluster 64 in `docs/real-machine-acceptance-backlog.md` (feed like hits only the Nth card, no DOM-first fallback, multi_permalinks no collision, three-stage locks main post only, comment does not misfire, humanized scroll without teleport).

## 6. Change Record

- [ ] 6.1 Update this task record with commits and validation; `openspec validate facebook-note-scoped-targeting --strict`.
