## Context

Current publishing is structurally reusable at the cloud orchestration level, but the execution shape is still Xiaohongshu-specific:

- cloud already has draft generation, approval, account-level dispatch coordination, edge task lease, fail-fast sequencing, and publish logs.
- edge `PublishCommandDispatcher` navigates to the XHS creator URL and implements XHS-specific mode selection, title/body fields, topics, submit, and post-id capture.
- Facebook driver and cloud registry currently declare browse/comment/interact/join, not publish.
- prior no-submit Facebook probing found homepage composer entry and image/video input in both wide and narrow desktop layouts, but opening/focusing the composer is not yet validated enough for production execution.

The product direction is to avoid model-generated images for the Facebook MVP. Operators will upload image assets in the account's Facebook configuration; each Facebook post consumes the corresponding account image asset(s). This keeps the first release closer to an operator-controlled publish queue and removes image generation/provider variability from the Facebook path.

## Goals / Non-Goals

**Goals:**

- Add a Facebook post-publishing capability for personal timeline posts with text and operator-uploaded images.
- Add a per-account Facebook publish media pool in cloud and console, backed by OSS stable public URLs.
- Route Facebook publish generation and dispatch through platform publish profiles instead of XHS assumptions.
- Ensure Facebook edge publishing is explicit, fail-closed, and never falls back to XHS handlers.
- Preserve existing approval, draft version, account lease, dispatch resilience, risk gate, and content schedule semantics.
- Validate Facebook composer behavior on wide and narrow layouts before enabling real submit.

**Non-Goals:**

- Facebook group posting, Page posting, video posting, mentions, locations, background styles, or platform-native scheduled posts.
- Auto-approve Facebook posting in the first implementation pass.
- Model-generated images for Facebook.
- Building a desktop installer/package as part of this change.
- Changing Facebook commenting, joining, browsing, or group import behavior except where platform capability registration must stay consistent.

## Decisions

### 1. Account media pool is the Facebook image source of truth

Facebook publishing will use a new per-account media pool instead of the existing publish image generation roles.

Data model:

```text
account_facebook_publish_image_set
  set_id
  account_id
  sort_index
  status: available | reserved | used | disabled | quarantine
  reserved_record_id
  used_record_id
  created_at / updated_at

account_facebook_publish_image
  image_id
  set_id
  account_id
  oss_url
  object_key
  filename
  content_type
  byte_size
  sha256
  sort_index
  caption_hint
```

MVP upload behavior: each uploaded image becomes a one-image set. The schema keeps image sets so multi-image posts can be enabled later without a migration.

Alternatives considered:

- Reuse generated-image roles and replace the provider with a "pool provider". Rejected because it would hide the fact that Facebook images are operator-controlled inventory and would entangle model planning with asset consumption.
- Store image URLs directly on `accounts`. Rejected because status, ordering, usage history, dedupe, captions, and multi-image sets require an owned table.

### 2. Draft creation reserves media; final result consumes or releases it

Facebook draft creation locks the next available image set and writes those URLs into `publish_log.images`.

State transitions:

```text
available --reserve(recordId)--> reserved
reserved --approval rejected / failed before submit--> available
reserved --same-page permalink confirmed--> used
reserved --page accepted submit but permalink missing--> quarantine
reserved --operator disables/deletes--> disabled
```

If the draft is edited, the editor may remove selected images from that draft, but it must not inject arbitrary external URLs. Removing all Facebook images makes the draft unpublishable for this MVP unless a future pure-text mode is explicitly added.

The important boundary is "submitted but permalink missing". A page-level success signal means Facebook accepted the submission for the user's workflow, but it is not the same as a stable post identity. The record therefore becomes `submitted`, the media stays quarantined, and the system must not release or retry automatically because the post may already exist.

### 3. Platform publish profile owns generation and command shape

Cloud will introduce a platform publish profile alongside the existing comment profile shape:

```ts
interface PublishPlatformProfile {
  platform: PlatformId;
  supportsPublish: boolean;
  imageSource: 'generated' | 'account_pool';
  imageRequired: boolean;
  titleField: 'required' | 'internal_only' | 'none';
  supportedMetadata: readonly PublishMetadataKind[];
  commandPlan: 'xhs_creator_image_text' | 'facebook_timeline_composer';
}
```

For Facebook MVP:

