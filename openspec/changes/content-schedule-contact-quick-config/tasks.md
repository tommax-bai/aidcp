## 1. Console implementation

- [x] 1.1 Add a controlled missing-contact quick editor to `ContentSchedulePage` that reuses the account contact-info endpoint, preserves verbatim non-empty input, and exposes pending/error states honestly.
  <!-- implementation: aidcp-console src/pages/ContentSchedulePage.tsx; controlled Popover, explicit save/cancel, verbatim non-empty payload, pending and mapped error states. -->
- [x] 1.2 Wire the clickable missing-contact indicator to the editor and update/invalidate schedule and account query state only after confirmed success.
  <!-- implementation: the missing tag is keyboard/click operable; confirmed non-empty response patches only hasContactInfo, then invalidates exact schedule and account queries. -->

## 2. Regression coverage

- [x] 2.1 Extend `ContentSchedulePage` tests for direct opening, whitespace rejection, verbatim request payload, pending gate behavior, confirmed unlock, and failure draft retention.
  <!-- coverage: aidcp-console src/pages/ContentSchedulePage.test.tsx exercises all six specified interaction boundaries through the real page/query mutation path with only HTTP mocked. -->
- [x] 2.2 Run focused tests, the console full test suite, typecheck, and production build.
  <!-- validation: focused ContentSchedulePage 9/9 passed; isolated prior-timeout WechatChannelsReplySettings 36/36 passed; full silent single-worker suite 34/34 files, 212 passed, 1 gated skip; typecheck passed; production build transformed 3724 modules and emitted index-Bus66Bfp.js / index-10ja52e5.css. -->

## 3. Validation and rollout

- [x] 3.1 Run `openspec validate content-schedule-contact-quick-config --strict` and record implementation/validation evidence in this task file.
  <!-- validation: `openspec validate content-schedule-contact-quick-config --strict` passed on 2026-07-20; implementation remains console-only and reuses the existing account contact-info endpoint. -->
- [x] 3.2 Rebase and integrate the console and control changes onto their default branches, push them, deploy the console build to `dev`, and verify the served assets without touching unrelated services.
  <!-- integration: console rebased onto origin/master, focused 9/9 and typecheck passed on the rebased tree, then fast-forward pushed as d18337c; control artifacts rebased, strict-validated, and fast-forward pushed as 5fc051d before this rollout record. deployment: dev target check passed; clean canonical console master d18337c rebuilt 3724 modules, backed up /opt/aidcp/console.bak.20260720-145717.tar.gz, and rsynced dist without --delete or service restart. verification: remote index-B-lONqB8.js / index-B5zsgl89.css and index.html SHA256 matched local; homepage/JS/CSS returned HTTP 200; aidcp-cloud remained active; 8787/8090/8088/5432 listened; /api/health and PostgreSQL SELECT 1 passed; Feishu WSClient onReady was present; four isales services remained active. The pre-deploy backup contained no intro.html or intro.payload.html, so their absence was pre-existing rather than caused by this deploy. -->
