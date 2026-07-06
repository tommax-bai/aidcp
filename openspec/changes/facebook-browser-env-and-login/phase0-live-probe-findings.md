# Facebook Phase-0 Live Probe Findings

Date: 2026-07-06

Probe runner:

- edge branch: `codex/facebook-browser-env-and-login`
- manual runner: `test/manual/facebook-phase0-probe.ts`
- logged-in profile: `k1ebny3j` (`FB Probe - 2026-07-06`)
- logged-out F2 profile: `k1ecc0b2` (`FB F2 Logged-out Probe - 2026-07-06`)

No credentials, cookie values, raw storage values, raw storage key names, raw IndexedDB/cache names, raw Facebook account id, user names, or post body text were recorded in committed artifacts.

## Storage Redaction Correction

The first local-only baseline run showed that Facebook storage key/name strings can contain account-scoped numeric fragments or HMAC/token-like substrings. That invalidated the earlier assumption that raw key names were safe metadata.

Implementation correction:

- `localStorage`, `sessionStorage`, `IndexedDB`, and cache names now output only:
  - count
  - key/name hash
  - length bucket
  - contains-digit flag
  - token-like flag
- Page-structure permalinks now strip nonessential query/hash data such as tracking/context params.
- Raw internal `permalinkHrefs` is removed from final page-structure output.

Safety check:

- Local grep over generated `/tmp/aidcp-fb-phase0-*.json` reports found no `__cft__`, no `permalinkHrefs`, and no raw storage key/name sentinel strings. Cookie names such as `presence` can still appear as cookie names; cookie values are not output. The temporary JSON reports were deleted after findings were summarized.

## Logged-In Baseline

Target:

```text
https://www.facebook.com/Meta/posts/meta-ai-is-built-into-all-our-apps-and-new-tech-meta-leads-the-way-on-social-and/833823022640243/
```

Result summary:

- profile `k1ebny3j` launched through AdsPower and CDP.
- overlay classification: `none`
- identity probe: stable id present, recorded only as hash `8def0ee3fc55260f`
- fingerprint sanity:
  - provider `adspower`
  - stealth `false`
  - `navigator.webdriver === false`
  - language `zh-CN`
  - timezone `Asia/Shanghai`
  - plugins length `5`
- page surface: `page_post`
- gated submit preflight: `disabled`
- no editor input and no submit attempt were run in this baseline.

Observation:

- The Meta Page post did not expose a visible comment editor in the final safe baseline run. Earlier read-only editor probes had seen an editor on the same public Page post; this confirms editor availability can drift by session/layout/load state and must remain probed per target.

## F2 Blocking-State Probe

### Logged-In Profile

Profile `k1ebny3j`:

| Requested URL | Final URL shape | Classification |
| --- | --- | --- |
| `/login/` | `/home.php` | `none` |
| `/checkpoint/` | `/home.php` | `none` |
| `/two_step_verification/authentication/` | same route | `captcha` |

Interpretation:

- On an already logged-in profile, Facebook redirects direct login/checkpoint routes back to normal home; those redirects are not evidence of blocking.
- Direct `two_step_verification` remained on the route and was correctly classified as `captcha`.

### Logged-Out Profile

Profile `k1ecc0b2`:

| Requested URL | Final URL shape | Classification |
| --- | --- | --- |
| `/` | `/` | `login` |
| `/login/` | `/login/` | `login` |
| `/checkpoint/` | `/` | `login` |
| `/two_step_verification/authentication/` | same route | `captcha` |

Interpretation:

- Logged-out root and login routes fail closed as `login`.
- Direct checkpoint on a logged-out profile normalized to the root page but still failed closed as `login`, which is acceptable for account-scoped work.
- `two_step_verification` fails closed as `captcha`.

F2 result:

- Passed for the observed login and two-step/challenge states.
- No automated password, 2FA, or checkpoint solving was attempted.

## F3 Stability Observation

### Day-0 Read-Only Sample

Timestamp:

```text
2026-07-06T14:02:12.870Z
```

Profile `k1ebny3j`:

- profile status before probe: `Inactive`
- probe target: `https://www.facebook.com/`
- final URL: `https://www.facebook.com/`
- overlay classification: `none`
- identity probe: stable id present, recorded only as hash `8def0ee3fc55260f`
- fingerprint sanity:
  - provider `adspower`
  - stealth `false`
  - `navigator.webdriver === false`
  - language `zh-CN`
  - timezone `Asia/Shanghai`
  - plugins length `5`
- storage shape:
  - localStorage count `13`
  - sessionStorage count `1`
  - IndexedDB count `22`
  - cacheStorage count `0`
  - cookie metadata count `15`
- page surface: `home`
- visible article count: `3`
- gated submit preflight: `disabled`
- profile status after probe stop: `Inactive`

Safety check:

- Local grep over `/tmp/aidcp-fb-f3-day0-20260706T140132Z.json` found no `__cft__`, no `permalinkHrefs`, no synthetic raw secret markers, no `Authorization`, and no `Bearer`.
- The temporary JSON report was deleted after this summary was recorded.

Interpretation:

- This is a successful Day-0 low-frequency read-only sample.
- It does not pass F3 yet. F3 still requires several days of low-frequency observations without checkpoint or provider instability.

## Remaining Gates

- F1 is still blocked: no operator-owned disposable Facebook post URL has been supplied for a real submit and server-confirmation probe.
- F3 is still pending: current evidence is Day-0 read-only startup/attach plus earlier short single-run checks, not several days of low-frequency stability.
