## 1. aidcp-edge — Feed continuity (no flag; verify a round on its own)

- [ ] 1.1 `feed-reader.ts` `ensureFeed`: skip the `Page.navigate` only when `URL==activeFeedUrl && hydrated && no blocking overlay`; keep running `blockingReason()` every scroll (cookie consent / login+captcha recheck must not degrade from per-scroll to per-session).
- [ ] 1.2 `scanCards` / `FEED_SCAN_JS`: report only newly-appeared top-level non-nested hydrated cards (exclude nested comment articles; take noteId from the card-header timestamp link, not the first permalink); keep a session-level postId-set cursor (not a DOM-order watermark).
- [ ] 1.3 Zero-new-cards this scan ⇒ bounded continued scroll; still zero ⇒ honestly return `feed_exhausted` (recycled top cards reappearing must not be misread as new).
- [ ] 1.4 Implement FB `feed.refresh` = controlled re-navigation of the feed URL + clear cursor + return to top (matches C1a `feed_refresh.supported=true`).

## 2. aidcp-edge — Inline reader (flag-gated)

- [ ] 2.1 New `src/facebook/inline-reader.ts`: lock the top-level article by command postId (reuse C0 `canonicalPostId` + three-stage); shortcut when message `textContent.length >> innerText.length` (full text already in DOM, do not click); else click an anchored, `<a>`-excluded, in-message expand control via `el.click()`.
- [ ] 2.2 Verify `location.href` + dialog count + target card index unchanged around expansion; any change ⇒ abort in-place, fall back to detail navigation, report `note.detail{surface:'detail'}` honestly.
- [ ] 2.3 Post-check: re-measure the article `innerText.length`; unchanged ⇒ `expand_no_effect` (not success); a short post with no expand control ⇒ normal success (not `no_target`). Report `note.detail{noteId=page-derived, content=full text}`.

## 2b. aidcp-edge — Feed like two-step actuation (real-machine P4 finding)

- [ ] 2b.1 **Feed like is two-step** (probe P4, 2026-07-14): on the home feed `el.click()` on the `留下心情` button pops the **reaction-selector overlay** and does NOT commit — the button stays neutral, so the current single-click `FacebookLikeExecutor` returns `state_unchanged` (a **false failure on the feed**). Add a feed-aware commit: after the neutral-button click, if a reaction picker overlay is present, `el.click()` the `赞` item (`aria-label` exactly `赞`/`Like`, number-guarded against the reaction-count summary) inside the currently-open overlay, then run the existing post-verify (`isReactedState` already recognizes the reacted string `aria-label="从…移除赞" text="赞"` captured by the probe). If the single click *does* flip the state (`directToggle`), skip the second step. Keep the detail-page path unchanged (behavior may differ between surfaces — do not apply the two-step blindly to detail).
- [ ] 2b.2 Reflect 2b.1 in grayscale stage 5 precondition: "enable real like" must gate on the two-step commit landing + shadow-witness match, not just the single-click executor.

## 3. aidcp-edge — note.open routing + independent witness

- [ ] 3.1 `facebook-session.ts` note.open branches on `surface`/`purpose`: `surface:'feed'` ⇒ inline-reader; `purpose:'navigate'` onOpen MUST skip `reportNoteDetail`, returning `action.completed{observation, page-derived noteId}` only.
- [ ] 3.2 Populate `action.completed.observation` from measurement: author/textPreviewHead/reactionText/articleIndex/listKey/surface + page-derived canonical postId.

## 4. aidcp-edge — Target volatility + inline dwell + comments + XHS refusal

- [ ] 4.1 Target gone from DOM ⇒ `no_target(stale)` with no rollback search; only scroll into view when still in DOM but off-screen.
- [ ] 4.2 Inline read dwell = edge-local read floor (content length × dispatched tempo, anchor `inlineReadStartedAt`, max with feed-scroll dwell, never summed) + disconnect fallback.
- [ ] 4.3 Best-effort capture of a feed card's visible comments into `note.detail.comments[]` (protocol field already exists).
- [ ] 4.4 `browse-session.ts` (XHS): receiving `note.open{surface:'feed'}` ⇒ `capability_unsupported`, never silently fall back to detail.

## 5. Real-machine probes + ghost-doc fix

- [x] 5.1 Run probes P0–P7 on the desktop-UA test env; land the probe findings into this change directory and fix the three comment references to the non-existent probe doc (`a9df78d`) in `cta-labels.ts` / `feed-reader.ts` / `post-reader.ts` (re-sample on real machine first, then write the doc). <!-- edge facebook-feed-inline-browse 1819c94: P1/P3/P4/P7 ran automated on Dennis k1ej3o8f via scripts/fb-inline-probe.ts (reuses production FB_TARGET_HELPERS_JS + FacebookLikeExecutor, no re-impl); P0/P2/P5/P6 carried from prior manual single-probe. Findings doc docs/facebook-browse-and-like-loop-probe-findings.md created — resolves the 3 dangling refs (now docs/-pathed). See ## Notes for the design-changing P4 two-step result. -->
- [ ] 5.2 Backlog (cluster 67, `docs/real-machine-acceptance-backlog.md`) — remaining real-machine items from the probe run: cross-entry/cross-session postId identity, group `multi_permalinks` form (not on home feed), and whether a real pointer sequence bypasses the two-step picker.

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
