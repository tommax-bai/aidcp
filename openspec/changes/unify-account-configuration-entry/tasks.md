## 1. Console implementation

- [x] 1.1 Replace the account table platform addon and video-only runtime prop with one optional account configuration render prop.
- [x] 1.2 Render the unified “配置” column with explicit empty state while keeping read-only table consumers unchanged.
- [x] 1.3 Route Facebook configuration and Video Channels runtime control into the unified column from `AccountsPage`.

## 2. Regression coverage

- [x] 2.1 Update account-page tests to verify the “配置” header, platform-only cells, per-platform entry placement, and unsupported-platform empty state.
- [x] 2.2 Run focused Console tests plus full test, typecheck, and build validation.
  <!-- Validation: focused `WechatChannelsReplySettings.test.tsx` 44/44 passed; full single-worker suite 37 files, 255 passed, 1 skipped; `npm run typecheck` passed; `npm run build` produced `dist/assets/index-Bv4dvn6e.js` and `index-6m7oiVLn.css`. Parallel full-suite attempt timed out under contention and was superseded by the clean serial run. -->
- [x] 2.3 Run `openspec validate unify-account-configuration-entry --strict` and record validation evidence.
  <!-- `openspec validate unify-account-configuration-entry --strict`: valid on 2026-07-22. -->

## 3. Integration and delivery

- [ ] 3.1 Commit the Console implementation and OpenSpec artifacts with scoped pathspecs.
- [ ] 3.2 Rebase and fast-forward integrate the Console change to `master`, then push without force.
- [ ] 3.3 Deploy the Console static build to dev from the clean canonical checkout with backup and verify hashes, HTTP health, and the account-page UI.
- [ ] 3.4 Update this task log with repo commit, validation, deployment, and deviation evidence.
