# Facebook Post-Challenge Logged-In Probe Findings

Date: 2026-07-06

Probe environment:

- AdsPower profile: `k1ebny3j`
- State: operator manually completed the Meta reCAPTCHA login challenge
- Probe artifacts: `/tmp/aidcp-fb-post-challenge-probe-2026-07-06T03-42-59-644Z`
- Probe mode: read-only DOM and target inspection; no comment submit, no storage value reads

No credentials, cookies, tokens, localStorage values, sessionStorage values, IndexedDB values, or comment content were saved.

## Summary

After the operator completed the human-verification challenge, the tested Facebook pages entered a logged-in candidate state:

- no `/login/`, `/checkpoint/`, or `/two_step_verification/` URL
- no `fbsbx.com/captcha` or `google.com/recaptcha` frame
- no email/password/login form
- account/menu-like controls and profile-link candidates were present
- Page and permalink targets exposed visible comment controls and `contenteditable` textboxes

This is still only `logged_in_candidate`, not full `account_verified`, because the probe intentionally did not persist a raw Facebook id. A production identity probe must resolve a stable non-display-name-only id and store only the approved account identity representation.

## Observed States

| Key | URL | Classification | Notable Signals |
| --- | --- | --- | --- |
| `home_after_challenge` | `https://www.facebook.com/` | `logged_in_candidate` | No login form; account/menu-like controls present; `fbsbx` non-captcha iframe present. |
| `page_meta` | `https://www.facebook.com/Meta` | `logged_in_candidate` | Two visible comment textboxes with `aria-label="写评论…"`. |
| `page_post_permalink` | Meta post permalink | `logged_in_candidate` | One visible comment textbox with `aria-label="写评论…"`. |
| `group_post` | Facepager group post permalink | `logged_in_candidate` with membership caveat | One visible textbox with `aria-label="输入回答…"` and a visible `加入` control. |

## Detector Results

All probed targets after challenge completion showed:

- `urlLogin=false`
- `urlCheckpoint=false`
- `urlTwoStep=false`
- `hasCaptchaFrame=false`
- `hasRecaptchaFrame=false`
- `hasEmailInput=false`
- `hasPasswordInput=false`
- `hasLoginForm=false`
- `hasHumanVerificationText=false`

All probed targets still showed `hasFbsbxFrame=true`. This should not be treated as captcha by itself. The blocking detector should match `fbsbx.com/captcha`, not every `fbsbx.com` frame. A non-captcha `fbsbx` frame should be recorded as a diagnostic signal.

## Editor Shape

### Public Page Feed

Observed on `https://www.facebook.com/Meta`:

- visible editors: `2`
- editor tag/role: `div[contenteditable="true"][role="textbox"]`
- editor aria label: `写评论…`
- comment action controls included: `发表评论`, `查看更多评论`, `回复`

### Public Page Permalink

Observed on the Meta permalink:

- visible editors: `1`
- editor tag/role: `div[contenteditable="true"][role="textbox"]`
- editor aria label: `写评论…`
- comment action controls included: `发表评论`, `回复`

This is the best candidate for the next read-only editor focus/type/clear probe, because it is a single-post surface.

### Public Group Post

Observed on the Facepager group post:

- visible editors: `1`
- editor tag/role: `div[contenteditable="true"][role="textbox"]`
- editor aria label: `输入回答…`
- visible action controls included: `加入`, `发表评论`, `回复`

Do not treat this as group-comment readiness yet. The visible `加入` control means membership status is not proven. Group support needs a membership/permission classifier before any submit attempt.

## Storage-Safe Summary

The probe recorded only counts:

- localStorage count: `11-12`
- sessionStorage count: `1-3`
- IndexedDB database count: `22`
- Cache count: `0`

These counts prove storage exists after login, but they are not identity proof and must not be used as raw session material.

## Follow-Up Requirements

1. Implement `login_challenge_required` detection before any navigation-heavy probe.
2. Implement stable identity resolution; keep display-name-only results as honest failure.
3. Implement read-only editor focus/type/clear probe on a Page permalink first.
4. Add a group membership/permission classifier; visible `加入` must block group submit.
5. Keep gated submit disabled until a disposable operator-controlled target URL is available.
