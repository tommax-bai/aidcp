# Facebook Phase-0 F1 Gated Submit Runbook

Date: 2026-07-06

Purpose: verify whether a disposable Facebook account can post a test comment on an operator-owned disposable target and distinguish optimistic local rendering from server-confirmed acceptance.

This runbook MUST NOT be used on public third-party posts, production accounts, or targets not controlled by the operator.

## Scope

Profile:

- logged-in disposable profile: `k1ebny3j`
- profile name: `FB Probe - 2026-07-06`

Probe:

- edge worktree: `/Users/baitianxing/codes/aidcp-edge.wt/facebook-browser-env-and-login`
- runner: `test/manual/facebook-phase0-probe.ts`
- mode: real gated submit
- verification: post comment, wait, reload target, then check whether the same marker text is visible after reload

Required operator input:

- `FB_GATED_TEST_POST_URL`: an operator-owned disposable Facebook post URL
- `FB_GATED_TEST_COMMENT`: a short disposable test comment, not a secret and not reused elsewhere

## Safety Gates

The runner will not attempt a real submit unless all of these are set:

- `AIDCP_FB_EXECUTE_GATED_SUBMIT=1`
- `AIDCP_FB_GATED_SUBMIT=1`
- `AIDCP_FB_DISPOSABLE_CONFIRMED=1`
- `AIDCP_FB_GATED_TARGET_URL=<operator-owned disposable post URL>`
- `AIDCP_FB_GATED_COMMENT_TEXT=<short disposable test comment>`

Do not combine F1 submit mode with:

- `AIDCP_FB_RUN_EDITOR_PROBE=true`
- `AIDCP_FB_RUN_F2=1`

The committed report MUST NOT include raw comment text. Record only the comment hash, booleans, labels, and stop reasons.

## Command

Run from the edge worktree:

```bash
cd /Users/baitianxing/codes/aidcp-edge.wt/facebook-browser-env-and-login

TARGET='<operator-owned disposable post URL>'
COMMENT='AIDCP disposable F1 probe <short unique suffix>'
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="/tmp/aidcp-fb-f1-${STAMP}.json"

curl -sS 'http://local.adspower.net:50325/api/v1/browser/active?user_id=k1ebny3j'

AIDCP_ADS_USER_ID=k1ebny3j \
AIDCP_FB_EXECUTE_GATED_SUBMIT=1 \
AIDCP_FB_GATED_SUBMIT=1 \
AIDCP_FB_DISPOSABLE_CONFIRMED=1 \
AIDCP_FB_GATED_TARGET_URL="$TARGET" \
AIDCP_FB_GATED_COMMENT_TEXT="$COMMENT" \
AIDCP_FB_PROBE_OUT="$OUT" \
npx tsx test/manual/facebook-phase0-probe.ts

node - "$OUT" <<'NODE'
const fs = require('fs');
const p = process.argv[2];
const r = JSON.parse(fs.readFileSync(p, 'utf8'));
const s = r.gatedSubmitProbe || {};
const summary = {
  generatedAt: r.generatedAt,
  profileId: r.profileId,
  targetUrl: r.targetUrl,
  finalUrl: r.finalUrl,
  overlay: r.overlay,
  identityOk: r.identity?.ok,
  accountIdHash: r.identity?.accountIdHash,
  preflightOk: r.gatedSubmitPreflight?.ok,
  submitOk: s.ok,
  submitReason: s.reason,
  submitted: s.submitted,
  serverConfirmed: s.serverConfirmed,
  markerHash: s.markerHash,
  editorFound: s.editorFound,
  focused: s.focused,
  permissionGated: s.permissionGated,
  markerAccepted: s.markerAccepted,
  submitControlObserved: s.submitControlObserved,
  submitControlLabel: s.submitControlLabel,
  optimisticVisible: s.optimisticVisible,
  reloadedVisible: s.reloadedVisible,
};
console.log(JSON.stringify(summary, null, 2));
NODE

rg -n '__cft__|permalinkHrefs|SECRET_CONTEXT|rawSecret|cookieValue|password|access_token|Authorization|Bearer' "$OUT" || true

rm -f "$OUT"

curl -sS 'http://local.adspower.net:50325/api/v1/browser/active?user_id=k1ebny3j'
```

## Pass Criteria

F1 can pass only when all of these are true:

- profile status before probe is `Inactive`
- runner exits with code `0`
- overlay classification is `none`
- identity probe succeeds and matches the expected disposable profile hash
- preflight result is `ok`
- `submitted === true`
- `serverConfirmed === true`
- `optimisticVisible === true`
- `reloadedVisible === true`
- no credential, raw storage, raw account id, raw user name, or raw comment text is committed
- temporary JSON is deleted after a safe summary is recorded

## Fail-Closed Conditions

F1 does not pass if:

- preflight refuses for any reason
- editor is missing, permission-gated, or cannot focus
- marker text is not accepted by the editor
- submit control is missing or disabled
- the probe submits but `reloadedVisible !== true`
- Facebook redirects to login/checkpoint/two-step/account recovery
- the redaction grep finds forbidden raw fields in the temporary JSON

If the probe submits but cannot confirm after reload, later automation MUST NOT report `commented`; it may only report an honest unconfirmed/unknown result until a better confirmation path is designed.

## Recording Template

Append a dated subsection to `phase0-live-probe-findings.md`:

````markdown
## F1 Gated Submit Probe

### Disposable Target Sample

Timestamp:

```text
<ISO timestamp>
```

Profile `k1ebny3j`:

- target: `<operator-owned disposable post URL shape, no private query params>`
- overlay classification: `<none|login|captcha|unknown>`
- identity probe: `<stable id present, hash ... | failure reason>`
- preflight: `<ok|reason>`
- submit result:
  - submitted: `<true|false>`
  - server confirmed: `<true|false>`
  - marker hash: `<hash>`
  - editor found: `<true|false>`
  - marker accepted: `<true|false>`
  - submit control observed: `<true|false>`
  - optimistic visible before reload: `<true|false>`
  - visible after reload: `<true|false>`

Safety check:

- No raw comment text, credentials, cookie values, storage values, raw storage key names, raw account id, user names, or post body text were recorded.
- Temporary JSON report was deleted after this summary was recorded.

Interpretation:

- `<F1 passed | F1 failed because ...>`
````

After adding the note, run:

```bash
cd /Users/baitianxing/codes/aidcp.wt/facebook-browser-env-and-login
openspec validate facebook-browser-env-and-login --strict
```

Do not mark F1 complete until an operator-owned disposable target sample is actually run and recorded.
