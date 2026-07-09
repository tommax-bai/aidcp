# Facebook Phase-0 F3 Observation Runbook

Date: 2026-07-06

Purpose: collect low-frequency AdsPower/CDP stability evidence for F3 without turning the probe itself into high-frequency automation.

F3 is passed only after repeated read-only observations across several calendar days show that the disposable Facebook AdsPower profile can start, attach, classify cleanly, read a stable identity signal, and stop cleanly without checkpoint/login/captcha regression.

## Scope

Profile:

- logged-in disposable profile: `k1ebny3j`
- profile name: `FB Probe - 2026-07-06`

Probe:

- edge worktree: `/Users/baitianxing/codes/aidcp-edge.wt/facebook-browser-env-and-login`
- runner: `test/manual/facebook-phase0-probe.ts`
- target URL: `https://www.facebook.com/`
- mode: read-only
- forbidden actions: password entry, 2FA, checkpoint solving, editor typing, submit/send, reaction/follow/join/post actions

## Cadence

- Run at most one counted F3 sample per calendar day.
- Prefer at least 20 hours between counted samples.
- Same-day reruns are allowed only to diagnose a local tooling failure and MUST NOT be counted as a separate F3 stability day.
- A conservative pass needs at least 3 counted samples on distinct calendar days, with no checkpoint/login/captcha regression and no provider lifecycle failure.

## Command

Run from the edge worktree:

```bash
cd /Users/baitianxing/codes/aidcp-edge.wt/facebook-browser-env-and-login

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="/tmp/aidcp-fb-f3-${STAMP}.json"

curl -sS 'http://local.adspower.net:50325/api/v1/browser/active?user_id=k1ebny3j'

AIDCP_ADS_USER_ID=k1ebny3j \
AIDCP_FB_PROBE_OUT="$OUT" \
npx tsx test/manual/facebook-phase0-probe.ts

node - "$OUT" <<'NODE'
const fs = require('fs');
const p = process.argv[2];
const r = JSON.parse(fs.readFileSync(p, 'utf8'));
const summary = {
  generatedAt: r.generatedAt,
  profileId: r.profileId,
  targetUrl: r.targetUrl,
  finalUrl: r.finalUrl,
  overlay: r.overlay,
  identityOk: r.identity?.ok,
  accountIdHash: r.identity?.accountIdHash,
  providerKind: r.providerKind,
  webdriverExposed: r.fingerprint?.webdriverExposed,
  language: r.fingerprint?.language,
  timezone: r.fingerprint?.timezone,
  pluginsLength: r.fingerprint?.pluginsLength,
  localStorageCount: r.storage?.localStorage?.count,
  sessionStorageCount: r.storage?.sessionStorage?.count,
  indexedDBCount: r.storage?.indexedDB?.count,
  cacheStorageCount: r.storage?.cacheStorage?.count,
  cookieMetadataCount: r.storage?.cookies?.length,
  surface: r.pageStructure?.surface,
  articleCount: r.pageStructure?.articleCount,
  gatedSubmitReason: r.gatedSubmitPreflight?.reason,
};
console.log(JSON.stringify(summary, null, 2));
NODE

rg -n '__cft__|permalinkHrefs|SECRET_CONTEXT|rawSecret|cookieValue|password|access_token|Authorization|Bearer' "$OUT" || true

rm -f "$OUT"

curl -sS 'http://local.adspower.net:50325/api/v1/browser/active?user_id=k1ebny3j'
```

If `npx tsx` fails because project dependencies are missing, run `npm ci` in the edge worktree and rerun the probe. Do not commit `node_modules`.

## Counted Sample Criteria

A sample can count toward F3 only when all of these are true:

- profile status before probe is `Inactive`
- runner exits with code `0`
- final URL is a normal Facebook route for the requested target
- overlay classification is `none`
- identity probe succeeds and the account id hash matches the expected disposable profile hash
- `navigator.webdriver === false`
- provider is `adspower`
- gated submit preflight is `disabled`
- no editor probe ran
- no blocking/F2 URL probe ran
- profile status after stop is `Inactive`
- temporary JSON is deleted after a safe summary is recorded
- committed notes contain no credentials, cookie values, raw storage values, raw storage key names, raw IndexedDB/cache names, raw Facebook account id, user names, or post body text

## Failure and Non-Count Conditions

Fail closed and do not continue to scheduled-comment work if a counted run observes:

- `overlay` is `login`, `captcha`, or `unknown`
- identity cannot be read or resolves to a different hash
- `navigator.webdriver === true`
- browser stop leaves the profile `Active`
- Facebook redirects to checkpoint/two-step/account recovery during the read-only sample
- the redaction grep finds forbidden raw fields in the temporary JSON

Do not count the sample, but treat it as an operational issue, if:

- AdsPower local API is unreachable
- profile is already `Active` before the probe
- `browser/start` fails because another machine/user is occupying the profile
- local dependencies are missing before the runner touches AdsPower/Facebook

## Recording Template

Append a new dated subsection to `phase0-live-probe-findings.md`:

````markdown
### Day-N Read-Only Sample

Timestamp:

```text
<ISO timestamp>
```

Profile `k1ebny3j`:

- profile status before probe: `<Inactive|...>`
- probe target: `https://www.facebook.com/`
- final URL: `<final URL shape>`
- overlay classification: `<none|login|captcha|unknown>`
- identity probe: `<stable id present, hash ... | failure reason>`
- fingerprint sanity:
  - provider `adspower`
  - stealth `false`
  - `navigator.webdriver === <false|true>`
  - language `<language>`
  - timezone `<timezone>`
  - plugins length `<n>`
- storage shape:
  - localStorage count `<n>`
  - sessionStorage count `<n>`
  - IndexedDB count `<n>`
  - cacheStorage count `<n>`
  - cookie metadata count `<n>`
- page surface: `<surface>`
- visible article count: `<n>`
- gated submit preflight: `disabled`
- profile status after probe stop: `<Inactive|...>`

Safety check:

- Local grep over `<tmp path>` found no forbidden raw fields.
- The temporary JSON report was deleted after this summary was recorded.

Interpretation:

- `<counted toward F3 | not counted because ...>`
````

After adding the note, run:

```bash
cd /Users/baitianxing/codes/aidcp
openspec validate facebook-browser-env-and-login --strict
```

Do not mark F3 complete until the multi-day count criteria are met.
