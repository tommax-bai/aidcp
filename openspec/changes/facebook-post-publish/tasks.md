## 1. OpenSpec And Probe Baseline

- [ ] 1.1 Confirm sibling repo state with `git worktree list`, `../aidcp-cloud`, `../aidcp-edge`, and `../aidcp-console` availability before implementation.
- [ ] 1.2 Re-run read-only Facebook composer probe on a known Facebook test/import profile for wide `1365x900`, medium `768x900`, and narrow `430x932`; record sanitized counts/status only.
- [ ] 1.3 Add no-submit probe plan for composer open/focus/type/clear and media attach/remove; keep real submit blocked behind disposable target gates.
- [ ] 1.4 Validate OpenSpec proposal shape with `openspec validate facebook-post-publish --strict` before coding.

## 2. aidcp-cloud Media Pool

- [ ] 2.1 Add `account_facebook_publish_image_set` and `account_facebook_publish_image` self-healing DDL with account FK, status enum/checks, ordering indexes, and usage record references.
- [ ] 2.2 Implement `FacebookPublishMediaStore` with list/upload insert/reorder/update-status/reserve/release/mark-used/quarantine operations and transaction-safe reservation.
- [ ] 2.3 Enforce account existence and `accounts.platform === 'facebook'` before any media write; reject retired/missing/non-Facebook accounts without creating ghost rows.
- [ ] 2.4 Add upload byte validation for image content type, size limit, sha256, filename metadata, and per-file failure reporting.
- [ ] 2.5 Use injected `ObjectStore` to upload manual images to OSS with account-isolated object keys; fail honestly when OSS is unavailable or upload fails.
- [ ] 2.6 Add unit tests for DDL idempotency, platform gating, upload success/failure, dedupe metadata, reservation race, release, used, quarantine, disabled, and deleted states.

## 3. aidcp-cloud Panel API

- [ ] 3.1 Extend panel deps/types with Facebook publish media store and DTOs for image sets, images, status summary, upload results, and update patches.
- [ ] 3.2 Add `GET /api/accounts/:id/facebook-publish-media` returning ordered image sets and status counts.
- [ ] 3.3 Add upload endpoint for Facebook publish media with a request body limit appropriate for images, separate from the existing small JSON body limit.
- [ ] 3.4 Add reorder/update-status/delete endpoints with non-optimistic write-after-read responses and explicit handling for `reserved` / `quarantine` sets.
- [ ] 3.5 Add panel API tests for auth, account/platform gating, upload body limits, partial upload failures, reorder, disable/delete, and reserved/quarantine protections.

## 4. aidcp-console Media Management

- [ ] 4.1 Extend `FacebookSearchConfig` or replace it with a tabbed `FacebookAccountConfig` that keeps existing comment config and adds a publish media tab.
- [ ] 4.2 Add batch image upload UI with thumbnails, per-file success/failure, status counts, and server-returned true state refresh.
- [ ] 4.3 Add ordered media list controls for reorder, caption hint editing, disable/delete, and status filtering.
- [ ] 4.4 Hide Facebook publish media UI for non-Facebook accounts and show actionable "素材不足" status for Facebook accounts.
- [ ] 4.5 Add console tests for upload flow, non-optimistic refresh, platform gating, partial failures, and reserved/quarantine action restrictions.

## 5. aidcp-cloud Platform Publish Pipeline

- [ ] 5.1 Add `PublishPlatformProfile` or equivalent profile registry for XHS and Facebook publish behavior.
- [ ] 5.2 Keep XHS publish profile behavior equivalent to current title/topic/generated-image/image-text path.
- [ ] 5.3 Implement Facebook publish profile with `imageSource='account_pool'`, image-required MVP, no XHS topics/cover/title field, and personal timeline target.
- [ ] 5.4 Add a Facebook media selector role/service that reserves account media and produces standard `imageDirective` / `assembledContent.imageUrls` inputs without calling image models.
- [ ] 5.5 Update `PublishExecutor` / draft creation to write Facebook draft images from reserved media and store media reservation metadata for later state transitions.
- [ ] 5.6 Update `CommandSequencer` / dispatch path to build platform-specific command plans and reject unsupported platform publish without fallback.
- [ ] 5.7 On approval rejection, submit-before-failure, confirmed success, and submitted-unconfirmed outcomes, update media state to available/used/quarantine consistently.
- [ ] 5.8 Add cloud tests proving Facebook does not call `ImageGenerator`, does not emit XHS-only commands, fails closed without media, and preserves XHS behavior.

## 6. aidcp-edge Facebook Post Executor

- [ ] 6.1 Add a Facebook publish executor/capability handler separate from XHS `PublishCommandDispatcher`.
- [ ] 6.2 Implement no-submit composer open/focus/type/clear using structural locators and real CDP/mouse events for wide and narrow layouts.
- [ ] 6.3 Implement media upload from OSS URL via temporary local file and Facebook file input, with thumbnail/readiness verification and cleanup.
- [ ] 6.4 Implement submit flow with pre-submit validation, post-submit confirmation, and distinct `published_confirmed`, `submitted_unconfirmed`, and `failed_before_submit` outcomes.
- [ ] 6.5 Wire Facebook driver `publish` capability only after executor, cloud profile, tests, and probe gates are present.
- [ ] 6.6 Add edge unit/manual tests for wide/narrow no-submit flow, media attach/remove, login/checkpoint/overlay fail-closed, and no XHS fallback.

## 7. Scheduling And Operator Flow

- [ ] 7.1 Extend content scheduler checks so Facebook post slots require publish capability and at least one available media set before draft generation.
- [ ] 7.2 Keep Facebook scheduled posting in `review` mode for MVP; reject or fail-closed any `auto_approve` Facebook publish configuration.
- [ ] 7.3 Ensure Feishu approval/result cards show Facebook platform, account name, selected media thumbnails/count, and material shortage/unconfirmed-submit reasons.
- [ ] 7.4 Ensure draft editing can only delete existing Facebook draft images and cannot inject arbitrary URLs.

## 8. Gated Real Submit Probe

- [ ] 8.1 Add explicit environment gates for Facebook real-submit probe, including disposable target/profile confirmation and submit enable flag.
- [ ] 8.2 Run no-submit composer and media probes first; real submit remains blocked if either fails.
- [ ] 8.3 Run one gated real-submit probe on an operator-owned disposable Facebook target/profile and require reload/server/permalink confirmation for success.
- [ ] 8.4 Record only sanitized evidence: status, counts, hashes, viewport, reason codes, and no raw cookies/tokens/body secrets.

## 9. Validation And Closeout

- [ ] 9.1 Cloud: run focused media/publish tests, `npm run test:acceptance`, `npm test`, and `npm run typecheck`.
- [ ] 9.2 Edge: run focused Facebook publish tests/probes, `npm run test:acceptance`, `npm test`, and `npm run typecheck`.
- [ ] 9.3 Console: run focused component/API tests, then full test/typecheck/build as applicable for the console repo.
- [ ] 9.4 Control repo: run `openspec validate facebook-post-publish --strict`.
- [ ] 9.5 Commit and push touched sibling repos plus this OpenSpec change; update this tasks file with repo commit SHAs and any deviations.
- [ ] 9.6 Deploy production-facing cloud/console changes to `dev` after validation through the documented safe path; do not deploy `ol` without explicit request.
- [ ] 9.7 Do not build or publish an edge desktop installer unless explicitly requested; stop at source commit/push plus runtime/probe validation.
