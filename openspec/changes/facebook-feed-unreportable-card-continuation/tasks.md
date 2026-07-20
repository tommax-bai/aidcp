## 1. Regression Evidence

- [x] 1.1 Add a lightweight media-only first-card fixture using the observed Vietnamese `/` timestamp/media-resource shape and prove it remains unreportable.
- [x] 1.2 Add the live `Mời các bác ăn sáng #Buffet` lightweight video-card fixture and prove its exact-card `watch?v=1547652190157533` identity remains reportable and scoped.
- [x] 1.3 Add session coverage proving an unreportable initial card triggers bounded continuation, emits only a later canonical `page.cards`, and never emits an unsolicited action receipt.

## 2. Edge Continuation

- [x] 2.1 Reuse the existing bounded feed-scroll routine when initial settling returns no reportable cards but the homepage probe returns `cards_ready`.
- [x] 2.2 Preserve confirmed-empty, loading, unknown, login, and captcha behavior while changing diagnostics to distinguish unreportable cards from an empty homepage.

## 3. Validation and Delivery

- [x] 3.1 Run focused Facebook reader/session tests, acceptance tests, the full Edge suite, and Edge typecheck.
  <!-- Edge validation: focused reader/session 70/70; acceptance 26/26; full suite 2047/2047 on the rebased `origin/master`; `npm run typecheck`; `git diff --check`. The startup regression includes one delayed round where `scrollHeight` grows before the later card hydrates. -->
- [x] 3.2 Run read-only live CDP validation on Mi Xu for the exact `watch?v=1547652190157533` video card and a visible unreportable lightweight card without performing Facebook interactions.
  <!-- Live read-only evidence: Mi Xu (`k1es035u`) exposed `Đưa Béo Vlog` / `Mời các bác ăn sáng #Buffet… Xem thêm` as `https://www.facebook.com/watch?v=1547652190157533`, `isVideo=true`; the visible `Trầm Hương Phúc Tử Vi` lightweight media-only card exposed only `/` and `/photo/?fbid=...` identities and correctly yielded no reportable card. No Facebook write interaction was performed. -->
- [x] 3.3 Validate the OpenSpec change strictly and record Edge/control commits, validations, delivery target, and deviations in this task file.
  <!-- Delivery: `aidcp-edge` commit `154f406` was fast-forwarded to `origin/master`; control artifacts were introduced by commit `96d7e39` and this closeout commit. `openspec validate facebook-feed-unreportable-card-continuation --strict` passed after rebasing both repos. This is an Edge source/runtime behavior fix: no Cloud/protocol change, no ECS deployment, no desktop installer/package, and no Facebook write interaction. -->
