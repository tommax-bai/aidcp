## 1. aidcp-edge — Feed continuity (no flag; verify a round on its own)

- [x] 1.1 `feed-reader.ts` `ensureFeed`: skip the `Page.navigate` only when `URL==activeFeedUrl && hydrated && no blocking overlay`; keep running `blockingReason()` every scroll (cookie consent / login+captcha recheck must not degrade from per-scroll to per-session). <!-- edge: pre-existing idempotent ensureFeed guard (change facebook-feed-scroll-refresh-fix, cluster 72); C2 did not re-touch it. blockingReason runs in ensureFeed + per-round in settleCards. -->
- [x] 1.2 `scanCards` / `FEED_SCAN_JS`: report only newly-appeared top-level non-nested hydrated cards (exclude nested comment articles; take noteId from the card-header timestamp link, not the first permalink); keep a session-level postId-set cursor (not a DOM-order watermark). <!-- edge bae3ad4: session-level `seenPostIds` Set keyed by canonicalPostId; `takeNewCards` filters unseen + re-indexes; `seedCursor` for initial/refresh/search/back. scanCards stays stateless (already skips shells + card-header permalink). -->
- [x] 1.3 Zero-new-cards this scan ⇒ bounded continued scroll; still zero ⇒ honestly return `feed_exhausted` (recycled top cards reappearing must not be misread as new). <!-- edge bae3ad4: scrollFeed bounded loop (FEED_SCROLL_EXTRA_ROUNDS=2); 0 new after bounded ⇒ action.completed{scroll, feed_exhausted}; cloud maps to refresh (C1b). -->
- [x] 1.4 Implement FB `feed.refresh` = controlled re-navigation of the feed URL + clear cursor + return to top (matches C1a `feed_refresh.supported=true`). <!-- edge bae3ad4: refreshFeed home-icon SPA换批 (pre-existing) + resetCursor+seedCursor on success (C2). Reload fallback still frequency-floored. -->

<!-- NOTE 1.1/1.4: the refresh MECHANISM (home-icon click, not full re-navigation) landed earlier in facebook-feed-scroll-refresh-fix; C2 adds the cursor clear on top. -->


## 2. aidcp-edge — Inline reader (flag-gated)

- [x] 2.1 New `src/facebook/inline-reader.ts`: lock the top-level article by command postId (reuse C0 `canonicalPostId` + three-stage); shortcut when message `textContent.length >> innerText.length` (full text already in DOM, do not click); else click an anchored, `<a>`-excluded, in-message expand control via `el.click()`. <!-- edge bae3ad4: FacebookInlineReader; buildInlineResolveJs reuses FB_TARGET_HELPERS_JS three-stage; SHORTCUT_RATIO 1.2 + 30-char delta guard; fbInlExpandControl = [role=button] expand-word, non-<a>, in message container. -->
- [x] 2.2 Verify `location.href` + dialog count + target card index unchanged around expansion; any change ⇒ abort in-place, fall back to detail navigation, report `note.detail{surface:'detail'}` honestly. <!-- edge bae3ad4: inline-read re-check href/dialogCount/articleIndex/postId; any mismatch ⇒ reason 'context_changed' ⇒ session openInlineNote falls back to openBrowseNote (detail read). -->
- [x] 2.3 Post-check: re-measure the article `innerText.length`; unchanged ⇒ `expand_no_effect` (not success); a short post with no expand control ⇒ normal success (not `no_target`). Report `note.detail{noteId=page-derived, content=full text}`. <!-- edge bae3ad4: clicked && innerTextLen not grown ⇒ 'expand_no_effect'; short post no-control not-shortcut ⇒ ok (read as-is); note.detail noteId = card's own DOM permalink (normalizeFacebookPermalinks). -->


## 2b. aidcp-edge — Feed like two-step actuation (real-machine P4 finding)

