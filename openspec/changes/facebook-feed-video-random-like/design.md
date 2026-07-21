## Context

The existing Facebook Feed scanner keys reportable cards from own-level canonical anchors. Real Feed probes on Mi Xu and Tianxing Bai showed a second layout: a lightweight video card can expose one `data-video-id`, one `<video>`, publisher, caption, reaction summary, and post-level like/comment controls while lacking `[role="article"]` or an explicit post permalink. Mi Xu exposed only hashtag links; Tianxing Bai exposed both `data-video-id` and a matching `/watch/?v=` link. Both could be liked safely only after locating the action inside the same strict card root and verifying `Gỡ Thích` / `移除赞` afterward.

The same probes also showed an embedded Reels rail with three mounted `<video>` elements at one viewport position, no `data-video-id`, and no local post action boundary. An unconstrained ancestor search incorrectly associated that rail with a preceding ordinary post. Therefore video presence alone is not identity evidence, and the scan, read, action, and verification paths must share one strict card/identity primitive.

Cloud already receives `listKind`, `isVideo`, `noteId`, author, and title in `page.cards`. The existing Reels policy already provides an injectable 25% draw, session-local idempotency, ordinary-appraiser bypass, note-scoped dispatch, and confirmed-receipt accounting. No wire shape is needed.

## Goals / Non-Goals

**Goals:**

- Make strict lightweight ordinary-Feed video cards reportable and actionable without cross-card or Reels-rail attribution.
- Count each actually presented Feed video once and make one fixed 25% ordinary-like decision while the target is still current.
- Preserve mandatory interaction precedence and all existing risk, quota, cooldown, duplicate, retry, and receipt invariants.
- Support the exact Vietnamese Facebook controls observed on extant accounts.
- Keep ordinary non-video Feed behavior and existing Reels behavior unchanged.

**Non-Goals:**

- Video-frame, audio, OCR, or multimodal content understanding.
- A Console probability setting, per-account tuning, or database migration.
- Liking a video with missing/ambiguous identity, missing caption safety evidence, or no same-card verification witness.
- Applying this policy to embedded Reels rails, the dedicated Reels tab, search results, or another platform.
- Packaging or releasing an Edge installer.

## Decisions

### 1. One shared strict card identity primitive owns scan and action parity

`post-identity.ts` will add a helper that returns a card identity only from either:

1. one own-level canonical post anchor; or
2. a strict lightweight video fallback containing exactly one numeric `data-video-id`, exactly one video, a publisher or story-message witness, and one post-level like/comment action boundary.

An explicit canonical anchor wins only when its canonical post id agrees with the strict video id. Multiple explicit ids, multiple video ids, multiple videos, missing action witnesses, or explicit/data-id disagreement return the null sentinel. A strict fallback without a permalink synthesizes `https://www.facebook.com/watch?v=<video-id>` for the existing noteId contract.

The Feed scanner, inline reader, like/comment target resolver, exclusive-region checks, and post-action verification will call the same helper. Adding a scanner-only synthetic noteId was rejected because the existing target resolver would still return `no_target`; DOM-order fallback was rejected because it can act on the adjacent card.

### 2. Merge strict lightweight videos with semantic cards, but present at most one primary video

The layout helper will continue to prefer semantic top-level Feed articles and will additionally merge strict lightweight video roots found inside the same Feed container. It will deduplicate ancestor/descendant overlaps and exclude a lightweight candidate contained by a semantic card already representing the same identity.

A video card is presentation-eligible only when its video has meaningful horizontal intersection and at least 35% vertical viewport intersection. If more than one eligible video exists in a scan, Edge reports only the one whose video center is closest to the viewport center; the others remain unseen by the session cursor and may be reported after a later scroll. Non-video card reporting is unchanged.

This keeps the existing wire shape while ensuring Cloud sees at most one primary ordinary-Feed video per batch. Merely checking computed style/positive rectangle was rejected because off-screen mounted video nodes pass that test.

### 3. Record presentation views before content selection, once per normalized video identity

