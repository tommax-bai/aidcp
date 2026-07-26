## 1. Contract

- [x] 1.1 Extend the frozen ReplyProfile and polisher input schemas with an optional nullable 20,000-character knowledge document.
- [x] 1.2 Update internal API and AI role fixtures plus contract validation tests without changing Edge protocol messages.

## 2. Cloud

- [x] 2.1 Add backward-compatible profile normalization/validation, defaults, bounded config request bodies, and scope version persistence for knowledge documents.
- [x] 2.2 Pass only the matched channel document to `reply_polisher` and harden its prompt for grounded answers, not-found honesty, and untrusted-document instructions.
- [x] 2.3 Add focused Cloud tests for legacy/null/valid/oversized profiles, model-call gating, grounded prompt content, injection boundaries, and protected template guidance fallback.

## 3. Console

- [x] 3.1 Mirror the contract field, normalize missing values, and add a per-channel “AI 回答说明文档” editor to the existing profile save chain.
- [x] 3.2 Add Console tests for editing/saving, 20,000-character limits, draft preview use, permission/CAS behavior, and stale scope isolation.

## 4. Verification

- [x] 4.1 Run focused and full Cloud tests, Cloud typecheck, full Console tests/build, contract validation, and strict OpenSpec validation.
  <!-- Validation: Cloud focused 7/7, full 2806 passed + 8 skipped, typecheck passed; Console reply settings 39/39, full 233 passed + 1 skipped with a 30s runner timeout after isolated 5s contention reruns, production build passed; three contract schema/fixture checks and OpenSpec strict passed. -->

## 5. Delivery

- [x] 5.1 Commit, rebase, integrate, and push the control, Cloud, and Console default branches with validation evidence.
  <!-- Delivery: control main 80d4800, Cloud master 7d02d1f, and Console master 65b9df0 were fast-forward integrated and pushed after validation; no Edge protocol or installer change. -->
- [x] 5.2 Deploy Cloud then Console from clean default checkouts to `dev`; verify hashes, services, health, logs, PostgreSQL, Feishu, unchanged reply/contact counts, and no real platform write.
  <!-- Dev 2026-07-22: Cloud deployed from clean current master 833b160 (contains feature 7d02d1f), then Console 65b9df0. Backups: cloud.bak.20260722-145823.tar.gz, cloud.env.20260722-145823.bak, console.bak.20260722-145944.tar.gz. Local/remote feature-file and static-asset hashes matched; aidcp-cloud active with NRestarts=0; 8787/8090/8088/5432 listened; panel/public health returned ok; PostgreSQL SELECT 1 passed; Feishu bot Dev.A and WSClient onReady verified; recent error count was zero; isales-api/isales-scheduler remained active. Reply jobs/send attempts/contact comment attempts stayed 4/0/63 before and after, so no real platform write occurred. No migration or Edge package was involved. -->

## 6. Maximum-length follow-up

- [x] 6.1 Specify that initial AI generation and polishing receive the concrete channel `maxLength`, count the complete candidate, and never truncate protected content.
- [x] 6.2 Implement the hard prompt constraint plus at most one compression retry for an otherwise valid over-length polisher candidate.
- [x] 6.3 Add focused retry/boundary tests and run Cloud full tests, typecheck, contract checks, and strict OpenSpec validation.
  <!-- Follow-up validation: Cloud focused 5/5, full 2863 passed + 8 skipped, typecheck passed; contract metaschema/internal-api/AI fixtures and OpenSpec strict passed. The boundary test proves two model calls maximum and no string truncation. -->
- [x] 6.4 Commit, integrate, push, deploy the Cloud follow-up to `dev`, and verify service health, logs, state counts, and no real platform write.
  <!-- Follow-up delivery 2026-07-22: Cloud master e179025 was pushed and deployed to dev from the clean default checkout. Backups: cloud.bak.20260722-162458.tar.gz and cloud.env.20260722-162458.bak. Only reply-ai.ts and its test changed remotely; local/remote hashes matched. aidcp-cloud stayed active/running with NRestarts=0; 5432/8088/8090/8787 listened; public /api/health and /capi/health returned ok; PostgreSQL SELECT 1 passed; Feishu remained Dev.A with WSClient onReady; no actual error-priority journal entries were present; isales services remained active. Reply jobs/send attempts/contact comment attempts stayed 4/0/63, so deployment performed no real platform write. -->

## 7. Knowledge-answer effectiveness and explainable risk

- [x] 7.1 Specify required knowledge answering, one shared correction retry, ordinary-consultation risk rubric, preview reasons, and missing-contact honesty.
- [x] 7.2 Extend the frozen polisher input with classifier intent and the internal preview contract with a named fallback reason.
- [x] 7.3 Implement Cloud knowledge-answer correction, bounded retry sharing, reviewer rubric, deterministic rejection reason, and focused tests.
- [x] 7.4 Update Console preview reason labels and tests without exposing discarded candidates or knowledge document bodies.
- [x] 7.5 Run contract validation, focused/full Cloud and Console tests, Cloud typecheck, Console build, and strict OpenSpec validation.
  <!-- Effectiveness validation: Cloud focused reply-config/AI 28/28, full 2867 passed + 8 skipped across 200 suites, and typecheck passed. Console focused 52/52, full 253 passed + 1 skipped, and production build passed. Contract metaschema/internal-api/AI fixture checks, diff checks, and OpenSpec strict validation passed. -->
- [x] 7.6 Commit, integrate, push, deploy Cloud then Console to `dev`, live-preview the current v8 question without sending, and verify health/logs/state counts.
  <!-- Delivery 2026-07-22: control main 9212810, Cloud master 11bc104, and Console master 4d8eced were fast-forward integrated and pushed. Cloud then Console were deployed from clean default checkouts to dev; initial rollback backups are cloud.bak.20260722-171506.tar.gz, cloud.env.20260722-171506.bak, and console.bak.20260722-171506.tar.gz, with final Cloud follow-up rollback at cloud.bak.20260722-173438.tar.gz plus matching env backup. Current v8 live preview for “适合几岁的孩子啊” returned the 29/30-character grounded answer “主要适合三至六年级，一二年级需看基础。收到，我们单独聊一下”, fallbackReason=none, content risk=low with introduced_claim, and action=review_required. Local/remote Cloud and Console hashes matched; aidcp-cloud active/running with NRestarts=0; 5432/8088/8090/8091/8787 listened; /api/health and /capi/health returned ok; PostgreSQL SELECT 1 passed; Feishu was Dev.A with WSClient onReady; error-priority journal was empty; isales services remained active. Reply jobs/send attempts/contact comment attempts stayed 4/0/63, so no platform reply was sent. Account k1esb68e contact length remained 0; real template + contact requires operator configuration and was not fabricated. -->