- [x] 2b.1 **Feed like is two-step** (probe P4, 2026-07-14): on the home feed `el.click()` on the `留下心情` button pops the **reaction-selector overlay** and does NOT commit — the button stays neutral, so the current single-click `FacebookLikeExecutor` returns `state_unchanged` (a **false failure on the feed**). Add a feed-aware commit: after the neutral-button click, if a reaction picker overlay is present, `el.click()` the `赞` item (`aria-label` exactly `赞`/`Like`, number-guarded against the reaction-count summary) inside the currently-open overlay, then run the existing post-verify (`isReactedState` already recognizes the reacted string `aria-label="从…移除赞" text="赞"` captured by the probe). If the single click *does* flip the state (`directToggle`), skip the second step. Keep the detail-page path unchanged (behavior may differ between surfaces — do not apply the two-step blindly to detail). <!-- edge bae3ad4: in likeTagged verify loop — reacted-first (directToggle wins, no picker) else commitFeedPicker (buildPickerProbeJs overlay≥2 items → buildPickerCommitJs clicks the LIKEITEM 赞); pickerCommitted guard = commit once. isReactedState unchanged. detail path unaffected (single click reacts → returns before picker). -->
- [x] 2b.1b Independent-witness observation on the like receipt (N4): FacebookLikeResult.observation = {surface, page-derived fb:postId, author, textPreviewHead, reactionText, articleIndex}, read (buildObservationJs) on shadow AND real success. surface = dialog-ancestor→'detail' else feed-container→'feed'. Session attaches noteId+observation to action.completed **only when surface==='feed'** ⇒ detail likes stay byte-identical (zero regression), feed likes activate cloud arbitration. <!-- edge bae3ad4 -->

- [ ] 2b.2 Reflect 2b.1 in grayscale stage 5 precondition: "enable real like" must gate on the two-step commit landing + shadow-witness match, not just the single-click executor.

## 3. aidcp-edge — note.open routing + independent witness

