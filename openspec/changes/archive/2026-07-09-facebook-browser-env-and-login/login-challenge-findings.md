# Facebook Login Challenge Findings

Date: 2026-07-06

Probe environment:

- AdsPower profile: `k1ebny3j`
- Trigger phase: manual login after opening `https://www.facebook.com/login/`
- Challenge observed: Meta human verification backed by Google reCAPTCHA Enterprise
- User handling: operator solved it manually

No credentials, verification answers, cookies, tokens, localStorage values, or IndexedDB values were saved.

## Observation

During manual login, Facebook opened a challenge route under:

```text
/two_step_verification/authentication/
```

The page embedded reCAPTCHA targets, including:

```text
https://www.fbsbx.com/captcha/recaptcha/iframe/...
https://www.google.com/recaptcha/enterprise/...
```

After the operator handled the challenge, the page returned to `https://www.facebook.com/`, while an `fbsbx.com/maw_proxy_page` iframe was still visible in the CDP target list. This should be treated as a potential challenge residue until the main page is re-verified by identity and blocking probes.

## Likely Causes

This challenge is expected for early Facebook support and should not be considered an implementation bug by itself. Likely contributing signals:

- New AdsPower profile with no trusted Facebook device history.
- No proxy configured at profile creation time; network/IP may differ from the account's normal environment.
- Browser fingerprint, locale, timezone, WebRTC, network, and device signals may not form a sufficiently trusted combination yet.
- Account trust may be low due to new account status, low activity, recent device/location changes, or prior login attempts.
- The driver attempted read-only navigation before proving the challenge flow had fully cleared; future probes must fail closed earlier.

## Required Runtime Classification

The Facebook driver must classify these as blocking states before any account-scoped read/write action:

- URL contains `/two_step_verification/`
- URL contains `/checkpoint/`
- Any frame URL contains `fbsbx.com/captcha`
- Any frame URL contains `google.com/recaptcha`
- Page text includes `进行人机身份验证`
- Page text includes `reCAPTCHA Enterprise`

Expected behavior when matched:

1. Return `login_challenge_required` or `captcha_required`.
2. Activate or report the blocked tab for manual operator handling.
3. Do not retry automatically.
4. Do not navigate through Page/Post/Group probe URLs.
5. Do not submit comments.
6. After operator completion, rerun identity, login/checkpoint, challenge-frame, and editor probes before considering the account actionable.

## Design Impact

The login detector cannot rely on "login button clicked" or the absence of the initial login form. A Facebook account is actionable only after all of these are true:

- no login form is visible,
- no `/two_step_verification/`, `/checkpoint/`, captcha, or recaptcha frame is present,
- identity probe resolves a stable non-display-name-only account id,
- target page probe exposes an expected editor/action surface for the intended operation.
