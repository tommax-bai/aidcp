## 1. Contract and evidence

- [x] 1.1 Add a strict OpenSpec delta for the capture-backed comment-create descriptor, local-only write context, acknowledgement truth, and no-resend boundary.
- [x] 1.2 Add a sanitized structural fixture containing synthetic identifiers/content and the observed HTTP 201 acknowledgement shape.

## 2. Edge implementation

- [x] 2.1 Parse and persist the bounded target-comment write context in account-local Edge state without expanding Cloud payloads.
- [x] 2.2 Promote only `commentCreate` to capture-backed evidence and serialize its observed referer/body shape with a fresh client ID.
- [x] 2.3 Require the target context before dispatch and preserve the existing non-retry-safe failure/ambiguous-result state machine.

## 3. Verification

- [x] 3.1 Cover parsing, local persistence/reset, exact request serialization, HTTP 201 acknowledgement, and missing-context no-comment-create behavior.
- [x] 3.2 Run focused WeChat tests, Edge acceptance/full tests, typecheck, and strict OpenSpec validation.
- [x] 3.3 Record implementation/test evidence and integrate through the repository landing workflow without an installer, online deployment, or another real write.

## Verification evidence

- Focused WeChat tests: 42 passed, 0 failed.
- Edge acceptance: 25 passed, 0 failed, gated real-machine E2E skipped as designed.
- Edge full suite: 1840 passed, 0 failed.
- `npm run typecheck`: passed.
- `npm run build:dist`: passed; no installer was built.
- `openspec validate wechat-comment-capture-backed-write --strict`: passed.
- Edge implementation commit: `d715606` (`wechat-comment-capture-backed-write: match confirmed reply shape`), landed on `origin/master` through `scripts/land-change`.
- Control contract rebased onto the latest `origin/main` and validated before fast-forward publication.
- No additional platform write was dispatched during implementation or automated verification.