- [x] 3.1 `facebook-session.ts` note.open branches on `surface`/`purpose`: `surface:'feed'` ⇒ inline-reader; `purpose:'navigate'` onOpen MUST skip `reportNoteDetail`, returning `action.completed{observation, page-derived noteId}` only. <!-- edge bae3ad4: openNoteRouted → navigate→navigateForMigration (postReader open, NO note.detail, action.completed{ok, noteId=landed permalink, observation{surface:'detail'}}); feed→openInlineNote; default→openBrowseNote (today). -->
- [x] 3.2 Populate `action.completed.observation` from measurement: author/textPreviewHead/reactionText/articleIndex/listKey/surface + page-derived canonical postId. <!-- edge bae3ad4: like observation (buildObservationJs) + navigate observation (from detail read). listKey not populated (feed URL is session-side activeFeedUrl; cloud already knows the list it's on) — deferred, not load-bearing for stage-0. -->


## 4. aidcp-edge — Target volatility + inline dwell + comments + XHS refusal

- [x] 4.1 Target gone from DOM ⇒ `no_target(stale)` with no rollback search; only scroll into view when still in DOM but off-screen. <!-- edge bae3ad4: inline-read.found===false ⇒ reason 'stale' (no rollback); like-executor already had verify_indeterminate/target_lost + bounded scrollTargetIntoView (facebook-note-scoped-targeting). -->
- [x] 4.2 Inline read dwell = edge-local read floor (content length × dispatched tempo, anchor `inlineReadStartedAt`, max with feed-scroll dwell, never summed) + disconnect fallback. <!-- edge bae3ad4: computeInlineReadFloorMs (base 1200 + 20/char, cap 9000, ×tempo); ensureFeedDwell max(cloud-dwell-remaining, floor - elapsed-since-inlineReadStartedAt), consumed once. disconnect = chain drain / command timeout. -->
- [x] 4.3 Best-effort capture of a feed card's visible comments into `note.detail.comments[]` (protocol field already exists). <!-- edge bae3ad4: inline-read scans the card's direct nested [role=article] comment items (chrome-filtered); usually empty on home feed (comments need detail per probe §Detail) — honest empty, never fabricated. -->
- [x] 4.4 `browse-session.ts` (XHS): receiving `note.open{surface:'feed'}` ⇒ `capability_unsupported`, never silently fall back to detail. <!-- edge bae3ad4: guard before gate — surface==='feed' ⇒ reportActionCompleted{open_note, capability_unsupported}, no openAndReportNote. Test added. -->


## 5. Real-machine probes + ghost-doc fix

- [x] 5.1 Run probes P0–P7 on the desktop-UA test env; land the probe findings into this change directory and fix the three comment references to the non-existent probe doc (`a9df78d`) in `cta-labels.ts` / `feed-reader.ts` / `post-reader.ts` (re-sample on real machine first, then write the doc). <!-- edge facebook-feed-inline-browse 1819c94: P1/P3/P4/P7 ran automated on Dennis k1ej3o8f via scripts/fb-inline-probe.ts (reuses production FB_TARGET_HELPERS_JS + FacebookLikeExecutor, no re-impl); P0/P2/P5/P6 carried from prior manual single-probe. Findings doc docs/facebook-browse-and-like-loop-probe-findings.md created — resolves the 3 dangling refs (now docs/-pathed). See ## Notes for the design-changing P4 two-step result. -->
- [ ] 5.2 Backlog (cluster 67, `docs/real-machine-acceptance-backlog.md`) — remaining real-machine items from the probe run: cross-entry/cross-session postId identity, group `multi_permalinks` form (not on home feed), and whether a real pointer sequence bypasses the two-step picker.

## 6. Verification

- [x] 6.1 Edge unit tests (jsdom/FakeCdp): expand shortcut (`textContent>>innerText` ⇒ no click, content=textContent); `expand_no_effect` when length unchanged; expand control outside message / is an `<a>` ⇒ not clicked; abort-to-detail when location/dialog/index change; cursor (scan reports only new top-level cards, recycled reappearance not misread, zero-new ⇒ bounded scroll ⇒ `feed_exhausted`); ensureFeed guard (skip navigate only when URL==activeFeedUrl && hydrated && no blocking, but `blockingReason()` still called); `purpose:'navigate'` does not report note.detail; observation witness from acted-upon article; XHS honest refusal on `surface:'feed'`; AC-PROTO green. <!-- edge bae3ad4: 3 new test files (inline-reader 11 / like-executor-two-step 5 / facebook-session-inline 11) + XHS refusal in browse-session.test + driver.test edgeCapabilities. Note: expand-control <a>-exclusion + shortcut are unit-stubbed via IIFE markers; real DOM anchoring/reacted-string are probe-covered (real machine), not stubbed (memory fb-comment-editor-label-gap). -->
- [x] 6.2 Run `npm run test:acceptance`, full `npm test`, `npm run typecheck`. <!-- edge bae3ad4: acceptance 19/19 (AC-PROTO green) + full 1302/1302 + typecheck clean. -->
- [x] 6.3 Rebase on `origin/master` (coordinate with `facebook-dev-autobrowse-enable` browse-loop-resilience overlap), integrate, push edge to `master`. <!-- edge bae3ad4: rebased twice onto origin/master (6 unrelated electron commits, zero overlap with FB browse loop); ff-merged to master; pushed 4fbca0d..bae3ad4. facebook-dev-autobrowse landed portions already in master, no conflict. -->

## 7. Grayscale (cloud flags; after probes)

- [~] 7.1 Stage 2: land feed continuity (no flag), verify a real-machine round (cluster 66): no reload-to-top, page.cards only new top-level cards, front door still runs each scroll, depth threshold ⇒ controlled refresh, zero-new ⇒ bounded scroll ⇒ feed_exhausted, taken-over-to-group-page ⇒ listKey mismatch not adopted + recovery. <!-- edge bae3ad4: CODE LANDED (cursor + feed_exhausted are NOT flag-gated; active when AIDCP_FB_BROWSE_AUTO=on). Real-machine round VERIFICATION pending → cluster 66 (backlog). Dormant until edge rebuilt on dev. -->
- [x] 7.2 Stage 3: land inline code with all flags off (zero behavior). <!-- edge bae3ad4: inline reader + two-step + surface/purpose routing landed; cloud flags default off + edge declares inline_targeting (cloud version-skew gate only opens inline when its flag on) ⇒ zero behavior at stage 0. -->
- <!-- 7.3–7.5 (shadow like / real like / inline read) are cloud-flag grayscale on dev+test acct — deploy-time, after real-machine verification. Left [ ]. -->

- [ ] 7.3 Stage 4: dev `AIDCP_FB_INLINE_LIKE` shadow — inline lock runs, not clicked; cloud compares independent witness vs selected card; sample P4 (already-liked state) on dev + test account (authorized).
- [ ] 7.4 Stage 5: enable real like — hard precondition P0+P3+P4 pass + shadow witness 100% match + no_target rate <10%; remove FB like from `RETRIABLE_INTERACTION_REASONS`.
- [ ] 7.5 Stage 6: enable inline read `AIDCP_FB_INLINE_READ` — hard precondition P1+P2; observe expand_no_effect rate / content completeness / feed navigation → 0 / view rate / like-view ratio.

## 8. Change Record

- [~] 8.1 Update this task record with commits, validation, probes, and grayscale; `openspec validate facebook-feed-inline-browse --strict`; register clusters 66/67/68 in `docs/real-machine-acceptance-backlog.md`. <!-- edge bae3ad4: task record updated (§1–§4/§6 landed); openspec validate --strict pending final; clusters 66/67/68 backlog registration pending (with grayscale). Change stays ACTIVE for grayscale (7.3–7.5) + real-machine acceptance. -->

### Landing status (2026-07-14)

**Edge code LANDED to `aidcp-edge` master `bae3ad4`** (probe commit `278d79f`). Rebased twice onto latest
origin/master (6 unrelated electron commits, zero overlap); ff-merged; pushed `4fbca0d..bae3ad4`.
acceptance 19/19 + full 1302/1302 + typecheck clean. Canonical `../aidcp-edge` now on master (picks up on next `electron:dev`).

Landed: §1 feed continuity (postId cursor + feed_exhausted, **not flag-gated**), §2 inline reader, §2b two-step
feed like + witness observation, §3 note.open surface/purpose routing, §4 stale/dwell/comments/XHS-refusal,
§6 tests, driver `inline_targeting` capability, §7.2 (inline code with flags off).

**Stage-0 dormant / zero-regression**: cloud inline flags default off + version-skew gate ⇒ cloud never sends
`surface:'feed'`/`purpose:'navigate'` ⇒ note.open stays detail (today), like stays detail directToggle
(observation.surface='detail' ⇒ receipt byte-identical to today). XHS untouched (only adds honest refusal on
`surface:'feed'`). The **one** not-flag-gated behavior is the FB feed cursor (§1.2/1.3): when `AIDCP_FB_BROWSE_AUTO=on`
on dev, page.scroll now reports only unseen cards + emits `feed_exhausted` on recycling (cloud maps to refresh, C1b).
Dormant until the dev edge is rebuilt.

**Remaining (change stays ACTIVE)**: 7.1 real-machine round (cluster 66), 7.3 shadow-like witness sampling,
7.4 real-like enable, 7.5 inline-read enable — all cloud-flag grayscale on dev+test acct; 5.2/8.1 backlog cluster
registration (66/67/68). NOT deployed (edge is client-side, no ECS).

## Notes — 真机探针发现（2026-07-14, Dennis `k1ej3o8f`, cluster 67）

探针 P1/P3/P4/P7 已自动化跑通（edge branch `facebook-feed-inline-browse` `1819c94`；脚本 `scripts/fb-inline-probe.ts`
注入**生产** `FB_TARGET_HELPERS_JS` + 实例化**生产** `FacebookLikeExecutor`，结论建立在线上逻辑上；findings
`docs/facebook-browse-and-like-loop-probe-findings.md`）。直接影响本 change：

- **P4（设计增量 → 新增 §2b）**：feed 点赞是**两段**——`el.click()` 打 `留下心情` 只弹反应选择器浮层、不提交（按钮不翻转），
  第二段点浮层「赞」项才提交。**现役单击执行器在 feed 上 `state_unchanged` 误判失败**。已赞态确切串已拿到
  （`aria-label="从…移除赞" text="赞"`，`isReactedState` 已能判）——只缺执行第二段，检测无需改。P4 已提交一次真实点赞
  （Dennis→iQIYI 帖，未撤销，作线上证据）。
- **P3（task 1.2/2.1 地基）**：39 帖全 `resolve=ok`、反查命中=1、零撞卡（pfbid+video 两形态；group `multi_permalinks`
  本轮 home feed 未采到）——按 postId 锁卡真机成立。
- **P1（task 2.1/2.3）**：展开控件 = `div[role=button]` "展开"、**非 `<a>`**、message 容器内；textContent 捷径对**折叠帖证伪**
  （须点展开）、对无折叠帖成立（实测 ratio 1.51）。
- **P7（task 1.2/1.3）**：feed **回收**已滚过的卡（卡数 3→23 后回落、首屏 postId 第 1 轮即退出 DOM）——postId 集合游标是硬要求。
- P0/P2/P5/P6 沿用此前 Dennis 手动单针结论（已并记进 findings doc）。P2（展开不离 feed）+ P1（展开控件非 `<a>`）共同支撑 §2 inline reader。
