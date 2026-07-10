# Tasks — facebook-browse-and-like-loop

## 1. Preconditions

- [ ] 1.1 Ground the edge and cloud worktrees on the latest default branch (`master`) before touching any hot file; `fetch` + rebase so the platform registry and the edge assembly gate are current.
- [ ] 1.2 Confirm the dependency `account-nurture-discipline-spine` is landed (or its cold-start ramped quotas + real throttle-backoff are available) so a fresh Facebook account is not run at full `normal` tempo by this loop.
- [ ] 1.3 Confirm the design target of ZERO changes to either `protocol.ts`: enumerate the platform-neutral messages and optional payloads the Facebook browse loop will reuse, and confirm none of them require a new `MessageType` (explicitly avoid the sibling feed-refresh change's new `feed.refresh` message).
- [ ] 1.4 Mark the hot files as single-writer / serialize-only for this change: cloud platform registry (`facebook` capabilities), the edge assembly gate that keys BrowseSession on the `browse` capability, and the edge active-command allowlist. Do not run these lines in parallel with another Facebook-registry change.

## 2. aidcp-edge — FB BrowseSession + selectors

- [ ] 2.1 Run a real-machine probe on a disposable Facebook account to pin the feed selectors (post/card container, author, permalink, media, text body) across the wide and narrow layouts before writing extraction code.
- [ ] 2.2 Implement a Facebook-specific BrowseSession under `src/facebook/` that produces structured `page.cards` from the pinned selectors, with faithful field mapping into the existing structured shape (Facebook has no collect/favorite → `collect` is an honest default/absent, never fabricated).
- [ ] 2.3 Implement Facebook detail deep-read producing `note.detail` (post body + comments as available) using the same selectors as the render gate, so the extraction and the readiness check agree.
- [ ] 2.4 Keep all Facebook difference below the driver selector/atomic/mapping layer; the cloud roles must remain able to decide on structured reports without any Facebook selector knowledge.

## 3. aidcp-edge — FB like atomic execution + post-action verification

- [ ] 3.1 Implement the Facebook like as an atomic edge action.
- [ ] 3.2 Add mandatory post-action verification: only report `ok` when the like button/state truly toggled; if the target is not found or the state did not change, report `no_target` honestly.
- [ ] 3.3 Never `count||1` and never fabricate a like count; report by real observed state.
- [ ] 3.4 Route Facebook like success accounting through the cloud `RiskController.record` PG path; do NOT add any parallel in-memory like counter on the edge.

## 4. aidcp-edge — active-command allowlist + FB idle watchdog + route regression assertion

- [ ] 4.1 Add the Facebook browse/like standalone (non-`plan.response`) commands to the edge `onMessage` active-command routing allowlist so they reach the browse handler and are not swallowed by the "other active message ignored" branch.
- [ ] 4.2 Give each Facebook browse/like command a bounded timeout that returns an honest `timeout`/`no_target` receipt instead of hanging.
- [ ] 4.3 Attach a bounded idle watchdog on the Facebook browse path (reuse browse-loop-resilience bounded-idle) so a cloud-`sent` command that produces no edge action and no receipt cannot livelock the session.
- [ ] 4.4 Add a route regression assertion proving the Facebook browse/like command types are in the allowlist (typecheck does not catch allowlist omissions).

## 5. aidcp-cloud — registry facebook gains browse/interact + open session-start gate

- [ ] 5.1 Add `browse` and `interact` to the `facebook` entry in the cloud platform registry.
- [ ] 5.2 Open the session-start platform gate so a Facebook account can start the browse loop (previously refused because `facebook` did not declare `browse`).
- [ ] 5.3 Drive the Facebook browse loop through the existing role-dispatcher two-layer translation — no new orchestration surface; roles keep acting on structured `page.cards`/`note.detail`.
- [ ] 5.4 Align the edge driver capability vocabulary and the cloud registry capability vocabulary word-for-word for Facebook (fix any pre-existing `join`-vocabulary mismatch rather than adding a new one).

## 6. Capability-flip atomicity

- [ ] 6.1 Ensure the `browse` capability flip for Facebook and the Facebook BrowseSession implementation land in this single change together — never split across changes/commits — so the assembly gate can never mount the xhs BrowseSession on a Facebook edge.
- [ ] 6.2 Add a test/assertion that a Facebook edge with `browse` declared resolves the Facebook BrowseSession (not the xhs one), locking the co-landing invariant.

## 7. Verification

- [ ] 7.1 edge: `npm run test:acceptance` → `npm test` → `npm run typecheck`.
- [ ] 7.2 cloud: `npm run test:acceptance` → `npm test` → `npm run typecheck`.
- [ ] 7.3 Confirm `AC-PROTO-*` still green — the two `protocol.ts` files remain a word-for-word pair (this change targets zero protocol edits).
- [ ] 7.4 Add explicit post-action-verification tests: like button truly toggled → `ok` + risk recorded via PG path; target not found / state unchanged → `no_target` and NO fake success, NO parallel counter.
- [ ] 7.5 Add the route-regression and idle-watchdog tests proving Facebook commands are not silently dropped and a stuck Facebook session is bounded.
- [ ] 7.6 Run `openspec validate facebook-browse-and-like-loop --strict`.

## 8. Rollout (isolation period, ol)

- [ ] 8.1 Ship default-off behind `AIDCP_FB_BROWSE_AUTO`; with the switch off there is no automatic Facebook browsing or liking.
- [ ] 8.2 Run shadow first on a disposable account: browse-only, or like logged but not executed; inspect that structured reports and the honest receipts look right without executing real likes.
- [ ] 8.3 Enable real likes only after the shadow observation passes; keep quotas conservative via the account-nurture discipline spine.
- [ ] 8.4 Deploy to `ol` (isolation period), record commit SHAs / validation / probe / deployment notes in this `tasks.md`, and register the real-machine acceptance items (feed selector coverage, like verification fidelity, watchdog behavior) in the real-machine backlog.
