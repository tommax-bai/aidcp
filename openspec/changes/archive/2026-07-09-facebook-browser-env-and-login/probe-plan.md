# Facebook Probe Plan

## AdsPower Environment

- Group: `aidcp-probe`
- Profile name: `FB Probe - 2026-07-06`
- Profile user_id: `k1ebny3j`
- Serial number: `17`
- Status: `unverified`
- Proxy: none configured in AdsPower at creation time
- Template: `win11-intel`
- Intended account label: `facebook-probe-disposable`

This environment was created through the existing AdsPower write allowlist (`user/create`) and is not production-ready. Before any real Facebook probe, the operator must configure proxy/network as needed, open the profile, and manually log in a disposable Facebook account. Do not store cookies, passwords, tokens, or 2FA material in repo artifacts.

## Probe URL Matrix

### Login and Blocking Classification

Use these to verify URL/location and page-text classification before any account-scoped action.

- `https://www.facebook.com/`
  - Purpose: baseline landing/home/login-wall classification.
- `https://www.facebook.com/login/`
  - Purpose: explicit login-wall classification.
- `https://www.facebook.com/checkpoint/`
  - Purpose: URL-pattern checkpoint classification. This may render differently, but the route itself must be fail-closed.
- `https://www.facebook.com/Meta/posts/facebook-privacy-checkup-puts-you-in-charge-of-privacy-security-ad-preferences-a/670097992346081/`
  - Purpose: observed public fetch can redirect to login and expose "temporarily blocked" copy; useful for block-text detector tests.

### Public Page Shape

Use these read-only. Do not submit comments on third-party public pages.

- `https://www.facebook.com/Meta`
  - Purpose: Page landing/timeline layout, page identity, tabs, first-screen post containers.
- `https://www.facebook.com/Meta/posts`
  - Purpose: Page posts list route, infinite list hydration, post-card shape.
- `https://www.facebook.com/Meta/posts/meta-ai-is-built-into-all-our-apps-and-new-tech-meta-leads-the-way-on-social-and/833823022640243/`
  - Purpose: Page post permalink shape, article/post boundary, comments region, permalink/id candidates.
- `https://www.facebook.com/story.php?id=100044561550831&story_fbid=1235234580681413`
  - Purpose: legacy `story.php?id=...&story_fbid=...` permalink shape; confirms canonicalization and post-id extraction fallback.

### Public Group Shape

Use these read-only. Treat group membership prompts, login walls, and permission walls as honest blocking outcomes.

- `https://www.facebook.com/groups/facepagerusers`
  - Purpose: public/custom group landing, feed/list shape, membership/prompt classification.
- `https://www.facebook.com/groups/facepagerusers/posts/1038125326805326/`
  - Purpose: group post permalink with custom group slug.
- `https://www.facebook.com/groups/spacehipsters/posts/27271475875803937/`
  - Purpose: second group post sample to compare permalink/post container shape.

When a group uses a custom web address, the probe should try to discover the numeric group id from an accessible overview/page state and record whether the canonical URL can be normalized to `/groups/<numeric-id>/posts/<post-id>/`.

### Gated Submit Target

Do not use public Meta/NASA/group posts for gated submit. F1 must use a disposable-account-controlled target:

- `FB_GATED_TEST_POST_URL=<operator-created disposable post URL>`
  - Recommended target: a post created by the disposable account or a test Page/Group controlled by the operator.
  - Required before gated submit: explicit env flag, target URL, disposable account login, and confirmation that posting there is acceptable.
  - Success criterion: server-confirmed comment id/permalink or delayed reload/requery proof on the same target post; optimistic DOM row alone is not success.

## First Probe Order

1. Start `k1ebny3j` manually in AdsPower and log in a disposable Facebook account.
2. Run storage-safe summary probe on `https://www.facebook.com/`.
3. Run fingerprint/provider sanity probe.
4. Run login/blocking classifier against the login/checkpoint URL set.
5. Run read-only Page structure probes.
6. Run read-only Group structure probes.
7. Run comment editor probe without submit.
8. Only after 1-7 are clean, run gated submit on `FB_GATED_TEST_POST_URL`.

## Source Notes

- Facebook group post links are commonly obtained by clicking the group post timestamp; for groups with custom addresses, replace the custom slug with the numeric group id for the complete post link.
- Buffer documents that automatic Facebook Group posting via Meta API is no longer available after API changes and falls back to notification publishing; this supports treating browser probes as the only viable group path for this change.