- `imageSource = 'account_pool'`
- `imageRequired = true`
- `titleField = 'internal_only'` or `none` for page execution; title may remain for approval cards/history but is not filled into a Facebook title field.
- no XHS topics, collection, cover, visibility, or platform-native schedule commands are emitted.

This keeps XHS behavior unchanged while making unsupported platform actions explicit.

### 4. Facebook edge publish executor is separate from XHS publish dispatcher

The Facebook publish path should be implemented as a `FacebookPostExecutor` or equivalent capability handler under the Facebook runtime, not as branches inside the XHS `PublishCommandDispatcher`.

Executor phases:

1. navigate to Facebook home/profile publish entry.
2. open composer using real mouse/CDP events with layout-aware structural locators.
3. focus editor, type text character-by-character with the shared humanized keystroke rhythm, and verify editor content.
4. upload image(s), wait for thumbnail/attachment readiness, and verify count.
5. submit only after cloud authorization sequence reaches submit.
6. first classify the current-page dialog close or positive submit message as `submitted`; then capture a post ID/permalink from the same page. Normal dispatch MUST NOT reload the page merely to upgrade that state.

Result classes:

- `published_confirmed`: a stable post ID/permalink is present on the current page; mark publish record success and media `used`.
- `submitted_unconfirmed`: the current page accepted the submit action but has no stable post ID/permalink; persist the user-visible `submitted` status, retain media `quarantine`, and do not retry or force a reload.
- `failed_before_submit`: no post side effect; release media where safe.

### 5. Probe gates precede enabling the `publish` capability

The registry must not declare Facebook `publish` until the cloud profile, edge executor, tests, and no-submit probes are co-landed. The first implementation must include probes before real submit:

- composer open/focus/type/clear on wide `1365x900`, medium/narrow `768x900`, and narrow `430x932`.
- media attach/remove no-submit probe using a disposable local image.
- gated real submit only on an operator-owned disposable target/profile, with explicit environment gates and server confirmation.

This follows the existing Facebook safety boundary: real-write probes stay blocked unless disposable target inputs and explicit gates are present.

### 6. Console keeps FB configuration operator-focused

The existing `FB配置` entry can become a tabbed modal:

- 评论配置: current keywords/comment mode/template controls.
- 发帖素材: upload, thumbnails, order, caption hints, status, disable/delete.

The UI should be dense and operational, not a marketing page. The operator needs to see how many usable image sets remain before enabling review-mode scheduling.

## Risks / Trade-offs

- Facebook composer DOM/layout changes -> use structural locators, wide/narrow probes, and no-submit typed-input tests before enabling submit.
- Submit ambiguity -> split page-level `submitted` from permalink-confirmed `published`; never auto-retry after possible submit and never use a normal-page refresh as the confirmation mechanism.
- Asset exhaustion -> fail-closed and notify; do not publish pure text or reuse used images silently.
- OSS missing or upload failure -> reject upload with a clear reason; do not store local-only or fake URLs.
- Draft rejection after media reservation -> release only if no submit was attempted.
- Multi-image grouping deferred -> schema supports sets now, but MVP console treats each uploaded image as a set to reduce first-pass UI complexity.
- Platform routing drift -> add tests proving Facebook publish does not emit XHS-only command kinds and XHS behavior remains unchanged.

## Migration Plan

1. Add OpenSpec contracts and tests first.
2. Add cloud media-pool tables and store with self-healing DDL.
3. Add panel API and console media upload UI behind Facebook-account-only gating.
4. Add platform publish profile and Facebook media selector without enabling edge submit.
5. Add no-submit edge probes for composer open/type/clear and media attach/remove across wide/narrow layouts.
6. Add `FacebookPostExecutor` and wire `publish` capability only after probes and unit tests pass.
7. Run gated disposable real-submit probe; keep `auto_approve` disabled.
8. Deploy cloud/console to dev after validation; edge source changes are committed/pushed, but no installer is built unless explicitly requested.

Rollback:

- If cloud/console media pool has issues, keep Facebook `publish` capability disabled; existing FB browse/comment/join paths continue unaffected.
- If edge executor probe fails, leave media pool usable but block publish dispatch for Facebook with `unsupported_capability` / `probe_not_passed`.

## Open Questions

- Whether the first enabled target is home timeline only, or also account profile composer if home composer becomes unreliable.
- Whether operators need multi-image grouping in the first console UI, or whether "one uploaded image = one post" is enough for launch.
- Whether rejected drafts should release media immediately or keep a configurable hold for audit review.