The Cloud `page.cards` handler will treat the single strict `isVideo` Feed card as an actual presentation and emit the existing `interaction.occurred{action:'view'}` once per normalized note identity in the connection session. A later `note.detail` for the same video will not count a second view. Empty, ambiguous, multi-video, non-Feed, and non-Facebook batches do not use this path.

This mirrors the existing active-Reel browse accounting and fixes the denominator: a skipped or randomly abstained Feed video is still a real view. Counting only after `note.open` was rejected because the content evaluator can skip the video and leave no view record.

### 4. Generalize the existing presented-video policy without broadening it

RoleDispatcher will generalize the existing Reel decision bookkeeping to presented Facebook videos while keeping distinct validation by surface:

- `reels`: exactly one canonical `/reel/<id>` card, unchanged;
- ordinary `feed`: exactly one `isVideo` card in the batch with a canonical Facebook video identity, a non-empty caption, and no bounded obvious-risk text signal.

The Feed policy marks the normalized identity handled before drawing. An injectable random value strictly below `0.25` selects an ordinary like intent; `>=0.25` abstains. Invalid random values, missing text safety evidence, or obvious-risk caption terms abstain without a draw retry. Existing budget, account risk, cooldown, duplicate-action, note-scoped dispatch, retry, and confirmed-receipt paths remain authoritative.

The ordinary interaction appraiser keeps its mandatory branch before the external-handled skip. Thus a later confirmed mandatory rule can still force its required action after a random miss, while the random policy remains the sole ordinary like decision. This matches the deployed Reels ordering.

### 5. Vietnamese compatibility is bounded to verified post-level controls

The CTA normalization adds exact verified forms: neutral `Thích`, selected/unlike `Gỡ Thích` and `Bỏ thích`, comment `Viết bình luận`, and reacted word `Thích`. Numeric reaction summaries such as `Thích: 27K người` remain excluded from toggle targeting and may be parsed as counts.

This is a bounded compatibility fallback for existing localized sessions, not a generalized N-language selector system; the en-US environment pin remains the normative provisioning behavior.

### 6. Browsing continues after every terminal decision

A view record, probability miss, safety abstention, blocked hit, already-liked result, or failed like receipt does not terminate the Feed loop. Once the card is reportable it follows the existing `page.cards → selection/read/scroll` chain; truly ambiguous/unreportable cards retain the existing bounded continuation behavior.

## Risks / Trade-offs

- [Facebook moves or duplicates `data-video-id`] → Require independent card/action witnesses, one id/video, and explicit-id agreement; otherwise fail closed and continue browsing.
- [Two videos are simultaneously visible on a large viewport] → Report only the center-nearest primary video and defer the other until a later scan.
- [Caption-only safety cannot understand the actual video] → Require non-empty caption evidence, apply only a bounded obvious-risk exclusion, keep probability at 25%, and explicitly leave multimodal understanding out of scope.
- [A random hit can be blocked or fail verification] → Define 25% as intent selection; only the existing confirmed `ok:true` receipt counts as a like.
- [A mandatory rule is discovered after the early draw] → Mandatory appraisal stays ahead of the handled skip and can still force required actions; already-liked remains an honest no-op.
- [Existing imported accounts remain localized] → Cover only exact probed Vietnamese labels and retain fail-closed numeric/action disambiguation.

## Migration Plan

1. Implement and fixture-test the shared Edge card identity, viewport qualification, Vietnamese CTA support, and exact action verification.
2. Implement Cloud Feed-video view accounting and the generalized presented-video probability policy with focused and acceptance tests.
3. Run Edge and Cloud focused tests, acceptance suites, full suites, and typechecks; validate this OpenSpec change strictly.
4. Integrate each repository serially to its latest default branch and push. Deploy only the Cloud runtime delta to `dev` from the clean canonical checkout; Edge source changes require a restarted development client but no installer.
5. Re-run a bounded Mi Xu / Tianxing Bai probe to verify one view, one decision log, exact-target receipt, and continued scrolling. Roll back the respective default-branch commits if validation fails.

## Open Questions

None. The temporary probability is fixed at 25%; video understanding and configurability require separate changes.
