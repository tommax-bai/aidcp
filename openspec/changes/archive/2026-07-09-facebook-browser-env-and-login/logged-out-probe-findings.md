# Facebook Logged-Out Probe Findings

Date: 2026-07-06

Probe environment:

- AdsPower profile: `k1ebny3j`
- AdsPower group: `aidcp-probe`
- Profile name: `FB Probe - 2026-07-06`
- Auth state: not logged in
- Probe artifacts: `/tmp/aidcp-fb-logged-out-probe-v2`
- Screenshots: `/tmp/aidcp-fb-logged-out-probe-v2/*.png`

No Facebook credentials, cookies, tokens, localStorage values, or IndexedDB values were saved in this repo.

## Summary

The logged-out Facebook surface has at least three distinct states that must not be collapsed into a single "login page" boolean:

1. Pure login page: the home page, explicit login page, and some redirected targets show only the login experience.
2. Public content with login overlay: Page and some post URLs render public content behind a modal/login rail while still requiring login for account-scoped actions.
3. Login redirect with `next`: some URLs redirect to `/login/?next=<encoded-target>`.

For comment automation, all three states are "not actionable". A visible post container is not proof that the account is logged in or that the comment editor is available.

## Observed States

| Key | Requested URL | Final URL | Result |
| --- | --- | --- | --- |
| `home` | `https://www.facebook.com/` | `https://www.facebook.com/` | Pure login page. |
| `login` | `https://www.facebook.com/login/` | `https://www.facebook.com/login/` | Pure login page. |
| `checkpoint` | `https://www.facebook.com/checkpoint/` | `https://www.facebook.com/` | Logged-out direct checkpoint route normalized to home login. |
| `page_meta` | `https://www.facebook.com/Meta` | `https://www.facebook.com/Meta` | Public Page content visible with login form/modal. |
| `page_posts` | `https://www.facebook.com/Meta/posts` | `https://www.facebook.com/Meta/` | Canonicalized to Page landing with login form/modal. |
| `page_post_permalink` | Meta post permalink | same permalink | Public post content visible with login form/modal. |
| `story_legacy` | `https://www.facebook.com/story.php?...` | `https://www.facebook.com/login/?next=...` | Login redirect with `next`. |
| `group_landing` | `https://www.facebook.com/groups/facepagerusers` | `https://www.facebook.com/login/?next=...` | Group landing login redirect with `next`. |
| `group_post` | `https://www.facebook.com/groups/facepagerusers/posts/1038125326805326/` | same permalink | Public group post content visible with login form/modal. |

## Detector Implications

### Pure login page

Use a combined URL and DOM classifier:

- `location.href` contains `/login/`, or
- `form#login_form` exists with `input[name="email"]` and `input[name="pass"]`, and
- there are no content articles (`[role="article"]` count is `0`), and
- account recovery or registration affordances are present.

Observed examples:

- `home`: `forms=1`, `roleArticle=0`, `contenteditable=0`
- `login`: `forms=1`, `roleArticle=0`, `contenteditable=0`
- `story_legacy`: redirected to `/login/?next=...`
- `group_landing`: redirected to `/login/?next=...`

### Public content with login overlay

Do not treat visible posts as logged-in readiness. The logged-out Page and group-post pages showed:

- login inputs present: `input[name="email"]`, `input[name="pass"]`
- login form action: `/login/device-based/regular/login/?login_attempt=1`
- dialog count: `1`
- content articles visible: `[role="article"] > 0`
- comment editor absent: `[contenteditable="true"] == 0`

Observed examples:

- `page_meta`: `roleArticle=4`, `forms=2`, `contenteditable=0`
- `page_post_permalink`: `roleArticle=7`, `forms=1`, `contenteditable=0`
- `group_post`: `roleArticle=4`, `forms=2`, `contenteditable=0`

This state should return a blocking reason such as `login_required_public_content`, not `no_target`.

### Checkpoint

Directly opening `/checkpoint/` while logged out redirected to the home login page, so the logged-out baseline does not provide a real checkpoint UI.

The runtime classifier should still fail closed when the current URL contains `/checkpoint`, but F2 must capture a real checkpoint/blocking state from a logged-in or challenged disposable account before gated submit is considered safe.

### Locale

The probe returned Simplified Chinese UI. Text detectors must not be English-only.

Useful observed labels include:

- `登录`
- `邮箱或手机号`
- `密码`
- `忘记密码了？`
- `创建新账户`
- `加入`
- `评论`

The first detector implementation should prefer stable DOM and URL signals, then use multilingual text as a secondary signal.

## Login Trigger Design

For pure login pages, no extra trigger is needed; the current page already contains the login form.

For public content pages, the observed login link is:

```text
https://www.facebook.com/login/device-based/regular/login/?login_attempt=1&next=<encoded-current-target>
```

Observed examples:

- `page_meta`: `/login/device-based/regular/login/?login_attempt=1&next=https%3A%2F%2Fwww.facebook.com%2FMeta`
- `group_post`: `/login/device-based/regular/login/?login_attempt=1&next=https%3A%2F%2Fwww.facebook.com%2Fgroups%2Ffacepagerusers%2Fposts%2F1038125326805326%2F`

Preferred trigger order:

1. If a visible login anchor with `next=<current-target>` exists, click or navigate to that href.
2. Else navigate to `https://www.facebook.com/login/?next=<encoded-current-target>`.
3. After manual login, re-open the original target URL and re-run identity, blocking, and editor probes.

The driver must record the original target URL before login trigger. Successful login is not inferred from navigation alone; it requires identity resolution and absence of login/checkpoint/blocking overlays.

## Page Structure Notes

- `/Meta/posts` canonicalized to `/Meta/`.
- Some `story.php` permalinks redirected directly to login with `next`.
- A group post URL with a custom group slug exposed a numeric group id in article links:
  - requested: `/groups/facepagerusers/posts/1038125326805326/`
  - observed canonical group id candidate: `136224396995428`
  - observed timestamp/multi permalink pattern: `/groups/136224396995428/?multi_permalinks=1038125326805326`

For group URLs, the probe should extract both the requested slug URL and any numeric group id candidates from timestamp or group header links.

## Follow-Up Probe Requirements

Before implementation is considered ready for comments:

1. Run the same detector against a manually logged-in disposable account.
2. Capture the logged-in Page/post/group editor shape without submitting.
3. Capture a real checkpoint or temporarily-blocked state if possible; otherwise keep F2 as not passed.
4. Run gated submit only on `FB_GATED_TEST_POST_URL` with explicit operator approval and server-confirmed verification.
