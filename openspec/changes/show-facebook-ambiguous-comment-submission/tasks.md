## 1. Receipt Projection

- [x] 1.1 Add a typed `verification_ambiguous` branch to the Cloud join-comment receipt that stays warning/non-success and says “已加群，已评论，未确认发布结果”.
- [x] 1.2 Preserve the existing confirmed-success and generic not-submitted/known-not-live receipt branches.

## 2. Regression Coverage

- [x] 2.1 Add focused assertions for the ambiguous title, submitted wording, unconfirmed boundary, and warning status.
- [x] 2.2 Add or retain a focused assertion that a pre-submit failure does not use submitted wording.

## 3. Validation

- [x] 3.1 Run the focused Cloud comment-scheduler tests and Cloud typecheck.
  <!-- aidcp-cloud: `npx tsx --test test/comment-agent/comment-scheduler.test.ts` passed 122/122; `npm run typecheck` exited 0. -->
- [x] 3.2 Run `openspec validate show-facebook-ambiguous-comment-submission --strict`.
  <!-- aidcp control: strict validation passed. -->

## 4. Delivery

- [ ] 4.1 Commit and integrate the Cloud and control changes with repository SHAs and validation evidence recorded here.
- [ ] 4.2 Deploy the integrated clean Cloud default branch to DEV and verify the documented service, listener, health, and schema gates without issuing a real Facebook write.
