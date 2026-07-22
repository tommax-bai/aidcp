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

- [ ] 5.1 Commit, rebase, integrate, and push the control, Cloud, and Console default branches with validation evidence.
- [ ] 5.2 Deploy Cloud then Console from clean default checkouts to `dev`; verify hashes, services, health, logs, PostgreSQL, Feishu, unchanged reply/contact counts, and no real platform write.
