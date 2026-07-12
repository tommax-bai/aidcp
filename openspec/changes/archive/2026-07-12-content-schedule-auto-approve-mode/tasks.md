## 1. Cloud Data Contract

- [x] 1.1 Add schedule action mode types and self-healing DB columns/checks for `post_mode`, `comment_mode`, and `contact_comment_mode`, preserving boolean compatibility.
  <!-- repo: aidcp-cloud; commit: 1b4ba1b4b928c91b249112d06155387c2b68b339; note: added mode enum, DB columns/checks, and boolean backfill compatibility. -->
- [x] 1.2 Update `ContentScheduleStore` row/catalog/effective DTOs, validation, old boolean patch compatibility, mode patch writes, and contact-info gating for `contactCommentMode !== 'off'`.
  <!-- repo: aidcp-cloud; commit: 1b4ba1b4b928c91b249112d06155387c2b68b339; note: catalog/effective rows now expose modes; old booleans map to review/off. -->
- [x] 1.3 Update panel API types and `/api/content-schedule/:accountId` parsing to accept mode fields while still accepting old boolean fields.
  <!-- repo: aidcp-cloud; commit: 1b4ba1b4b928c91b249112d06155387c2b68b339; note: panel PUT accepts postMode/commentMode/contactCommentMode and legacy booleans. -->

## 2. Cloud Runtime Behavior

- [x] 2.1 Update `ContentScheduler` to gate on modes and pass `approvalMode` to post/comment/contact triggers.
  <!-- repo: aidcp-cloud; commit: 1b4ba1b4b928c91b249112d06155387c2b68b339; note: off/review/auto_approve gates and propagation added for all three actions. -->
- [x] 2.2 Implement scheduled publish auto-approval by writing the normal approval signal with content version, triggering the existing dispatcher, and sending a non-interactive Feishu notification.
  <!-- repo: aidcp-cloud; commit: 1b4ba1b4b928c91b249112d06155387c2b68b339; note: auto approve reuses approval signal + dispatcher; falls back to review card if signal write fails. -->
- [x] 2.3 Update XHS and Facebook comment approval flows so `auto_approve` sends a notification and proceeds without waiting for a Feishu approval button.
  <!-- repo: aidcp-cloud; commit: 1b4ba1b4b928c91b249112d06155387c2b68b339; note: comment auto approve is fail-closed if notification is unavailable. -->
- [x] 2.4 Update scheduled contact comments and hot-lead contact comments to use `contactCommentMode` consistently.
  <!-- repo: aidcp-cloud; commit: 1b4ba1b4b928c91b249112d06155387c2b68b339; note: hot-lead and scheduled contact comments now derive approval mode from contactCommentMode. -->

## 3. Console UI

- [x] 3.1 Update console API types to expose `postMode`, `commentMode`, and `contactCommentMode` with fallback compatibility.
  <!-- repo: aidcp-console; commit: 867fc256a74394733e4b97e940883123be77e9ff; note: API row and patch types expose ContentScheduleActionMode. -->
- [x] 3.2 Replace the three action switches on Content Schedule with three-state controls (`关` / `开` / `免审`) and preserve total-switch effective-state behavior.
  <!-- repo: aidcp-console; commit: 867fc256a74394733e4b97e940883123be77e9ff; note: Segmented controls keep stored child modes while total switch controls effective state. -->
- [x] 3.3 Update console tests for optimistic updates, disabled total-switch behavior, and mode patch payloads.
  <!-- repo: aidcp-console; commit: 867fc256a74394733e4b97e940883123be77e9ff; note: added auto_approve payload assertion for comment mode. -->

## 4. Validation and Closeout

- [x] 4.1 Add/update cloud tests for store mode compatibility, scheduler gating/propagation, publish auto-approval, and comment auto-approve.
  <!-- repo: aidcp-cloud; commit: 1b4ba1b4b928c91b249112d06155387c2b68b339; note: added/updated content schedule store, scheduler, publish executor, and compose approve tests. -->
- [x] 4.2 Run targeted cloud and console tests plus typechecks.
  <!-- validation: cloud npm run typecheck; cloud tsx targeted suite 183 tests passed; console npm run typecheck; console ContentSchedulePage vitest 5 tests passed with existing jsdom getComputedStyle stderr noise. -->
- [x] 4.3 Run `openspec validate content-schedule-auto-approve-mode --strict` and update task notes with commits/validation/deployment.
  <!-- validation: openspec validate content-schedule-auto-approve-mode --strict passed; deployment: dev 121.89.85.150 backed up at 20260712-132620, cloud restarted active, 8787/8090/8091 listening, panel health ok, PG select 1 ok, Feishu WS onReady, console public HTML/asset 200. -->
